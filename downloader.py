"""
Download Manager using yt-dlp
Handles downloading audio, metadata embedding, and sponsor block removal
"""

import os
import re
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import sys

# yt-dlp is an optional runtime dependency; handle missing imports gracefully
try:
    import yt_dlp
except Exception:
    yt_dlp = None
from yt_dlp.utils import DownloadError

from config import (
    AUDIO_QUALITIES, 
    DownloadStatus,
    DEFAULT_DOWNLOAD_PATH
)
from settings import settings
from utils import (
    sanitize_filename, 
    create_filename,
    get_quality_extension,
    format_file_size
)
from queue_manager import queue_manager, QueueItem


class ProgressHook:
    """Hook to track download progress"""
    
    def __init__(self, item_id: str):
        self.item_id = item_id
    
    def __call__(self, d):
        """Called by yt-dlp with progress updates"""
        if queue_manager.is_cancelled(self.item_id):
            raise Exception("Download cancelled by user")
        
        if d['status'] == 'downloading':
            # Calculate progress
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            
            if total > 0:
                progress = (downloaded / total) * 100
            else:
                progress = d.get('fragment_index', 0) / max(d.get('fragment_count', 1), 1) * 100
            
            # Format speed
            speed = d.get('speed', 0)
            if speed:
                speed_str = f"{format_file_size(int(speed))}/s"
            else:
                speed_str = ""
            
            # Format ETA
            eta = d.get('eta', 0)
            if eta:
                eta_str = f"{int(eta)}s"
            else:
                eta_str = ""
            
            queue_manager.update_item_progress(
                self.item_id, 
                progress, 
                speed_str, 
                eta_str
            )
            
            # Update status if not already downloading
            item = queue_manager.get_item(self.item_id)
            if item and item.status != DownloadStatus.DOWNLOADING:
                queue_manager.update_item_status(
                    self.item_id, 
                    DownloadStatus.DOWNLOADING
                )
        
        elif d['status'] == 'finished':
            queue_manager.update_item_status(
                self.item_id, 
                DownloadStatus.CONVERTING
            )


