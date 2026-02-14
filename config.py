"""
Configuration file for YouTube Music Downloader
Contains constants, default settings, and API configurations
"""

import os
import platform
from pathlib import Path

# API Configuration
YOUTUBE_API_KEY = "AIzaSyBcoHE4l3UtUTS9EjcrmHHMluDWxhREPzE"
YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3"

# Detect if running on Android
def is_android():
    """Check if running on Android"""
    # Check multiple indicators
    android_indicators = [
        'ANDROID_ROOT' in os.environ,
        'ANDROID_DATA' in os.environ,
        os.path.exists('/system/build.prop'),
        os.path.exists('/data/data'),
        os.environ.get('ANDROID_STORAGE') is not None,
        str(Path.home()) == '/data' or str(Path.home()).startswith('/data/'),
    ]
    return any(android_indicators)

def get_android_storage_path():
    """Get the best available storage path on Android"""
    # Try environment variables first
    storage_vars = ['EXTERNAL_STORAGE', 'ANDROID_STORAGE', 'SECONDARY_STORAGE']
    for var in storage_vars:
        path = os.environ.get(var)
        if path and os.path.exists(path):
            return Path(path)
    
    # Try common Android paths
    common_paths = [
        '/storage/emulated/0',
        '/sdcard',
        '/mnt/sdcard',
        '/storage/self/primary',
    ]
    for path in common_paths:
        if os.path.exists(path) and os.access(path, os.W_OK):
            return Path(path)
    
    return None

def get_download_path():
    """Get appropriate download path for the platform"""
    if is_android():
        # Try to get Android external storage
        storage = get_android_storage_path()
        if storage:
            return storage / "Music" / "YouTubeDownloads"
        
        # Fallback to app files directory (where the app has permission)
        app_files = os.environ.get('ANDROID_APP_FILES')
        if app_files and os.path.exists(app_files):
            return Path(app_files) / "Downloads"
        
        # Last resort: use cache directory
        cache_dir = os.environ.get('CACHE_DIR') or os.environ.get('TMPDIR')
        if cache_dir:
            return Path(cache_dir) / "YT_Downloads"
        
        # Final fallback
        return Path('/data/local/tmp') / "YT_Downloads"
    else:
        # Desktop platforms
        return Path.home() / "Music" / "YouTubeDownloads"

def get_config_dir():
    """Get configuration directory"""
    if is_android():
        # Try app data directory first
        app_data = os.environ.get('ANDROID_APP_DATA')
        if app_data and os.path.exists(app_data):
            return Path(app_data) / ".youtube_music_downloader"
        
        # Try app files directory
        app_files = os.environ.get('ANDROID_APP_FILES')
        if app_files and os.path.exists(app_files):
            return Path(app_files) / ".config"
        
        # Fallback to cache directory
        cache_dir = os.environ.get('CACHE_DIR') or os.environ.get('TMPDIR') or '/data/local/tmp'
        return Path(cache_dir) / ".yt_config"
    else:
        return Path.home() / ".youtube_music_downloader"

# Default paths
DEFAULT_DOWNLOAD_PATH = get_download_path()
SETTINGS_FILE = get_config_dir() / "settings.json"
HISTORY_FILE = get_config_dir() / "history.json"
QUEUE_EXPORT_DIR = get_config_dir() / "queues"

# Create directories if they don't exist (with error handling)
for path in [DEFAULT_DOWNLOAD_PATH, SETTINGS_FILE.parent, QUEUE_EXPORT_DIR]:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError) as e:
        print(f"Warning: Could not create directory {path}: {e}")
        # Use fallback path in temp directory
        import tempfile
        temp_path = Path(tempfile.gettempdir()) / "YT_Music_Downloader"
        if path == DEFAULT_DOWNLOAD_PATH:
            DEFAULT_DOWNLOAD_PATH = temp_path / "Downloads"
        elif path == SETTINGS_FILE.parent:
            SETTINGS_FILE = temp_path / "settings.json"
            HISTORY_FILE = temp_path / "history.json"
            QUEUE_EXPORT_DIR = temp_path / "queues"

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
