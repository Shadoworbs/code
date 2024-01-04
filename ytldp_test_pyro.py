######################
###### Youtube  ######
######################

# importing main modules
import asyncio
import time
from pyrogram import Client, filters 
import os
import yt_dlp
from datetime import datetime
import shutil
import config as cfg
from pyrogram.types import (ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery)
from pyrogram import enums


# importing some texts from replies.py
from replies import *


# importing inline buttons from buttons.py
from buttons import *

# importing api_id and hash from config.py
api_id = cfg.api_id
api_hash = cfg.api_hash
LINK_LOGS = cfg.LINK_LOGS # Telegram group id


# get the current path/directory
cwd = os.getcwd()


# Start the client object
bot = Client("bot_account")


# assign date time to a variable
now = datetime.now()


# creating command handler for /start
@bot.on_message(filters.command('start') & filters.private) # filters start commands from private chats
async def start_command(bot, message): # initiate a function to respond to the command
    # send a reply message to the command
    await message.reply(text = f'{start_text.format(message.from_user.mention)}',
                        reply_markup = InlineKeyboardMarkup(START_BUTTON),
                        disable_web_page_preview = True
                       )


# creating command handler for /help
@bot.on_message(filters.command('help') & filters.private) # filters help commands from private chats
async def help_command(bot, message): # initiate a function to respond to the command
    await message.reply(help_text) # send a reply message to the command


# creating command handler for /about
@bot.on_message(filters.command('about') & filters.private) # filters about commands from private chats
async def about_command(bot, message): # initiate a function to respond to the command
    # send a reply message to the command
    await message.reply(text = "**💁 Some details about Me 💁**",
                        reply_markup = InlineKeyboardMarkup(ABOUT_BUTTON),
                        disable_web_page_preview = True
                        )
    

# list placeholders to hold global variables
VIDEO_TITLE = []
VIDEO_EXTENSION = []
LINK = []
CHAT_ID = []
MESSAGE_FROM_USER_ID = []
USER_MENTION = []
USER_ID = []
CALLBACK_MSG_ID = []
CALLBACK_MESSAGE = []
INIT_TIME = []


# defining the function to download the video
async def download_vid(height, url):
    # options to download the video with i.e video resolution
    opts = {"format": f"((bv*[fps>=60]/bv*)[height<={height}]/(wv*[fps>=60]/wv*)) + ba / (b[fps>60]/b)[height<={height}]/(w[fps>=60]/w)"}
    # initiate the extraction process and download the video
    with yt_dlp.YoutubeDL(opts) as ydl:
        # assign the extracted data to a variable
        info_dict = ydl.extract_info(url, download=True)  # extract info from the url
        title: str = info_dict.get('title', str) # title of the video
        extension: str = info_dict.get('ext', str) # extension of the video .mp4, .mkv etc
        dur: str = info_dict.get('duration_string', str) # duration of the vide
        res: str = info_dict.get('resolution', str) # resolution of the video
        upload_date = info_dict.get('upload_date') # date of upload (youtube)
        id = info_dict.get('id') # unique ID of the video
        VIDEO_TITLE.append(title) # add video title as a global variable
        VIDEO_EXTENSION.append(extension) # add video extension as a global variable



@bot.on_message(filters.regex("youtu") & filters.group)
async def check_youtube_links(bot, message):
    if len(message.text) > 30:
        CALLBACK_MSG = await message.reply(VIDEO_HEIGHT_TEXT, reply_markup=InlineKeyboardMarkup(VIDEO_HEIGHT_BUTTON))
        callback_time = datetime.now().strftime("%Y%m%d%H%M")
        INIT_TIME.append(int(callback_time))
        CALLBACK_MESSAGE.append(CALLBACK_MSG)
        LINK.append(message.text)
        CHAT_ID.append(message.chat.id)
        MESSAGE_FROM_USER_ID.append(message.id)
        USER_MENTION.append(message.from_user.mention)
        CALLBACK_MSG_ID.append(CALLBACK_MSG.id)
        USER_ID.append(message.from_user.id)


# function to retrieve the video downloaded
def get_video_path():
    """
    This function will check the current directory and see if there is
    a video with the same title as the video doenloaded from the link.
    If there is such a video, return the path of that video as a string.
    """
    title = VIDEO_TITLE[-1]
    extension = VIDEO_EXTENSION[-1]
    for file in os.listdir(cwd):
        if file.startswith(title[0:5]) and file.endswith(extension):
            path = os.path.join(cwd, file)
            return str(path)


