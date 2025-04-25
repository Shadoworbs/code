import os
import sys
import asyncio
import time
import shutil
import re
from functools import wraps
from pymongo import MongoClient
from pyrogram import Client, filters
import pyrogram
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, PeerIdInvalid

from .bot_instance import bot
from .config import (
    COMMAND_PREFIXES,
    LOG_CHANNEL,
    LINK_LOGS,
    AUTH_USERS,
    RATE_LIMIT_DOWNLOAD_DURATION,
    RATE_LIMIT_DOWNLOADS,
    THUMBNAIL_PATH,
    url_cache,
    last_update_time,
    UPDATE_INTERVAL,
    active_downloads,
    rate_limit_cache,
    RATE_LIMIT_MESSAGES,
    RATE_LIMIT_DURATION,
    download_limit_cache,
)
from .helpers import (
    convert_thumbnail_to_jpeg,
    count_bot_users,
    count_sudo_users,
    download_thumbnail,
    get_commands,
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
    list_all_users,
    ban_user_in_mongodb,
    set_commands,
    unban_user_in_mongodb,
    broadcast_message,
    check_rate_limit,
    is_user_banned,
)
from .downloader import get_playlist_info, get_video_info, download_video_async
from .playlist_buttons import (
    get_playlist_info_button,
    get_playlist_videos_buttons,
    get_video_selection_buttons,
    format_duration,
)
from replies import *  # Assuming replies.py exists and contains text variables
from buttons import (
    START_BUTTON,
    ABOUT_BUTTON,
    DL_COMPLETE_BUTTON,
)  # Assuming buttons.py exists


# --- Rate Limit Decorator ---
def check_user_rate_limit(func):
    """Decorator to check rate limit for regular messages"""

    @wraps(func)
    async def wrapper(client: Client, message, *args, **kwargs):
        user_id = str(message.from_user.id)

        # Skip rate limiting for sudo users and AUTH_USERS
        if user_id in AUTH_USERS or find_sudo_user_by_id(user_id) == "True":
            return await func(client, message, *args, **kwargs)

        # Check if user is banned
        if is_user_banned(user_id):
            await message.reply("⛔ You are banned from using this bot.")
            return

        # Check rate limit
        if check_rate_limit(
            user_id, rate_limit_cache, RATE_LIMIT_MESSAGES, RATE_LIMIT_DURATION
        ):
            remaining_time = max(
                [
                    t + RATE_LIMIT_DURATION - time.time()
                    for t in rate_limit_cache[user_id]
                ]
            )
            await message.reply(
                f"⚠️ Rate limit exceeded. Please try again in {int(remaining_time)} seconds."
            )
            return

        return await func(client, message, *args, **kwargs)

    return wrapper


