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
    print(f"Start command received from user {message.from_user.id}")
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
    print(f"Help command received from user {message.from_user.id}")

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
    print(f"About command received from user {message.from_user.id}")
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
    errors = []
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
                except PermissionError as pe:
                    print(f"PermissionError deleting {file_path}: {pe}")
                    errors.append(
                        f"Could not delete '{filename}': Permission denied (file might be in use)."
                    )
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
                    errors.append(f"Could not delete '{filename}': {e}")

            result_message = f"**__Cleanup complete.__**\n\n✅ Deleted {deleted_count} items."
            if errors:
                result_message += "\n\n⚠️ **Errors encountered:**\n" + "\n".join(errors)
            await deleting_msg.edit(result_message)
        else:
            await deleting_msg.edit("**__You have no downloaded videos to clean ✅__**")

    except Exception as e:
        print(f"Error during cleanup for user {user_id}: {e}")
        await deleting_msg.edit(f"**__An error occurred during cleanup:__**\n`{e}`")

    await asyncio.sleep(10)  # Increased sleep duration
    try:
        await message.delete()
        await deleting_msg.delete()
    except Exception:
        pass


async def _do_restart(client: Client):
    """Helper function to perform the actual stop and restart."""
    print("Stopping client for restart...")
    await client.stop()
    try:
        print("Executing restart...")
        os.execv(sys.executable, ["python"] + sys.argv)
    except Exception as e:
        print(f"FATAL: Failed to execute restart: {e}")
        sys.exit(1)


