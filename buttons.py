from pyrogram.types import (
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
)


START_BUTTON = [
    [
        InlineKeyboardButton(
            text="💻Software Channel💻", url="https://t.me/+a_rlC_BtkEpmZmVk"
        ),
        InlineKeyboardButton(
            text="🎬Movie Channel🎬", url="https://t.me/+vA7ql6uZ0ZMxZjU8"
        ),
    ]
]

ABOUT_BUTTON = [
    [
        InlineKeyboardButton(text="👨‍💻 Owner 👨‍💻", url="https://shadoworbs.t.me"),
        InlineKeyboardButton(text="⌨️ Language ⌨️", url="https://python.org"),
    ],
    [
        InlineKeyboardButton(text="📚 Library 📚", url="https://pyrogram.org"),
        InlineKeyboardButton(text="ℹ️ Repo ℹ️", url="https://github.com/shadoworbs/code"),
    ],
]

DL_COMPLETE_BUTTON = START_BUTTON

REPLY_BUTTONS = [[("Hi"), ("Hello")], [("How is work?"), ("How are you?")]]


MAIN_PAGE_TEXT = "Do you wish to start reading?"
MAIN_PAGE_BUTTON = [
    [InlineKeyboardButton("Start Reading ▶️", callback_data="page1")],
    [InlineKeyboardButton("CANCEL", callback_data="cancel")],
]

PAGE1_TEXT = "This is the first page, select a resolution."
PAGE1_BUTTON = [
    [
        InlineKeyboardButton("⬅️ BACK", callback_data="back_to_main_menu"),
        InlineKeyboardButton("PAGE 2 ➡️", callback_data="page2"),
    ],
    [InlineKeyboardButton("CANCEL", callback_data="cancel")],
]


PAGE2_TEXT = "This is the second page, select another thing."
PAGE2_BUTTON = [
    [
        InlineKeyboardButton("⬅️ BACK", callback_data="back_to_page_1"),
        InlineKeyboardButton("PAGE 3 ➡️", callback_data="page3"),
    ],
    [InlineKeyboardButton("CANCEL", callback_data="cancel")],
]


PAGE3_TEXT = "Now we are on the third page, select the height."
PAGE3_BUTTON = [
    [
        InlineKeyboardButton("⬅️ BACK", callback_data="back_to_page_2"),
        InlineKeyboardButton("💠 MAIN MENU 💠", callback_data="back_to_main_menu"),
    ],
    [InlineKeyboardButton("CANCEL", callback_data="cancel")],
]


VIDEO_HEIGHT_TEXT = (
    "Youtube link detected!\nPlease select a video quality.\nTimout 120 secs [2 mins]"
)
VIDEO_HEIGHT_BUTTON = [
    [InlineKeyboardButton("140p", callback_data="140")],
    [InlineKeyboardButton("240p", callback_data="240")],
    [InlineKeyboardButton("270p", callback_data="270")],
    [InlineKeyboardButton("360p [SD]", callback_data="360")],
    [InlineKeyboardButton("480p [SD]", callback_data="480")],
    [InlineKeyboardButton("540p", callback_data="540")],
    [InlineKeyboardButton("640p", callback_data="640")],
    [InlineKeyboardButton("720p [HD]", callback_data="720")],
    [InlineKeyboardButton("1080 [HD]", callback_data="1080")],
]

MEMBERSHIP_BUTTONS = [
    [
        InlineKeyboardButton("➡️ Software Channel", url="SOFTWARE_CHANNEL_LINK"),
        InlineKeyboardButton("➡️ Movie Channel", url="MOVIE_CHANNEL_LINK"),
    ],
    [InlineKeyboardButton("🔄 Retry", callback_data="retry_start")],
]
