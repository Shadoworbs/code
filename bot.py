######################
###### Youtube  ######
######################

# importing main modules
import sys
import asyncio
import time
from pyrogram import Client, filters
import os
import yt_dlp
from datetime import datetime
import shutil
from dotenv import load_dotenv
from pyrogram.types import (
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)


from pyrogram import enums

# Import PeerIdInvalid
from pyrogram.errors import FloodWait, UserNotParticipant, PeerIdInvalid
import logging
from replies import *
from buttons import START_BUTTON, ABOUT_BUTTON, DL_COMPLETE_BUTTON, MEMBERSHIP_BUTTONS

# --- Constants ---
PROGRESS_BAR_LENGTH = 12  # Length of the progress bar
UPDATE_INTERVAL = 5  # Seconds between progress updates

load_dotenv()
api_id = os.getenv("api_id")
api_hash = os.getenv("api_hash")
bot_token = os.getenv("bot_token")
LOG_CHANNEL = os.getenv("LOG_CHANNEL")
LINK_LOGS = os.getenv("LINK_LOGS")
AUTH_USERS = os.getenv("AUTH_USERS", "")
SOFTWARE_CHANNEL_ID = os.getenv("SOFTWARE_CHANNEL_ID")
MOVIE_CHANNEL_ID = os.getenv("MOVIE_CHANNEL_ID")
SOFTWARE_CHANNEL_LINK = os.getenv(
    "SOFTWARE_CHANNEL_LINK", "https://t.me/+sblvkmvCZ45hMTc0"
)
MOVIE_CHANNEL_LINK = os.getenv("MOVIE_CHANNEL_LINK", "https://t.me/+BdXh4y_MFqBhZTA0")

# --- Log the loaded Channel IDs ---
print(f"Loaded SOFTWARE_CHANNEL_ID: {SOFTWARE_CHANNEL_ID}")
print(f"Loaded MOVIE_CHANNEL_ID: {MOVIE_CHANNEL_ID}")
# --- End Log ---

cwd = os.getcwd()
BASE_DOWNLOAD_PATH = os.path.join(cwd, "downloads")
os.makedirs(BASE_DOWNLOAD_PATH, exist_ok=True)

url_cache = {}
last_update_time = {}

bot = Client(
    "bot_account", api_id=api_id, api_hash=api_hash, bot_token=bot_token, workers=16
)

now = datetime.now()


# --- Helper Function ---
def create_progress_bar(percentage: float, length: int = PROGRESS_BAR_LENGTH) -> str:
    """Creates a text-based progress bar."""
    if not 0 <= percentage <= 100:
        percentage = max(0, min(100, percentage))  # Clamp percentage
    filled_length = int(length * percentage // 100)
    bar = "█" * filled_length + "░" * (length - filled_length)
    return f"[{bar}]"


async def check_membership(client: Client, user_id: int):
    if not SOFTWARE_CHANNEL_ID or not MOVIE_CHANNEL_ID:
        print(
            "Warning: SOFTWARE_CHANNEL_ID or MOVIE_CHANNEL_ID not set. Skipping membership check."
        )
        return True
    try:
        # Ensure IDs are integers before using them
        soft_id = int(SOFTWARE_CHANNEL_ID)
        mov_id = int(MOVIE_CHANNEL_ID)
        await client.get_chat_member(chat_id=soft_id, user_id=user_id)
        await client.get_chat_member(chat_id=mov_id, user_id=user_id)
        return True
    except UserNotParticipant:
        return False
    # Catch PeerIdInvalid specifically
    except PeerIdInvalid:
        print(
            f"Error checking membership for user {user_id}: PEER_ID_INVALID. "
            f"Check if Channel IDs ({SOFTWARE_CHANNEL_ID}, {MOVIE_CHANNEL_ID}) are correct numerical IDs "
            f"and if the bot is a member/admin in both channels."
        )
        # Optionally, treat this as 'cannot check' -> allow access or deny based on policy
        return False  # Or True, depending on how you want to handle this failure
    except ValueError:
        print(
            f"Error: One or both Channel IDs ({SOFTWARE_CHANNEL_ID}, {MOVIE_CHANNEL_ID}) are not valid integers."
        )
        return False  # Cannot check membership if IDs are not integers
    except Exception as e:
        print(f"Error checking membership for user {user_id}: {e}")
        return False


def get_membership_buttons():
    buttons = [
        [
            InlineKeyboardButton("➡️ Software Channel", url=SOFTWARE_CHANNEL_LINK),
            InlineKeyboardButton("➡️ Movie Channel", url=MOVIE_CHANNEL_LINK),
        ],
        [InlineKeyboardButton("🔄 Retry", callback_data="retry_start")],
    ]
    return InlineKeyboardMarkup(buttons)


@bot.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message):
    user_id = message.from_user.id
    if not await check_membership(client, user_id):
        await message.reply(
            text=membership_fail_text.format(mention=message.from_user.mention),
            reply_markup=get_membership_buttons(),
            disable_web_page_preview=True,
        )
        return
    await message.reply(
        text=f"{start_text.format(message.from_user.mention)}",
        reply_markup=InlineKeyboardMarkup(START_BUTTON),
        disable_web_page_preview=True,
    )


