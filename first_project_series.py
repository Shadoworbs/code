import time
from pyrogram import Client, filters, emoji
from datetime import datetime, timedelta
from replies import *
from pyrogram import enums

api_id = 11518683
api_hash = "100b7f1911bdb7d71a0bcde24e3408e6"
# bot_token = "6740634486:AAHNYCfCcpSdZk6-kBOX6lhGxrV7F_HCbwM"
# bot = client('bot_account'


############### Global variables #############
CHAT = "pyrotestrobot"
STARTED = datetime.now().strftime("%Y-%m-%d %H:%M")
ADMINS = [1854174598]



#################### creating a bot that replies to commands #####################
bot = Client("bot_account", api_id=api_id, api_hash=api_hash)

# creating a command handler for /start
@bot.on_message(filters.command("start"))
async def start_command(bot, message):
    await bot.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    time.sleep(3)
    await bot.send_message(message.chat.id, f'Hello {message.from_user.mention} 👀\n{start_text}')
    
# creating a command handler for /help
@bot.on_message(filters.command("help"))
async def help_command(bot, message):
    await bot.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    time.sleep(3)
    await message.reply(help_text)

# creating a command handler for /about
@bot.on_message(filters.command('about'))
async def about_command(bot, message):
    await bot.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    time.sleep(3)
    await message.reply(about_text)



################ creating a bot to send user detais i.e username, DC_ID, ID, first_name, last_name etc #############
@bot.on_message(filters.command('id'))
async def user_info(bot, message):
    await bot.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    time.sleep(3)
    await message.reply(f"""
**__--User Details:--__**
Username: <code>{message.from_user.username}</code>
ID: <code>{message.from_user.id}</code>
First Name: <code>{message.from_user.first_name}</code>
Last Name: <code>{message.from_user.last_name}</code>
DC: <code>{message.from_user.dc_id}</code>\n
**__--Chat Details:--__**
Chat type: **{message.chat.type}**
Chat ID: `{message.chat.id}`
Chat Username: `{message.chat.username}`
Chat First Name: `{message.chat.first_name}`
Chat Last Name: `{message.chat.last_name}`
Date: `{message.date}`\n
**__--Message Details--__**
Message ID: {message.id}""")
    # await message.reply(message) # details of the message object
    


#################### creating an echo bot that sends back what the user sent #####################
@bot.on_message(filters.text & filters.private)
async def echo(bot, message):
    await bot.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    time.sleep(3)
    await message.reply(message.text)


################## creating a welcome bot that welcomes users upon joining #####################
@bot.on_message(filters.chat(CHAT) & filters.new_chat_members)
async def welcome(bot, message):
    await message.reply(f"Hello {message.from_user.mention} {emoji.SPARKLES}\nWelcome to {message.chat.username}")


############# making the bot leave the chat (admins only)######################
@bot.on_message(filters.command('leave') & filters.group)
async def bot_leave_chat(bot, message):
    if message.from_user.id in ADMINS: # check if the user's ID is in the list of admins (local variable ADMINS line 17)
        await message.reply(f"Alright, I'm leaving now. Bye {emoji.WAVING_HAND_LIGHT_SKIN_TONE}")
        await bot.leave_chat(message.chat.id)
    else:
        # await message.reply(f"You can't tell me to leave this chat.\nYou are not my boss! {emoji.ANGRY_FACE}")
        await message.reply(f"{emoji.CANCEL_TAG} You need admin permission for this.")



################## sending a photo from a url #########################
@bot.on_message(filters.command("photo"))
async def photo_command(bot, message):
    await bot.send_chat_action(message.chat.id, enums.ChatAction.UPLOAD_PHOTO)
    time.sleep(3)
    await bot.send_photo(message.chat.id, "AgACAgQAAx0CfM1D4AACARBlhNgwDxXypP1QNu381ehMXtZVBAACHr4xGxVSKVCSwZ4iYek0ZwAIAQADAgADeQAHHgQ", caption='photo from unsplash.com')


@bot.on_message(filters.photo)
async def get_photo_id(bot, message):
    await bot.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    time.sleep(3)
    await message.reply(message.photo.file_id)



#################### ban a user from a chat ####################
@bot.on_message(filters.command("ban") & filters.group)
async def ban_user(bot, message):
    await bot.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    time.sleep(3)
    if message.from_user.id in ADMINS:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id, datetime.now() + timedelta(seconds=120.0))
        await message.reply(f"{message.reply_to_message.from_user.mention} banned !")
    else:
        await message.reply(f"{emoji.RED_EXCLAMATION_MARK} You need admin permission for this.")



################### Unban a user from chat ######################
@bot.on_message(filters.command("unban") & filters.group)
async def unban_user(bot, message):
    await bot.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    time.sleep(3)
    if message.from_user.id in ADMINS:
        await bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.reply(f"{message.reply_to_message.from_user.mention} unbannd")
    else:
        await message.reply(f"{emoji.CANCEL_TAG} You need admin permission for this.")



#################### Deleting text messages #########################
@bot.on_message(filters.text) # filter incoming text messages
async def delete_message(bot, message): # function to handle the incoming messages
    await bot.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    time.sleep(3)
    blacklist = ["fuck", "wtf"] # a list of words not allowed
    if message.text in blacklist: # if someone sends one of the above words
        await bot.delete_messages(message.chat.id, message.id) # delete their message
        await message.reply(f"@{message.from_user.username}, your message was deleted because it's blacklisted !")




# print to the console
print(f'\nBOT STARTED AT {STARTED}')
# run the current program
bot.run()
