from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def format_duration(seconds):
    """Format duration in seconds to HH:MM:SS"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def get_playlist_info_button(message_id: int):
    """Create button for initial playlist view"""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📋 Show Playlist Videos",
                    callback_data=f"playlist_videos:{message_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬇️ Download All", callback_data=f"download_all:{message_id}"
                )
            ],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{message_id}")],
        ]
    )


def get_playlist_videos_buttons(message_id: int, entries, page=0, videos_per_page=5):
    """Create paginated buttons for playlist videos"""
    buttons = []
    start_idx = page * videos_per_page
    end_idx = min(start_idx + videos_per_page, len(entries))

    # Add video selection buttons
    for i in range(start_idx, end_idx):
        entry = entries[i]
        duration = (
            format_duration(entry["duration"]) if entry.get("duration") else "N/A"
        )
        title = (
            entry["title"][:30] + "..." if len(entry["title"]) > 30 else entry["title"]
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{i+1}. {title} [{duration}]",
                    callback_data=f"select_video:{message_id}:{i}",
                )
            ]
        )

    # Navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                "⬅️ Previous", callback_data=f"playlist_page:{message_id}:{page-1}"
            )
        )
    if end_idx < len(entries):
        nav_buttons.append(
            InlineKeyboardButton(
                "➡️ Next", callback_data=f"playlist_page:{message_id}:{page+1}"
            )
        )
    if nav_buttons:
        buttons.append(nav_buttons)

    # Control buttons
    buttons.append(
        [
            InlineKeyboardButton(
                "✅ Confirm Selection", callback_data=f"confirm_selection:{message_id}"
            )
        ]
    )
    buttons.append(
        [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{message_id}")]
    )

    return InlineKeyboardMarkup(buttons)


def get_video_selection_buttons(message_id: int, height=None):
    """Create buttons for individual video resolution selection"""
    buttons = [
        [InlineKeyboardButton("1080p", callback_data=f"1080:{message_id}")],
        [InlineKeyboardButton("720p", callback_data=f"720:{message_id}")],
        [InlineKeyboardButton("480p", callback_data=f"480:{message_id}")],
        [InlineKeyboardButton("360p", callback_data=f"360:{message_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{message_id}")],
    ]
    return InlineKeyboardMarkup(buttons)