# --- MongoDB tools ---
async def mongo_check_user_database(userid: str, userdict=None, message=None) -> bool:
    if find_user_by_id_in_mongodb(userid) == "False":
        # If user not found, create a new document in MongoDB for the user
        info: dict = {
            "_id": str(userdict.id),
            "date_time": message.date or "None",
            "first_name": userdict.first_name or "None",
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
    userid: str, userdict: dict = None, message=None
) -> bool:
    if not await find_sudo_user_by_id(userid):
        # If user not found, create a new document in MongoDB for the user
        info: dict = {
            "_id": str(userdict.id),
            "date_time": message.date or "None",
            "first_name": userdict.first_name or "None",
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

        await add_a_sudo_user_to_the_db(info)
        return "True"
    return "False"


# --- Command Handlers ---


@bot.on_message(filters.command("start", COMMAND_PREFIXES))
async def start_command(client: Client, message):
    user_id = str(message.from_user.id)
    userdict: dict = message.from_user
    await mongo_check_user_database(str(user_id), userdict, message)

    await message.reply(
        text=f"{start_text.format(message.from_user.mention)}",
        reply_markup=InlineKeyboardMarkup(START_BUTTON),
        disable_web_page_preview=True,
    )


@bot.on_message(filters.command("help", COMMAND_PREFIXES))
async def help_command(client: Client, message):
    user_id = str(message.from_user.id)
    userdict: dict = message.from_user
    await mongo_check_user_database(str(user_id), userdict, message)

    await message.reply(help_text)


@bot.on_message(filters.command("about", COMMAND_PREFIXES))
async def about_command(client: Client, message):
    user_id = str(message.from_user.id)
    userdict: dict = message.from_user
    await mongo_check_user_database(str(user_id), userdict, message)

    text = """**__🤖 Bot Details:__**\n
**Creator:** Shadow Orbs
**Language:** Python 3
**Library:** Pyrogram
**Repo:** Click button below."""

    await message.reply(
        text=text,
        reply_markup=InlineKeyboardMarkup(ABOUT_BUTTON),
        disable_web_page_preview=True,
    )


@bot.on_message(filters.command("clean", COMMAND_PREFIXES))
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


@bot.on_message(filters.command("restart", COMMAND_PREFIXES))
async def restart_command(client: Client, message):
    user_id = str(message.from_user.id)
    userdict: dict = message.from_user
    await mongo_check_user_database(str(user_id), userdict, message)
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
VIDEO_ID = []
playlist_cache = {}
selected_videos = {}


@bot.on_message(
    filters.regex(
        r"(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+(watch\?v=|embed/|v/|.+\?v=)?([^&\n]{11}|playlist\?list=[a-zA-Z0-9_-]+)",
        re.IGNORECASE,
    )
)
async def youtube_url_handler(client: Client, message):
    global VIDEO_ID
    user_id = str(message.from_user.id)
    userdict: dict = message.from_user
    await mongo_check_user_database(str(user_id), userdict, message)

    # Skip rate limiting for sudo users and AUTH_USERS
    if user_id not in AUTH_USERS and find_sudo_user_by_id(user_id) == "False":
        # Check if user is banned
        if is_user_banned(user_id):
            await message.reply("⛔ You are banned from using this bot.")
            return

        # Check download rate limit
        if check_rate_limit(
            user_id,
            download_limit_cache,
            RATE_LIMIT_DOWNLOADS,
            RATE_LIMIT_DOWNLOAD_DURATION,
        ):
            remaining_time = max(
                [
                    t + RATE_LIMIT_DOWNLOAD_DURATION - time.time()
                    for t in download_limit_cache[user_id]
                ]
            )
            await message.reply(
                f"⚠️ Download rate limit exceeded. Please try again in {int(remaining_time)} seconds."
            )
            return

    url = message.text.strip()
    processing_msg = await message.reply("⏳ Processing link...")

    try:
        # Check if it's a playlist URL
        if "playlist?list=" in url:
            playlist_info = await get_playlist_info(url)
            if not playlist_info:
                await processing_msg.edit_text(
                    "❌ Could not fetch playlist information."
                )
                return

            # Cache playlist info
            playlist_cache[message.id] = {
                "info": playlist_info,
                "url": url,
                "selected_videos": set(),  # Track selected videos
            }

            # Calculate total duration
            total_duration = format_duration(playlist_info["total_duration"])

            # Create playlist info message
            text = (
                f"📋 **Playlist: {playlist_info['title']}**\n"
                f"👤 Uploader: {playlist_info['uploader']}\n"
                f"🎬 Videos: {playlist_info['video_count']}\n"
                f"⏱ Total Duration: {total_duration}\n\n"
                "Select an option below:"
            )

            await processing_msg.edit_text(
                text, reply_markup=get_playlist_info_button(message.id)
            )
            return

        # Existing single video logic...
        title, thumbnail_url, video_id = await get_video_info(url)

        if title is None:
            await processing_msg.edit_text(
                "❌ Sorry, couldn't fetch video details. The link might be invalid, private, or unavailable."
            )
            return
        elif title == "Private Video" or title == "Video Unavailable":
            await processing_msg.edit_text(f"❌ **{title}**. Cannot download.")
            return

        url_cache[message.id] = url

        print("Checking thumbnail status...")
        args: tuple = (
            thumbnail_url,
            video_id,
            user_id,
        )
        # convert_thumbnail_to_jpeg(args)  # Convert thumbnail to JPEG
        VIDEO_ID.append(video_id)  # Store the video ID for later use
        print("Thumbnail conversion complete.")

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
        print(f"Error processing URL {url}: {e}")
        await processing_msg.edit_text(
            f"⚠️ An error occurred while processing the link:\n`{e}`"
        )
        url_cache.pop(message.id, None)
        playlist_cache.pop(message.id, None)  # Clean up playlist cache too


##### Add a sudo user ########


@bot.on_message(filters.command("addsudo", COMMAND_PREFIXES))
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
            "first_name": user_to_add_info.first_name or "None",
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
        user_info = await bot.get_users(sudo_user_id)
        info: dict = {
            "_id": sudo_user_id or "None",
            "date_time": message.date or "None",
            "first_name": user_info.first_name or "None",
            "last_name": user_info.last_name or "None",
            "username": user_info.username or "None",
            "language_code": user_info.language_code or "None",
            "Dc_id": user_info.dc_id or "None",
            "is_premium": user_info.is_premium or "None",
            "is_verified": user_info.is_verified or "None",
        }
        add_a_sudo_user_to_the_db(info)
        await message.reply(f"{user_info.first_name} added as a Sudo user")
        return
    elif not message.reply_to_message and len(message.text.split(" ")) == 1:
        await message.reply("Please provide a user ID.")
    else:
        await message.reply("User already added.")


##### remove sudo user ########


@bot.on_message(filters.command("rmsudo", COMMAND_PREFIXES))
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
        user_info = await bot.get_users(sudo_user_id)
        remove_a_sudo_user_from_the_db(sudo_user_id)
        await message.reply(f"{user_info.first_name} removed from Sudo users")
        return
    elif not message.reply_to_message and len(message.text.split(" ")) == 1:
        await message.reply("Please provide a user ID.")
    else:
        await message.reply("User already removed.")


# ---- List sudo users --------#


@bot.on_message(filters.command("sudo", COMMAND_PREFIXES))
async def list_sudo_users(client: Client, message):
    sudo_user_names = list_all_sudo_users()
    enumerated_sudo_user_names = []
    user_id = str(message.from_user.id)
    if user_id not in AUTH_USERS and find_sudo_user_by_id(user_id) == "False":
        not_authorized = await message.reply(
            "You are not authorized to use this command"
        )
        await asyncio.sleep(5)
        await message.delete()
        await not_authorized.delete()
        return
    checking = await message.reply("Checking sudo users...")
    sudo_users_count = count_sudo_users()

    if sudo_users_count > 0:
        # print all the elements in the list with a prefix starting with 1
        for i in range(len(sudo_user_names)):
            enumerated_sudo_user_names.append(f"{i+1}. {sudo_user_names[i]}\n")
        await message.delete()
        await checking.edit(
            f"**__Sudo Users:__** `{sudo_users_count}`\n\n"
            + "".join(enumerated_sudo_user_names)
        )
    else:
        err = await message.reply("Error counting sudo users.")
        await message.delete()
        await checking.delete()
        await asyncio.sleep(5)
        await err.delete()
        return


### -------- List bot users -----


@bot.on_message(filters.command("users", COMMAND_PREFIXES))
async def list_users(client: Client, message):
    bot_user_names = list_all_users()
    bot_user_count = count_bot_users()
    enumerated_bot_user_names = []
    user_id = str(message.from_user.id)
    if user_id not in AUTH_USERS and find_user_by_id_in_mongodb(user_id) == "False":
        not_authorized = await message.reply(
            "You are not authorized to use this command"
        )
        await message.delete()
        await asyncio.sleep(5)
        await not_authorized.delete()
        return
    checking = await message.reply("Checking database...")
    if bot_user_count > 0:
        # print all the elements in the list with a prefix starting with 1
        for i in range(len(bot_user_names)):
            enumerated_bot_user_names.append(f"{i+1}. {bot_user_names[i]}\n")

        await checking.edit(
            f"**__Total Users:__** `{bot_user_count}`\n\n"
            + "".join(enumerated_bot_user_names)
        )

        await message.delete()

    else:
        err = await message.reply("Error counting users.")
        await message.delete()
        await checking.delete()
        await asyncio.sleep(5)
        await err.delete()


# --- Command to show information about the lunux system
@bot.on_message(filters.command("server", COMMAND_PREFIXES))
async def server_info(client: Client, message):
    user_id = str(message.from_user.id)
    userdict: dict = message.from_user
    await mongo_check_user_database(str(user_id), userdict, message)

    server_info_text = (
        f"**__Server Information__**\n\n"
        f"**Python Version:** {sys.version.split()[0]}\n"
        f"**Pyrogram Version:** {pyrogram.__version__}\n"
        f"**CPU Count:** {os.cpu_count()}\n"
        f"**Total Disk Space:** {shutil.disk_usage('/').total / (1024. ** 3):.2f} GB total\n"
        f"**Used:** {shutil.disk_usage('/').used / (1024. ** 3):.2f} GB used\n"
        f"**Free:** {shutil.disk_usage('/').free / (1024. ** 3):.2f} GB free\n"
    )
    await message.reply(server_info_text)


# --- Admin Commands ---


@bot.on_message(filters.command("broadcast", COMMAND_PREFIXES))
async def broadcast_cmd(client: Client, message):
    """Broadcast a message to all users"""
    user_id = str(message.from_user.id)
    if user_id not in AUTH_USERS and find_sudo_user_by_id(user_id) == "False":
        await message.reply("⛔ You are not authorized to broadcast messages.")
        return

    # Check if there's a message to broadcast
    if not message.reply_to_message and len(message.command) < 2:
        await message.reply(
            "Please provide a message to broadcast or reply to a message."
        )
        return

    # Get the message to broadcast
    if message.reply_to_message:
        broadcast_text = (
            message.reply_to_message.text or message.reply_to_message.caption
        )
    else:
        broadcast_text = " ".join(message.command[1:])

    if not broadcast_text:
        await message.reply("Cannot broadcast empty message.")
        return

    status_msg = await message.reply("Broadcasting message to all users...")
    success_count, fail_count = await broadcast_message(client, broadcast_text)

    await status_msg.edit(
        f"📣 Broadcast completed!\n"
        f"✅ Success: {success_count}\n"
        f"❌ Failed: {fail_count}"
    )


@bot.on_message(filters.command(["ban", "unban"], COMMAND_PREFIXES))
async def ban_unban_cmd(client: Client, message):
    """Ban or unban a user"""
    user_id = str(message.from_user.id)
    if user_id not in AUTH_USERS and find_sudo_user_by_id(user_id) == "False":
        await message.reply("⛔ You are not authorized to ban/unban users.")
        return

    command = message.command[0].lower()

    # Get target user ID
    target_user_id = None
    if message.reply_to_message:
        target_user_id = str(message.reply_to_message.from_user.id)
    elif len(message.command) > 1:
        target_user_id = message.command[1]

    if not target_user_id:
        await message.reply(
            f"Please provide a user ID or reply to a user's message to {command}."
        )
        return

    # Prevent banning sudo users or AUTH_USERS
    if target_user_id in AUTH_USERS or find_sudo_user_by_id(target_user_id) == "True":
        await message.reply("Cannot ban/unban admin users.")
        return

    if command == "ban":
        if ban_user_in_mongodb(target_user_id):
            await message.reply(f"🚫 User `{target_user_id}` has been banned.")
        else:
            await message.reply("Failed to ban user. They might not exist in database.")
    else:  # unban
        if unban_user_in_mongodb(target_user_id):
            await message.reply(f"✅ User `{target_user_id}` has been unbanned.")
        else:
            await message.reply(
                "Failed to unban user. They might not exist in database."
            )


@bot.on_message(filters.command("stats", COMMAND_PREFIXES))
async def stats_cmd(client: Client, message):
    """Show bot statistics"""
    user_id = str(message.from_user.id)
    if user_id not in AUTH_USERS and find_sudo_user_by_id(user_id) == "False":
        await message.reply("⛔ You are not authorized to view statistics.")
        return

    total_users = count_bot_users()
    sudo_users = count_sudo_users()
    auth_users = len(AUTH_USERS)

    # Get active downloads count
    active_dl_count = len(active_downloads)

    # Calculate storage usage
    total_storage = shutil.disk_usage("/").total / (1024**3)
    used_storage = shutil.disk_usage("/").used / (1024**3)
    free_storage = shutil.disk_usage("/").free / (1024**3)

    stats_text = (
        "📊 **Bot Statistics**\n\n"
        f"👥 Total Users: `{total_users}`\n"
        f"👮 Admin Users: `{auth_users}`\n"
        f"⭐️ Sudo Users: `{sudo_users}`\n"
        f"⏳ Active Downloads: `{active_dl_count}`\n\n"
        "💾 **Storage Info**\n"
        f"Total: `{total_storage:.2f}` GB\n"
        f"Used: `{used_storage:.2f}` GB\n"
        f"Free: `{free_storage:.2f}` GB\n"
    )

    await message.reply(stats_text)


# --- Set and get bot commands ---
@bot.on_message(filters.command(["setcommands", "getcommands"], COMMAND_PREFIXES))
async def set_commands_handler(bot: Client, message: pyrogram.types.Message):
    user_id = str(message.from_user.id)
    if user_id not in AUTH_USERS and find_sudo_user_by_id(user_id) == "False":
        await message.reply("⛔ You are not authorized to use this command.")
        return

    command = message.command[0].lower()

    if command == "setcommands":
        await set_commands(bot, message)
    else:
        await get_commands(bot, message)


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

    # --- Playlist Related Callbacks ---
    if data.startswith("playlist_videos:"):
        try:
            msg_id = int(data.split(":")[1])
            playlist_data = playlist_cache.get(msg_id)

            if not playlist_data:
                await callbackQuery.answer(
                    "⌛ Playlist data expired. Please send the link again.",
                    show_alert=True,
                )
                return

            # Show the first page of videos
            await message.edit_text(
                f"📋 **Select videos from {playlist_data['info']['title']}**\n"
                f"Click on videos to select/deselect them:",
                reply_markup=get_playlist_videos_buttons(
                    msg_id, playlist_data["info"]["entries"]
                ),
            )
            await callbackQuery.answer()
        except Exception as e:
            print(f"Error handling playlist videos: {e}")
            await callbackQuery.answer(
                "⚠️ An error occurred while loading playlist videos.", show_alert=True
            )

    elif data.startswith("playlist_page:"):
        try:
            msg_id, page = map(int, data.split(":")[1:])
            playlist_data = playlist_cache.get(msg_id)

            if not playlist_data:
                await callbackQuery.answer(
                    "⌛ Playlist data expired. Please send the link again.",
                    show_alert=True,
                )
                return

            await message.edit_reply_markup(
                reply_markup=get_playlist_videos_buttons(
                    msg_id, playlist_data["info"]["entries"], page=page
                )
            )
            await callbackQuery.answer()
        except Exception as e:
            print(f"Error handling playlist page navigation: {e}")
            await callbackQuery.answer(
                "⚠️ An error occurred while navigating playlist pages.", show_alert=True
            )

    elif data.startswith("select_video:"):
        try:
            msg_id, video_idx = map(int, data.split(":")[1:])
            playlist_data = playlist_cache.get(msg_id)
            video_idx = int(video_idx)

            if not playlist_data:
                await callbackQuery.answer(
                    "⌛ Playlist data expired. Please send the link again.",
                    show_alert=True,
                )
                return

            # Toggle video selection
            if video_idx in playlist_data["selected_videos"]:
                playlist_data["selected_videos"].remove(video_idx)
                await callbackQuery.answer("✅ Video removed from selection")
            else:
                playlist_data["selected_videos"].add(video_idx)
                await callbackQuery.answer("✅ Video added to selection")

            # Update the message to reflect the new selection state
            await message.edit_reply_markup(
                reply_markup=get_playlist_videos_buttons(
                    msg_id,
                    playlist_data["info"]["entries"],
                    page=0,  # Reset to first page after selection
                )
            )
        except Exception as e:
            print(f"Error handling video selection: {e}")
            await callbackQuery.answer(
                "⚠️ An error occurred while selecting the video.", show_alert=True
            )

    elif data.startswith("confirm_selection:"):
        try:
            msg_id = int(data.split(":")[1])
            playlist_data = playlist_cache.get(msg_id)

            if not playlist_data:
                await callbackQuery.answer(
                    "⌛ Playlist data expired. Please send the link again.",
                    show_alert=True,
                )
                return

            if not playlist_data["selected_videos"]:
                await callbackQuery.answer(
                    "⚠️ Please select at least one video first!", show_alert=True
                )
                return

            # Show resolution selection for the first selected video
            selected_videos = sorted(playlist_data["selected_videos"])
            first_video = playlist_data["info"]["entries"][selected_videos[0]]
            total_selected = len(selected_videos)

            selection_text = (
                f"🎬 **{first_video['title']}**"
                f"{f' (and {total_selected-1} more videos)' if total_selected > 1 else ''}\n\n"
                "Select video quality for all selected videos:"
            )

            await message.edit_text(
                selection_text, reply_markup=get_video_selection_buttons(msg_id)
            )
            await callbackQuery.answer()
        except Exception as e:
            print(f"Error handling selection confirmation: {e}")
            await callbackQuery.answer(
                "⚠️ An error occurred while confirming selection.", show_alert=True
            )

    elif data.startswith("download_all:"):
        try:
            msg_id = int(data.split(":")[1])
            playlist_data = playlist_cache.get(msg_id)

            if not playlist_data:
                await callbackQuery.answer(
                    "⌛ Playlist data expired. Please send the link again.",
                    show_alert=True,
                )
                return

            # Select all videos
            playlist_data["selected_videos"] = set(
                range(len(playlist_data["info"]["entries"]))
            )

            # Show resolution selection
            first_video = playlist_data["info"]["entries"][0]
            total_videos = len(playlist_data["info"]["entries"])

            await message.edit_text(
                f"🎬 **{first_video['title']}** (and {total_videos-1} more)\n\n"
                "Select video quality for all videos:",
                reply_markup=get_video_selection_buttons(msg_id),
            )
            await callbackQuery.answer("✅ Selected all videos in playlist")
        except Exception as e:
            print(f"Error handling download all: {e}")
            await callbackQuery.answer(
                "⚠️ An error occurred while selecting all videos.", show_alert=True
            )

    # Add this section before the existing resolution selection logic
    elif ":" in data and data.split(":")[0].isdigit() and data.split(":")[1].isdigit():
        try:
            height_str, msg_id_str = data.split(":", 1)
            height = int(height_str)
            msg_id = int(msg_id_str)

            # Check if this is a playlist download
            playlist_data = playlist_cache.get(msg_id)
            if playlist_data and playlist_data["selected_videos"]:
                # Process playlist download
                await process_playlist_download(
                    client, message, user, height, playlist_data, callbackQuery
                )
                return

            # Continue with existing single video download logic...
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
                                    "❌ Cancel",
                                    callback_data=f"cancel:{original_msg_id}",
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
                            await edit_status_message(
                                status_msg, "❌ Download cancelled."
                            )
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
                    await asyncio.sleep(1)  # Brief pause before upload

                    thumbnail = THUMBNAIL_PATH[-1] or None

                    print("Uploading...")
                    send = await client.send_video(
                        chat_id=chat_id,
                        video=filepath,
                        thumb=thumbnail,  # Use thumbnail if available
                        reply_markup=InlineKeyboardMarkup(
                            DL_COMPLETE_BUTTON
                        ),  # Final message buttons
                        caption=f"✅ **Hey** {user.mention}\n{DL_COMPLETE_TEXT.format(url, title)}\n\nVia @{client.me.username}\n",
                        file_name=f"{title}.{extension}",
                        supports_streaming=True,
                        progress=upload_progress,
                    )
                    print("Upload complete.")

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
                            await bot.copy_message(log_channel_id, chat_id, send.id)
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
                            await edit_status_message(
                                status_msg, "❌ Upload cancelled."
                            )
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
                            reply_to_message_id=(
                                original_msg_id if original_msg_id else None
                            ),
                        )
                    try:
                        # Acknowledge the callback query even on error
                        await callbackQuery.answer(
                            "⚠️ An error occurred.", show_alert=True
                        )
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

        except Exception as e:
            print(f"Error processing callback data: {e}")
            await callbackQuery.answer(
                "⚠️ An error occurred while processing your request.", show_alert=True
            )

    # --- Fallback for Unrecognized Callbacks ---
    else:
        await callbackQuery.answer(
            "Button action not recognized or expired.", show_alert=True
        )


