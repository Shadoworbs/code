import os
import sys
import asyncio
import time
import shutil
import re
from pymongo import MongoClient
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
    convert_thumbnail_to_jpeg,
    count_bot_users,
    count_sudo_users,
    download_thumbnail_async,
    get_resolution_buttons,
    create_progress_bar,
    edit_status_message,
    cleanup_progress_state,
    get_user_download_path,
    create_user_document_in_mongodb,
    find_user_by_id_in_mongodb,
    add_a_sudo_user_to_the_db,
    find_sudo_user_by_id,
    remove_a_sudo_user_from_the_db,
    list_all_sudo_users,
    list_all_users
)
from .downloader import get_video_info, download_video_async
from replies import *  # Assuming replies.py exists and contains text variables
from buttons import (
    START_BUTTON,
    ABOUT_BUTTON,
    DL_COMPLETE_BUTTON,
)  # Assuming buttons.py exists


# --- MongoDB tools ---
async def mongo_check_user_database(
    userid: str, userdict=None, message=None
) -> bool:
    if find_user_by_id_in_mongodb(userid) == "False":
        # If user not found, create a new document in MongoDB for the user
        info: dict = {
            "_id": str(userdict.id),
            "date_time": message.date or "None",
            "fist_name": userdict.first_name or "None",
            "last_name": userdict.last_name or "None",
            "username": userdict.username or "None",
            "language_code": userdict.language_code or "None",
            "Dc_id": userdict.dc_id or "None",
            "is_premium": userdict.is_premium or "None",
            "is_verified": userdict.is_verified or "None",
            "message_body": message.text or "None",
            "message_id": message.id or "None",
            "chat_id": message.chat.id or "None",
            "chat_title": message.chat.title or "None",
            "chat_type": str(message.chat.type) or "None",
            "chat_username": message.chat.username or "None",
        }

        create_user_document_in_mongodb(info)
        return "True"
    return "False"


async def mongo_check_sudo_database(
    userid: str, userdict: dict=None, message=None
) -> bool:
    if not await find_sudo_user_by_id(userid):
        # If user not found, create a new document in MongoDB for the user
        info: dict = {
            "_id": str(userdict.id),
            "date_time": message.date or "None",
            "fist_name": userdict.first_name or "None",
            "last_name": userdict.last_name or "None",
            "username": userdict.username or "None",
            "language_code": userdict.language_code or "None",
            "Dc_id": userdict.dc_id or "None",
            "is_premium": userdict.is_premium or "None",
            "is_verified": userdict.is_verified or "None",
            "message_body": message.text or "None",
            "message_id": message.id or "None",
            "chat_id": message.chat.id or "None",
            "chat_title": message.chat.title or "None",
            "chat_type": str(message.chat.type) or "None",
            "chat_username": message.chat.username or "None"
            }

        await add_a_sudo_user_to_the_db(info)
        return "True"
    return "False"


# --- Command Handlers ---


@bot.on_message(filters.command("start"))
async def start_command(client: Client, message):
    user_id = str(message.from_user.id)
    userdict: dict = message.from_user
    await mongo_check_user_database(str(user_id), userdict, message)

    await message.reply(
        text=f"{start_text.format(message.from_user.mention)}",
        reply_markup=InlineKeyboardMarkup(START_BUTTON),
        disable_web_page_preview=True,
    )



@bot.on_message(filters.command("help"))
async def help_command(client: Client, message):

    user_id = str(message.from_user.id)
    userdict: dict = message.from_user
    await mongo_check_user_database(str(user_id), userdict, message)

    await message.reply(help_text)


@bot.on_message(filters.command("about"))
async def about_command(client: Client, message):
    user_id = str(message.from_user.id)
    userdict: dict = message.from_user
    await mongo_check_user_database(str(user_id), userdict, message)

    await message.reply(
        text="**💁 Some details about Me 💁**",
        reply_markup=InlineKeyboardMarkup(ABOUT_BUTTON),
        disable_web_page_preview=True,
    )