@bot.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message):
    user_id = message.from_user.id
    if not await check_membership(client, user_id):
        await message.reply(
            text=membership_fail_text.format(mention=message.from_user.mention),
            reply_markup=get_membership_buttons(),
            disable_web_page_preview=True,
        )
        return
    await message.reply(help_text)


@bot.on_message(filters.command("about") & filters.private)
async def about_command(client: Client, message):
    user_id = message.from_user.id
    if not await check_membership(client, user_id):
        await message.reply(
            text=membership_fail_text.format(mention=message.from_user.mention),
            reply_markup=get_membership_buttons(),
            disable_web_page_preview=True,
        )
        return
    await message.reply(
        text="**💁 Some details about Me 💁**",
        reply_markup=InlineKeyboardMarkup(ABOUT_BUTTON),
        disable_web_page_preview=True,
    )


async def get_video_info(url):
    opts = {
        "cookiefile": "cookies.txt",
        "skip_download": True,
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=False)
            title = info_dict.get("title", "Untitled Video")
            thumbnail_url = info_dict.get("thumbnail")
            return title, thumbnail_url
        except yt_dlp.utils.DownloadError as e:
            print(f"Error fetching video info: {e}")
            return None, None


async def download_vid(
    user_id: int,
    height: int,
    url: str,
    status_msg: Client.send_message,
    user_mention: str,
):
    filepath = None
    title = None
    extension = None
    user_download_dir = os.path.join(BASE_DOWNLOAD_PATH, str(user_id))
    try:
        os.makedirs(user_download_dir, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory {user_download_dir}: {e}")
        raise

    # Create a synchronous progress hook that uses asyncio
    def download_progress_hook(d):
        if d["status"] == "downloading":
            message_id = status_msg.id
            chat_id = status_msg.chat.id
            current_time = time.time()

            # Increase update interval to prevent FloodWait
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
                    f"`{downloaded_mb:.2f} MB / {total_mb:.2f} MB`\n"
                    f"**Speed:** {speed}\n"
                    f"**ETA:** {eta}"
                )

                # Create task in event loop to edit message
                loop = asyncio.get_event_loop()

                async def update_message():
                    try:
                        await status_msg.edit_text(progress_text)
                        last_update_time[(chat_id, message_id)] = current_time
                    except FloodWait as fw:
                        # Log flood wait and wait slightly longer than suggested
                        print(
                            f"FloodWait during download progress: sleeping for {fw.value + 1}s"
                        )
                        await asyncio.sleep(fw.value + 1)
                    except Exception as e:
                        # Log other errors but allow potential recovery
                        print(f"Error editing download status message: {e}")
                        # Optionally reset time to allow quicker retry if it was temporary
                        # last_update_time[(chat_id, message_id)] = 0
                    finally:
                        # Ensure the time is updated even if an error occurred,
                        # to prevent rapid retries on persistent errors.
                        last_update_time[(chat_id, message_id)] = time.time()

                loop.create_task(update_message())

        elif d["status"] == "finished":
            print(f"Download finished for {d['filename']}")
            message_id = status_msg.id
            chat_id = status_msg.chat.id
            last_update_time.pop((chat_id, message_id), None)

    opts = {
        "cookiefile": "cookies.txt",
        # Prioritize mp4 format, then select best video with specified height (or lower) + best audio
        # Fallback to best available format if mp4 is not directly available
        "format": f"bestvideo[ext=mp4][height<={height}]+bestaudio[ext=m4a]/bestvideo[height<={height}]+bestaudio/best[height<={height}]/best",
        "outtmpl": os.path.join(user_download_dir, "%(title)s_%(id)s.%(ext)s"),
        "progress_hooks": [download_progress_hook],
        "quiet": True,
        "no_warnings": True,
        # Add postprocessor to ensure the final output is mp4
        "postprocessors": [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }
        ],
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=True)
            title = info_dict.get("title", "untitled")
            # Ensure the extension is mp4 due to the postprocessor
            extension = "mp4"
            # Construct the expected final filename after potential remuxing
            base_filepath = ydl.prepare_filename(info_dict).rsplit(".", 1)[0]
            filepath = f"{base_filepath}.{extension}"

            if not os.path.exists(filepath):
                # Check if the original downloaded file exists before remuxing
                original_ext = info_dict.get("ext")
                original_filepath = f"{base_filepath}.{original_ext}"
                if os.path.exists(original_filepath):
                    print(
                        f"Original file {original_filepath} found, but remuxed file {filepath} is missing."
                    )
                    # Attempt to find any mp4 file with the video ID if the constructed path fails
                    for file in os.listdir(user_download_dir):
                        if info_dict.get("id") in file and file.endswith(".mp4"):
                            filepath = os.path.join(user_download_dir, file)
                            print(f"Found matching mp4 file: {filepath}")
                            break
                    if not os.path.exists(filepath):
                        raise FileNotFoundError(
                            f"Downloaded file (expected: {filepath}) not found for video {info_dict.get('id')}"
                        )
                else:
                    raise FileNotFoundError(
                        f"Neither original ({original_filepath}) nor remuxed ({filepath}) file found."
                    )

        except Exception as download_err:
            print(f"Error during yt-dlp download/extraction: {download_err}")
            raise

    return filepath, title, extension


