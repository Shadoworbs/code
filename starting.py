
from pyrogram import client, filters
import config as cfg


api_id = cfg.api_id
api_hash = cfg.api_hash
# bot_token = "6740634486:AAHNYCfCcpSdZk6-kBOX6lhGxrV7F_HCbwM"
# bot = client('bot_account')



from pyrogram import Client
from datetime import datetime


bot = Client("bot_account", api_id=api_id, api_hash=api_hash)
STARTED = datetime.now().strftime("%Y-%m-%d %H:%M")


@bot.on_message(filters.command('start') & filters.private)
def command1(bot, message):
    bot.send_message(message.chat.id, f'Hello, {message.from_user.mention} I am a simple pyrogram bot.')

@bot.on_message(filters.text)
def echo(bot, message):
    message.reply(f"""
DC: <code>{message.from_user.dc_id}</code>
ID: <code>{message.from_user.id}</code>
First Name: <code>{message.from_user.first_name}</code>
Last Name: <code>{message.from_user.last_name}</code>
Username: <code>{message.from_user.username}</code>
message: <code>{message.text}</code>""".strip()
    )



print(f"BOT STARTED AT {STARTED}")
bot.run()


