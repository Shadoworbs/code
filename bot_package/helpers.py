import traceback
import aiohttp
import os
import time
import asyncio
import pyrogram
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from pyrogram.types import BotCommand as bc
import requests
from .config import (
    PROGRESS_BAR_LENGTH,
    last_update_time,
    UPDATE_INTERVAL,
    THUMBNAIL_PATH,
)
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# --- MongoDB Connection ---

pwd = os.getenv("MONGO_PWD")

# connection string
connection_string = f"mongodb+srv://myAtlasDBUser:{pwd}@pyroytbot.p1vptc2.mongodb.net/?retryWrites=true&w=majority&appName=PyroYtBot"

# initialize the client
client = MongoClient(connection_string)


# --- Progress Bar ---
def create_progress_bar(percentage: float, length: int = PROGRESS_BAR_LENGTH) -> str:
    """Creates a text-based progress bar."""
    if not 0 <= percentage <= 100:
        percentage = max(0, min(100, percentage))  # Clamp percentage
    filled_length = int(length * percentage // 100)
    bar = "•" * filled_length + "°" * (length - filled_length)
    return f"[{bar}]"


def get_resolution_buttons(message_id: int) -> InlineKeyboardMarkup:
    """Returns resolution selection buttons including a Cancel button."""
    resolutions = {"1080": "1080p", "720": "720p", "480": "480p", "360": "360p"}
    buttons = []
    for height, label in resolutions.items():
        callback_data = f"{height}:{message_id}"
        if len(callback_data.encode("utf-8")) <= 64:
            buttons.append([InlineKeyboardButton(label, callback_data=callback_data)])
        else:
            print(f"Warning: Callback data too long, skipping button: {callback_data}")
    # Add Cancel button
    buttons.append(
        [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{message_id}")]
    )
    return InlineKeyboardMarkup(buttons)


# --- Progress Update Helper ---
async def edit_status_message(
    status_msg, text: str, reply_markup=None
):  # Add reply_markup parameter
    """Safely edits a status message, handling FloodWait and preserving markup."""
    message_id = status_msg.id
    chat_id = status_msg.chat.id
    current_time = time.time()

    # Check if enough time has passed since the last update
    if current_time - last_update_time.get((chat_id, message_id), 0) > UPDATE_INTERVAL:
        try:
            # Pass reply_markup to edit_text
            await status_msg.edit_text(text, reply_markup=reply_markup)
            last_update_time[(chat_id, message_id)] = current_time
        except FloodWait as fw:
            print(f"FloodWait: sleeping for {fw.value + 1}s")
            await asyncio.sleep(fw.value + 1)
            # Retry after waiting
            try:
                # Pass reply_markup on retry as well
                await status_msg.edit_text(text, reply_markup=reply_markup)
                last_update_time[(chat_id, message_id)] = current_time
            except Exception as e_retry:
                print(f"Error editing status message after FloodWait: {e_retry}")
        except Exception as e:
            # Log other errors but allow potential recovery
            print(f"Error editing status message: {e}")
            # Optionally reset time to allow quicker retry if it was temporary
            last_update_time[(chat_id, message_id)] = 0
        # No finally block needed here for time update, handled in try blocks


def cleanup_progress_state(chat_id: int, message_id: int):
    """Removes state associated with a progress message."""
    last_update_time.pop((chat_id, message_id), None)


def get_user_download_path(user_id: int) -> str:
    """Gets the download path for a specific user."""
    from .config import BASE_DOWNLOAD_PATH  # Avoid circular import at top level

    user_download_dir = os.path.join(BASE_DOWNLOAD_PATH, str(user_id))
    os.makedirs(user_download_dir, exist_ok=True)
    return user_download_dir


# create a document inside a collection
def create_user_document_in_mongodb(info: dict) -> str:
    """Inserts a single document into the MongoDB collection.
    - Args:
    info (dict): The document to insert.
    - Returns:
    bool: True if the document was inserted successfully, False otherwise.
    - Raises:
    Exception: If there is an error during the insertion process.
    """
    try:
        bot_db = client.bot_db
        bot_collection = bot_db.bot_collection
        bot_collection.insert_one(info)
        return "True"
    except Exception as e:
        print(f"Error inserting document: {e}")
        return "False"


def find_user_by_id_in_mongodb(id: str) -> str:
    """Finds a user by ID in the MongoDB collection.
    - Args:
        id (str): The ID of the user to find.
    - Returns:
        dict: The user document if found, None otherwise.
    """
    id = str(id)
    try:
        find_user = client.bot_db.bot_collection.find_one({"_id": id})
        if find_user is None:
            print(f"User with ID: {id} not found")
            return "False"
        else:
            return "True"
    except Exception as e:
        return "False"


def add_a_sudo_user_to_the_db(info: dict) -> str:
    """Adds a sudo user to the MongoDB collection.
    - Args:
        info (dict): The document to insert.
    - Returns:
        bool: True if the document was inserted successfully, False otherwise.
    """
    try:
        sudo_db = client.sudo_db
        bot_collection = sudo_db.sudo_users
        bot_collection.insert_one(info)
        return "True"
    except Exception as e:
        print(f"Error inserting document: {e}")
        return "False"


def find_sudo_user_by_id(id: str) -> str:
    """Finds a sudo user by ID in the MongoDB collection.
    - Args:
        id (str): The ID of the user to find.
    - Returns:
        dict: The user document if found, None otherwise.
    """
    id = str(id)
    try:
        find_user = client.sudo_db.sudo_users.find_one({"_id": id})
        if find_user is None:
            print(f"User with ID: {id} not found")
            return "False"
        else:
            return "True"
    except Exception as e:
        return "False"


def remove_a_sudo_user_from_the_db(id: str) -> str:
    """Removes a sudo user from the MongoDB collection.
    - Args:
        id (str): The ID of the user to remove.
    - Returns:
        bool: True if the document was removed successfully, False otherwise.
    """
    id = str(id)
    try:
        sudo_db = client.sudo_db
        bot_collection = sudo_db.sudo_users
        result = bot_collection.delete_one({"_id": id})
        if result.deleted_count > 0:
            return "True"
        else:
            return "False"
    except Exception as e:
        print(f"Error removing document: {e}")
        return "False"


# counting all documents in a database
def count_sudo_users() -> int:
    count: int = client.sudo_db.sudo_users.count_documents(filter={})
    return count


def count_bot_users() -> int:
    count: int = client.bot_db.bot_collection.count_documents(filter={})
    return count


# list all users in the bot database by their first name
def list_all_users() -> list:
    """Lists all users in the bot database."""
    try:
        bot_db = client.bot_db
        bot_collection = bot_db.bot_collection
        users = bot_collection.find({})
        user_list = [f"{user['first_name']} `{user['_id']}`" for user in users]
        return user_list
    except Exception as e:
        print(f"Error listing users: {e}")
        return f"Error listing user names: {e}"


# list all sudo users in the bot database by their first name
def list_all_sudo_users() -> list:
    """Lists all sudo users in the bot database."""
    try:
        sudo_db = client.sudo_db
        bot_collection = sudo_db.sudo_users
        users = bot_collection.find({})
        sudo_list = [f"{user['first_name']} `{user['_id']}`" for user in users]
        return sudo_list
    except Exception as e:
        print(f"Error listing sudo users: {e}")
        return f"Error listing sudo user names: {e}"


# download thumbnail form a url and save it to a local path using requests asyncio
def download_thumbnail(thumbnail_url, thumb_name, user_id) -> tuple:
    """Downloads a thumbnail from a url and saves it at a local path without asyncio"""
    if not thumbnail_url or not thumb_name or not user_id:
        print("Missing required parameters for thumbnail download.")
        return None, None
    try:
        # Create the download path if it doesn't exist
        download_path = get_user_download_path(user_id)
        thumbnail_path = os.path.join(download_path, f"{thumb_name}.jpg")
        # Download the thumbnail using requests
        response = requests.get(thumbnail_url, stream=True)
        if response.status_code == 200:
            with open(thumbnail_path, "wb") as f:
                for chunk in response.iter_content(2048):
                    f.write(chunk)
            print(f"Thumbnail downloaded successfully: {thumbnail_path}")
            return True, thumbnail_path
        else:
            print(f"Failed to download thumbnail: {response.status_code}")
            return False, None
    except Exception as e:
        print(f"Error downloading thumbnail: {e}")
        return False, None


# convert the downloaded thumbnail to a Jpeg image with width and height not more than 320px320px using ffmpeg
def convert_thumbnail_to_jpeg(args: tuple) -> bool:
    global THUMBNAIL_PATH
    """Converts a thumbnail to JPEG format with a maximum size of 320x320."""

    thumbnail_url, thumb_name, user_id = args
    _, thumbnail_path = download_thumbnail(thumbnail_url, thumb_name, user_id)
    if not thumbnail_path:
        print("Thumbnail path is None, conversion skipped.")
        return
    try:
        # Use ffmpeg to convert and resize the image
        os.system(
            f"ffmpeg -i {thumbnail_path} -vf scale=320:320 -q:v 2 {thumbnail_path} -y"
        )
        # Update the global THUMBNAIL_PATH variable
        THUMBNAIL_PATH.append(thumbnail_path)
        print(f"Thumbnail converted successfully: {thumbnail_path}")
        return True
    except Exception as e:
        print(f"Error converting thumbnail: {e}")
        return


# --- Ban Management ---
def ban_user_in_mongodb(user_id: str) -> bool:
    """Bans a user by adding banned=True to their document"""
    try:
        bot_db = client.bot_db
        bot_collection = bot_db.bot_collection
        result = bot_collection.update_one(
            {"_id": str(user_id)}, {"$set": {"banned": True}}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error banning user: {e}")
        return False


def unban_user_in_mongodb(user_id: str) -> bool:
    """Unbans a user by setting banned=False in their document"""
    try:
        bot_db = client.bot_db
        bot_collection = bot_db.bot_collection
        result = bot_collection.update_one(
            {"_id": str(user_id)}, {"$set": {"banned": False}}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error unbanning user: {e}")
        return False


def is_user_banned(user_id: str) -> bool:
    """Checks if a user is banned"""
    try:
        bot_db = client.bot_db
        bot_collection = bot_db.bot_collection
        user = bot_collection.find_one({"_id": str(user_id)})
        return user and user.get("banned", False)
    except Exception as e:
        print(f"Error checking ban status: {e}")
        return False


# --- Rate Limiting ---
def check_rate_limit(
    user_id: str, rate_limit_cache: dict, max_requests: int, duration: int
) -> bool:
    """
    Check if user has exceeded rate limit
    Returns True if rate limit exceeded, False otherwise
    """
    current_time = time.time()

    # Initialize empty list for new users
    if user_id not in rate_limit_cache:
        rate_limit_cache[user_id] = []

    # Remove old timestamps
    rate_limit_cache[user_id] = [
        t for t in rate_limit_cache[user_id] if current_time - t < duration
    ]

    # Check if limit exceeded
    if len(rate_limit_cache[user_id]) >= max_requests:
        return True

    # Add new timestamp
    rate_limit_cache[user_id].append(current_time)
    return False


# --- Broadcast Message ---
async def broadcast_message(
    pyroclient: Client, message_text: str, exclude_banned: bool = False
) -> tuple[int, int]:
    """
    Broadcasts a message to all users
    Returns tuple of (success_count, fail_count)
    """
    success_count = 0
    fail_count = 0

    try:
        bot_db = client.bot_db
        bot_collection = bot_db.bot_collection

        # Build query to exclude banned users if requested
        query = {} if not exclude_banned else {"banned": {"$ne": True}}

        for user in bot_collection.find(query):
            try:
                chat_id = int(user["_id"])
                await pyroclient.send_message(
                    chat_id=chat_id, text=message_text, disable_web_page_preview=True
                )
                success_count += 1
                await asyncio.sleep(0.1)  # Rate limit prevention
            except Exception as e:
                print(f"Failed to send broadcast to {chat_id}: {e}")
                fail_count += 1

    except Exception as e:
        print(f"Error during broadcast: {e}")

    return success_count, fail_count


# --- Set bot commands 
async def set_commands(bot: Client, message: pyrogram.types.Message) -> None:
    """Sets bot commands for a Pyrogram Client bot.
    This function processes command settings in two formats:
    1. Direct message with pipe-separated commands: "command | cmd1-desc1, cmd2-desc2"
    2. Reply to a message with commands in format: "/cmd1 - desc1\n/cmd2 - desc2"
    Args:
        bot (Client): The Pyrogram Client bot instance
        message (pyrogram.types.Message): The message containing command settings
    Returns:
        None
    Raises:
        Exception: If there's an error setting the bot commands
    Example:
        Direct format:
        ```
        /setcommands | start-Start the bot, help-Show help
        ```
        Reply format:
        ```
        /start - Start the bot
        /help - Show help
        ```
    """
    
    if not message.reply_to_message and len(message.text.split(" ")) > 2:
        setting_commands = await message.reply("Setting bot commands...")
        await asyncio.sleep(1)
        text = message.text
        cmds = text.split("|")[1]
        right_cmds = cmds.split(",")
        cleaned_cmd = [i.strip() for i in right_cmds]
        cmd_list_to_show_after_completion: str = ''
        # Or to get a dictionary of commands and descriptions:
        final_cmds: dict = {i.split("-")[0].strip(): i.split("-")[1].strip() for i in cleaned_cmd}

        for key, value in final_cmds.items():
                cmd_list_to_show_after_completion += f'/{key} - {value}\n'

    elif message.reply_to_message and len(message.reply_to_message.text) != 0:
        text = message.reply_to_message.text
        setting_commands = await message.reply("Setting bot commands...")
        await asyncio.sleep(1)
        cmds = text.split("\n")
        cleaned_cmd = [i.strip().lstrip("/") for i in cmds]
        final_cmds: dict = {i.split("-")[0].strip(): i.split("-")[1].strip() for i in cleaned_cmd}
        cmd_list_to_show_after_completion = ''

        for key, value in final_cmds.items():
                cmd_list_to_show_after_completion += f'/{key} - {value}\n'

    else:
        empty_commends = await message.reply("Bot commands cannot be empty!")
        await message.delete()
        await asyncio.sleep(5)
        await empty_commends.delete()
        return
    
    commands = [bc(key, value) for key, value in final_cmds.items()]

    try:
        await bot.set_bot_commands(
            commands=commands
        )
        await setting_commands.edit(f"__**✅ Commands set successfully.**__\n\n{cmd_list_to_show_after_completion}")
    except Exception as e:
        print(f"Error setting commands: {e.add_note('Error setting commands')}\n{traceback.format_exc()}")
        await message.reply(f"Error setting commands: {e}")



# --- Get bot commands
async def get_commands(
    bot: Client, 
    message: pyrogram.types.Message
) -> None:
    """
    Retrieves and displays the list of available bot commands.
    This asynchronous function fetches all registered commands from the bot and sends them
    as a formatted message to the user. Each command is displayed with its description
    in the format: /command - description.
    Args:
        bot (Client): The Pyrogram Client instance representing the bot
        message (pyrogram.types.Message): The message object that triggered this command
    Returns:
        None
    Raises:
        Exception: Any error that occurs while fetching or sending bot commands will be
                  caught, logged, and reported back to the user
    """
    try:
        commands = await bot.get_bot_commands()
        command_list = "\n".join([f"/{cmd.command} - {cmd.description}" for cmd in commands])
        getting_cmds = await message.reply("Getting commands...")
        await asyncio.sleep(1)
        await getting_cmds.edit(f"__**Current bot commands:**__\n\n{command_list}")
    except Exception as e:
        print(f"Error getting commands: {e.add_note('Error getting commands')}\n{traceback.format_exc()}")
        await message.reply(f"Error getting commands: {e}")