@bot.on_message(filters.regex(r"youtu\.be/|youtube\.com/") & filters.private)
async def check_youtube_urls(client: Client, message):
    user_id = message.from_user.id
    if not await check_membership(client, user_id):
        await message.reply(
            text=membership_fail_text.format(mention=message.from_user.mention),
            reply_markup=get_membership_buttons(),
            disable_web_page_preview=True,
        )
        return

    url = message.text
    if not ("youtu.be/" in url or "youtube.com/" in url) or "https://" not in url:
        return

    processing_msg = await message.reply("Processing link...")
    try:
        title, thumbnail_url = await get_video_info(url)

        if not title:
            await processing_msg.edit_text(
                "Sorry, couldn't fetch video details. Please check the link or it might be private/restricted."
            )
            return

        url_cache[message.id] = url

        resolutions = {"1080": "1080p", "720": "720p", "480": "480p", "360": "360p"}
        buttons = []
        for height, label in resolutions.items():
            callback_data = f"{height}:{message.id}"
            if len(callback_data.encode("utf-8")) <= 64:
                buttons.append(
                    [InlineKeyboardButton(label, callback_data=callback_data)]
                )
            else:
                print(
                    f"Warning: Callback data too long, skipping button: {callback_data}"
                )

        if not buttons:
            await processing_msg.edit_text("Could not generate resolution options.")
            return

        keyboard = InlineKeyboardMarkup(buttons)
        caption = f"**{title}**\n\n{VIDEO_HEIGHT_TEXT}"

        send_method = message.reply_photo if thumbnail_url else message.reply
        kwargs = {"caption": caption, "reply_markup": keyboard}
        if thumbnail_url:
            kwargs["photo"] = thumbnail_url
        else:
            kwargs["disable_web_page_preview"] = True

        await send_method(**kwargs)
        await processing_msg.delete()

    except Exception as e:
        print(f"Error processing YouTube URL {url}: {e}")
        await processing_msg.edit_text(f"An error occurred: {e}")


