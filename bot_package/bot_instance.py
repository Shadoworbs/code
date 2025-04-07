from pyrogram import Client
from .config import API_ID, API_HASH, BOT_TOKEN

if not all([API_ID, API_HASH, BOT_TOKEN]):
    raise ValueError(
        "API_ID, API_HASH, and BOT_TOKEN must be set in the environment variables."
    )

bot = Client(
    "bot_account", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