async def process_playlist_download(
    client, message, user, height, playlist_data, callback_query
):
    """Process the download of selected videos from a playlist."""
    chat_id = message.chat.id
    user_id = user.id
    selected_videos = sorted(playlist_data["selected_videos"])
    total_videos = len(selected_videos)

    # Create status message for playlist download
    status_msg = await message.edit_text(
        f"⏳ Processing {total_videos} video{'s' if total_videos > 1 else ''} from playlist..."
    )

    # Setup cancellation
    cancel_event = asyncio.Event()
    active_downloads[message.id] = cancel_event

    cancel_button_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{message.id}")]]
    )

    try:
        successful_downloads = 0
        failed_downloads = 0

        for index, video_idx in enumerate(selected_videos, 1):
            if cancel_event.is_set():
                await status_msg.edit_text("❌ Playlist download cancelled.")
                return

            video = playlist_data["info"]["entries"][video_idx]
            video_url = video["url"]

            await status_msg.edit_text(
                f"⬇️ Downloading video {index}/{total_videos}\n"
                f"🎬 **{video['title']}**",
                reply_markup=cancel_button_markup,
            )

            try:
                filepath, title, extension = await download_video_async(
                    user_id,
                    height,
                    video_url,
                    status_msg,
                    user.mention,
                    message.id,
                    cancel_button_markup,
                )

                if filepath:
                    # Upload the video
                    thumbnail = THUMBNAIL_PATH[-1] if THUMBNAIL_PATH else None

                    await client.send_video(
                        chat_id=chat_id,
                        video=filepath,
                        thumb=thumbnail,
                        caption=f"✅ **{index}/{total_videos}** - {title}\nFrom playlist: {playlist_data['info']['title']}\n\n"
                        f"Via @{client.me.username}",
                        file_name=f"{title}.{extension}",
                        supports_streaming=True,
                    )

                    successful_downloads += 1

                    # Clean up the file
                    try:
                        os.remove(filepath)
                    except Exception as e:
                        print(f"Error removing file {filepath}: {e}")
                else:
                    failed_downloads += 1

            except Exception as e:
                print(f"Error processing video {video['title']}: {e}")
                failed_downloads += 1
                continue

        # Final status update
        if successful_downloads > 0:
            completion_text = (
                f"✅ Playlist download complete!\n\n"
                f"Successfully downloaded: {successful_downloads}/{total_videos}\n"
            )
            if failed_downloads > 0:
                completion_text += f"Failed downloads: {failed_downloads}"

            await status_msg.edit_text(completion_text)
        else:
            await status_msg.edit_text(
                "❌ Failed to download any videos from the playlist."
            )

    except Exception as e:
        await status_msg.edit_text(f"❌ Error processing playlist: {str(e)}")
    finally:
        # Clean up
        active_downloads.pop(message.id, None)
        playlist_cache.pop(message.id, None)
