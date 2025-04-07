import sys
from datetime import datetime
import pyrogram

# Import necessary components from the new package structure
from bot_package.bot_instance import bot
import bot_package.helpers as helpers
from bot_package import handlers


# --- Main Execution ---
if __name__ == "__main__":
    now = datetime.now()
    print("-" * 30)
    print(f"BOT STARTING")
    print(f"{now:%A, %d %B %Y} - {now:%H:%M:%S}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Pyrogram: {pyrogram.__version__}")
    print("-" * 30)

    try:
        bot.run()
    except Exception as e:
        print(f"FATAL ERROR: Bot crashed with exception: {e}")
        # Consider adding more robust error logging here
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    except SystemExit:
        print("System exit requested.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Handle other exceptions as needed
    finally:
        print("-" * 30)
        print("BOT STOPPED")
        print("-" * 30)
