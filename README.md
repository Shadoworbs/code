# YouTube Video Downloader Bot

A feature-rich Telegram bot for downloading YouTube videos and playlists. Built with Python and Pyrogram.

## Features

- Download YouTube videos in multiple resolutions (360p, 480p, 720p, 1080p)
- Playlist support with video selection
- Real-time progress tracking with cancel option
- Video streaming support
- Rate limiting and user management
- MongoDB integration for user tracking
- Admin commands for bot management
- Channel/Group logging support

## Requirements

- Python 3.8 or higher
- MongoDB database
- FFmpeg (for video processing)
- A Telegram Account
- API ID and Hash from [my.telegram.org](https://my.telegram.org)
- Bot Token from [@BotFather](https://t.me/BotFather)
- MongoDB connection string

## Installation

1. Clone this repository:

Windows:

```cmd
git clone https://github.com/Shadoworbs/code.git
cd code
```

Linux:

```bash
git clone https://github.com/Shadoworbs/code.git && cd code
```

2. Create and activate a virtual environment:

Windows:

```cmd
python -m venv .venv
.venv\Scripts\activate
```

Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install required packages:

Windows:

```cmd
pip install -r requirements.txt
```

Linux:

```bash
pip install -r requirements.txt
```

4. Install FFmpeg:

Windows:

- Download FFmpeg from official website
- Add it to system PATH or place in project directory

Linux:

```bash
sudo apt update
sudo apt install ffmpeg
```

5. Set up environment variables:

- Create a `.env` file in the project root
- Add the following variables:

```env
api_id=YOUR_API_ID
api_hash=YOUR_API_HASH
bot_token=YOUR_BOT_TOKEN
AUTH_USERS=["user_id1","user_id2"]  # List of authorized user IDs
LINK_LOGS=channel_id  # Optional: Channel ID for logging downloaded links
LOG_CHANNEL=channel_id  # Optional: Channel ID for forwarding downloaded videos
MONGO_PWD=your_mongodb_password
```

## Starting the Bot

1. Initialize the bot (first time only):

Windows:

```cmd
python login.py
```

Linux:

```bash
python3 login.py
```

2. Start the bot:

Windows:

```cmd
python bot.py
```

Linux:

```bash
python3 bot.py
```

## Available Commands

### User Commands

- `/start` - Start the bot
- `/help` - Show help message
- `/about` - Show bot information
- `/clean` - Clean downloaded videos
- `/server` - Show server information

### Admin Commands

- `/stats` - Show bot statistics
- `/broadcast` - Send message to all users
- `/ban` - Ban a user
- `/unban` - Unban a user
- `/addsudo` - Add a sudo user
- `/rmsudo` - Remove a sudo user
- `/sudo` - List sudo users
- `/users` - List all users
- `/restart` - Restart the bot
- `/setcommands` - Set bot commands
- `/getcommands` - Get current bot commands

## Usage

1. Start bot with `/start`
2. Send a YouTube video/playlist link
3. For single videos:
   - Select resolution (360p-1080p)
   - Wait for download/upload
   - Use cancel button to stop process
4. For playlists:
   - Select individual videos or download all
   - Choose resolution
   - Videos will be processed sequentially

## Rate Limiting

- Regular users: 5 messages per minute
- Downloads: 2 per 5 minutes
- Sudo users and admins are exempt

## Error Handling

- Use `/clean` to free up storage space
- Check bot logs for detailed error messages
- Restart bot if buttons become unresponsive
- Ensure bot has admin rights in logging channels

## Notes

- Downloaded files are stored in user-specific directories
- Files are automatically cleaned up after upload
- Bot requires admin rights in logging channels
- Some videos may not be available in all resolutions
- Cache is cleared on bot restart
- Progress bars show real-time download/upload status

## Contributing

Feel free to open issues and submit pull requests on GitHub.

## License

This project is licensed under the MIT License.