@bot.on_callback_query()
async def handle_callback_query(client: Client, callbackQuery: CallbackQuery):
    user = callbackQuery.from_user
    user_id = user.id
    data = callbackQuery.data

    if data == "retry_start":
        await callbackQuery.answer("Checking membership again...")
        if await check_membership(client, user_id):
            try:
                await callbackQuery.message.delete()
            except Exception:
                pass
            await start_command(client, callbackQuery.message)
        else:
            await callbackQuery.answer(
                "You still need to join the channels.", show_alert=True
            )
        return

    if filters.regex(r"^\d+:\d+$")(client, callbackQuery):
        if not await check_membership(client, user_id):
            await callbackQuery.answer(
                "Please join the required channels first and click Retry.",
                show_alert=True,
            )
            return

        status_msg = None
        filepath = None

        async def upload_progress(current, total):
            if total == 0:  # Avoid division by zero
                return
            message_id = status_msg.id
            chat_id = status_msg.chat.id
            current_time = time.time()
            # Increase update interval to prevent FloodWait
            if (
                current_time - last_update_time.get((chat_id, message_id), 0)
                > UPDATE_INTERVAL
            ):
                percentage = current * 100 / total
                progress_bar = create_progress_bar(percentage)
                current_mb = current / (1024 * 1024)
                total_mb = total / (1024 * 1024)

                progress_text = (
                    f"{upl_text}\n"
                    f"**By:** {user.mention}\n**User ID:** `{user_id}`\n\n"
                    f"**Progress:** {progress_bar} {percentage:.1f}%\n"
                    f"`{current_mb:.2f} MB / {total_mb:.2f} MB`"
                )
                try:
                    await status_msg.edit_text(progress_text)
                    last_update_time[(chat_id, message_id)] = current_time
                except FloodWait as fw:
                    print(
                        f"FloodWait during upload progress: sleeping for {fw.value + 1}s"
                    )
                    await asyncio.sleep(fw.value + 1)
                except Exception as e:
                    print(f"Error editing upload status message: {e}")
                    # Optionally reset time to allow quicker retry if it was temporary
                    # last_update_time[(chat_id, message_id)] = 0
                finally:
                    # Ensure the time is updated even if an error occurred,
                    # to prevent rapid retries on persistent errors.
                    last_update_time[(chat_id, message_id)] = time.time()

        try:
            height_str, original_msg_id_str = data.split(":", 1)
            height = int(height_str)
            original_msg_id = int(original_msg_id_str)
            chat_id = callbackQuery.message.chat.id

            url = url_cache.pop(original_msg_id, None)
            if not url:
                await callbackQuery.answer(
                    "Request expired or bot restarted. Send link again.",
                    show_alert=True,
                )
                try:
                    await callbackQuery.message.delete()
                except Exception:
                    pass
                return

            await callbackQuery.answer("Processing...")
            try:
                await callbackQuery.message.delete()
            except Exception:
                pass

            status_msg = await client.send_message(
                chat_id, f"{dl_text}\n**By:** {user.mention}\n**User ID:** `{user_id}`"
            )
            last_update_time[(chat_id, status_msg.id)] = time.time()

            filepath, title, extension = await download_vid(
                user_id, height, url, status_msg, user.mention
            )

            if not filepath or not os.path.exists(filepath):
                raise Exception("Download failed or file path not found.")

            last_update_time.pop((chat_id, status_msg.id), None)
            await status_msg.edit_text(f"**Download complete.** Preparing upload...")
            await asyncio.sleep(1)

            await status_msg.edit_text(
                f"{upl_text}\n**By:** {user.mention}\n**User ID:** `{user_id}`"
            )
            last_update_time[(chat_id, status_msg.id)] = time.time()

            send = await client.send_video(
                chat_id=chat_id,
                video=filepath,
                reply_markup=InlineKeyboardMarkup(DL_COMPLETE_BUTTON),
                caption=f"**Hey** {user.mention}\n{DL_COMPLETE_TEXT.format(url)}\nVia @{client.me.username}",
                file_name=f"{title}.{extension}",
                reply_to_message_id=original_msg_id,
                supports_streaming=True,
                progress=upload_progress,
            )

            last_update_time.pop((chat_id, status_msg.id), None)
            await status_msg.delete()

            url_LOG_BUTTON = [[InlineKeyboardButton("url 🔗", url=url)]]
            log_caption = f"**Filename:**\n`{title}.{extension}`\n\n**User:** {user.mention}\n**ID:** `{user_id}`"
            if LOG_CHANNEL:
                try:
                    await bot.forward_messages(LOG_CHANNEL, chat_id, send.id)
                except PeerIdInvalid:
                    print(
                        f"Error: LOG_CHANNEL peer ID invalid. Ensure the bot is a member and has interacted with the chat."
                    )
                except Exception as fwd_err:
                    print(f"Error forwarding message: {fwd_err}")

            if LINK_LOGS:
                try:
                    await bot.send_message(
                        LINK_LOGS,
                        log_caption,
                        reply_markup=InlineKeyboardMarkup(url_LOG_BUTTON),
                    )
                except PeerIdInvalid:
                    print(
                        f"Error: LINK_LOGS peer ID invalid. Ensure the bot is a member and has interacted with the chat."
                    )
                except Exception as log_err:
                    print(f"Error sending link log: {log_err}")

        except Exception as e:
            print(f"Error in callback handler for user {user_id}: {e}")
            error_message = f"{user.mention} **an error occurred.⚠️**\n\n`{e}`"
            if status_msg:
                try:
                    last_update_time.pop((status_msg.chat.id, status_msg.id), None)
                    await status_msg.edit_text(error_message)
                except Exception:
                    await client.send_message(
                        chat_id, error_message, reply_to_message_id=original_msg_id
                    )
            else:
                await client.send_message(
                    chat_id, error_message, reply_to_message_id=original_msg_id
                )
            try:
                await callbackQuery.answer("An error occurred.", show_alert=True)
            except Exception:
                pass

        finally:
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"Removed file: {filepath}")
                except OSError as rm_err:
                    print(f"Error removing file {filepath}: {rm_err}")
            if "original_msg_id" in locals():
                url_cache.pop(original_msg_id, None)
            if status_msg:
                last_update_time.pop((status_msg.chat.id, status_msg.id), None)

    else:
        await callbackQuery.answer(
            "Button action not recognized or expired.", show_alert=True
        )


