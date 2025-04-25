import os
import yt_dlp
import asyncio
import time
from pyrogram import Client
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup  # Add this import
from .config import last_update_time, UPDATE_INTERVAL, active_downloads
from .helpers import (
    create_progress_bar,
    edit_status_message,
    cleanup_progress_state,
    get_user_download_path,
)
from replies import dl_text  # Assuming replies.py exists


async def get_video_info(url: str):
    """Fetches video title and thumbnail URL without downloading."""
    opts = {
        "cookiefile": "cookies.txt",
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
    }
    try:
        # Run yt-dlp in a separate thread to avoid blocking asyncio loop
        with yt_dlp.YoutubeDL(opts) as ydl:
            info_dict = await asyncio.to_thread(ydl.extract_info, url, download=False)
            title = info_dict.get("title", "Untitled Video")
            thumbnail_url = info_dict.get("thumbnail")
            video_id: str = info_dict.get("id")
            return title, thumbnail_url, video_id
    except yt_dlp.utils.DownloadError as e:
        # Handle specific yt-dlp errors (e.g., private video, unavailable)
        print(f"yt-dlp error fetching video info for {url}: {e}")
        if "Private video" in str(e):
            return "Private Video", None, None
        elif "Video unavailable" in str(e):
            return "Video Unavailable", None, None
        # Add more specific error checks if needed
        return None, None, None  # General fetch error
    except Exception as e:
        print(f"Unexpected error fetching video info for {url}: {e}")
        return None, None, None  # General error


