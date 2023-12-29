######################
###### Youtube  ######
######################

# importing main modules
import time
from pyrogram import Client, filters 
import os
import yt_dlp
from datetime import datetime
import shutil
import config as cfg
from pyrogram.types import (ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton)
from pyrogram import enums


# importing some texts from replies.py
from replies import (help_text, 
                     dl_text, 
                     upl_text, 
                     about_text, 
                     err_dl_vid_text, 
                     err_upl_vid_text, 
                     start_text, 
                     VIDEO_FORMATS,
                     liness
                    )


# importing inline buttons from buttons.py
from buttons import START_BUTTON, ABOUT_BUTTON, DL_COMPLETE_BUTTON

# calling api_id and hash to variables
api_id = cfg.api_id
api_hash = cfg.api_hash
LINK_LOGS = cfg.LINK_LOGS # Telegram group id


# get the current path/directory
cwd = os.getcwd()


# Start the client object
bot = Client("bot_account")


# date time
started = datetime.now().strftime('Date: %Y-%m-%d Time: %H:%M')


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
@bot.on_message(filters.text) # check for new incoming text messages
async def download_video(bot, message):
    
    # creating a variable that will print username and id of users who contact the bot (console)
    # this is useful to know who sent what to the bot
    display_log = print(f"""\nName: {message.from_user.first_name}
ID: {message.from_user.id}
Message: {message.text}
Chat Type: {message.chat.type}
{liness}""")
    

################## deleting existing videos before program starts ######################
    try: # using a try tatement to control errors
        for file in os.listdir(cwd): # for evry file in the current directory
            for i in VIDEO_FORMATS: # check all the items/strings in the list "VIDEO_FORMATS"
                if file.lower().endswith(i): # if the file ends with a variable in the list "VIDEO_FORMATS"
                    os.remove(file) # remove that file
    except Exception as e: # when an error occurs
        print(e) # print the error

    # check if the new text message is a youtube link
    if message.text.startswith('https://youtu') or "https://www.youtu" in message.text:
        downloading = await message.reply(dl_text) # send a message to the user (telegram)
        

        #############################################################################
        #########################  Downloading the video ############################
        #############################################################################
        try: # using try statement so that code continues when there is an error
            height: str = 140
            fps: str = 25
            # 'outtmpl':'video','windowsfilenames': '',
            # options to download the video with i.e video resolution
            opts = {"format": f"((bv*[fps>={fps}]/bv*)[height<={height}]/(wv*[fps>={fps}]/wv*)) + ba / (b[fps>{fps}]/b)[height<={height}]/(w[fps>={fps}]/w)"}
            # initiate the extraction process and download the video
            with yt_dlp.YoutubeDL(opts) as ydl:
                # assign the extracted data to a variable
                info_dict = ydl.extract_info(url = message.text, download=True)
                title: str = info_dict.get('title', str) # title of the video
                extension: str = info_dict.get('ext', str) # extension of the video .mp4, .mkv etc
                dur: str = info_dict.get('duration_string', str) # duration of the vide
                res: str = info_dict.get('resolution', str) # resolution of the video
                upload_date = info_dict.get('upload_date') # date of upload (youtube)
                id = info_dict.get('id') # unique ID of the video



            ######## check if there is a vidoe file that ends with the current video extension ######
            for file in os.listdir(cwd):
                if file.endswith(extension): # if the video is found
                    video_path = os.path.join(cwd, file) # assign the filename to a variable
                    # info.append(v_path) # add the filename to a list[]
            # video_path: str = info[-1] # assign the index of the filename from the list to a variable

            
        except Exception as e: # if there was an error
            print(e) # print the error message and continue
            await downloading.delete() # delete the downloading message sent to the user
            await message.reply(f"Hey {message.from_user.mention}\n{err_dl_vid_text}") # and send and error message
            print(liness) # print some lines when everything is complete (console)
            return
        

        ################### Uploading the video ####################
        uploading = await downloading.edit(upl_text) # send message status of the video to the user
        print('\nStatus: Sending video...') # print status to the console


        async def progress(current, total): # defining a function to show the progress of the upload (console)
            print(f"{current * 100 / total:.1f}%")
            return


        try: # using try statement so that code continues when there is an error

            await bot.send_chat_action(message.chat.id, enums.ChatAction.UPLOAD_VIDEO)
            reply_markup = InlineKeyboardMarkup(DL_COMPLETE_BUTTON)
            await bot.send_video(message.chat.id,
                                 video_path,
                                 caption=f"<code>{title}.{extension}</code>",
                                 progress=progress,
                                 file_name=f"{title}.{extension}",
                                 reply_to_message_id = message.id,
                                 reply_markup = reply_markup
                                ) # send that video
            print(liness) # print a horizontal line
            # display_log # print username and id of users who contact the bot (console)

            await uploading.delete() # send success message to user
         
                

        except Exception as e: # if there was an error

            print(f'\nError sending video\n{e}\npath: {video_path}\ntitle: {title}\nextension: {extension}') # print an error message (console)
            await uploading.delete()

            await bot.send_message(message.chat.id, err_upl_vid_text, reply_to_message_id = message.id) # send an error message to the user
            print(liness)

            return # stop the program
        


################ setting up the link logs ########################
        try: # using try statement so that code continues when there is an error
            
            await bot.send_message(LINK_LOGS, f"""
**Filename:**
<code>{title}.{extension}</code>

**Download by:** @{message.from_user.username}
**ID:** <code>{message.from_user.id}</code>

**Chat_username:** {'@'+message.chat.username if message.chat.username is not None else None}
**Chat_type:** __{message.chat.type}__
**Chat_id:** `{message.chat.id}`
**Time:** `{message.date}`

<b>Link:</b>
{message.text}
""",
disable_web_page_preview=True     )

        except Exception as e:
            print(e)
            await bot.send_message(LINK_LOGS, f"""@{message.from_user.username}\n{err_dl_vid_text}\n""")
        



####################### Moving the video to folder (/videos) ##############################

        try: # using try statement so that code continues when there is an error
            
            shutil.move(f"{video_path}", f"videos/{title}.{extension}") # moving the video file to the folder
        except Exception as e: # if that doesn't work...
            print(e) # print the particular error
            print('Error moving file to directory. Deleting file...') # print an error message to the console
            os.remove(video_path) # remove the video
            print('File deleted!') # print "file deleted"
            print(liness) # print some liness to represent the end of the program
            return # stop the program
        
        
        

# print a message to the console when the bot starts (console)
print(f'\nStarted successfully at {started}\nPress CTRL + C to stop')

# Automatically start() and idle()
bot.run()