# function to delete all video files from the directory
async def remove_all_videos():
    """
    This function looks through all the files in the current directory
    and then if the filename ends with a video format.
    There is a list conatining all known vido formats.
    If the video in the directory's extension is in the list of video extensions,
    delete that video.
    """
    for file in os.listdir(cwd):
        for i in VIDEO_FORMATS:
            if file.endswith(i):
                os.remove(file)


@bot.on_callback_query()
async def youtube_video_downloader_bot(Client, callbackQuery):
    def progress(current, total):
        print(f"Uploaded {current} of {total} bytes ({current * 100 / total:.1f}%)")
    if callbackQuery.data:
        if int(datetime.now().strftime("%Y%m%d%H%M")) < int(INIT_TIME[-1]) + 2:
            try:
                await bot.delete_messages(chat_id=CHAT_ID[-1], message_ids=int(CALLBACK_MSG_ID[-1]))
                await asyncio.sleep(1)
                statu_msg = await bot.send_message(CHAT_ID[-1], f"{dl_text}\n**By:** {USER_MENTION[-1]}\n**User ID:** `{USER_ID[-1]}`")
            except Exception as e:
                print(e)
                await bot.send_message(CHAT_ID[-1], "You clicked on an old button. Please send a new link.")
            try:
                await download_vid(height=callbackQuery.data, url=LINK[-1])
            except Exception as e:
                print(e)
                await bot.delete_messages(CHAT_ID[-1],statu_msg.id)
                await bot.send_message(CHAT_ID[-1], f"{USER_MENTION[-1]} **an error occured when downloading.**\n\n`{e}`")
                print("\nExiting...\n",liness)
                return
            try:
                await bot.edit_message_text(CHAT_ID[-1], statu_msg.id, f"**Download complete.**")
                await asyncio.sleep(1)
            except Exception as e:
                print(e)
                print(liness)
                await bot.delete_messages(CHAT_ID[-1], statu_msg.id)
                await bot.send_message(CHAT_ID, f"This error occured while sending Download complete.\n`{e}`")
                return
            try:
                await bot.edit_message_text(CHAT_ID[-1], statu_msg.id, f"{upl_text}\n**By:** {USER_MENTION[-1]}\n**User ID:** `{USER_ID[-1]}`")
            except Exception as e:
                print(e)
                print(liness)
                await bot.delete_messages(CHAT_ID[-1], statu_msg.id)
                await bot.send_message(CHAT_ID, f"This error occured when editing a message.\n`{e}`")
                return
            
            try:
                send = await bot.send_video(
                CHAT_ID[-1],
                get_video_path(),
                reply_markup=InlineKeyboardMarkup(DL_COMPLETE_BUTTON),
                caption = f"**Hey** {USER_MENTION[-1]}\n{DL_COMPLETE_TEXT.format(LINK[-1])}\nVia @pyroseriesrobot",
                file_name=f"{VIDEO_TITLE[-1]}.{VIDEO_EXTENSION[-1]}",
                reply_to_message_id=MESSAGE_FROM_USER_ID[-1],
                supports_streaming=True,
                progress=progress
                )
                print(liness)
                await bot.delete_messages(CHAT_ID[-1], statu_msg.id)
                os.remove(get_video_path())
            except Exception as e:
                print(e)
                await bot.send_message(CHAT_ID[-1], f"⚠️ {USER_MENTION[-1]} **an error occured while uploading.⚠️**\n\n`{e}`")
        else:
            await bot.send_message(CHAT_ID[-1], f"Hey {USER_MENTION[-1]}\nThis button has expired ⛓. Please send another link 🔗")


# command to delete all videos in directory
@bot.on_message(filters.command("clean"))
async def clean_directory(bot, message):
    deleting = await message.reply("**__Deleting all videos in directory 🗑__**")
    await asyncio.sleep(3)
    try:
        await remove_all_videos()
    except Exception as e:
        print(e)
        pass
    await deleting.edit("**__All videos removed sucessfully ✅__**")
    await asyncio.sleep(3)
    await message.delete(message.text)
    await asyncio.sleep(1)
    await deleting.delete()
            
        

# print to the console
print(f"\nBOT STARTED\n{now:%A, %d %B %Y}. {now:%H:%M}")
# run the current program
bot.run()