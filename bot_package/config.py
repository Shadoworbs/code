import os
from dotenv import load_dotenv

load_dotenv()

# --- Constants ---
PROGRESS_BAR_LENGTH = 12  # Length of the progress bar
UPDATE_INTERVAL = 5  # Seconds between progress updates

# --- Environment Variables ---
API_ID = os.getenv("api_id")
API_HASH = os.getenv("api_hash")
BOT_TOKEN = os.getenv("bot_token")
LOG_CHANNEL = os.getenv("LOG_CHANNEL")
LINK_LOGS = os.getenv("LINK_LOGS")
AUTH_USERS = os.getenv("AUTH_USERS", "")
SOFTWARE_CHANNEL_ID = os.getenv("SOFTWARE_CHANNEL_ID")
MOVIE_CHANNEL_ID = os.getenv("MOVIE_CHANNEL_ID")
SOFTWARE_CHANNEL_LINK = os.getenv(
    "SOFTWARE_CHANNEL_LINK", "https://t.me/+sblvkmvCZ45hMTc0"
)
MOVIE_CHANNEL_LINK = os.getenv("MOVIE_CHANNEL_LINK", "https://t.me/+BdXh4y_MFqBhZTA0")

# --- Log the loaded Channel IDs ---
print(f"Loaded SOFTWARE_CHANNEL_ID: {SOFTWARE_CHANNEL_ID}")
print(f"Loaded MOVIE_CHANNEL_ID: {MOVIE_CHANNEL_ID}")
print(f"Loaded LOG_CHANNEL: {LOG_CHANNEL}")
print(f"Loaded LINK_LOGS: {LINK_LOGS}")
print(f"Loaded AUTH_USERS: {AUTH_USERS}")
# --- End Log ---

# --- Paths ---
CWD = os.getcwd()
BASE_DOWNLOAD_PATH = os.path.join(CWD, "downloads")
os.makedirs(BASE_DOWNLOAD_PATH, exist_ok=True)

# --- Runtime Cache ---
url_cache = {}
last_update_time = (
    {}
)  # Stores last update time for progress messages {(chat_id, message_id): timestamp}
active_downloads = (
    {}
)  # Stores cancel flags for downloads {original_msg_id: asyncio.Event}
