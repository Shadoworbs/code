# import the necessary modules
from datetime import datetime
from pyrogram import Client, filters
from dotenv import load_dotenv
import os
import asyncio
from thousand_words import thousand_words as sp


# load the environment variables
load_dotenv()
api_id = os.getenv("api_id")
api_hash = os.getenv("api_hash")
bot_token = os.getenv("bot_token")
app = Client(name='my_account', api_id=api_id, api_hash=api_hash)
chat_: int = os.getenv("spam_chat_id")
my_id: int = os.getenv("my_id")


# the infos dictionary
infos = dict()
# the list of completed tasks
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
        messages_left = len(sp)
        # messages sent
        messages_sent = 0
        # estimated time of completion
        eta = messages_left * 10


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
                messages_left -= 1
                # decrease the ETA by 10
                eta -= 10
                # increase the number of messages sent by 1
                messages_sent += 1
                # change seconds to (hours, minutes and seconds)
                seconds: int = eta
                minutes, seconds = divmod(seconds, 60)
                hours, minutes = divmod(minutes, 60)
                days, hours = divmod(hours, 24)
                eta_ = f"{hours}h {minutes}m {seconds}s"
                # edit the reply message with some text
                await reply.edit(f"""
**Total messages 💬:** `{len(sp)}`
**Messages sent 💬:** `{messages_sent}`
**Messages left 💬:** `{messages_left}`
**Time left ⏳:** `{eta_}`
**Made with ❤️ by:** @shadoworbs""")
                # print messages left
                print(f'{messages_left} messages left', end='\r')
                # delay for 1 second
                await asyncio.sleep(1)
                # delete the word sent from the list
                await repl.delete()
                # create an updated infos dict
                updated_infos = {"messages_left": messages_left, 
                                 "messages_sent": messages_sent, 
                                 "reply": reply.id}
                # update the infos dict the newly created dict
                infos.update(updated_infos)
            # append 1 to the completed list (to show how many times the task has been completed)
            completed.append("1")
            # print a message to the console
            print(f'Task Completed {len(completed)} times')
            # send a complete message
            victory = await app.send_message(chat_, f"""
**Task completed ✅**
**Total messages 💬:** `{len(sp) * len(completed)}`✨""")
            # delete the reply message
            await reply.delete()
            # delete the command message
            await message.delete()
        except Exception as e:
            print(e)
            # when there is an error in edit message
            # delete the current word sent
            # (may not work because the word may have been deleted already)
            await repl.delete()
            # clear the infos dict to show no tasks running
            infos.clear()

            # return the function and start listening for a new command
            return
    
    # if the user is not me and the message is sent in the specified chat
    elif message.from_user.id != int(my_id) and message.chat.id == int(chat_) and 'start@spam_bot' in message.text:
        # wait for 1 second
        await asyncio.sleep(1)
        # delete the user's message
        await message.delete()
        # send a reply to the user
        unauth = await app.send_message(chat_,
                                     f"Hey {message.from_user.mention}\nSorry, you can't use me 🤭.")
        # wait for 10 seconds
        await asyncio.sleep(10)
        # delete the reply sent to the user
        await unauth.delete()


# Get bot status
@app.on_message(filters.command('stats'))
async def status(app, message):
    # if the user sends the stats command
    if message.from_user.id == int(my_id) and message.chat.id == int(chat_):
        # if there are tasks running (infos dict is not empty)
        if len(infos) > 0 and infos["messages_left"] > 0 :
            await message.delete()
            # print a message to the console
            print(f"Current task ID: {infos['reply']}")
            # send a reply
            task = await app.send_message(chat_, 
                                          f"**[Current task ✍️](https://t.me/GGGLTB/{infos['reply']})**",
                                          disable_web_page_preview=True)
            # wait for 10 seconds
            await asyncio.sleep(10)
            # delete the reply sent to the user
            await task.delete()

        # if there are no tasks running (infos dict is empty)
        else:
            # print a message to the console
            print("No tasks running!")
            await message.delete()
            # send a reply
            task_ = await message.reply("No tasks running!")
            # wait for 5 seconds
            await asyncio.sleep(5)
            # delete the reply
            await task_.delete()
        # stop the function and start listening for a new command
        return

    # if the user is not me and the message is sent in the specified chat
    elif message.from_user.id != int(my_id) and message.chat.id == int(chat_) and 'stats' in message.text:
        # delete the user's message
        await message.delete()
        # wait for 1 second
        await asyncio.sleep(1)
        # send a reply to the user
        unauth = await app.send_message(chat_,
                                            f"Hey {message.from_user.mention}\nSorry, you can't use me 🤭.")
        # wait for 5 seconds
        await asyncio.sleep(5)
        # delete the reply sent to the user
        await unauth.delete()
    # stop the function and start listening for a new command
    return


# Stop the bot
@app.on_message(filters.command('stop@spam_bot'))
async def stop(app, message):
    # if the user sends the stop command
    if message.from_user.id == int(my_id) and message.chat.id == int(chat_):
        # print a message to the console
        print("Task stopped")
        # send a reply that the bot is stopped
        stopped = await message.reply(f"Bot Stopped by {message.from_user.mention}")
        # wait for 1 second
        await asyncio.sleep(1)
        # delete the user's message
        await message.delete()
        # wait for 1 second
        await asyncio.sleep(1)
        # delete the reply sent to the user
        await stopped.delete()
        try:
            # delete the reply message to deliberately -
            # cause an error in edit message
            # that's the only way to stop the task
            await app.delete_messages(chat_, infos["reply"])
        except:
            pass
        return

    # if the user is not me and the message is sent in the specified chat
    elif message.from_user.id != int(my_id) and message.chat.id == int(chat_) and 'stop@spam_bot' in message.text:
        # delete the user's message
        await message.delete()
        # send a reply to the user
        unauth = await message.reply(chat_, 
                                     f"Hey {message.from_user.mention}\nSorry, you can't use me 🤭.")
        # wait for 5 seconds
        await asyncio.sleep(5)
        # delete the reply sent to the user
        await unauth.delete()
    # stop the function and start listening for a new command
    return



print("Bot Started at " + datetime.now().strftime("%H:%M:%S"))
app.run()




# todo:
# add percentage of messages left
# add progress bar for messages left


