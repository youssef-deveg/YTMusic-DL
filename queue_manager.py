"""
Download Queue Manager
Manages the download queue with support for parallel downloads,
progress tracking, and status updates
"""

import asyncio
import uuid
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor

from config import DownloadStatus, MAX_CONCURRENT_DOWNLOADS
from settings import settings


@dataclass
class QueueItem:
    """Represents a single item in the download queue"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    video_id: str = ""
    title: str = ""
    channel: str = ""
    url: str = ""
    thumbnail: str = ""
    quality: str = "best_opus"
    status: str = DownloadStatus.WAITING
    progress: float = 0.0
    speed: str = ""
    eta: str = ""
    error_message: str = ""
    file_path: str = ""
    file_size: str = ""
    added_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    is_short: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export"""
        return {
            'id': self.id,
            'video_id': self.video_id,
            'title': self.title,
            'channel': self.channel,
            'url': self.url,
            'thumbnail': self.thumbnail,
            'quality': self.quality,
            'is_short': self.is_short
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueueItem':
        """Create QueueItem from dictionary"""
        item = cls()
        item.id = data.get('id', str(uuid.uuid4()))
        item.video_id = data.get('video_id', '')
        item.title = data.get('title', '')
        item.channel = data.get('channel', '')
        item.url = data.get('url', '')
        item.thumbnail = data.get('thumbnail', '')
        item.quality = data.get('quality', 'best_opus')
        item.is_short = data.get('is_short', False)
        return item


class QueueManager:
    """Manages the download queue with parallel download support"""
    
    def __init__(self):
        self.queue: List[QueueItem] = []
        self.callbacks: List[Callable] = []
        self._lock = threading.Lock()
        self._executor: Optional[ThreadPoolExecutor] = None
        self._active_downloads = 0
        self._stop_event = threading.Event()
        self._current_tasks = {}
    
    def add_callback(self, callback: Callable) -> None:
        """Add a callback to be called when queue changes"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable) -> None:
        """Remove a callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _notify_callbacks(self) -> None:
        """Notify all registered callbacks"""
        for callback in self.callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Callback error: {e}")
    
    def add_item(self, item: QueueItem) -> str:
        """Add item to queue"""
        with self._lock:
            self.queue.append(item)
        self._notify_callbacks()
        return item.id
    
    def add_items(self, items: List[QueueItem]) -> List[str]:
        """Add multiple items to queue"""
        with self._lock:
            self.queue.extend(items)
        self._notify_callbacks()
        return [item.id for item in items]
    
    def remove_item(self, item_id: str) -> bool:
        """Remove item from queue"""
        with self._lock:
            for i, item in enumerate(self.queue):
                if item.id == item_id:
                    if item.status == DownloadStatus.DOWNLOADING:
                        # Cancel active download
                        self.cancel_download(item_id)
                    self.queue.pop(i)
                    self._notify_callbacks()
                    return True
        return False
    
    def cancel_download(self, item_id: str) -> bool:
        """Cancel a specific download"""
        with self._lock:
            for item in self.queue:
                if item.id == item_id:
                    if item.status in [DownloadStatus.DOWNLOADING, DownloadStatus.PROCESSING]:
                        item.status = DownloadStatus.CANCELLED
                        # Mark for cancellation
                        if item_id in self._current_tasks:
                            self._current_tasks[item_id]['cancelled'] = True
                        self._notify_callbacks()
                        return True
        return False
    
    def cancel_all(self) -> None:
        """Cancel all active downloads"""
        with self._lock:
            for item in self.queue:
                if item.status in [DownloadStatus.DOWNLOADING, DownloadStatus.PROCESSING, DownloadStatus.WAITING]:
                    item.status = DownloadStatus.CANCELLED
                    if item.id in self._current_tasks:
                        self._current_tasks[item.id]['cancelled'] = True
        self._notify_callbacks()
    
    def retry_item(self, item_id: str) -> bool:
        """Retry a failed download"""
        with self._lock:
            for item in self.queue:
                if item.id == item_id and item.status == DownloadStatus.ERROR:
                    item.status = DownloadStatus.WAITING
                    item.progress = 0
                    item.error_message = ""
                    item.retry_count += 1
                    self._notify_callbacks()
                    return True
        return False
    
    def retry_all_failed(self) -> int:
        """Retry all failed downloads"""
        count = 0
        with self._lock:
            for item in self.queue:
                if item.status == DownloadStatus.ERROR:
                    item.status = DownloadStatus.WAITING
                    item.progress = 0
                    item.error_message = ""
                    item.retry_count += 1
                    count += 1
        if count > 0:
            self._notify_callbacks()
        return count
    
    def clear_completed(self) -> int:
        """Clear completed downloads from queue"""
        count = 0
        with self._lock:
            self.queue = [
                item for item in self.queue 
                if item.status not in [DownloadStatus.DONE, DownloadStatus.CANCELLED]
            ]
            count = len(self.queue)
        self._notify_callbacks()
        return count
    
    def clear_queue(self) -> None:
        """Clear entire queue"""
        self.cancel_all()
        with self._lock:
            self.queue = []
        self._notify_callbacks()
    
    def get_item(self, item_id: str) -> Optional[QueueItem]:
        """Get item by ID"""
        with self._lock:
            for item in self.queue:
                if item.id == item_id:
                    return item
        return None
    
    def get_queue(self) -> List[QueueItem]:
        """Get copy of queue"""
        with self._lock:
            return list(self.queue)
    
    def get_active_downloads(self) -> int:
        """Get number of active downloads"""
        with self._lock:
            return sum(1 for item in self.queue 
                      if item.status in [DownloadStatus.DOWNLOADING, DownloadStatus.PROCESSING])
    
    def get_pending_count(self) -> int:
        """Get number of pending downloads"""
        with self._lock:
            return sum(1 for item in self.queue if item.status == DownloadStatus.WAITING)
    
    def get_completed_count(self) -> int:
        """Get number of completed downloads"""
        with self._lock:
            return sum(1 for item in self.queue if item.status == DownloadStatus.DONE)
    
    def get_failed_count(self) -> int:
        """Get number of failed downloads"""
        with self._lock:
            return sum(1 for item in self.queue if item.status == DownloadStatus.ERROR)
    
    def update_item_progress(
        self, 
        item_id: str, 
        progress: float, 
        speed: str = "", 
        eta: str = ""
    ) -> None:
        """Update item progress"""
        with self._lock:
            for item in self.queue:
                if item.id == item_id:
                    item.progress = progress
                    if speed:
                        item.speed = speed
                    if eta:
                        item.eta = eta
                    break
        self._notify_callbacks()
    
    def update_item_status(self, item_id: str, status: str, error_msg: str = "") -> None:
        """Update item status"""
        with self._lock:
            for item in self.queue:
                if item.id == item_id:
                    item.status = status
                    if error_msg:
                        item.error_message = error_msg
                    
                    if status == DownloadStatus.DOWNLOADING and not item.started_at:
                        item.started_at = datetime.now()
                    elif status in [DownloadStatus.DONE, DownloadStatus.ERROR, DownloadStatus.CANCELLED]:
                        item.completed_at = datetime.now()
                    
                    break
        self._notify_callbacks()
    
    def is_cancelled(self, item_id: str) -> bool:
        """Check if item has been cancelled"""
        task_info = self._current_tasks.get(item_id, {})
        return task_info.get('cancelled', False)
    
    def get_global_progress(self) -> tuple:
        """Get global progress percentage and counts"""
        with self._lock:
            if not self.queue:
                return 0, 0, 0
            
            total_progress = 0
            completed = 0
            failed = 0
            
            for item in self.queue:
                if item.status == DownloadStatus.DONE:
                    total_progress += 100
                    completed += 1
                elif item.status == DownloadStatus.ERROR:
                    failed += 1
                elif item.status != DownloadStatus.CANCELLED:
                    total_progress += item.progress
            
            active_items = [item for item in self.queue 
                          if item.status not in [DownloadStatus.DONE, DownloadStatus.ERROR, DownloadStatus.CANCELLED]]
            
            if active_items:
                progress = total_progress / len(self.queue)
            else:
                progress = 100 if self.queue else 0
            
            return progress, completed, failed
    
    def export_queue(self, filename: str) -> bool:
        """Export queue to file"""
        items = [item.to_dict() for item in self.queue 
                if item.status in [DownloadStatus.WAITING, DownloadStatus.ERROR]]
        return settings.export_queue(items, filename)
    
    def import_queue(self, filename: str) -> int:
        """Import queue from file"""
        items = settings.import_queue(filename)
        if items:
            queue_items = [QueueItem.from_dict(item) for item in items]
            for item in queue_items:
                item.status = DownloadStatus.WAITING
                item.progress = 0
            self.add_items(queue_items)
            return len(queue_items)
        return 0
    
    def get_next_pending(self) -> Optional[QueueItem]:
        """Get next pending item"""
        with self._lock:
            for item in self.queue:
                if item.status == DownloadStatus.WAITING:
                    return item
        return None
    
    def can_start_download(self) -> bool:
        """Check if can start new download based on concurrent limit"""
        max_concurrent = settings.max_concurrent_downloads
        return self.get_active_downloads() < max_concurrent


# Global queue manager instance
queue_manager = QueueManager()
