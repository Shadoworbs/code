import os
import sys
import asyncio
import time
import shutil
import re
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, PeerIdInvalid

from .bot_instance import bot
from .config import (
    LOG_CHANNEL,
    LINK_LOGS,
    AUTH_USERS,
    url_cache,
    last_update_time,
    UPDATE_INTERVAL,
    active_downloads,
)
from .helpers import (
    check_membership,
    get_membership_buttons,
    get_resolution_buttons,
    create_progress_bar,
    edit_status_message,
    cleanup_progress_state,
    get_user_download_path,
)
from .downloader import get_video_info, download_video_async
from replies import *  # Assuming replies.py exists and contains text variables
from buttons import (
    START_BUTTON,
    ABOUT_BUTTON,
    DL_COMPLETE_BUTTON,
)  # Assuming buttons.py exists

# --- Command Handlers ---


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


@bot.on_message(filters.command("clean") & filters.private)
async def clean_directory(client: Client, message):
    user_id = message.from_user.id
    user_download_dir = get_user_download_path(user_id)  # Use helper
    deleting_msg = await message.reply(
        f"**__Deleting your videos in directory 🗑__** (`{user_download_dir}`)"
    )
    deleted_count = 0
    try:
        if os.path.isdir(user_download_dir):
            # Use shutil.rmtree for simplicity if deleting the whole user dir is acceptable
            # shutil.rmtree(user_download_dir)
            # deleted_count = 'all' # Or count files before deleting if needed
            # Or keep the file-by-file approach:
            for filename in os.listdir(user_download_dir):
                file_path = os.path.join(user_download_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                        deleted_count += 1
                    elif os.path.isdir(
                        file_path
                    ):  # Should ideally not happen with current structure
                        shutil.rmtree(file_path)
                        deleted_count += 1  # Count directory as one item
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
            await deleting_msg.edit(
                f"**__Your {deleted_count} videos/files removed successfully ✅__**"
            )
        else:
            await deleting_msg.edit("**__You have no downloaded videos to clean ✅__**")

    except Exception as e:
        print(f"Error during cleanup for user {user_id}: {e}")
        await deleting_msg.edit(f"**__An error occurred during cleanup:__**\n`{e}`")

    # Auto-delete messages after a delay
    await asyncio.sleep(5)
    try:
        await message.delete()
        await deleting_msg.delete()
    except Exception:
        pass  # Ignore if messages are already gone


@bot.on_message(filters.command("restart") & filters.private)
async def restart_command(client: Client, message):
    user_id = message.from_user.id
    if str(user_id) not in AUTH_USERS:
        await message.reply("⛔ You are not authorized to use this command.")
        return

    restarting_msg = await message.reply("🔄 **Restarting bot...**")
    print(f"Restart initiated by user {user_id}")

    # Clean up cache before restart (optional)
    url_cache.clear()
    last_update_time.clear()
    # Signal any active downloads to cancel (optional, might be complex)
    # for event in active_downloads.values():
    #     event.set()

    await asyncio.sleep(2)  # Short delay

    try:
        await restarting_msg.edit("Bot is restarting now. Please wait a moment.")
    except Exception as e:
        print(f"Error editing restart message: {e}")

    # Stop the client gracefully before exiting
    await client.stop()

    # Execute the script again, replacing the current process
    try:
        print("Executing restart...")
        os.execv(sys.executable, ["python"] + sys.argv)
    except Exception as e:
        print(f"FATAL: Failed to execute restart: {e}")
        # If execv fails, try to exit normally
        sys.exit(1)  # Exit with error code


@bot.on_message(filters.command("exit") & filters.private)
async def exit_command(client: Client, message):
    user_id = message.from_user.id
    if user_id not in AUTH_USERS:
        await message.reply("⛔ You are not authorized to use this command.")
        return

    shutting_msg = await message.reply("🛑 **Shutting down bot...**")
    print(f"Shutdown initiated by user {user_id}")
    await asyncio.sleep(2)
    try:
        await shutting_msg.edit("Bot is now offline.")
    except Exception as e:
        print(f"Error editing shutdown message: {e}")

    print("Stopping Pyrogram client...")
    await client.stop()
    print("Exiting process.")
    sys.exit(0)  # Clean exit


# --- URL Handler ---


@bot.on_message(
    filters.regex(
        r"(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+(watch\?v=|embed/|v/|.+\?v=)?([^&\n]{11})",
        re.IGNORECASE,
    )
    & filters.private
)
async def youtube_url_handler(client: Client, message):
    user_id = message.from_user.id
    if not await check_membership(client, user_id):
        await message.reply(
            text=membership_fail_text.format(mention=message.from_user.mention),
            reply_markup=get_membership_buttons(),
            disable_web_page_preview=True,
        )
        return

    url = message.text.strip()
    # Basic validation if regex didn't catch everything
    if not ("youtu" in url or "youtube" in url):
        print(f"Ignoring non-YouTube URL passed regex: {url}")
        return  # Should not happen with the refined regex

    processing_msg = await message.reply("⏳ Processing link...")
    try:
        title, thumbnail_url = await get_video_info(url)

        if title is None:
            await processing_msg.edit_text(
                "❌ Sorry, couldn't fetch video details. The link might be invalid, private, or unavailable."
            )
            return
        elif title == "Private Video" or title == "Video Unavailable":
            await processing_msg.edit_text(f"❌ **{title}**. Cannot download.")
            return

        # Store URL with message ID as key
        url_cache[message.id] = url

        keyboard = get_resolution_buttons(message.id)  # Use helper
        caption = f"🎬 **{title}**\n\n{VIDEO_HEIGHT_TEXT}"  # Use VIDEO_HEIGHT_TEXT from replies

        send_method = message.reply_photo if thumbnail_url else message.reply
        kwargs = {"caption": caption, "reply_markup": keyboard}
        if thumbnail_url:
            kwargs["photo"] = thumbnail_url
        else:
            # If no thumbnail, send as text message
            send_method = message.reply_text
            kwargs = {
                "text": caption,
                "reply_markup": keyboard,
                "disable_web_page_preview": True,
            }

        await send_method(**kwargs)
        await processing_msg.delete()

    except Exception as e:
        print(f"Error processing YouTube URL {url}: {e}")
        await processing_msg.edit_text(
            f"⚠️ An error occurred while processing the link:\n`{e}`"
        )
        url_cache.pop(message.id, None)  # Clean cache on error


# --- Callback Query Handler ---


@bot.on_callback_query()
async def handle_callback_query(client: Client, callbackQuery: CallbackQuery):
    user = callbackQuery.from_user
    user_id = user.id
    data = callbackQuery.data
    message = callbackQuery.message  # The message where the button was clicked

    # --- Retry Start ---
    if data == "retry_start":
        await callbackQuery.answer("Checking membership again...")
        if await check_membership(client, user_id):
            try:
                await message.delete()  # Delete the "join channels" message
            except Exception:
                pass
            # Find the original /start message to reply to (might be tricky/not possible directly)
            # Instead, just send a new start message
            await client.send_message(
                chat_id=user_id,
                text=f"{start_text.format(user.mention)}",
                reply_markup=InlineKeyboardMarkup(START_BUTTON),
                disable_web_page_preview=True,
            )
        else:
            await callbackQuery.answer(
                "❌ You still need to join the required channels.", show_alert=True
            )
        return

    # --- Cancel Download ---
    if data.startswith("cancel:"):
        try:
            original_msg_id = int(data.split(":", 1)[1])
            url = url_cache.pop(original_msg_id, None)  # Remove from cache
            # Signal cancellation if download is active
            cancel_event = active_downloads.get(original_msg_id)
            if cancel_event:
                cancel_event.set()
                print(
                    f"Cancellation signal sent for download related to message {original_msg_id}"
                )

            await message.delete()
            await callbackQuery.answer("✅ Request cancelled.")
            print(f"Cancelled request for message {original_msg_id} by user {user_id}")
        except Exception as e:
            print(f"Error handling cancel callback: {e}")
            await callbackQuery.answer("⚠️ Error cancelling request.", show_alert=True)
        return

    # --- Resolution Selection ---
    if (
        ":" in data
        and data.split(":", 1)[0].isdigit()
        and data.split(":", 1)[1].isdigit()
    ):
        if not await check_membership(client, user_id):
            await callbackQuery.answer(
                "🔒 Please join the required channels first and click Retry.",
                show_alert=True,
            )
            return

        status_msg = None
        filepath = None
        original_msg_id = 0  # Initialize

        try:
            height_str, original_msg_id_str = data.split(":", 1)
            height = int(height_str)
            original_msg_id = int(
                original_msg_id_str
            )  # ID of the user's original message with the link
            chat_id = message.chat.id

            url = url_cache.get(original_msg_id)  # Get URL without popping yet
            if not url:
                await callbackQuery.answer(
                    "⌛ Request expired or bot restarted. Please send the link again.",
                    show_alert=True,
                )
                try:
                    await message.delete()  # Delete the resolution button message
                except Exception:
                    pass
                return

            await callbackQuery.answer("⏳ Processing your request...")
            try:
                # Delete the resolution selection message
                await message.delete()
            except Exception:
                pass

            # Create a cancellation event for this download
            cancel_event = asyncio.Event()
            active_downloads[original_msg_id] = cancel_event

            # Send initial status message
            status_msg = await client.send_message(
                chat_id, f"{dl_text}\n**By:** {user.mention}\n**User ID:** `{user_id}`"
            )
            last_update_time[(chat_id, status_msg.id)] = (
                time.time()
            )  # Initialize progress timer

            # Start download
            filepath, title, extension = await download_video_async(
                user_id, height, url, status_msg, user.mention, original_msg_id
            )

            # Check if download was successful (filepath is not None) or cancelled
            if not filepath:
                print(f"Download failed or was cancelled for {url}. Filepath is None.")
                # Status message should have been updated in download_video_async
                # Clean up cache entry if it wasn't already
                url_cache.pop(original_msg_id, None)
                # No need to delete status_msg here, it shows the final status (error/cancelled)
                return  # Stop processing here

            # --- Upload Process ---
            cleanup_progress_state(
                chat_id, status_msg.id
            )  # Clean download progress state
            await edit_status_message(
                status_msg, f"✅ **Download complete.** Preparing upload..."
            )
            await asyncio.sleep(1)  # Brief pause

            # Prepare upload progress tracking
            last_update_time[(chat_id, status_msg.id)] = (
                time.time()
            )  # Reset timer for upload

            async def upload_progress(current, total):
                if total == 0:
                    return
                message_id = status_msg.id
                # Use the same edit_status_message helper for consistency
                percentage = current * 100 / total
                progress_bar = create_progress_bar(percentage)
                current_mb = current / (1024 * 1024)
                total_mb = total / (1024 * 1024)
                progress_text = (
                    f"{upl_text}\n"  # Use upl_text from replies
                    f"**By:** {user.mention}\n**User ID:** `{user_id}`\n\n"
                    f"**Progress:** {progress_bar} {percentage:.1f}%\n"
                    f"`{current_mb:.2f} MB / {total_mb:.2f} MB`"
                )
                # Schedule edit in case upload_progress runs in a different context (though usually not for pyrogram)
                # await edit_status_message(status_msg, progress_text) # Direct await should be fine
                # Safer approach:
                loop = asyncio.get_running_loop()
                asyncio.run_coroutine_threadsafe(
                    edit_status_message(status_msg, progress_text), loop
                )

            await edit_status_message(
                status_msg,
                f"{upl_text}\n**By:** {user.mention}\n**User ID:** `{user_id}`",
            )

            # Send the video
            send = await client.send_video(
                chat_id=chat_id,
                video=filepath,
                reply_markup=InlineKeyboardMarkup(
                    DL_COMPLETE_BUTTON
                ),  # Use DL_COMPLETE_BUTTON from buttons
                # Pass url as a positional argument assuming DL_COMPLETE_TEXT uses {}
                caption=f"✅ **Hey** {user.mention}\n{DL_COMPLETE_TEXT.format(url)}\n\nVia @{client.me.username}",
                file_name=f"{title}.{extension}",
                # reply_to_message_id=original_msg_id, # Replying to original link msg can be noisy
                supports_streaming=True,
                progress=upload_progress,
            )

            cleanup_progress_state(
                chat_id, status_msg.id
            )  # Clean upload progress state
            await status_msg.delete()  # Delete the status message

            # --- Logging ---
            log_caption = f"**Filename:**\n`{title}.{extension}`\n\n**User:** {user.mention}\n**ID:** `{user_id}`"
            if LINK_LOGS:
                try:
                    link_log_id = int(LINK_LOGS)  # Ensure it's an int
                    url_LOG_BUTTON = [
                        [InlineKeyboardButton("Original URL 🔗", url=url)]
                    ]
                    await bot.send_message(
                        link_log_id,
                        log_caption,
                        reply_markup=InlineKeyboardMarkup(url_LOG_BUTTON),
                    )
                except ValueError:
                    print(
                        f"Error: LINK_LOGS ('{LINK_LOGS}') is not a valid integer chat ID."
                    )
                except PeerIdInvalid:
                    print(
                        f"Error: LINK_LOGS peer ID ({LINK_LOGS}) invalid. Ensure the bot is a member and has interacted with the chat."
                    )
                except Exception as log_err:
                    print(f"Error sending link log to {LINK_LOGS}: {log_err}")

            if LOG_CHANNEL:
                try:
                    log_channel_id = int(LOG_CHANNEL)  # Ensure it's an int
                    await bot.forward_messages(log_channel_id, chat_id, send.id)
                except ValueError:
                    print(
                        f"Error: LOG_CHANNEL ('{LOG_CHANNEL}') is not a valid integer chat ID."
                    )
                except PeerIdInvalid:
                    print(
                        f"Error: LOG_CHANNEL peer ID ({LOG_CHANNEL}) invalid. Ensure the bot is a member and has interacted with the chat."
                    )
                except Exception as fwd_err:
                    print(f"Error forwarding message to {LOG_CHANNEL}: {fwd_err}")

        except Exception as e:
            print(f"Error in callback handler for user {user_id}, data '{data}': {e}")
            error_message = (
                f"⚠️ {user.mention}, an error occurred processing your request.\n\n`{e}`"
            )
            if status_msg:
                try:
                    cleanup_progress_state(status_msg.chat.id, status_msg.id)
                    await status_msg.edit_text(error_message)
                except Exception:
                    # Fallback if editing status fails
                    await client.send_message(
                        chat_id,
                        error_message,
                        reply_to_message_id=(
                            original_msg_id if original_msg_id else None
                        ),
                    )
            else:
                # Send error as a new message if status_msg wasn't created
                await client.send_message(
                    chat_id,
                    error_message,
                    reply_to_message_id=original_msg_id if original_msg_id else None,
                )
            try:
                # Try to answer callback query even on error
                await callbackQuery.answer("⚠️ An error occurred.", show_alert=True)
            except Exception:
                pass  # Ignore if answering fails

        finally:
            # --- Cleanup ---
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"Removed file: {filepath}")
                except OSError as rm_err:
                    print(f"Error removing file {filepath}: {rm_err}")
            # Clean up cache and active download state
            if original_msg_id:
                url_cache.pop(original_msg_id, None)
                active_downloads.pop(original_msg_id, None)
            if status_msg:
                cleanup_progress_state(status_msg.chat.id, status_msg.id)

    else:
        # Handle unrecognized button clicks
        await callbackQuery.answer(
            "Button action not recognized or expired.", show_alert=True
        )


# --- Register Handlers (Optional, can be done in main script) ---
# Pyrogram automatically discovers handlers if they are defined using the decorator
# on an imported Client instance (`bot` in this case).
