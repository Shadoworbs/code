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
from pyrogram.errors import FloodWait


# importing some texts from replies.py
from replies import *


# importing inline buttons from buttons.py
from buttons import *

# importing api_id and hash from config.py
api_id = cfg.api_id
api_hash = cfg.api_hash
LINK_LOGS = cfg.LINK_LOGS # Telegram group id
LOG_CHANNEL = cfg.LOG_CHANNEL


# get the current path/directory
cwd = os.getcwd()


# Start the client object
# @pyroseriesrobot
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
SELETCT_RESOLUTION_MESSAGE_ID = []
CALLBACK_MESSAGE = []
INIT_TIME = []
formats = []

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
        size = info_dict.get('filesize')
        format = info_dict.get('formats', {})
        formats.append(format)
        VIDEO_TITLE.append(title) # add video title as a global variable
        VIDEO_EXTENSION.append(extension) # add video extension as a global variable
    async def progress(current, total):
        print(f"Downloaded {current} bytes of {total} bytes ({current * 100 / total:.1f})%")



@bot.on_message(filters.regex("youtu") & filters.group)
async def check_youtube_links(bot, message):
    """
    Check the message sent by the user if its a youtu 
    """
    if len(message.text) > 30 and "https://" in message.text:
        SELETCT_RESOLUTION_MESSAGE = await message.reply(VIDEO_HEIGHT_TEXT, reply_markup=InlineKeyboardMarkup(VIDEO_HEIGHT_BUTTON))
        SELETCT_RES_MSG_TIME = datetime.now().strftime("%Y%m%d%H%M")
        INIT_TIME.append(int(SELETCT_RES_MSG_TIME))
        CALLBACK_MESSAGE.append(SELETCT_RESOLUTION_MESSAGE)
        LINK.append(message.text)
        CHAT_ID.append(message.chat.id)
        MESSAGE_FROM_USER_ID.append(message.id)
        USER_MENTION.append(message.from_user.mention)
        SELETCT_RESOLUTION_MESSAGE_ID.append(SELETCT_RESOLUTION_MESSAGE.id)
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

    # PROGRESS_ARGS = []
    @bot.on_callback_query()
    async def youtube_video_downloader_bot(bot, callbackQuery):
        async def progress(current, total):
            print(f"Uploaded {current} of {total} bytes ({current * 100 / total:.1f}%)")
            for i in range(1, total):
                if current != total:
                    pass
                    # await asyncio.sleep(3)
                    # print("Still uploading...")
                    
            # current = current
            # total = total
            # PROGRESS_ARGS.append(current)
            # PROGRESS_ARGS.append(total)
            # msg_id = status_msg.id
    #         if current == total //5 or current == total /5:
    #             await bot.edit_message_text(
    #                 chat_id=message.chat.id,
    #                 message_id=msg_id,
    #                 text=f"""
    # **Statu: [Uploading]({message.text})**

    # ({current * 100 / total:.1f}%) of {total/1000000:.2f} MB.

    # **By:** {message.from_user.mention}
    # **ID:** `{message.from_user.id}`
    # """,
    # disable_web_page_preview=True,
    #         )
        LINK_LOG_BUTTON = [
            [
                InlineKeyboardButton("LINK 🔗", url= f"{message.text}")
            ]
        ]
        if callbackQuery.data:
            if int(datetime.now().strftime("%Y%m%d%H%M")) < int(SELETCT_RES_MSG_TIME) + 2:
                try:
                    await bot.delete_messages(message.chat.id, message_ids=int(SELETCT_RESOLUTION_MESSAGE.id))
                    await asyncio.sleep(1)
                    status_msg = await bot.send_message(message.chat.id, f"{dl_text}\n**By:** {message.from_user.mention}\n**User ID:** `{message.from_user.id}`")
                except Exception as e:
                    print(e)
                    await bot.send_message(message.chat.id, "You clicked on an old button. Please send a new link.")
                try:
                    await download_vid(height=callbackQuery.data, url=message.text)
                except Exception as e:
                    print(e)
                    await bot.delete_messages(message.chat.id,status_msg.id)
                    await bot.send_message(message.chat.id, f"{message.from_user.mention} **an error occured when downloading.**\n\n`{e}`")
                    print("\nExiting...\n",liness)
                    return
                try:
                    await bot.edit_message_text(message.chat.id, status_msg.id, f"**Download complete.**")
                    await asyncio.sleep(1)
                except Exception as e:
                    print(e)
                    print(liness)
                    await bot.delete_messages(message.chat.id, status_msg.id)
                    await bot.send_message(message.chat.id, f"This error occured while sending Download complete.\n`{e}`")
                    return
                try:
                    await bot.edit_message_text(message.chat.id, status_msg.id, f"{upl_text}\n**By:** {message.from_user.mention}\n**User ID:** `{message.from_user.id}`")
                except Exception as e:
                    print(e)
                    print(liness)
                    await bot.delete_messages(message.chat.id, status_msg.id)
                    await bot.send_message(message.chat.id, f"This error occured when editing a message.\n`{e}`")
                    return
                
                try:
                    send = await bot.send_video(
                    message.chat.id,
                    get_video_path(),
                    reply_markup=InlineKeyboardMarkup(DL_COMPLETE_BUTTON),
                    caption = f"**Hey** {message.from_user.mention}\n{DL_COMPLETE_TEXT.format(message.text)}\nVia @pyroseriesrobot",
                    file_name=f"{VIDEO_TITLE[-1]}.{VIDEO_EXTENSION[-1]}",
                    reply_to_message_id=message.id,
                    supports_streaming=True,
                    progress=progress
                    )
                    print(liness)
                    print(formats)
                    await bot.delete_messages(message.chat.id, status_msg.id)
                    # os.remove(get_video_path())
                except Exception as e:
                    print(e)
                    await bot.send_message(message.chat.id, f"{message.from_user.mention} **an error occured while uploading.⚠️**\n\n`{e}`")
                try:
                    await bot.send_message(
                        LINK_LOGS,
                        f"**Filename:**\n`{VIDEO_TITLE[-1]}.{VIDEO_EXTENSION[-1]}`\n\n**User:** {message.from_user.mention}\n**ID:** `{message.from_user.id}`",
                        reply_markup= InlineKeyboardMarkup(LINK_LOG_BUTTON)
                    )
                except Exception as e:
                    pass
                try:
                    await bot.forward_messages(LOG_CHANNEL, message.chat.id, send.id)
                except Exception as e:
                    pass
            else:
                await bot.send_message(message.chat.id, f"Hey {message.from_user.mention}\nThis button has expired ⛓. Please send another link 🔗")


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