@bot.on_message(filters.command("clean") & filters.private)
async def clean_directory(client: Client, message):
    user_id = message.from_user.id
    user_download_dir = os.path.join(BASE_DOWNLOAD_PATH, str(user_id))
    deleting_msg = await message.reply(
        f"**__Deleting your videos in directory 🗑__** (`{user_download_dir}`)"
    )
    deleted_count = 0
    try:
        if os.path.isdir(user_download_dir):
            for filename in os.listdir(user_download_dir):
                file_path = os.path.join(user_download_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                        deleted_count += 1
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        deleted_count += 1
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
            await deleting_msg.edit(
                f"**__Your {deleted_count} videos/files removed successfully ✅__**"
            )
        else:
            await deleting_msg.edit("**__You have no downloaded videos to clean ✅__**")

    except Exception as e:
        print(e)
        await deleting_msg.edit(f"**__An error occurred during cleanup:__**\n`{e}`")

    await asyncio.sleep(5)
    try:
        await message.delete()
        await deleting_msg.delete()
    except Exception:
        pass


@bot.on_message(filters.command("exit") & filters.private)
async def exit_command(client: Client, message):
    user_id = message.from_user.id
    if user_id not in AUTH_USERS:
        return await message.reply("You are not authorized to use this command.")

    shutting = await message.reply("Shutting down...")
    print("Shutting down the system...")
    await asyncio.sleep(2)
    await shutting.edit("Bot is now offline.")
    print("System off!")
    await client.stop()
    sys.exit()


print(f"\nBOT STARTED\n{now:%A, %d %B %Y}. {now:%H:%M}")
print(
    f"\nPython version {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n"
)
bot.run()
