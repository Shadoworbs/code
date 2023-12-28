######################
###### Youtube  ######
######################


import time
from pyrogram import Client, filters 
import os
import yt_dlp
from datetime import datetime
from genericpath import isfile
import shutil
import config as cfg
from pyrogram.types import (ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton)
from pyrogram import enums


# importing some texts from replies.py
from replies import help_text, dl_text, upl_text, about_text, err_dl_vid_text, err_upl_vid_text, start_text

# importing from buttons.py
from buttons import START_BUTTON, ABOUT_BUTTON, DL_COMPLETE_BUTTON


api_id = cfg.api_id
api_hash = cfg.api_hash

cwd = os.getcwd()



################### adding a link log ############################
LINK_LOGS = -1001707194213



# Start the client object
bot = Client("bot_account")

# date time
started = datetime.now().strftime('Date: %Y-%m-%d Time: %H:%M')

# some lines to display at the bottom when everything is done.
from replies import liness



# creating command handler for /start
@bot.on_message(filters.command('start') & filters.private)
async def start_command(bot, message):
    reply_markup = InlineKeyboardMarkup(START_BUTTON)
    await bot.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    time.sleep(1)
    await message.reply(text = f'Hello {message.from_user.mention} 👀\n{start_text}',
                        reply_markup = reply_markup,
                        disable_web_page_preview = True
                        )


# creating command handler for /help
@bot.on_message(filters.command('help') & filters.private)
async def help_command(bot, message):
    await bot.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    time.sleep(1)
    await message.reply(help_text)



# creating command handler for /about
@bot.on_message(filters.command('about') & filters.private)
async def about_command(bot, message):
    reply_markup = InlineKeyboardMarkup(ABOUT_BUTTON)
    await bot.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    time.sleep(1)
    await message.reply(text = "**Some details about Me**",
                        reply_markup = reply_markup,
                        disable_web_page_preview = True
                        )
    
    
# chat_id = "-1002093827040"
@bot.on_message(filters.text) #check if the message is a text message
async def download_video(bot, message): # main function to download the video
    info = []
    

    # creating a variable that will print username and id of users who contact the bot (console)
    display_log = print(f"\nName: {message.from_user.first_name}\nID: {message.from_user.id}\nMessage: {message.text}\n{liness}" )
    
    if message.text.startswith('https://youtu'):
        downloading = await message.reply(dl_text)
        

        #########################  Downloading the video ############################

        try:
            ############### creating a list to store values from the function below ################
            
            # async def download_vid(url):
            height: str = 360
            fps: str = 30
            # 'outtmpl':'video','windowsfilenames': '',
            opts = {"format": f"((bv*[fps>={fps}]/bv*)[height<={height}]/(wv*[fps>={fps}]/wv*)) + ba / (b[fps>{fps}]/b)[height<={height}]/(w[fps>={fps}]/w)"}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info_dict = ydl.extract_info(url = message.text, download=True)
                title_original: str = info_dict.get('title', str)
                extension: str = info_dict.get('ext', str)
                dur: str = info_dict.get('duration_string', str)
                res: str = info_dict.get('resolution', str)

                upload_date = info_dict.get('upload_date')
                id = info_dict.get('id')
                info.append(extension)
                info.append(dur)
                info.append(res)
                info.append(height)
                info.append(upload_date)
                info.append(id)
                info.append(title_original)
            # download_vid(url = message.text)
            extension = info[0]
            dur = info[1]
            res = info[2]
            height = info[3]
            upload_date = info[4]
            id = info[5]
            title_original = info[6]
            # time.sleep(5)
            for file in os.listdir(cwd):
                if file.startswith(title_original[:5]) and file.endswith(extension):
                    info.append(os.path.join(cwd, file))
            video_path: str = info[-1]

            
        except:
            print('\nVideo download error!')
            await message.reply(err_dl_vid_text)
            print(liness)
            return
        


        ################### Uploading the video ####################

        uploading = await downloading.edit(upl_text) # send message status of the video to the user
        

        print('\nStatus: Sending video...') # print status to the console

        async def progress(current, total): # defining a function to show us the progress of the upload
            print(f"{current * 100 / total:.1f}%")
        # extension:str = info[0]
        # dur:str = info[1]
        # res:str = info[2]
        # height:str = info[3]
        # title_original:str = info[-2]
        # video_path:str = info[-1]    
        try: # using try statement so that code continues when there is an error

            await bot.send_chat_action(message.chat.id, enums.ChatAction.UPLOAD_VIDEO)
            await bot.send_video(message.chat.id,
                                 video_path,
                                 caption=f"<code>{title_original}.{extension}</code>",
                                 progress=progress,
                                 file_name=f"{title_original}.{extension}") # send that video
            print(liness) # print a horizontal line
                # display_log # print username and id of users who contact the bot (console)

            await uploading.edit(f"Hey {message.from_user.mention}\nVideo uploaded successfully ✅") # send success message to user
                
                

        except: # if there was an error

            print('\nError sending video') # print an error message (console)

            await uploading.edit(err_upl_vid_text) # send an error message to the user
            print(liness)

            return # stop the program
        


################ setting up the link logs ########################
        try:
            
            await bot.send_message(LINK_LOGS, f"""
**Filename:**
<code>{title_original}.{extension}</code>

**Download by:** @{message.from_user.username}
**ID:** <code>{message.from_user.id}</code>

**Chat_username:** {'@'+message.chat.username if message.chat.username is not None else None}
**Chat_type:** __{message.chat.type}__
**Chat_id:** `{message.chat.id}`
**Time:** `{message.date}`

<b>Link:</b>
{message.text}
""", disable_web_page_preview=True)
        except:
            await bot.send_message(LINK_LOGS, f"""@{message.from_user.username}\n{err_dl_vid_text}\n""")
        



        ####################### Moving the video to folder (/videos) ##############################

        try: # using try statement so that code continues when there is an error
            
            shutil.move(f"{video_path}", f"videos/{title_original}.{extension}") # moving the video file to the folder
        except: # if that doesn't work...
            print('Error moving file to directory. Deleting file...') # print an error message to the console
            os.remove(video_path)
            print('File deleted!')
            print(liness)
            return # stop the program
        

        # create a function to print out resolution of downloaded videos
        def resolution(res)-> str:
            try:
                return res.split('x')[-1]
            except:
                AttributeError
                return height       



    # # log all the links to a log file for debugging
    
    with open('yl.log', 'a', encoding="utf-8") as f:
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"""Video name: {title_original}.{extension}
Video Duration: {dur}
Video Resolution: {resolution(res)}p
Video Location: {cwd}
Video Link: {message.text}
Date & Time: {date}\n\n""")
        
        

# print a message to the console when the bot starts (console)
print(f'\nStarted successfully at {started}\nPress CTRL + C to stop')

# Automatically start() and idle()
bot.run()