"""
Utility functions for YouTube Music Downloader
Contains helper functions for formatting, validation, and data processing
"""

import re
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import httpx

from config import YOUTUBE_API_KEY, YOUTUBE_API_BASE_URL, AUDIO_QUALITIES


def format_duration(duration_str: str) -> str:
    """Format ISO 8601 duration to readable format"""
    if not duration_str:
        return "--:--"
    
    # Parse PT#M#S format
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match:
        return "--:--"
    
    hours, minutes, seconds = match.groups()
    hours = int(hours) if hours else 0
    minutes = int(minutes) if minutes else 0
    seconds = int(seconds) if seconds else 0
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def format_file_size(size_bytes: int) -> str:
    """Format file size to human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename"""
    # Remove invalid characters for Windows and Unix
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename.strip()


def create_filename(template: str, metadata: Dict[str, Any], quality: str) -> str:
    """Create filename from template and metadata"""
    artist = metadata.get('artist', metadata.get('uploader', 'Unknown'))
    title = metadata.get('title', 'Unknown')
    
    filename = template.format(
        artist=sanitize_filename(artist),
        title=sanitize_filename(title),
        quality=quality,
        upload_date=metadata.get('upload_date', ''),
        id=metadata.get('id', '')
    )
    
    return sanitize_filename(filename)


def get_video_id(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\s?]+)',
        r'youtube\.com\/shorts\/([^&\s?]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def is_playlist_url(url: str) -> bool:
    """Check if URL is a playlist"""
    return 'list=' in url or 'playlist' in url.lower()


def extract_playlist_id(url: str) -> Optional[str]:
    """Extract playlist ID from URL"""
    match = re.search(r'list=([^&\s]+)', url)
    return match.group(1) if match else None


def is_shorts_url(url: str) -> bool:
    """Check if URL is a YouTube Short"""
    return 'shorts' in url.lower()


def parse_iso_datetime(iso_string: str) -> datetime:
    """Parse ISO 8601 datetime string"""
    # Remove 'Z' and parse
    iso_string = iso_string.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(iso_string)
    except:
        return datetime.now()


def format_datetime(dt: datetime) -> str:
    """Format datetime to readable string"""
    return dt.strftime("%Y-%m-%d %H:%M")


def time_ago(dt: datetime) -> str:
    """Return human-readable time difference"""
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        return f"{int(diff.seconds / 60)} minutes ago"
    elif diff < timedelta(days=1):
        return f"{int(diff.seconds / 3600)} hours ago"
    elif diff < timedelta(days=30):
        return f"{diff.days} days ago"
    else:
        return format_datetime(dt)


def get_quality_label(quality_key: str) -> str:
    """Get human-readable quality label"""
    return AUDIO_QUALITIES.get(quality_key, {}).get('label', quality_key)


def get_quality_extension(quality_key: str) -> str:
    """Get file extension for quality"""
    return AUDIO_QUALITIES.get(quality_key, {}).get('ext', 'mp3')


def format_views(views: int) -> str:
    """Format view count to readable format"""
    if views >= 1_000_000_000:
        return f"{views / 1_000_000_000:.1f}B views"
    elif views >= 1_000_000:
        return f"{views / 1_000_000:.1f}M views"
    elif views >= 1_000:
        return f"{views / 1_000:.1f}K views"
    return f"{views} views"


def truncate_text(text: str, max_length: int = 60) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


async def check_internet_connection() -> bool:
    """Check if internet connection is available"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("https://www.google.com")
            return response.status_code == 200
    except:
        return False


def is_wifi_connected() -> bool:
    """Check if connected to WiFi (Linux/Android)"""
    try:
        # Check for common WiFi indicators
        if os.path.exists('/sys/class/net/wlan0/operstate'):
            with open('/sys/class/net/wlan0/operstate', 'r') as f:
                return f.read().strip() == 'up'
        return True  # Assume connected if can't determine
    except:
        return True


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load JSON file safely"""
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
    return {}


def save_json_file(file_path: Path, data: Dict[str, Any]) -> bool:
    """Save JSON file safely"""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving {file_path}: {e}")
        return False


def get_duration_seconds(duration_str: str) -> int:
    """Convert ISO duration to seconds"""
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match:
        return 0
    
    hours, minutes, seconds = match.groups()
    hours = int(hours) if hours else 0
    minutes = int(minutes) if minutes else 0
    seconds = int(seconds) if seconds else 0
    
    return hours * 3600 + minutes * 60 + seconds


def format_eta(seconds: float) -> str:
    """Format seconds to ETA string"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds / 60)}m {int(seconds % 60)}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"


def calculate_global_progress(queue_items: List[Dict]) -> tuple:
    """Calculate global progress from queue items"""
    if not queue_items:
        return 0, 0
    
    total_progress = 0
    completed = 0
    
    for item in queue_items:
        if item.get('status') == 'done':
            total_progress += 100
            completed += 1
        elif item.get('status') == 'error':
            completed += 1
        elif 'progress' in item:
            total_progress += item['progress']
    
    overall_progress = total_progress / len(queue_items) if queue_items else 0
    return overall_progress, completed