@bot.on_message(filters.command("clean"))
async def clean_directory(client: Client, message):
    user_id = str(message.from_user.id)
    userdict: dict = message.from_user
    await mongo_check_user_database(str(user_id), userdict, message)

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

            result_message = (
                f"**__Cleanup complete.__**\n\n✅ Deleted {deleted_count} items."
            )
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


@bot.on_message(filters.command("restart"))
async def restart_command(client: Client, message):
    user_id = str(message.from_user.id)
    userdict: dict = message.from_user
    mongo_check_user_database(str(user_id), userdict, message)
    chat_id = message.chat.id

    if user_id not in AUTH_USERS:
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


# --- URL Handler ---


@bot.on_message(
    filters.regex(
        r"(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+(watch\?v=|embed/|v/|.+\?v=)?([^&\n]{11})",
        re.IGNORECASE,
    )
)
async def youtube_url_handler(client: Client, message):
    user_id = str(message.from_user.id)
    userdict: dict = message.from_user
    await mongo_check_user_database(str(user_id), userdict, message)

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


##### Add a sudo user ########

@bot.on_message(filters.command("addsudo"))
async def add_sudo_user(client: Client, message):
    user_id = str(message.from_user.id)
    check_db_for_sudo_user = find_sudo_user_by_id(user_id)
    message_text: str = str(message.text).strip()
    if user_id not in AUTH_USERS and check_db_for_sudo_user == "False":
        not_authorized = await message.reply(
            "⛔ You are not authorized to use this command."
        )
        await asyncio.sleep(5)
        await not_authorized.delete()
        await message.delete()

    if (
        message.reply_to_message
        and find_sudo_user_by_id(str(message.reply_to_message.from_user.id)) == "False"
    ):
        user_to_add_info: dict = message.reply_to_message.from_user
        info: dict = {
            "_id": str(user_to_add_info.id) or "None",
            "date_time": message.reply_to_message.date or "None",
            "fist_name": user_to_add_info.first_name or "None",
            "last_name": user_to_add_info.last_name or "None",
            "username": user_to_add_info.username or "None",
            "language_code": user_to_add_info.language_code or "None",
            "Dc_id": user_to_add_info.dc_id or "None",
            "is_premium": user_to_add_info.is_premium or "None",
            "is_verified": user_to_add_info.is_verified or "None",
            "message_body": message.reply_to_message.text or "None",
            "message_id": message.reply_to_message.id or "None",
            "chat_id": message.chat.id or "None",
            "chat_title": message.chat.title or "None",
            "chat_type": str(message.chat.type) or "None",
            "chat_username": message.chat.username or "None",
        }
        add_a_sudo_user_to_the_db(info)
        await bot.send_message(f"{user_to_add_info.id} added as a Sudo user")
        await message.delete()
        return
    elif (
        message.reply_to_message
        and find_sudo_user_by_id(str(message.reply_to_message.from_user.id)) == "True"
    ):
        await message.reply("User already added.")
        return

    if (
        not message.reply_to_message
        and len(message.text.split(" ")) == 2
        and find_sudo_user_by_id(str(message.text.split(" ")[1].strip())) == "False"
    ):
        sudo_user_id: str = str(message_text).split(" ")[1]
        user_info = await bot.get_chat(sudo_user_id)
        info: dict = {
            "_id": sudo_user_id,
            "date_time": message.date,
            "fist_name": user_info.first_name,
            "last_name": user_info.last_name,
            "username": user_info.username,
        }
        add_a_sudo_user_to_the_db(info)
        await message.reply(f"{user_info.first_name} added as a Sudo user")
        return
    elif not message.reply_to_message and len(message.text.split(" ")) == 1:
        await message.reply("Please provide a user ID.")
    else:
        await message.reply("User already added.")


##### remove sudo user ########

