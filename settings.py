"""
Settings management module
Handles loading, saving, and updating application settings
Uses JSON file for persistence
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import flet as ft

from config import DEFAULT_SETTINGS, SETTINGS_FILE, HISTORY_FILE, QUEUE_EXPORT_DIR
from utils import load_json_file, save_json_file


class SettingsManager:
    """Manages application settings and persistent storage"""
    
    def __init__(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.history = []
        self.load_settings()
        self.load_history()
    
    def load_settings(self) -> None:
        """Load settings from file"""
        data = load_json_file(SETTINGS_FILE)
        if data:
            self.settings.update(data)
    
    def save_settings(self) -> bool:
        """Save settings to file"""
        return save_json_file(SETTINGS_FILE, self.settings)
    
    def get(self, key: str, default=None) -> Any:
        """Get setting value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set setting value and save"""
        self.settings[key] = value
        self.save_settings()
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple settings"""
        self.settings.update(updates)
        self.save_settings()
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults"""
        self.settings = DEFAULT_SETTINGS.copy()
        self.save_settings()
    
    def load_history(self) -> None:
        """Load download history"""
        data = load_json_file(HISTORY_FILE)
        if isinstance(data, list):
            self.history = data
        elif isinstance(data, dict) and 'history' in data:
            self.history = data['history']
    
    def save_history(self) -> bool:
        """Save download history"""
        return save_json_file(HISTORY_FILE, {"history": self.history})
    
    def add_to_history(self, item: Dict[str, Any]) -> None:
        """Add item to download history"""
        item['timestamp'] = str(Path().stat().st_mtime)  # Simple timestamp
        self.history.insert(0, item)  # Add to beginning
        
        # Keep only last 1000 items
        if len(self.history) > 1000:
            self.history = self.history[:1000]
        
        self.save_history()
    
    def get_history(self, limit: int = 100) -> list:
        """Get recent download history"""
        return self.history[:limit]
    
    def clear_history(self) -> None:
        """Clear download history"""
        self.history = []
        self.save_history()
    
    def export_queue(self, queue_items: list, filename: str) -> bool:
        """Export queue to JSON file"""
        try:
            export_path = QUEUE_EXPORT_DIR / f"{filename}.json"
            export_data = {
                "exported_at": str(Path().stat().st_mtime),
                "items": queue_items
            }
            return save_json_file(export_path, export_data)
        except Exception as e:
            print(f"Error exporting queue: {e}")
            return False
    
    def import_queue(self, filename: str) -> Optional[list]:
        """Import queue from JSON file"""
        try:
            import_path = QUEUE_EXPORT_DIR / f"{filename}.json"
            data = load_json_file(import_path)
            return data.get('items', [])
        except Exception as e:
            print(f"Error importing queue: {e}")
            return None
    
    def list_exported_queues(self) -> list:
        """List all exported queue files"""
        try:
            files = []
            for f in QUEUE_EXPORT_DIR.glob("*.json"):
                files.append({
                    "name": f.stem,
                    "path": str(f),
                    "modified": f.stat().st_mtime
                })
            return sorted(files, key=lambda x: x['modified'], reverse=True)
        except:
            return []
    
    def delete_exported_queue(self, filename: str) -> bool:
        """Delete exported queue file"""
        try:
            file_path = QUEUE_EXPORT_DIR / f"{filename}.json"
            if file_path.exists():
                file_path.unlink()
                return True
        except Exception as e:
            print(f"Error deleting queue file: {e}")
        return False
    
    # Convenience properties
    @property
    def download_path(self) -> Path:
        """Get download path"""
        path = Path(self.get('download_path', DEFAULT_SETTINGS['download_path']))
        try:
            path.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            print(f"Warning: Could not create download directory {path}: {e}")
            # Try to get Android external storage
            import os
            android_storage = os.environ.get('EXTERNAL_STORAGE') or '/storage/emulated/0'
            if os.path.exists(android_storage):
                path = Path(android_storage) / "Music" / "YouTubeDownloads"
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except:
                    pass
        return path
    
    @download_path.setter
    def download_path(self, value: str) -> None:
        """Set download path"""
        self.set('download_path', value)
    
    @property
    def theme(self) -> str:
        """Get theme setting"""
        return self.get('theme', 'dark')
    
    @theme.setter
    def theme(self, value: str) -> None:
        """Set theme"""
        self.set('theme', value)
    
    @property
    def max_concurrent_downloads(self) -> int:
        """Get max concurrent downloads"""
        return self.get('max_concurrent_downloads', 3)
    
    @max_concurrent_downloads.setter
    def max_concurrent_downloads(self, value: int) -> None:
        """Set max concurrent downloads"""
        value = max(1, min(5, value))
        self.set('max_concurrent_downloads', value)
    
    @property
    def default_quality(self) -> str:
        """Get default quality"""
        return self.get('default_quality', 'best_opus')
    
    @default_quality.setter
    def default_quality(self, value: str) -> None:
        """Set default quality"""
        self.set('default_quality', value)
    
    @property
    def data_saver_mode(self) -> bool:
        """Get data saver mode"""
        return self.get('data_saver_mode', False)
    
    @data_saver_mode.setter
    def data_saver_mode(self, value: bool) -> None:
        """Set data saver mode"""
        self.set('data_saver_mode', value)


# Global settings instance
settings = SettingsManager()
