import os
import time
import asyncio
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, PeerIdInvalid, FloodWait, ChannelInvalid
from .config import (
    PROGRESS_BAR_LENGTH,
    SOFTWARE_CHANNEL_ID,
    MOVIE_CHANNEL_ID,
    SOFTWARE_CHANNEL_LINK,
    MOVIE_CHANNEL_LINK,
    last_update_time,
    UPDATE_INTERVAL,
)
from replies import membership_fail_text  # Assuming replies.py exists


# --- Progress Bar ---
def create_progress_bar(percentage: float, length: int = PROGRESS_BAR_LENGTH) -> str:
    """Creates a text-based progress bar."""
    if not 0 <= percentage <= 100:
        percentage = max(0, min(100, percentage))  # Clamp percentage
    filled_length = int(length * percentage // 100)
    bar = "█" * filled_length + "░" * (length - filled_length)
    return f"[{bar}]"


# --- Membership Check ---
async def check_membership(client: Client, user_id: int) -> bool:
    """Checks if a user is a member of the required channels."""
    if not SOFTWARE_CHANNEL_ID or not MOVIE_CHANNEL_ID:
        print(
            "Warning: SOFTWARE_CHANNEL_ID or MOVIE_CHANNEL_ID not set. Skipping membership check."
        )
        return True
    try:
        soft_id = int(SOFTWARE_CHANNEL_ID)
        mov_id = int(MOVIE_CHANNEL_ID)
        # Check membership concurrently
        results = await asyncio.gather(
            client.get_chat_member(chat_id=soft_id, user_id=user_id),
            client.get_chat_member(chat_id=mov_id, user_id=user_id),
            return_exceptions=True,  # Return exceptions instead of raising them immediately
        )
        # Check if any of the calls resulted in an error indicating non-membership
        for result in results:
            if isinstance(result, UserNotParticipant):
                return False
            elif isinstance(
                result, (PeerIdInvalid, ChannelInvalid)
            ):  # Catch ChannelInvalid explicitly too
                print(
                    f"Error checking membership for user {user_id}: PEER_ID_INVALID or CHANNEL_INVALID. "
                    f"Check if Channel IDs ({SOFTWARE_CHANNEL_ID}, {MOVIE_CHANNEL_ID}) are correct numerical IDs "
                    f"and if the bot is a member/admin in both channels. Specific error: {type(result).__name__}"
                )
                return False  # Treat as failure if channel ID is wrong
            elif isinstance(result, Exception):  # Catch other potential errors
                print(
                    f"Unexpected error checking membership for user {user_id}: {type(result).__name__} - {result}"
                )
                return False  # Treat other errors as failure
        return True  # If no exceptions indicating failure occurred
    except ValueError:
        print(
            f"Error: One or both Channel IDs ({SOFTWARE_CHANNEL_ID}, {MOVIE_CHANNEL_ID}) are not valid integers."
        )
        return False
    except Exception as e:
        print(
            f"General error during membership check for user {user_id}: {type(e).__name__} - {e}"
        )
        return False


# --- Buttons ---
def get_membership_buttons() -> InlineKeyboardMarkup:
    """Returns buttons for users who haven't joined channels."""
    buttons = [
        [
            InlineKeyboardButton("➡️ Software Channel", url=SOFTWARE_CHANNEL_LINK),
            InlineKeyboardButton("➡️ Movie Channel", url=MOVIE_CHANNEL_LINK),
        ],
        [InlineKeyboardButton("🔄 Retry", callback_data="retry_start")],
    ]
    return InlineKeyboardMarkup(buttons)


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
async def edit_status_message(status_msg, text: str):
    """Safely edits a status message, handling FloodWait."""
    message_id = status_msg.id
    chat_id = status_msg.chat.id
    current_time = time.time()

    if current_time - last_update_time.get((chat_id, message_id), 0) > UPDATE_INTERVAL:
        try:
            await status_msg.edit_text(text)
            last_update_time[(chat_id, message_id)] = current_time
        except FloodWait as fw:
            print(f"FloodWait: sleeping for {fw.value + 1}s")
            await asyncio.sleep(fw.value + 1)
            # Retry after waiting
            try:
                await status_msg.edit_text(text)
                last_update_time[(chat_id, message_id)] = current_time
            except Exception as e_retry:
                print(f"Error editing status message after FloodWait: {e_retry}")
        except Exception as e:
            # Log other errors but allow potential recovery
            print(f"Error editing status message: {e}")
            # Optionally reset time to allow quicker retry if it was temporary
            last_update_time[(chat_id, message_id)] = 0
        finally:
            # Ensure the time is updated even if an error occurred,
            # to prevent rapid retries on persistent errors.
            # Update time only on successful edit or after handling FloodWait successfully
            pass  # Time is updated inside the try blocks now


def cleanup_progress_state(chat_id: int, message_id: int):
    """Removes state associated with a progress message."""
    last_update_time.pop((chat_id, message_id), None)


def get_user_download_path(user_id: int) -> str:
    """Gets the download path for a specific user."""
    from .config import BASE_DOWNLOAD_PATH  # Avoid circular import at top level

    user_download_dir = os.path.join(BASE_DOWNLOAD_PATH, str(user_id))
    os.makedirs(user_download_dir, exist_ok=True)
    return user_download_dir
