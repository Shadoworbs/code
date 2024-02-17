# import the necessary modules
import time
from pyrogram import Client, filters
from dotenv import load_dotenv
import os
import asyncio
import spam
from spam import spam as sp
import sys


# load the environment variables
load_dotenv()
api_id = os.getenv("api_id")
api_hash = os.getenv("api_hash")
bot_token = os.getenv("bot_token")
app = Client(name='my_account', api_id=api_id, api_hash=api_hash)
chat_ = os.getenv("spam_chat_id")
my_id = os.getenv("my_id")


infos = dict()
# listen for incoming messages
@app.on_message(filters=filters.command('start@spam_bot'))
async def sendMessage(app, message):
    # if the message is sent in the specified chat and by the specified user and is the start command
    if message.chat.id == int(chat_) and message.from_user.id == int(my_id):
        # delay for 2 seconds
        # await asyncio.sleep(2)
        # send a reply
        reply = await message.reply("Yes sir 🫡")
        # print a message to the console
        print("Task Started!")
        # messages left
        mleft = len(sp)
        # messages sent
        msent = 0
        # initiate an ETA
        eta = mleft * 10
        # number times the loop has completed
        completed = 0


        try:
            # loop through the list of words in ../spam.py
            for word in sp:
                # delay for 7 seconds
                await asyncio.sleep(7)
                # send one word from the list
                repl = await message.reply(word)
                # delay for 3 seconds
                await asyncio.sleep(2)
                # decrease the number of messages left by 1
                mleft -= 1
                # decrease the ETA by 10
                eta -= 18
                # increase the number of messages sent by 1
                msent += 1
                # change seconds to hours, minutes and seconds
                seconds: int = eta
                minutes, seconds = divmod(seconds, 60)
                hours, minutes = divmod(minutes, 60)
                days, hours = divmod(hours, 24)
                # {days}d
                ETA = f"{hours}h {minutes}m {seconds}s"
                # edit the reply message with some text
                await reply.edit(f"""
**Total messages:** `{len(sp)}`
**Messages sent:** `{msent}`
**Messages left:** `{mleft}`
**Time left:** `{ETA}`
**Task by:** @shadoworbs""")
                updated_infos = {"mleft": mleft, "msent": msent}
                infos.update(updated_infos)
                # print messages left
                print(f'{mleft} messages left', end='\r')
                # delay for 1 second
                await asyncio.sleep(1)
                # delete the word sent from the list
                await repl.delete()
            # if there are no more words left
            if mleft == 0:
                completed += 1
                completed = completed * mleft
                # print a message to the console
                print('Task Completed!')
                # send a complete message
                # change seconds to hours, minutes and seconds
                await app.send_message(chat_, f"""
I have sent {len(sp) * completed} messages today ✨
Victory is mine!""")
                # delete the reply message
                await reply.delete()
                await message.delete()
        except Exception as e:
            print(e)
            os.system("pause")
        except KeyboardInterrupt:
            await reply.edit("Task Stopped by User!")
            await reply.delete()
            # print a message to the console
            print(f"Task Stopped by User, {mleft} messages left")
            os.system("pause")


@app.on_message(filters.command("pause@spam_bot"))
async def stop(app, message):
    global infos
    # if the user sends the stop command
    if message.from_user.id == my_id and message.chat.id == chat_:
        # print a message to the console
        print('Task paused by User!')
        # send a message that the task has been stopped
        halt = await app.send_message(chat_, f"Task paused by {message.from_user.mention}\nMessages left: {infos['mleft']}")
        # delay for 2 seconds
        await asyncio.sleep(2)
        # pause the program
        os.system("pause")
        # await sys.exit(0)


# app.send_mess
print("bot on")
app.run()




# todo:
# add a command to stop the task
# add a command to restart the task
# add a command to check the task status
# reduce wait time to 5 secs
