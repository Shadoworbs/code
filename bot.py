import sys
import asyncio
from datetime import datetime

# Import necessary components from the new package structure
from bot_package.bot_instance import bot
from bot_package.config import AUTH_USERS  # Import AUTH_USERS if needed directly here

# Handlers are automatically registered because they use the @bot decorator
import bot_package.handlers
import bot_package.helpers
import bot_package.downloader

# --- Main Execution ---
if __name__ == "__main__":
    now = datetime.now()
    print("-" * 30)
    print(f"BOT STARTING")
    print(f"{now:%A, %d %B %Y} - {now:%H:%M:%S}")
    print(f"Python: {sys.version.split()[0]}")
    # You can add Pyrogram version here if needed:
    import pyrogram
    print(f"Pyrogram: {pyrogram.__version__}")
    print("-" * 30)

    try:
        bot.run()
    except Exception as e:
        print(f"FATAL ERROR: Bot crashed with exception: {e}")
        # Consider adding more robust error logging here
    finally:
        print("-" * 30)
        print("BOT STOPPED")
        print("-" * 30)
