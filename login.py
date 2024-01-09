from pyrogram import Client
from config import *

app = Client("my_account", api_id, api_hash)

app.run()