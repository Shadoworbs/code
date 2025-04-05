# YouTube Video Downloader Bot

A Telegram bot that downloads YouTube videos in various resolutions. Built with Python and Pyrogram.

## Features

- Download YouTube videos in multiple resolutions (360p, 480p, 720p, 1080p)
- Preview video thumbnails
- Video streaming support
- Progress tracking
- Channel/Group logging support

## Requirements

- Python 3.8 or higher
- A Telegram Account
- API ID and Hash from [my.telegram.org](https://my.telegram.org)
- Bot Token from [@BotFather](https://t.me/BotFather)

## Installation

1. Clone this repository:

```bash
git clone https://github.com/Shadoworbs/code.git && cd code
```

2. Install required packages:

```bash
pip install -r requirements.txt
```

3. Create environment variables:
   - Rename `config_example.py` to `config.py`
   - Fill in the required fields:

     ```python
     api_id = "YOUR_API_ID"
     api_hash = "YOUR_API_HASH"
     bot_token = "YOUR_BOT_TOKEN"
     AUTH_USERS = "your_user_id,another_user_id"  # Comma-separated list of authorized user IDs
     LINK_LOGS = "channel_id"  # Optional: Channel ID for logging downloaded links
     LOG_CHANNEL = "channel_id"  # Optional: Channel ID for forwarding downloaded videos
     ```

4. Initialize the bot:

```bash
python login.py
```

Follow the prompts to authenticate your Telegram account.

5. Start the bot:

```bash
python bot.py
```

## Usage

1. Start the bot by sending `/start` in private chat
2. Send a YouTube video link
3. Select desired resolution from the provided buttons
4. Wait for the video to download and upload
5. Access the video in your chat

## Commands

- `/start` - Start the bot
- `/help` - Show help message
- `/about` - Show bot information
- `/clean` - Clean downloaded videos (Admin only)
- `/exit` - Stop the bot (Admin only)

## Notes

- Large videos may take longer to process
- Bot needs to be admin in logging channels if enabled
- Some videos might not be available in all resolutions
- Cache is cleared on bot restart

## Error Handling

- If buttons don't respond, send the link again
- Use `/clean` if storage space runs low
- Check logs for detailed error messages

## Contributing

Feel free to open issues and submit pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