@bot.on_message(filters.command("rmsudo"))
async def remove_sudo_user(client: Client, message):
    user_id = str(message.from_user.id)
    check_db_for_sudo_user = find_sudo_user_by_id(user_id)
    message_text: str = str(message.text).strip()
    if user_id not in AUTH_USERS and check_db_for_sudo_user == "False":
        not_authorized = await message.reply(
            "⛔ You are not authorized to use this command."
        )
        await asyncio.sleep(5)
        await not_authorized.delete()
        await message.delete()

    if (
        message.reply_to_message
        and find_sudo_user_by_id(str(message.reply_to_message.from_user.id)) == "True"
    ):
        user_to_remove_info: dict = message.reply_to_message.from_user
        remove_a_sudo_user_from_the_db(user_to_remove_info.id)
        await bot.send_message(f"{user_to_remove_info.id} removed from Sudo users")
        await message.delete()
        return
    elif (
        message.reply_to_message
        and find_sudo_user_by_id(str(message.reply_to_message.from_user.id)) == "False"
    ):
        await message.reply("User already removed.")
        return

    if (
        not message.reply_to_message
        and len(message.text.split(" ")) == 2
        and find_sudo_user_by_id(str(message.text.split(" ")[1].strip())) == "True"
    ):
        sudo_user_id: str = str(message_text).split(" ")[1]
        user_info = await bot.get_chat(sudo_user_id)
        remove_a_sudo_user_from_the_db(sudo_user_id)
        await message.reply(f"{user_info.first_name} removed from Sudo users")
        return
    elif not message.reply_to_message and len(message.text.split(" ")) == 1:
        await message.reply("Please provide a user ID.")
    else:
        await message.reply("User already removed.")


# ---- List sudo users --------#

@bot.on_message(filters.command("sudo"))
async def list_sudo_users(client: Client, message):
    sudo_user_names = list_all_sudo_users()
    user_id = str(message.from_user.id)
    if (
        user_id not in AUTH_USERS
        and find_sudo_user_by_id(user_id) == "False"
    ):
        not_authorized = await message.reply(
            "You are not authorized to use this command"
        )
        await message.delete()
        await not_authorized.delete()
        return
    checking = await message.reply("Checking sudo users...")
    sudo_users_count = count_sudo_users()
    if sudo_users_count is not None:
        await message.delete()
        await checking.edit(
            f"""
__**Sudo User Status**__:
There are ({sudo_users_count}) sudo users.

{sudo_user_names}
"""
        )
    else:
        err = await message.reply("Error counting sudo users.")
        await message.delete()
        await checking.delete()
        await asyncio.sleep(5)
        await err.delete()
        return


### -------- List bot users -----

@bot.on_message(filters.command("users"))
async def list_users(client: Client, message):
    bot_user_names = list_all_users()
    user_id = str(message.from_user.id)
    if (
        user_id not in AUTH_USERS
        and find_user_by_id_in_mongodb(user_id) == "False"
    ):
        not_authorized = await message.reply(
            "You are not authorized to use this command"
        )
        await message.delete()
        await asyncio.sleep(5)
        await not_authorized.delete()
        return
    checking = await message.reply("Checking users...")
    user_count = count_bot_users()
    if user_count is not None:
        await message.delete()
        await checking.edit(
            f"""
__**User Status**__:
There are currently {user_count} users of the bot in the database.

{bot_user_names}
"""
        )
    else:
        err = await message.reply("Error counting users.")
        await message.delete()
        await checking.delete()
        await asyncio.sleep(5)
        await err.delete()


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

            title, thumbnail_url = await get_video_info(url)  # Get thumbnail URL again
            print("Checking thumbnail status...")
            args = (thumbnail_url, f"{filepath}.jpg", user_id)
            thumbnail = convert_thumbnail_to_jpeg(args)

            print("Uploading...")
            send = await client.send_video(
                chat_id=chat_id,
                video=filepath,
                thumb=thumbnail,  # Use thumbnail if available
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
                    link_log_id = LINK_LOGS  # Ensure it's an int
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
