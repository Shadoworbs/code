import asyncio
from imaplib import Commands
import json
import trace
import traceback
from pyrogram import Client, filters, emoji
from datetime import datetime, timedelta
from replies import *
from dotenv import load_dotenv
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import os

cwd = os.getcwd()

load_dotenv()
api_id = os.getenv("api_id")
api_hash = os.getenv("api_hash")
bot_token = os.getenv("bot_token")


############### Global variables #############
CHAT = "pyrotestrobot"
now = datetime.now()

ADMINS = [1854174598]
# callback_time = datetime.now().strftime("%Y%m%d%H%M")

# initializing the client object
bot = Client(
    "bot_account",
    api_id=api_id,
    api_hash=api_hash,
)


@bot.on_message(filters.command("info"))
async def get_photo(bot, message):
    _message = message.text
    first = _message.split(" ")[0].strip().lower()
    second = _message.split(" ")[-1].strip()

    if len(_message.split(" ")) < 2 or second.lower() == "me":
        if not message.reply_to_message:
            try:
                waiting = await message.reply("Getting User info...")
                await bot.send_message(
                    message.chat.id,
                    text=f"""
```Your Info
Username: {('@' + message.from_user.username) if message.from_user.username else None}
First Name: `{message.from_user.first_name or None}`
Last Name: `{message.from_user.last_name or None}`
ID 🆔: `{message.from_user.id}`
DC ID: `{message.from_user.dc_id}`
Premium User? {message.from_user.is_premium}     
Language Code: {message.from_user.language_code}```                                                               
    """,
                    reply_to_message_id=message.id,
                )
                await waiting.delete()
            except Exception as e:
                await message.reply(f"There was an error!\n{e}")
                print(e)
                pass

    elif len(message.text.split(" ")) == 2 and second.isdigit():
        try:
            userId = second
            waiting = await message.reply("Getting User info...")
            user_info = await bot.get_users(userId)
            await bot.send_message(
                message.chat.id,
                f"""
```Chat Info:
First Name: `{user_info.first_name or None}`
Last Name: `{user_info.last_name or None}`
Username: @{user_info.username or None}
ID 🆔: `{user_info.id}`
DC ID: `{user_info.dc_id}```""",
                reply_to_message_id=message.id,
            )
            await waiting.delete()
        except Exception as e:
            await message.reply(f"There was an error! in line 81\n{e}")
            print(e)
            pass
    if message.reply_to_message:
        try:
            waiting = await message.reply("Getting User info...")
            userId = message.reply_to_message.from_user.id
            print(f"User ID: {userId}   My ID: {message.from_user.id}")
            
            await bot.send_message(
                message.chat.id,
                f"""
```Chat Info:
First Name: `{(await bot.get_chat(userId)).first_name or None}`
Last Name: `{(await bot.get_chat(userId)).last_name or None}`
Username: @{(await bot.get_chat(userId)).username or None}
ID 🆔: `{(await bot.get_chat(userId)).id}`
DC ID: `{(await bot.get_chat(userId)).dc_id}```""",
                reply_to_message_id=message.id,
            )
            await waiting.delete()
        except Exception as e:
            await message.reply(f"There was an error!\n{e}")
            print(e)
            pass



