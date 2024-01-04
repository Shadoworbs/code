import time
from pyrogram import Client, filters, emoji
from datetime import datetime, timedelta
from replies import *
from pyrogram import enums
import config as cfg
import yt_dlp
from buttons import (DL_COMPLETE_BUTTON, PAGE3_BUTTON, PAGE3_TEXT, REPLY_BUTTONS, 
                     MAIN_PAGE_BUTTON, 
                     PAGE2_BUTTON, 
                     PAGE1_BUTTON, 
                     PAGE1_TEXT,
                     PAGE2_TEXT,
                     MAIN_PAGE_TEXT,
                     VIDEO_HEIGHT_BUTTON,
                     VIDEO_HEIGHT_TEXT
                    )
from pyrogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, CallbackQuery


api_id = cfg.api_id
api_hash = cfg.api_hash
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
    time.sleep(1)
    await bot.send_message(message.chat.id, f'Hello {message.from_user.mention} 👀\n{start_text}')
    
# creating a command handler for /help
@bot.on_message(filters.command("help"))
async def help_command(bot, message):
    await bot.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    time.sleep(1)
    await message.reply(help_text)

# creating a command handler for /about
@bot.on_message(filters.command('about'))
async def about_command(bot, message):
    await bot.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    time.sleep(1)
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
    


# #################### creating an echo bot that sends back what the user sent #####################
# @bot.on_message(filters.text & filters.private)
# async def echo(bot, message):
#     await bot.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
#     time.sleep(3)
#     await message.reply(message.text)


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
    time.sleep(1)
    await bot.send_photo(message.chat.id, "AgACAgQAAx0CfM1D4AACARBlhNgwDxXypP1QNu381ehMXtZVBAACHr4xGxVSKVCSwZ4iYek0ZwAIAQADAgADeQAHHgQ", caption='photo from unsplash.com')


@bot.on_message(filters.photo)
async def get_photo_id(bot, message):
    await bot.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    time.sleep(1)
    await message.reply(message.photo.file_id)



#################### ban a user from a chat ####################
@bot.on_message(filters.command("ban") & filters.group)
async def ban_user(bot, message):
    await bot.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    time.sleep(1)
    if message.from_user.id in ADMINS:
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id, datetime.now() + timedelta(seconds=120.0))
        await message.reply(f"{message.reply_to_message.from_user.mention} banned !")
    else:
        await message.reply(f"{emoji.RED_EXCLAMATION_MARK} You need admin permission for this.")



################### Unban a user from chat ######################
@bot.on_message(filters.command("unban") & filters.group)
async def unban_user(bot, message):
    await bot.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    time.sleep(1)
    if message.from_user.id in ADMINS:
        await bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.reply(f"{message.reply_to_message.from_user.mention} unbannd")
    else:
        await message.reply(f"{emoji.CANCEL_TAG} You need admin permission for this.")


##################### Trying out replykeyboardmarkup ###########################
@bot.on_message(filters.command("hello"))
async def reply_keyboard_hello(bot, message):
    reply_markup = ReplyKeyboardMarkup(REPLY_BUTTONS, resize_keyboard=True, one_time_keyboard=True, placeholder="placeholder")
    await message.reply(text = "This is an inlinekeyboard reply",
                        reply_markup = reply_markup
                       )
    time.sleep(3)
    await bot.send_message(message.chat.id, "new message", reply_markup= ReplyKeyboardRemove())




#################### Deleting text messages #########################
# @bot.on_message(filters.text) # filter incoming text messages
# async def delete_message(bot, message): # function to handle the incoming messages
#     await bot.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
#     time.sleep(1)
#     blacklist = ["fuck", "wtf"] # a list of words not allowed
#     if message.text in blacklist: # if someone sends one of the above words
#         await bot.delete_messages(message.chat.id, message.id) # delete their message
#         await message.reply(f"@{message.from_user.username}, your message was deleted because it's blacklisted !")
INFO_TITLE = []
INFO_EXTENSION = []
async def download_vid(height, url):
    # 'outtmpl':'video','windowsfilenames': '',
    # options to download the video with i.e video resolution
    opts = {"format": f"((bv*[fps>=60]/bv*)[height<={height}]/(wv*[fps>=60]/wv*)) + ba / (b[fps>60]/b)[height<={height}]/(w[fps>=60]/w)"}
    # initiate the extraction process and download the video
    with yt_dlp.YoutubeDL(opts) as ydl:
        # assign the extracted data to a variable
        info_dict = ydl.extract_info(url, download=True)
        title: str = info_dict.get('title', str) # title of the video
        extension: str = info_dict.get('ext', str) # extension of the video .mp4, .mkv etc
        dur: str = info_dict.get('duration_string', str) # duration of the vide
        res: str = info_dict.get('resolution', str) # resolution of the video
        upload_date = info_dict.get('upload_date') # date of upload (youtube)
        id = info_dict.get('id') # unique ID of the video
        INFO_TITLE.append(title)
        INFO_EXTENSION.append(extension)


