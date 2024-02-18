# import the necessary modules
from datetime import datetime
from pyrogram import Client, filters
from dotenv import load_dotenv
import os
import asyncio
from spam import spam as sp
import sys


# load the environment variables
load_dotenv()
api_id = os.getenv("api_id")
api_hash = os.getenv("api_hash")
bot_token = os.getenv("bot_token")
app = Client(name='my_account', api_id=api_id, api_hash=api_hash)
chat_: int = os.getenv("spam_chat_id")
my_id: int = os.getenv("my_id")


infos = dict()
completed: list = []


# Starting the bot
@app.on_message(filters=filters.command('start@spam_bot'))
async def sendMessage(app, message):
    # if the message is sent in the specified chat and by the specified user and is the start command
    if message.chat.id == int(chat_) and message.from_user.id == int(my_id):
        # send a reply
        reply = await message.reply("Yes sir 🫡")
        # print a message to the console
        print("Task Started!")
        # messages left
        mleft = len(sp)
        msent = 0
        eta = mleft * 10


        try:
            # loop through the list of words in ../spam.py
            for word in sp:
                # delay for 7 seconds
                await asyncio.sleep(7)
                # send one word from the list
                repl = await app.send_message(chat_, word, reply_to_message_id=99757)
                # delay for 3 seconds
                await asyncio.sleep(2)
                # decrease the number of messages left by 1
                mleft -= 1
                # decrease the ETA by 10
                eta -= 10
                # increase the number of messages sent by 1
                msent += 1
                # change seconds to hours, minutes and seconds
                seconds: int = eta
                minutes, seconds = divmod(seconds, 60)
                hours, minutes = divmod(minutes, 60)
                days, hours = divmod(hours, 24)
                eta_ = f"{hours}h {minutes}m {seconds}s"
                # edit the reply message with some text
                await reply.edit(f"""
**Total messages:** `{len(sp)}`
**Messages sent:** `{msent}`
**Messages left:** `{mleft}`
**Time left:** `{eta_}`
**Made with ❤️ by:** @shadoworbs""")
                # print messages left
                print(f'{mleft} messages left', end='\r')
                # delay for 1 second
                await asyncio.sleep(1)
                # delete the word sent from the list
                await repl.delete()
                updated_infos = {"mleft": mleft, "msent": msent, "reply": reply.id}
                infos.update(updated_infos)
            completed.append("1")
            # print a message to the console
            print(f'Task Completed {len(completed)} times')
            # send a complete message
            await app.send_message(chat_, f"""
I have sent {len(sp) * len(completed)} messages today ✨
Victory is mine!""")
            # delete the reply message
            await reply.delete()
            await message.delete()
        except Exception as e:
            print(e)
            await app.send_message(chat_, f"@shadoworbs, an error occured\n{e}")
            await asyncio.sleep(2)
            await reply.delete()
            await message.delete()
            await sys.exit(0)


# Get bot status
@app.on_message(filters.command('stats'))
async def status(app, message):
    # if the user sends the stats command
    if message.from_user.id == int(my_id) and message.chat.id == int(chat_):
        if len(infos) > 0 and infos["mleft"] > 0 :
            # print a message to the console
            print(f"Current task ID: {infos['reply']}")
            # send a reply
            await app.send_message(chat_, "Current task 👆", reply_to_message_id=infos["reply"])
        else:
            print("No tasks running!")
            await message.reply("No tasks running!")


# Stop the bot
@app.on_message(filters.command('stop@spam_bot'))
async def stop(app, message):
    # if the user sends the stop command
    if message.from_user.id == int(my_id) and message.chat.id == int(chat_):
        # print a message to the console
        print("Task stopped")
        # send a reply
        stopped = await message.reply(f"Bot Stopped by {message.from_user.mention}")
        # delete the reply message
        await asyncio.sleep(1)
        await message.delete()
        await asyncio.sleep(1)
        await stopped.delete()
        try:
            await app.delete_messages(chat_, infos["reply"])
        except:
            pass
        await sys.exit(0)


# app.send_mess
print("Bot Started at " + datetime.now().strftime("%H:%M:%S"))
app.run()




# todo:
# add a restart command

