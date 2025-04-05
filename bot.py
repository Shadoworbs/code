######################
###### Youtube  ######
######################

# importing main modules
import dotenv
import sys
import asyncio
import time
from pyrogram import Client, filters
import os
import yt_dlp
from datetime import datetime
import shutil
from dotenv import load_dotenv
from pyrogram.types import (
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from pyrogram import enums
from pyrogram.errors import FloodWait
import logging
from config import LINK_LOGS, LOG_CHANNEL


# importing some texts from replies.py
from replies import *


# importing inline buttons from buttons.py
from buttons import START_BUTTON, ABOUT_BUTTON, DL_COMPLETE_BUTTON

# importing api_id and hash from config.py

load_dotenv()
api_id = os.getenv("api_id")
api_hash = os.getenv("api_hash")
bot_token = os.getenv("bot_token")
LOG_CHANNEL = os.getenv("LOG_CHANNEL")
LINK_LOGS = os.getenv("LINK_LOGS")
AUTH_USERS = os.getenv("AUTH_USERS").split(",")


# get the current path/directory
cwd = os.getcwd()

# Simple in-memory cache for URLs {message_id: url}
# Note: This cache is lost on bot restart.
url_cache = {}


# Start the client object
# "@pyroseriesrobot"

bot = Client("bot_account")


# assign date time to a variable
now = datetime.now()


# creating command handler for /start
@bot.on_message(
    filters.command("start") & filters.private
)  # filters start commands from private chats
async def start_command(bot, message):  # initiate a function to respond to the command
    # send a reply message to the command
    await message.reply(
        text=f"{start_text.format(message.from_user.mention)}",
        reply_markup=InlineKeyboardMarkup(START_BUTTON),
        disable_web_page_preview=True,
    )


# creating command handler for /help
@bot.on_message(
    filters.command("help") & filters.private
)  # filters help commands from private chats
async def help_command(bot, message):  # initiate a function to respond to the command
    await message.reply(help_text)  # send a reply message to the command


# creating command handler for /about
@bot.on_message(
    filters.command("about") & filters.private
)  # filters about commands from private chats
async def about_command(bot, message):  # initiate a function to respond to the command
    # send a reply message to the command
    await message.reply(
        text="**💁 Some details about Me 💁**",
        reply_markup=InlineKeyboardMarkup(ABOUT_BUTTON),
        disable_web_page_preview=True,
    )


# Function to get video info without downloading
async def get_video_info(url):
    """Fetches video title and thumbnail URL without downloading."""
    opts = {
        "cookiefile": "cookies_from_browser firefox",
        "skip_download": True,
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=False)
            title = info_dict.get("title", "Untitled Video")
            thumbnail_url = info_dict.get("thumbnail")
            return title, thumbnail_url
        except yt_dlp.utils.DownloadError as e:
            print(f"Error fetching video info: {e}")
            return None, None


# defining the function to download the video
async def download_vid(height, url):
    """Downloads video and returns filepath, title, and extension."""
    filepath = None
    title = None
    extension = None
    # options to download the video with i.e video resolution
    # Ensure output filenames are unique or handled appropriately if downloads can overlap
    opts = {
        "cookiefile": "cookies_from_browser firefox",
        "format": f"((bv*[fps>=60]/bv*)[height<={height}]/(wv*[fps>=60]/wv*)) + ba / (b[fps>60]/b)[height<={height}]/(w[fps>=60]/w)",
        "outtmpl": f"{cwd}/%(title)s_%(id)s.%(ext)s",  # Example: Ensure unique filenames
    }
    # initiate the extraction process and download the video
    with yt_dlp.YoutubeDL(opts) as ydl:
        # assign the extracted data to a variable
        info_dict = ydl.extract_info(url, download=True)  # extract info from the url
        title = info_dict.get("title", "untitled")  # title of the video
        extension = info_dict.get("ext", "mp4")  # extension of the video .mp4, .mkv etc
        filepath = ydl.prepare_filename(
            info_dict
        )  # Get the actual path of the downloaded file
    return filepath, title, extension


@bot.on_message(filters.regex("youtu") & filters.private)
async def check_youtube_urls(bot, message):
    """
    Check the message sent by the user if its a youtube link.
    Fetches thumbnail and sends resolution options with callback data.
    """
    url = message.text
    if len(url) > 30 and "https://" in url:
        # Fetch video info first
        processing_msg = await message.reply("Processing link...")
        title, thumbnail_url = await get_video_info(url)

        if not title:
            await processing_msg.edit_text(
                "Sorry, couldn't fetch video details. Please check the link."
            )
            return

        # Store the URL in the cache before sending buttons
        url_cache[message.id] = url
        # Optional: Add a mechanism to clean up old entries from url_cache if needed

        # Define resolutions and create buttons dynamically
        resolutions = {"1080": "1080p", "720": "720p", "480": "480p", "360": "360p"}
        buttons = []
        for height, label in resolutions.items():
            # Format: height:message_id (URL is retrieved from cache)
            callback_data = f"{height}:{message.id}"
            # Check if callback_data exceeds Telegram limit (64 bytes)
            if len(callback_data.encode("utf-8")) > 64:
                print(f"Warning: Callback data might be too long: {callback_data}")
                # Handle potential error, maybe skip this button or log it
                continue
            buttons.append([InlineKeyboardButton(label, callback_data=callback_data)])

        keyboard = InlineKeyboardMarkup(buttons)

        caption = f"**{title}**\n\n{VIDEO_HEIGHT_TEXT}"  # Use fetched title

        try:
            if thumbnail_url:
                await message.reply_photo(
                    photo=thumbnail_url, caption=caption, reply_markup=keyboard
                )
            else:
                # Fallback if no thumbnail found
                await message.reply(
                    caption, reply_markup=keyboard, disable_web_page_preview=True
                )
            await processing_msg.delete()  # Delete "Processing link..." message
        except Exception as e:
            print(f"Error sending resolution options: {e}")
            await processing_msg.edit_text(
                f"An error occurred while sending options: {e}"
            )


# Moved callback handler to top level
@bot.on_callback_query(
    filters.regex(r"^\d+:\d+$")
)  # Filter for new format: height:message_id
async def youtube_video_downloader_bot(bot, callbackQuery):
    """Handles button clicks for video resolution selection."""

    # Parse data from callbackQuery
    try:
        height_str, original_msg_id_str = callbackQuery.data.split(":", 1)
        height = int(height_str)
        original_msg_id = int(original_msg_id_str)
        chat_id = callbackQuery.message.chat.id
        user = callbackQuery.from_user

        # Retrieve URL from cache
        url = url_cache.pop(original_msg_id, None)  # Use pop to remove after retrieval

        if not url:
            await callbackQuery.answer(
                "Sorry, the request expired or the bot was restarted. Please send the link again.",
                show_alert=True,
            )
            # Attempt to delete the message with buttons if it still exists
            try:
                await callbackQuery.message.delete()
            except Exception:
                pass  # Ignore if deletion fails
            return

    except ValueError:
        await callbackQuery.answer("Invalid callback data format.", show_alert=True)
        print(f"Invalid callback data: {callbackQuery.data}")
        return
    except Exception as e:
        await callbackQuery.answer("Error processing callback.", show_alert=True)
        print(f"Error parsing callback data: {e}")
        return

    status_msg = None  # Initialize status_msg to None

    # Define upload progress function here
    async def progress(current, total):
        # Simple console log for upload progress
        print(f"Uploaded {current} of {total} bytes ({current * 100 / total:.1f}%)")

    url_LOG_BUTTON = [
        [InlineKeyboardButton("url 🔗", url=url)]
    ]  # URL is now retrieved from cache

    try:
        # Delete the resolution selection message (photo or text)
        await callbackQuery.message.delete()
        # Send initial status message
        status_msg = await bot.send_message(
            chat_id, f"{dl_text}\n**By:** {user.mention}\n**User ID:** `{user.id}`"
        )

        # Download the video
        filepath, title, extension = await download_vid(height=height, url=url)

        if not filepath or not os.path.exists(filepath):
            raise Exception("Download failed or file path not found.")

        await status_msg.edit_text(f"**Download complete.**")
        await asyncio.sleep(1)  # Brief pause

        await status_msg.edit_text(
            f"{upl_text}\n**By:** {user.mention}\n**User ID:** `{user.id}`"
        )

        # Send the video
        send = await bot.send_video(
            chat_id=chat_id,
            video=filepath,
            reply_markup=InlineKeyboardMarkup(DL_COMPLETE_BUTTON),
            caption=f"**Hey** {user.mention}\n{DL_COMPLETE_TEXT.format(url)}\nVia @pyroseriesrobot",
            file_name=f"{title}.{extension}",
            reply_to_message_id=original_msg_id,
            supports_streaming=True,
            progress=progress,
        )
        

        await status_msg.delete()  # Delete status message after successful upload

        # Send logs
        try:
            await bot.send_message(
                LINK_LOGS,
                f"**Filename:**\n`{title}.{extension}`\n\n**User:** {user.mention}\n**ID:** `{user.id}`",
                reply_markup=InlineKeyboardMarkup(url_LOG_BUTTON),
            )
        except Exception as log_err:
            print(f"Error sending link log: {log_err}")
            pass  # Continue even if logging fails

        try:
            await bot.forward_messages(LOG_CHANNEL, chat_id, send.id)
        except Exception as fwd_err:
            print(f"Error forwarding message to log channel: {fwd_err}")
            pass  # Continue even if forwarding fails

    except Exception as e:
        print(f"Error in callback handler: {e}")
        error_message = f"{user.mention} **an error occurred.⚠️**\n\n`{e}`"
        if status_msg:
            try:
                await status_msg.edit_text(error_message)
            except Exception:  # If editing fails, send new message
                await bot.send_message(chat_id, error_message)
        else:
            await bot.send_message(chat_id, error_message)
        # Optional: Answer callback query on error
        try:
            await callbackQuery.answer("An error occurred.", show_alert=True)
        except Exception:
            pass  # Ignore if answering fails

    finally:
        # Clean up downloaded file
        # Ensure filepath variable exists before trying to remove
        if "filepath" in locals() and filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"Removed file: {filepath}")
            except OSError as rm_err:
                print(f"Error removing file {filepath}: {rm_err}")


# command to delete all videos in directory
@bot.on_message(filters.command("clean") & filters.private)
async def clean_directory(bot, message):
    deleting = await message.reply("**__Deleting all videos in directory 🗑__**")
    await asyncio.sleep(3)
    try:
        for file in os.listdir(cwd):
            for i in VIDEO_FORMATS:
                if file.endswith(i):
                    os.remove(file)
    except Exception as e:
        print(e)
        pass
    await deleting.edit("**__All videos removed sucessfully ✅__**")
    await asyncio.sleep(3)
    await message.delete(message.text)
    await asyncio.sleep(1)
    await deleting.delete()


@bot.on_message(filters.command("exit") & filters.private)
async def exit(bot, message):
    if message.from_user.id not in AUTH_USERS:
        return await message.reply("You are not authorized to use this command.")
    shutting = await message.reply("Shutting down...")
    print("Shutting down the system...")
    time.sleep(3)
    await shutting.edit("Bot is now offline.")
    print("System off!")
    print(liness)
    sys.exit()


# print to the console

print(f"\nBOT STARTED\n{now:%A, %d %B %Y}. {now:%H:%M}")
print(f"\nPython version {sys.version_info}\n")
# run the current program
bot.run()
