from pyrogram import Client
from config import *

app = Client("bot_account", api_id, api_hash)

print("BOT STARTED. Press CTRL+C to exit.")
app.run()