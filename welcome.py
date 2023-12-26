
from pyrogram import Client, emoji, filters

# Target chat. Can also be a list of multiple chat ids/usernames
TARGET = -1002093827040
# Welcome message template
MESSAGE = "{} Welcome to [Pyrogram](https://docs.pyrogram.org/)'s group chat {}!"

bot = Client("bot_account")


# Filter in only new_chat_members updates generated in TARGET chat
@bot.on_message(filters.chat(TARGET) & filters.new_chat_members)
async def welcome(client, message):
    # Build the new members list (with mentions) by using their first_name
    new_members = [u.mention for u in message.new_chat_members]
    # Build the welcome message by using an emoji and the list we built above
    text = MESSAGE.format(emoji.SMIRKING_FACE, message.from_user.mention)
    # Send the welcome message, without the web page preview
    await message.reply_text(text, disable_web_page_preview=True)

print("BOT STARTED")
bot.run()  # Automatically start() and idle()""