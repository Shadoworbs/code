import asyncio
from pyrogram import Client
from config import *


async def main():
    async with Client("my_account", api_id, api_hash) as app:
        print("LOGIN SUCCESS!")


asyncio.run(main())