##################### Callback Querry ############################

# @bot.on_message(filters.regex("youtu"))
# async def callback__Query(bot, message):
#     reply_markup = InlineKeyboardMarkup(MAIN_PAGE_BUTTON)
#     call_buttons = await message.reply(
#         MAIN_PAGE_TEXT,
#         reply_markup = reply_markup
#     )
#     LINK.append(message.text)
    
LINK = []
CHAT_ID = []
MSG_ID = []
USER_MENTION = []
USER_ID = []
MAIN_MSG = []
@bot.on_message(filters.regex("youtu") & filters.group)
async def call(bot, message):
    main_msg = await message.reply(VIDEO_HEIGHT_TEXT, reply_markup=InlineKeyboardMarkup(VIDEO_HEIGHT_BUTTON))
    LINK.append(message.text)
    CHAT_ID.append(message.chat.id)
    MSG_ID.append(message.id)
    USER_MENTION.append(message.from_user.mention)
    MAIN_MSG.append(main_msg.id)
    USER_ID.append(message.from_user.id)
    


# @bot.on_callback_query()
# async def callback_response(Client, callbackQuery):
#     if callbackQuery.data == "page1":
#         await callbackQuery.edit_message_text(
#             PAGE1_TEXT,
#             reply_markup = InlineKeyboardMarkup(PAGE1_BUTTON)
#         )
#     elif callbackQuery.data == "back_to_main_menu":
#         await callbackQuery.edit_message_text(
#             MAIN_PAGE_TEXT,
#             reply_markup = InlineKeyboardMarkup(MAIN_PAGE_BUTTON)
#         )
#     elif callbackQuery.data == "page2":
#         await callbackQuery.edit_message_text(
#             PAGE2_TEXT,
#             reply_markup = InlineKeyboardMarkup(PAGE2_BUTTON)
#         )
#     elif callbackQuery.data == "page3":
#         await callbackQuery.edit_message_text(
#             PAGE3_TEXT,
#             reply_markup = InlineKeyboardMarkup(PAGE3_BUTTON)
#         )
#     elif callbackQuery.data == "back_to_page_1":
#             await callbackQuery.edit_message_text(
#             PAGE1_TEXT,
#             reply_markup = InlineKeyboardMarkup(PAGE1_BUTTON)
#         )
#     elif callbackQuery.data == "back_to_page_2":
#             await callbackQuery.edit_message_text(
#             PAGE2_TEXT,
#             reply_markup = InlineKeyboardMarkup(PAGE2_BUTTON)
#         )
#     elif callbackQuery.data == "cancel":
#         await callbackQuery.edit_message_text("Message Cancelled")
#         await Client.send_message(CHAT_ID, "IT WORDED!")
#         download_vid(height=callbackQuery.data, url=LINK[-1])

import os
cwd = os.getcwd()
async def getpath():
    title = INFO_TITLE[-1]
    extension = INFO_EXTENSION[-1]
    for file in os.listdir(cwd):
        if file.startswith(title[0:5]) and file.endswith(extension):
            path = os.path.join(cwd, file)
            print(liness)
            return str(path)

@bot.on_callback_query()
async def dl(Client, callbackQuery):
    if callbackQuery.data:
        await callbackQuery.edit_message_text(f"{dl_text}\n**By:** {USER_MENTION[-1]}\n**User ID:** `{USER_ID[-1]}`")
        await download_vid(height=callbackQuery.data, url=LINK[-1])
        await callbackQuery.edit_message_text("**Download Complete**")
        time.sleep(1)
        await callbackQuery.edit_message_text(f"{upl_text}\n**By:** {USER_MENTION[-1]}\n**User ID:** `{USER_ID[-1]}`")
        await bot.send_video(
            CHAT_ID[-1],
            await getpath(),
            reply_markup=InlineKeyboardMarkup(DL_COMPLETE_BUTTON),
            caption = f"**Hey** {USER_MENTION[-1]}\n{DL_COMPLETE_TEXT}\n**Via:** @pyroseriesrobo",
            file_name=f"{INFO_TITLE[-1]}.{INFO_EXTENSION[-1]}",
            reply_to_message_id=MSG_ID[-1]
        )
        print(liness)
        await bot.delete_messages(chat_id=CHAT_ID[-1], message_ids=int(MAIN_MSG[-1]))



# print to the console
print(f'\nBOT STARTED AT {STARTED}')
# run the current program
bot.run()
