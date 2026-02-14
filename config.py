"""
Configuration file for YouTube Music Downloader
Contains constants, default settings, and API configurations
"""

import os
from pathlib import Path

# API Configuration
YOUTUBE_API_KEY = "AIzaSyBcoHE4l3UtUTS9EjcrmHHMluDWxhREPzE"
YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3"

# Default paths
DEFAULT_DOWNLOAD_PATH = Path.home() / "Music" / "YouTubeDownloads"
SETTINGS_FILE = Path.home() / ".youtube_music_downloader" / "settings.json"
HISTORY_FILE = Path.home() / ".youtube_music_downloader" / "history.json"
QUEUE_EXPORT_DIR = Path.home() / ".youtube_music_downloader" / "queues"

# Create directories if they don't exist
for path in [DEFAULT_DOWNLOAD_PATH, SETTINGS_FILE.parent, QUEUE_EXPORT_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Audio quality options
AUDIO_QUALITIES = {
    "best_opus": {
        "label": "Best Opus (~160kbps)",
        "format": "bestaudio[ext=webm]/bestaudio",
        "codec": "libopus",
        "ext": "opus"
    },
    "mp3_320": {
        "label": "MP3 320kbps",
        "format": "bestaudio/best",
        "codec": "libmp3lame",
        "bitrate": "320k",
        "ext": "mp3"
    },
    "flac": {
        "label": "FLAC Lossless",
        "format": "bestaudio/best",
        "codec": "flac",
        "ext": "flac"
    },
    "aac_256": {
        "label": "AAC/M4A 256kbps",
        "format": "bestaudio[ext=m4a]/bestaudio",
        "codec": "aac",
        "bitrate": "256k",
        "ext": "m4a"
    }
}

# Search sort options
SEARCH_SORT_OPTIONS = [
    {"label": "Relevance", "value": "relevance"},
    {"label": "View Count", "value": "viewCount"},
    {"label": "Upload Date", "value": "date"},
    {"label": "Rating", "value": "rating"}
]

# Duration filters
DURATION_FILTERS = [
    {"label": "Any Duration", "value": ""},
    {"label": "Short (< 4 min)", "value": "short"},
    {"label": "Medium (4-20 min)", "value": "medium"},
    {"label": "Long (> 20 min)", "value": "long"}
]

# Video type filters
VIDEO_TYPE_FILTERS = [
    {"label": "All Types", "value": ""},
    {"label": "Video", "value": "video"},
    {"label": "Audio Only", "value": "audio"},
    {"label": "Shorts", "value": "shorts"}
]

# Default settings
DEFAULT_SETTINGS = {
    "download_path": str(DEFAULT_DOWNLOAD_PATH),
    "default_quality": "best_opus",
    "max_concurrent_downloads": 3,
    "theme": "dark",
    "data_saver_mode": False,
    "auto_update_ytdlp": False,
    "filename_template": "{artist} - {title} [{quality}]",
    "embed_subtitles": True,
    "embed_thumbnail": True,
    "add_metadata": True,
    "remove_sponsors": True,
    "auto_add_audio_keyword": True,
    "download_subtitles": True,
    "search_sort": "relevance",
    "search_duration_filter": "",
    "search_type_filter": ""
}

# UI Configuration
UI_CONFIG = {
    "theme_colors": {
        "dark": {
            "bg": "#121212",
            "surface": "#1E1E1E",
            "primary": "#BB86FC",
            "secondary": "#03DAC6",
            "error": "#CF6679",
            "text": "#FFFFFF",
            "text_secondary": "#B3B3B3"
        },
        "light": {
            "bg": "#FFFFFF",
            "surface": "#F5F5F5",
            "primary": "#6200EE",
            "secondary": "#03DAC6",
            "error": "#B00020",
            "text": "#000000",
            "text_secondary": "#666666"
        }
    },
    "card_border_radius": 12,
    "button_border_radius": 8,
    "max_search_results": 25
}

# Status constants
class DownloadStatus:
    WAITING = "waiting"
    PROCESSING = "processing"
    DOWNLOADING = "downloading"
    CONVERTING = "converting"
    DONE = "done"
    ERROR = "error"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

# Concurrent download limits
MAX_CONCURRENT_DOWNLOADS = 5
MIN_CONCURRENT_DOWNLOADS = 1

# Network check intervals (seconds)
NETWORK_CHECK_INTERVAL = 30

# Progress update interval (seconds)
PROGRESS_UPDATE_INTERVAL = 0.5

# Audio preview duration (seconds)
PREVIEW_DURATION = 30
