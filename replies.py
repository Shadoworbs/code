# creating about message for when a user sends /about command
about_text = f"""--**Bot Info:**--
**Owner:** @shadoworbs
**Language: Python3**
**Library: Pyrogram**
**Repo: __coming soon...__**
"""


# some lines to display at the bottom
liness = f"----------------------------------------"

start_text = "✨ Hey {}\nWelcome to the world of Sky Monsters.\nSend /help to know what I can do."

help_text = f"__I'm a youtube video downloader.\nSend me a youtube video link 🔗 and I will download it for you.__"

dl_text = "**Status:** **__Downloading ⬇️__**"

err_dl_vid_text = "**Sorry an error occured, please try again or send another link.**"

upl_text = "**Status:** **__Uploading ⬆️__**"

ERR_UPL_VID_TEXT = "**⚠️ {} an error occured and I couldn't send the video.⚠️**"

link_log_err = "There was an error in the link logs section."

# video_caption = "Video "

DL_COMPLETE_TEXT = "**__Your [Video]({}) has been uploaded successfully ✅__**\n**Vidoe title:** `{}`"

VIDEO_FORMATS = [
    ".mp4",
    ".mkv",
    ".webm",
    ".avi",
    ".opus",
    ".flv",
    "prores",
    ".3gpp",
    ".mov",
    ".mpeg4",
    ".dnxhr",
    ".cineform",
    ".mpeg-1",
    ".mpeg-2",
    ".mpg",
    ".wmv",
    ".mpegps",
    ".hevc",
]


# Add this if it's not already in replies.py
VIDEO_HEIGHT_TEXT = "Please select your preferred video quality:"
