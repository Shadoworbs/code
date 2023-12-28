from pyrogram.types import (ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton)



START_BUTTON = [
    [
        InlineKeyboardButton(text = "💻Software Channel💻", url = "https://t.me/+a_rlC_BtkEpmZmVk"),
        InlineKeyboardButton(text = "🎬Movie Channel🎬", url = "https://t.me/+vA7ql6uZ0ZMxZjU8")
    ]
]

ABOUT_BUTTON = [
    [
        InlineKeyboardButton(text="👨‍💻 Owner 👨‍💻", url="https://shadoworbs.t.me"),
        InlineKeyboardButton(text="⌨️ Language ⌨️", url="https://python.org")
    ],
    [
        InlineKeyboardButton(text="📚 Library 📚", url="https://pyrogram.org"),
        InlineKeyboardButton(text="ℹ️ Repo ℹ️", url="https://github.com/shadoworbs/code"),
    ]
]

DL_COMPLETE_BUTTON = [
    [
        InlineKeyboardButton(text="Download complete", url="")
    ]
]