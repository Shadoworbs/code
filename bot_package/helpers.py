import os
import time
import asyncio
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, PeerIdInvalid, FloodWait, ChannelInvalid
from .config import (
    PROGRESS_BAR_LENGTH,
    last_update_time,
    UPDATE_INTERVAL,
)

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