class AudioDownloader:
    """Handles audio downloads using yt-dlp"""
    
    def __init__(self):
        self.download_path = Path(settings.download_path)
        self.download_path.mkdir(parents=True, exist_ok=True)
    
    def get_ydl_options(
        self, 
        item: QueueItem, 
        progress_hook: ProgressHook
    ) -> Dict[str, Any]:
        """Get yt-dlp options for download"""
        quality = AUDIO_QUALITIES.get(item.quality, AUDIO_QUALITIES['best_opus'])
        ext = quality.get('ext', 'mp3')
        
        # Build output template
        template = settings.get('filename_template', '{artist} - {title} [{quality}]')
        
        # Postprocessors
        postprocessors = []

        # Audio extraction postprocessor
        if quality.get('codec'):
            pp_audio = {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': quality['codec'],
            }
            if quality.get('bitrate'):
                pp_audio['preferredquality'] = quality['bitrate']
            postprocessors.append(pp_audio)

        # Embed thumbnail
        if settings.get('embed_thumbnail', True):
            postprocessors.append({
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': False
            })

        # Add metadata
        if settings.get('add_metadata', True):
            postprocessors.append({'key': 'FFmpegMetadata'})

        # Sponsor block - remove sponsors, intros, outros, ads
        sponsorblock = []
        if settings.get('remove_sponsors', True):
            sponsorblock = ['sponsor', 'intro', 'outro', 'selfpromo', 'preview', 'filler']

        options = {
            'format': quality['format'],
            'outtmpl': str(self.download_path / f'%(title)s.%(ext)s'),
            'postprocessors': postprocessors,
            'progress_hooks': [progress_hook],
            'writethumbnail': settings.get('embed_thumbnail', True),
            'writeinfojson': False,
            'writesubtitles': settings.get('download_subtitles', True),
            'writeautomaticsub': False,
            'subtitleslangs': ['en', 'en-US'],
            'quiet': True,
            'no_warnings': True,
            'extractaudio': True,
            'audioformat': ext,
            'audioquality': '0',  # Best quality
            'embed_subs': settings.get('embed_subtitles', True),
            'embed_chapters': True,
            'parse_metadata': [
                'artist:%(uploader)s',
                'title:%(title)s',
                'album:%(album)s',
                'date:%(release_date)s'
            ],
            # leave postprocessor_args empty by default to avoid malformed ffmpeg args
            'postprocessor_args': []
        }

        if sponsorblock:
            options['sponsorblock_remove'] = sponsorblock

        return options
    
    def download(self, item: QueueItem) -> bool:
        """Download a single item"""
        if yt_dlp is None:
            queue_manager.update_item_status(
                item.id,
                DownloadStatus.ERROR,
                "yt-dlp is not installed"
            )
            return False

        try:
            # Update status
            queue_manager.update_item_status(
                item.id, 
                DownloadStatus.PROCESSING
            )
            
            # Create progress hook
            progress_hook = ProgressHook(item.id)
            
            # Get options
            ydl_opts = self.get_ydl_options(item, progress_hook)
            
            # Download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(item.url, download=True)
                
                if info:
                    # Get downloaded file path
                    filename = ydl.prepare_filename(info)
                    quality = AUDIO_QUALITIES.get(item.quality, AUDIO_QUALITIES['best_opus'])
                    ext = quality.get('ext', 'mp3')
                    
                    # Update filename with correct extension
                    base_path = Path(filename)
                    final_path = base_path.with_suffix(f'.{ext}')
                    
                    # Check if file exists
                    if final_path.exists():
                        item.file_path = str(final_path)
                        item.file_size = format_file_size(final_path.stat().st_size)
                    
                    # Update status to done
                    queue_manager.update_item_status(
                        item.id, 
                        DownloadStatus.DONE
                    )
                    
                    # Add to history
                    from settings import settings
                    settings.add_to_history({
                        'title': item.title,
                        'channel': item.channel,
                        'url': item.url,
                        'file_path': item.file_path,
                        'quality': item.quality,
                        'file_size': item.file_size
                    })
                    
                    return True
                else:
                    raise Exception("Failed to extract video info")
                    
        except Exception as e:
            error_msg = str(e)
            if "cancelled" in error_msg.lower():
                queue_manager.update_item_status(
                    item.id, 
                    DownloadStatus.CANCELLED
                )
            else:
                queue_manager.update_item_status(
                    item.id, 
                    DownloadStatus.ERROR,
                    error_msg
                )
            return False
    
    async def download_async(self, item: QueueItem) -> bool:
        """Download item asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.download, item)
    
    def get_preview_url(self, url: str, duration: int = 30) -> Optional[str]:
        """Get direct audio URL for preview"""
        if yt_dlp is None:
            return None

        try:
            ydl_opts = {
                'format': 'bestaudio[ext=webm]/bestaudio',
                'quiet': True,
                'no_warnings': True,
                'simulate': True,
                'geturl': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info and 'url' in info:
                    return info['url']
                elif info and 'formats' in info:
                    # Get best audio format
                    audio_formats = [f for f in info['formats'] 
                                   if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                    if audio_formats:
                        best_audio = max(audio_formats, key=lambda x: x.get('abr', 0) or 0)
                        return best_audio.get('url')
            
            return None
            
        except Exception as e:
            print(f"Error getting preview URL: {e}")
            return None
    
    def get_playlist_info(self, url: str) -> Optional[Dict]:
        """Get playlist information"""
        if yt_dlp is None:
            return None

        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'playlistend': 1000  # Limit to 1000 items
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    return {
                        'title': info.get('title', 'Unknown Playlist'),
                        'uploader': info.get('uploader', 'Unknown'),
                        'entries': [
                            {
                                'id': entry.get('id'),
                                'title': entry.get('title', 'Unknown'),
                                'url': entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                            }
                            for entry in info.get('entries', [])
                            if entry
                        ]
                    }
            return None
            
        except Exception as e:
            print(f"Error getting playlist info: {e}")
            return None


class DownloadWorker:
    """Worker that processes the download queue"""
    
    def __init__(self):
        self.downloader = AudioDownloader()
        self._running = False
        self._task = None
    
    async def start(self):
        """Start the download worker"""
        self._running = True
        self._task = asyncio.create_task(self._process_queue())
    
    def stop(self):
        """Stop the download worker"""
        self._running = False
        if self._task:
            self._task.cancel()
    
    async def _process_queue(self):
        """Process download queue continuously"""
        while self._running:
            try:
                # Check if we can start a new download
                if queue_manager.can_start_download():
                    # Get next pending item
                    item = queue_manager.get_next_pending()
                    
                    if item:
                        # Start download
                        asyncio.create_task(self._download_item(item))
                    else:
                        # No pending items, wait a bit
                        await asyncio.sleep(1)
                else:
                    # Max concurrent downloads reached, wait
                    await asyncio.sleep(0.5)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Queue processing error: {e}")
                await asyncio.sleep(1)
    
    async def _download_item(self, item: QueueItem):
        """Download a single queue item"""
        try:
            # Track this task
            queue_manager._current_tasks[item.id] = {'cancelled': False}
            
            # Download
            success = await self.downloader.download_async(item)
            
            # Clean up
            if item.id in queue_manager._current_tasks:
                del queue_manager._current_tasks[item.id]
            
        except Exception as e:
            print(f"Download error for {item.title}: {e}")
            queue_manager.update_item_status(
                item.id,
                DownloadStatus.ERROR,
                str(e)
            )


def update_ytdlp() -> tuple:
    """Update yt-dlp to latest version"""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-U', 'yt-dlp'],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            return True, "yt-dlp updated successfully"
        else:
            return False, f"Update failed: {result.stderr}"
            
    except Exception as e:
        return False, f"Update error: {str(e)}"


# Global download worker
worker = DownloadWorker()