async def get_playlist_info(url: str):
    """Fetches playlist information without downloading."""
    opts = {
        "cookiefile": "cookies.txt",
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,  # Don't extract video info for each video
        "ignoreerrors": True,  # Skip unavailable videos
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info_dict = await asyncio.to_thread(ydl.extract_info, url, download=False)
            if info_dict.get("_type") != "playlist":
                return None  # Not a playlist

            # Extract playlist info
            playlist_info = {
                "title": info_dict.get("title", "Unknown Playlist"),
                "uploader": info_dict.get("uploader", "Unknown"),
                "video_count": info_dict.get("playlist_count", 0),
                "entries": [],
            }

            # Get duration if available
            total_duration = 0
            for entry in info_dict.get("entries", []):
                if entry:
                    duration = entry.get("duration", 0)
                    total_duration += duration
                    playlist_info["entries"].append(
                        {
                            "title": entry.get("title", "Unknown Video"),
                            "duration": duration,
                            "id": entry.get("id"),
                            "url": entry.get("url")
                            or f"https://youtu.be/{entry.get('id')}",
                            "thumbnail": entry.get("thumbnail"),
                        }
                    )

            playlist_info["total_duration"] = total_duration
            return playlist_info

    except Exception as e:
        print(f"Error fetching playlist info: {e}")
        return None


def _run_yt_dlp_download(
    opts,
    url,
    loop,
    status_msg,
    user_mention,
    user_id,
    original_msg_id,
    cancel_button_markup: InlineKeyboardMarkup,  # Add markup parameter
):
    """Synchronous function to run yt-dlp download, designed for asyncio.to_thread."""

    filepath = None
    title = None
    extension = None
    user_download_dir = get_user_download_path(user_id)
    cancel_event = active_downloads.get(original_msg_id)

    def download_progress_hook(d):
        # Check for cancellation signal
        if cancel_event and cancel_event.is_set():
            # Use a specific exception type if yt-dlp allows interrupting downloads
            # For now, we raise a generic exception to stop the process.
            raise asyncio.CancelledError("Download cancelled by user.")

        if d["status"] == "downloading":
            message_id = status_msg.id
            chat_id = status_msg.chat.id
            current_time = time.time()

            if (
                current_time - last_update_time.get((chat_id, message_id), 0)
                > UPDATE_INTERVAL
            ):
                percentage_str = d.get("_percent_str", "0%").strip("%")
                try:
                    percentage_float = float(percentage_str)
                except ValueError:
                    percentage_float = 0.0

                speed = d.get("_speed_str", "N/A")
                eta = d.get("_eta_str", "N/A")
                total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                downloaded_bytes = d.get("downloaded_bytes", 0)

                progress_bar = create_progress_bar(percentage_float)
                total_mb = total_bytes / (1024 * 1024) if total_bytes else 0
                downloaded_mb = (
                    downloaded_bytes / (1024 * 1024) if downloaded_bytes else 0
                )

                progress_text = (
                    f"{dl_text}\n"
                    f"**By:** {user_mention}\n**User ID:** `{user_id}`\n\n"
                    f"**Progress:** {progress_bar} {percentage_float:.1f}%\n"
                    f"File Size: `{total_mb:.2f} MB`\n"
                )

                # Schedule the edit_status_message coroutine on the main event loop
                asyncio.run_coroutine_threadsafe(
                    edit_status_message(
                        status_msg, progress_text, reply_markup=cancel_button_markup
                    ),  # Pass markup here
                    loop,
                )
                # Update time locally in this thread to avoid race conditions if needed,
                # but primary check relies on main thread's last_update_time
                # last_update_time[(chat_id, message_id)] = current_time # Be cautious with shared state

        elif d["status"] == "finished":
            print(f"Download finished hook for {d.get('filename', 'N/A')}")
            # Cleanup progress state from the main loop
            # asyncio.run_coroutine_threadsafe(
            #     cleanup_progress_state(status_msg.chat.id, status_msg.id), loop
            # ) # Cleanup happens after download completes anyway

    opts["progress_hooks"] = [download_progress_hook]
    opts["outtmpl"] = os.path.join(user_download_dir, "%(title)s_%(id)s.%(ext)s")

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            title = info_dict.get("title", "untitled")
            extension = "mp4"  # Due to postprocessor
            base_filepath = ydl.prepare_filename(info_dict).rsplit(".", 1)[0]
            filepath = f"{base_filepath}.{extension}"

            # Check if file exists after download and potential remuxing
            if not os.path.exists(filepath):
                original_ext = info_dict.get("ext")
                original_filepath = f"{base_filepath}.{original_ext}"
                print(
                    f"Expected final file {filepath} not found. Checking original: {original_filepath}"
                )
                if os.path.exists(original_filepath):
                    print(
                        f"Original file {original_filepath} found, but remuxed file {filepath} is missing."
                    )
                    # This might indicate an issue with FFmpeg post-processing
                    # Try finding *any* mp4 file with the ID as a fallback
                    found_fallback = False
                    for file in os.listdir(user_download_dir):
                        if info_dict.get("id") in file and file.endswith(".mp4"):
                            filepath = os.path.join(user_download_dir, file)
                            print(
                                f"Found matching mp4 file via fallback search: {filepath}"
                            )
                            found_fallback = True
                            break
                    if not found_fallback:
                        raise FileNotFoundError(
                            f"Remuxed file missing and no fallback MP4 found for video {info_dict.get('id')}"
                        )
                else:
                    # If neither exists, the download likely failed silently or was interrupted before file creation
                    raise FileNotFoundError(
                        f"Neither original ({original_filepath}) nor remuxed ({filepath}) file found. Download may have failed."
                    )

    except asyncio.CancelledError:
        print(f"Download for {url} cancelled by user.")
        # Clean up partially downloaded files if possible (yt-dlp might handle this)
        # Ensure filepath is None so it doesn't try to upload
        filepath = None
        raise  # Re-raise to signal cancellation upstream
    except Exception as download_err:
        print(f"Error during yt-dlp download/extraction for {url}: {download_err}")
        filepath = None  # Ensure filepath is None on error
        raise  # Re-raise the exception

    return filepath, title, extension


async def download_video_async(
    user_id: int,
    height: int,
    url: str,
    status_msg: Client.send_message,
    user_mention: str,
    original_msg_id: int,
    cancel_button_markup: InlineKeyboardMarkup,  # Add markup parameter
):
    """Asynchronously downloads a video using yt-dlp in a separate thread."""

    opts = {
        "cookiefile": "cookies.txt",
        "format": f"bestvideo[ext=mp4][height<={height}]+bestaudio[ext=m4a]/bestvideo[height<={height}]+bestaudio/best[height<={height}]/best",
        # "outtmpl" and "progress_hooks" are set in _run_yt_dlp_download
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }
        ],
        # Consider adding ffmpeg location if not in PATH
        # 'ffmpeg_location': '/path/to/ffmpeg',
    }

    loop = asyncio.get_running_loop()

    try:
        filepath, title, extension = await asyncio.to_thread(
            _run_yt_dlp_download,
            opts,
            url,
            loop,
            status_msg,
            user_mention,
            user_id,
            original_msg_id,
            cancel_button_markup,  # Pass markup here
        )
        return filepath, title, extension
    except asyncio.CancelledError:
        print(f"Download task for {url} received cancellation.")
        await edit_status_message(status_msg, f"Download cancelled by user for {url}")
        await asyncio.sleep(2)  # Give time for message edit
        # No need to re-raise CancelledError here, just return None
        return None, None, None
    except FileNotFoundError as fnf_err:
        print(f"File not found after download attempt for {url}: {fnf_err}")
        await edit_status_message(
            status_msg,
            f"Error: Download finished but output file not found.\n`{fnf_err}`",
        )
        return None, None, None
    except Exception as e:
        print(f"Error running download thread for {url}: {e}")
        # Try to edit the status message with the error
        error_text = f"Download failed for {url}.\nError: `{e}`"
        await edit_status_message(status_msg, error_text)
        return None, None, None
    finally:
        # Clean up cancellation event regardless of outcome
        active_downloads.pop(original_msg_id, None)
        # Clean up progress state
        cleanup_progress_state(status_msg.chat.id, status_msg.id)
