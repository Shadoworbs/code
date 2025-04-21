import aiohttp
import os
import time
import asyncio
from arrow import get
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from .config import (
    PROGRESS_BAR_LENGTH,
    last_update_time,
    UPDATE_INTERVAL,
)
from pymongo import MongoClient;
from dotenv import load_dotenv
load_dotenv()
import pprint

# --- Progress Bar ---
def create_progress_bar(percentage: float, length: int = PROGRESS_BAR_LENGTH) -> str:
    """Creates a text-based progress bar."""
    if not 0 <= percentage <= 100:
        percentage = max(0, min(100, percentage))  # Clamp percentage
    filled_length = int(length * percentage // 100)
    bar = "█" * filled_length + "░" * (length - filled_length)
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


# --- MongoDB Connection ---

pwd = os.getenv('MONGO_PWD')

# connection string
connection_string = f'mongodb+srv://myAtlasDBUser:{pwd}@pyroytbot.p1vptc2.mongodb.net/?retryWrites=true&w=majority&appName=PyroYtBot'

# initialize the client
client = MongoClient(connection_string)


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



def find_user_by_id_in_mongodb (id: str) -> str:
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
def count_sudo_users() -> str:
    count = client.sudo_db.sudo_users.count_documents(filter={})
    return str(count)

def count_bot_users() -> str:
    count = client.bot_db.bot_collection.count_documents(filter={})
    return str(count)

# list all users in the bot database by their first name
def list_all_users() -> list:
    """Lists all users in the bot database."""
    try:
        bot_db = client.bot_db
        bot_collection = bot_db.bot_collection
        users = bot_collection.find({})
        user_list = [f"{user["fist_name"]} ({user["_id"]})" for user in users]
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
        sudo_list = [user["fist_name"] for user in users]
        return sudo_list
    except Exception as e:
        print(f"Error listing sudo users: {e}")
        return f"Error listing sudo user names: {e}"


# download thumbnail form a url and save it to a local path using requests asyncio

async def download_thumbnail_async(url: str = None, local_path: str = None, user_id: str = None) -> tuple:
    """Downloads a thumbnail from a URL and saves it to a local path."""
    user_id = str(user_id)
    try:
        work_dir = get_user_download_path(user_id)
        if not os.path.exists(work_dir):
            os.makedirs(work_dir, exist_ok=True)
        os.chdir(work_dir)  # Change to the user's download directory
        local_path = os.path.join(work_dir, local_path)
    except Exception as e:
        print(f"Error creating directory: {e}")
        pass

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(local_path, "wb") as file:
                        file.write(await response.read())
                    print(f"Thumbnail downloaded successfully: {local_path}")
                    return (True, local_path)
                else:
                    print(f"Failed to download thumbnail. Status code: {response.status}")
                    return (False, None)
    except Exception as e:
        print(f"Error downloading thumbnail: {e}")
        return (False, None)