@bot.on_message(filters.command("link"))
async def get_invite_link(bot, message):
    if os.path.exists(f"link{message.chat.id}.json"):
        with open(f"link{message.chat.id}.json", "r") as f:
            link = json.load(f)
        try:
            waiting = await message.reply("Getting chat link...")
            await asyncio.sleep(2)
            await waiting.delete()
            await asyncio.sleep(1)
            await bot.send_message(
                message.chat.id,
                f"Chat link 🔗: \n<code>{link['invite_link']}</code>",
                reply_to_message_id=message.id,
            )
        except Exception as e:
            await message.reply(f"There was an error!\n{e}")
            print(e)
            pass
    else:
        try:
            chat_type = message.chat.type
            if str(chat_type) != "ChatType.PRIVATE":
                link = await bot.create_chat_invite_link(message.chat.id)
                invite_link = {"invite_link": link.invite_link}
                waiting = await message.reply("Getting chat link...")
                await asyncio.sleep(2)
                await waiting.delete()
                await asyncio.sleep(1)
                await bot.send_message(
                    message.chat.id,
                    f"Chat link 🔗: \n<code>{link.invite_link}</code>",
                    disable_web_page_preview=True,
                    reply_to_message_id=message.id,
                )
            with open(f"link{message.chat.id}.json", "w") as f:
                json.dump(invite_link, f)
        except Exception as e:  # Catch specific exceptions if possible
            print(f"Error creating invite link: {e}")  # Log the error
            await bot.send_message(
                message.chat.id,
                "An error occured, make sure I am an admin and give me the necessary rights.",
            )
            pass


@bot.on_message(filters.command("reply"))
async def send_replied_message_id(bot, message):  # Renamed function for clarity
    try:
        if message.reply_to_message:
            # Sends the ID of the message being replied to as text
            reply_id = await bot.send_message(
                message.chat.id,
                f"Replied message ID: `{message.reply_to_message.id}`",  # Added context to the sent ID
                reply_to_message_id=message.reply_to_message.id,
            )
            # await asyncio.sleep(3)
            # await bot.delete_messages(message.chat.id, [message.id,
            #                                             reply_id.id,
            #                                              message.reply_to_message.id])
    except Exception as e:
        print(e)
        await message.reply(f"There was an error!\n{e}")
        pass

# -------- START COMMAND --------- #
@bot.on_message(filters.command("start") & filters.private)
async def start(bot, message):
    await message.delete()
    await message.reply("Hello! I am a bot. Use /help to see my commands.")

from pyrogram.types import BotCommand as bc
# set commands
@bot.on_message(filters.command("setcommands") & filters.user(ADMINS))
async def set_commands(bot: Client, message):
    #
    # TODO Add admin checks
    # 
    #
    if not message.reply_to_message and len(message.text.split(" ")) > 2:
        text = message.text
        cmds = text.split("|")[1]
        right_cmds = cmds.split(",")
        cleaned_cmd = [i.strip() for i in right_cmds]

        cmd_list_to_show_after_completion: str = ''
        # Or to get a dictionary of commands and descriptions:
        final_cmds: dict = {i.split("-")[0].strip(): i.split("-")[1].strip() for i in cleaned_cmd}
        for key, value in final_cmds.items():
                cmd_list_to_show_after_completion += f'/{key} - {value}\n'
            
    else:
        empty_commends = await message.reply("Bot commands cannot be empty!")
        await message.delete()
        await asyncio.sleep(5)
        await empty_commends.delete()
        return
    
    commands = [bc(key, value) for key, value in final_cmds.items()]

    try:
        await bot.set_bot_commands(
            commands=commands
        )
        await message.reply(f"Commands set successfully!\n\n{cmd_list_to_show_after_completion}")
    except Exception as e:
        print(f"Error setting commands: {e.add_note('Error setting commands')}\n{traceback.format_exc()}")
        await message.reply(f"Error setting commands: {e}")

# get bot commands 
@bot.on_message(filters.command("getcommands") & filters.user(ADMINS))
async def get_commands(bot: Client, message):
    try:
        commands = await bot.get_bot_commands()
        command_list = "\n".join([f"/{cmd.command} - {cmd.description}" for cmd in commands])
        await message.reply(f"Current bot commands:\n{command_list}")
    except Exception as e:
        print(f"Error getting commands: {e.add_note('Error getting commands')}\n{traceback.format_exc()}")
        await message.reply(f"Error getting commands: {e}")


# print to the console
print(f"\nBOT STARTED\n{now:%A, %d %B %Y} | {now:%I:%M %p}")
# run the current program
bot.run()

