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


api_id = cfg.api_id
api_hash = cfg.api_hash

cwd = os.getcwd()



################### adding a link log ############################
link_logs = -1001707194213



# Start the client object
bot = Client("bot_account")

# date time
started = datetime.now().strftime('Date: %Y-%m-%d Time: %H:%M')

# some lines to display at the bottom when everything is done.
from replies import liness

# importing some texts from replies.py
from replies import help_text, dl_text, upl_text, about_text, err_dl_vid_text, err_upl_vid_text, start_text



# creating command handler for /start
@bot.on_message(filters.command('start'))
async def start_command(bot, message):
    await message.reply(f'Hello {message.from_user.mention} 👀\n{start_text}')
    

# creating command handler for /help
@bot.on_message(filters.command('help'))
async def help_command(bot, message):
    await message.reply(help_text)


# creating command handler for /about
@bot.on_message(filters.command('about'))
async def about_command(bot, message):
    await message.reply(about_text)

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
            
            async def download_vid(url):
                height: str = 360
                fps: str = 30
                # 'outtmpl':'video','windowsfilenames': '',
                opts = {"format": f"((bv*[fps>={fps}]/bv*)[height<={height}]/(wv*[fps>={fps}]/wv*)) + ba / (b[fps>{fps}]/b)[height<={height}]/(w[fps>={fps}]/w)"}
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info_dict = ydl.extract_info(url=message.text, download=True)
                    title: str = info_dict.get('title', str)
                    title_original: str = info_dict.get('title', str)
                    extension: str = info_dict.get('ext', str)
                    dur: str = info_dict.get('duration_string', str)
                    res: str = info_dict.get('resolution', str)
                    upload = info_dict.get('upload_date')
                    id = info_dict.get('id')
                    for i in str(title):
                        title = title.replace(" ", '_')
                    info.append(title)
                    info.append(extension)
                    info.append(dur)
                    info.append(res)
                    info.append(height)
                    info.append(title_original)
            await download_vid(url=message.text)
            title = info[0]
            extension = info[1]
            dur = info[2]
            res = info[3]
            height = info[4]
            title_original = info[-1]
            trimmed_title = info[-1][0:10]
            print(f"Title: {trimmed_title} Extension: {extension}") 
            for file in os.listdir(cwd):
                if file.startswith(trimmed_title) and file.endswith(extension):
                    title_final = os.path.join(cwd, file)
                    print(title_final)
            
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
            
        try: # using try statement so that code continues when there is an error

           
            await bot.send_video(message.chat.id, title_final, caption=f"<code>{title_original}.{extension}</code>", progress=progress, file_name=f"{title_original}.{extension}") # send that video
                
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
            await bot.send_message(link_logs, f"""
<b>Filename:</b> 
<code>{title_original}.{extension}</code>

<b>Task by:</b> @{message.from_user.username}
<b>ID:</b> <code>{message.from_user.id}</code>
<b>Chat_username:</b> @{message.chat.username}
**Chat_title:** {message.chat.title}
<b>Time:</b> <code>{message.date}</code>

<b>Link:</b>
<code>{message.text}</code>
""")
        except:
            await bot.send_message(link_logs, f"""@{message.from_user.username}\n{err_dl_vid_text}\n""")
        



        ####################### Moving the video to folder (/videos) ##############################

        try: # using try statement so that code continues when there is an error
            
            shutil.move(f"{title_final}", f"videos/{title_original}.{extension}") # moving the video file to the folder
        except: # if that doesn't work...
            print('Error moving file to directory. Deleting file...') # print an error message to the console
            os.remove(title_final)
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