@bot.on_message(filters.command("restart") & filters.private)
async def restart_command(client: Client, message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if str(user_id) not in AUTH_USERS:
        await message.reply("⛔ You are not authorized to use this command.")
        return

    restarting_msg = await message.reply("🔄 **Restarting bot...**")
    print(f"Restart initiated by user {user_id} in chat {chat_id}")

    url_cache.clear()
    last_update_time.clear()
    for event in active_downloads.values():
        try:
            event.set()
        except RuntimeError as e:
            print(f"Ignoring error setting event: {e}")

    active_downloads.clear()

    await asyncio.sleep(1)

    try:
        await restarting_msg.edit("Bot is restarting now...")
        await asyncio.sleep(0.5)
        await restarting_msg.delete()
    except Exception as e:
        print(f"Error updating/deleting restart message: {e}")

    loop = asyncio.get_running_loop()
    loop.call_soon(lambda: asyncio.create_task(_do_restart(client)))
    print("Scheduled restart task. Handler finishing.")


# @bot.on_message(filters.command("exit") & filters.private)
# async def exit_command(client: Client, message):
#     user_id = message.from_user.id
#     if str(user_id) not in AUTH_USERS:
#         await message.reply("⛔ You are not authorized to use this command.")
#         return

#     shutting_msg = await message.reply("🛑 **Shutting down bot...**")
#     print(f"Shutdown initiated by user {user_id}")
#     await asyncio.sleep(1)
#     try:
#         await shutting_msg.edit("Bot is going offline now...")
#     except Exception as e:
#         print(f"Error editing shutdown message: {e}")

#     loop = asyncio.get_running_loop()
#     loop.call_soon(lambda: asyncio.create_task(client.stop()))
#     print("Scheduled stop task. Handler finishing.")


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
    if not ("youtu" in url or "youtube" in url):
        print(f"Ignoring non-YouTube URL passed regex: {url}")
        return

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

        url_cache[message.id] = url

        keyboard = get_resolution_buttons(message.id)
        caption = f"🎬 **{title}**\n\n{VIDEO_HEIGHT_TEXT}"

        send_method = message.reply_photo if thumbnail_url else message.reply
        kwargs = {"caption": caption, "reply_markup": keyboard}
        if thumbnail_url:
            kwargs["photo"] = thumbnail_url
        else:
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
        url_cache.pop(message.id, None)


# --- Callback Query Handler ---


@bot.on_callback_query()
async def handle_callback_query(client: Client, callbackQuery: CallbackQuery):
    user = callbackQuery.from_user
    user_id = user.id
    data = callbackQuery.data
    message = callbackQuery.message
    filepath = None  # Initialize filepath outside try block
    original_msg_id = 0  # Initialize outside try block
    status_msg = None  # Initialize outside try block
    chat_id = message.chat.id if message else None  # Initialize chat_id

    # --- Retry Start Logic ---
    if data == "retry_start":
        await callbackQuery.answer("Checking membership again...")
        if await check_membership(client, user_id):
            try:
                await message.delete()
            except Exception:
                pass
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

    # --- Cancel Logic (Handles cancellation from resolution buttons AND status message) ---
    if data.startswith("cancel:"):
        try:
            original_msg_id = int(data.split(":", 1)[1])
            url = url_cache.pop(
                original_msg_id, None
            )  # Remove url from cache if cancelled
            cancel_event = active_downloads.get(original_msg_id)
            if cancel_event:
                cancel_event.set()  # Signal the download/upload task to stop
                print(
                    f"Cancellation signal sent for download/upload related to message {original_msg_id}"
                )
                active_downloads.pop(
                    original_msg_id, None
                )  # Clean up active download entry

            # Try to delete the message where the cancel button was clicked
            try:
                await message.delete()
            except Exception as del_err:
                print(f"Could not delete message during cancel: {del_err}")

            await callbackQuery.answer("✅ Request cancelled.")
            print(
                f"Cancelled request for message {original_msg_id} by user {user_id} ({user.first_name})"
            )

        except Exception as e:
            print(f"Error handling cancel callback: {e}")
            await callbackQuery.answer("⚠️ Error cancelling request.", show_alert=True)
        return

    # --- Resolution Selection & Download/Upload Logic ---
    if (
        ":" in data
        and data.split(":", 1)[0].isdigit()
        and data.split(":", 1)[1].isdigit()
    ):
        # Check membership again before proceeding
        if not await check_membership(client, user_id):
            await callbackQuery.answer(
                "🔒 Please join the required channels first and click Retry.",
                show_alert=True,
            )
            return

        try:
            height_str, original_msg_id_str = data.split(":", 1)
            height = int(height_str)
            original_msg_id = int(
                original_msg_id_str
            )  # Get the ID of the message that triggered the download

            # Check if the request is still valid (URL exists in cache)
            url = url_cache.get(original_msg_id)
            if not url:
                await callbackQuery.answer(
                    "⌛ Request expired or bot restarted. Please send the link again.",
                    show_alert=True,
                )
                try:
                    await message.delete()  # Delete the resolution selection message
                except Exception:
                    pass
                return

            # Acknowledge the button press
            await callbackQuery.answer("⏳ Processing your request...")
            try:
                await message.delete()  # Delete the resolution selection message
            except Exception:
                pass

            # --- Setup Cancellation ---
            cancel_event = asyncio.Event()
            active_downloads[original_msg_id] = (
                cancel_event  # Store the event using the original message ID
            )

            # --- Create Cancel Button Markup ---
            cancel_button_markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "❌ Cancel", callback_data=f"cancel:{original_msg_id}"
                        )
                    ]
                ]
            )

            # --- Send Initial Status Message (with Cancel Button) ---
            status_msg = await client.send_message(
                chat_id,
                f"{dl_text}\n**By:** {user.mention}\n**User ID:** `{user_id}`",
                reply_markup=cancel_button_markup,  # Add cancel button here
            )
            last_update_time[(chat_id, status_msg.id)] = (
                time.time()
            )  # Initialize update time

            # --- Start Download ---
            filepath, title, extension = await download_video_async(
                user_id,
                height,
                url,
                status_msg,
                user.mention,
                original_msg_id,
                cancel_button_markup,  # Pass the markup here
            )

            # --- Check for Cancellation or Download Failure ---
            if cancel_event.is_set():
                print(f"Download cancelled by user for {url}.")
                cleanup_progress_state(chat_id, status_msg.id)
                try:
                    await edit_status_message(status_msg, "❌ Download cancelled.")
                    await asyncio.sleep(5)
                    await status_msg.delete()
                except Exception as e:
                    print(
                        f"Error updating/deleting status message after download cancel: {e}"
                    )
                return  # Stop processing

            if not filepath:
                print(f"Download failed for {url}. Filepath is None.")
                # Error message should be handled within download_video_async or caught by the main exception block
                # Ensure cleanup if status_msg exists
                if status_msg:
                    cleanup_progress_state(chat_id, status_msg.id)
                return  # Stop processing

            # --- Download Complete, Prepare Upload ---
            cleanup_progress_state(
                chat_id, status_msg.id
            )  # Clean download progress state
            await edit_status_message(
                status_msg,
                f"✅ **Download complete.** Preparing upload...",
                reply_markup=cancel_button_markup,  # Keep cancel button during preparation
            )
            await asyncio.sleep(1)  # Brief pause

            # Re-initialize last update time for upload progress
            last_update_time[(chat_id, status_msg.id)] = time.time()

            # --- Upload Progress Callback ---
            async def upload_progress(current, total):
                # Check for cancellation signal during upload
                if cancel_event.is_set():
                    print(
                        "Upload cancellation signal received during progress callback."
                    )
                    # Attempt to stop the upload (Pyrogram might handle this with CancelledError)
                    raise asyncio.CancelledError("Upload cancelled by user.")

                if total == 0:
                    return
                message_id = status_msg.id
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
                loop = asyncio.get_running_loop()
                # Edit message with progress AND the cancel button
                asyncio.run_coroutine_threadsafe(
                    edit_status_message(
                        status_msg,
                        progress_text,
                        reply_markup=cancel_button_markup,  # Pass markup here
                    ),
                    loop,
                )

            # --- Start Upload ---
            await edit_status_message(
                status_msg,
                f"{upl_text}\n**By:** {user.mention}\n**User ID:** `{user_id}`",
                reply_markup=cancel_button_markup,  # Ensure cancel button is present at start of upload
            )

            send = await client.send_video(
                chat_id=chat_id,
                video=filepath,
                reply_markup=InlineKeyboardMarkup(
                    DL_COMPLETE_BUTTON
                ),  # Final message buttons
                caption=f"✅ **Hey** {user.mention}\n{DL_COMPLETE_TEXT.format(url)}\n\nVia @{client.me.username}",
                file_name=f"{title}.{extension}",
                supports_streaming=True,
                progress=upload_progress,
            )

            # --- Upload Complete ---
            cleanup_progress_state(
                chat_id, status_msg.id
            )  # Clean upload progress state
            await status_msg.delete()  # Delete the status message

            # --- Logging ---
            log_caption = f"**Filename:**\n`{title}.{extension}`\n\n**User:** {user.mention}\n**ID:** `{user_id}`"

            # Forward to LOG_CHANNEL
            if LOG_CHANNEL:
                try:
                    log_channel_id = int(LOG_CHANNEL)  # Ensure it's an int
                    await bot.forward_messages(log_channel_id, chat_id, send.id)
                except (ValueError, PeerIdInvalid) as log_err:
                    print(
                        f"Error forwarding to LOG_CHANNEL ({LOG_CHANNEL}): {log_err}. Check ID and bot membership."
                    )
                except Exception as fwd_err:
                    print(
                        f"Unexpected error forwarding message to {LOG_CHANNEL}: {fwd_err}"
                    )

            # Send info to LINK_LOGS
            if LINK_LOGS:
                try:
                    link_log_id = int(LINK_LOGS)  # Ensure it's an int
                    url_LOG_BUTTON = [[InlineKeyboardButton("URL 🔗", url=url)]]
                    await bot.send_message(
                        link_log_id,
                        log_caption,
                        reply_markup=InlineKeyboardMarkup(url_LOG_BUTTON),
                    )
                except (ValueError, PeerIdInvalid) as log_err:
                    print(
                        f"Error sending to LINK_LOGS ({LINK_LOGS}): {log_err}. Check ID and bot membership."
                    )
                except Exception as log_err:
                    print(
                        f"Unexpected error sending link log to {LINK_LOGS}: {log_err}"
                    )

        # --- General Exception Handling ---
        except asyncio.CancelledError:
            print(
                f"Upload cancelled explicitly for user {user_id}, original message {original_msg_id}."
            )
            if status_msg:
                try:
                    cleanup_progress_state(status_msg.chat.id, status_msg.id)
                    await edit_status_message(status_msg, "❌ Upload cancelled.")
                    await asyncio.sleep(5)
                    await status_msg.delete()
                except Exception as e:
                    print(
                        f"Error updating/deleting status message after upload cancel: {e}"
                    )

        except Exception as e:
            print(
                f"Error in callback handler for user {user_id}, data '{data}': {type(e).__name__} - {e}"
            )
            error_message = f"⚠️ {user.mention}, an error occurred processing your request.\n\n`{type(e).__name__}: {e}`"
            if status_msg:
                try:
                    cleanup_progress_state(status_msg.chat.id, status_msg.id)
                    # Edit status message without cancel button on error
                    await edit_status_message(status_msg, error_message)
                except Exception as edit_err:
                    print(f"Failed to edit status message on error: {edit_err}")
                    # Fallback to sending a new message if editing fails
                    await client.send_message(
                        chat_id,
                        error_message,
                        reply_to_message_id=(
                            original_msg_id if original_msg_id else None
                        ),
                    )
            else:
                # Send error message if status_msg was never created
                await client.send_message(
                    chat_id,
                    error_message,
                    reply_to_message_id=original_msg_id if original_msg_id else None,
                )
            try:
                # Acknowledge the callback query even on error
                await callbackQuery.answer("⚠️ An error occurred.", show_alert=True)
            except Exception:
                pass  # Ignore if answering fails (e.g., query expired)

        # --- Final Cleanup ---
        finally:
            # Add a small delay before attempting file deletion
            await asyncio.sleep(2)  # Wait 2 seconds

            # Remove downloaded file if it exists
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"Removed file: {filepath}")
                except PermissionError as pe:
                    print(
                        f"PermissionError removing file {filepath}: {pe}. File might still be locked."
                    )
                except OSError as rm_err:
                    print(f"Error removing file {filepath}: {rm_err}")

            # Clean up caches and active download state associated with the original message ID
            if original_msg_id:
                url_cache.pop(original_msg_id, None)
                active_downloads.pop(
                    original_msg_id, None
                )  # Ensure removal on success, error, or cancel
            # Clean up progress state if status_msg exists (redundant but safe)
            if status_msg and chat_id:  # Check chat_id exists
                cleanup_progress_state(chat_id, status_msg.id)

    # --- Fallback for Unrecognized Callbacks ---
    else:
        await callbackQuery.answer(
            "Button action not recognized or expired.", show_alert=True
        )
