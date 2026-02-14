"""
UI Components for YouTube Music Downloader
Contains all Flet UI elements, layouts, and event handlers
"""

import flet as ft
from typing import List, Dict, Any, Optional, Callable
import asyncio
from datetime import datetime

from config import (
    AUDIO_QUALITIES,
    SEARCH_SORT_OPTIONS,
    DURATION_FILTERS,
    VIDEO_TYPE_FILTERS,
    UI_CONFIG,
    DownloadStatus
)
from settings import settings
from queue_manager import queue_manager, QueueItem
from downloader import AudioDownloader, update_ytdlp, worker
from search import YouTubeSearcher
from utils import (
    format_duration,
    format_views,
    truncate_text,
    get_video_id,
    extract_playlist_id,
    is_playlist_url,
    is_shorts_url
)


class SearchResultCard(ft.Card):
    """Card component for displaying search results"""
    
    def __init__(
        self,
        video_data: Dict[str, Any],
        on_add_to_queue: Callable,
        default_quality: str = "best_opus"
    ):
        super().__init__()
        self.video_data = video_data
        self.on_add_to_queue = on_add_to_queue
        self.selected_quality = default_quality
        
        # Quality dropdown
        self.quality_dropdown = ft.Dropdown(
            label="Quality",
            value=default_quality,
            options=[
                ft.dropdown.Option(key=k, text=v['label'])
                for k, v in AUDIO_QUALITIES.items()
            ],
            width=150,
            on_change=self.on_quality_change
        )
        
        # Add to queue button
        self.add_button = ft.ElevatedButton(
            "Add to Queue",
            icon=ft.icons.ADD,
            on_click=self.on_add_click
        )
        
        # Preview button
        self.preview_button = ft.IconButton(
            icon=ft.icons.PLAY_ARROW,
            tooltip="Preview (30s)",
            on_click=self.on_preview_click
        )
        
        # Build card content
        thumbnail = ft.Image(
            src=video_data.get('thumbnail', ''),
            width=200,
            height=120,
            fit=ft.ImageFit.COVER,
            border_radius=8
        )
        
        # Short badge
        badges = []
        if video_data.get('is_short'):
            badges.append(ft.Chip(label=ft.Text("SHORT"), bgcolor=ft.Colors.PINK))
        
        # Content layout
        content = ft.Container(
            content=ft.Row(
                [
                    # Thumbnail
                    ft.Container(
                        content=thumbnail,
                        border_radius=8
                    ),
                    
                    # Info
                    ft.Expanded(
                        child=ft.Column(
                            [
                                ft.Row(badges) if badges else ft.Container(),
                                ft.Text(
                                    truncate_text(video_data.get('title', ''), 50),
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    no_wrap=True
                                ),
                                ft.Text(
                                    video_data.get('channel', ''),
                                    size=12,
                                    color=ft.Colors.GREY_400
                                ),
                                ft.Row(
                                    [
                                        ft.Text(
                                            video_data.get('duration', '--:--'),
                                            size=12
                                        ),
                                        ft.Text("•", size=12),
                                        ft.Text(
                                            video_data.get('views_formatted', '0 views'),
                                            size=12
                                        )
                                    ]
                                )
                            ],
                            spacing=4,
                            alignment=ft.MainAxisAlignment.START,
                            horizontal_alignment=ft.CrossAxisAlignment.START
                        )
                    ),
                    
                    # Actions
                    ft.Column(
                        [
                            self.quality_dropdown,
                            ft.Row(
                                [self.preview_button, self.add_button],
                                spacing=8
                            )
                        ],
                        spacing=8,
                        horizontal_alignment=ft.CrossAxisAlignment.END
                    )
                ],
                spacing=12
            ),
            padding=12
        )
        
        self.content = content
    
    def on_quality_change(self, e):
        """Handle quality selection change"""
        self.selected_quality = e.control.value
    
    def on_add_click(self, e):
        """Handle add to queue button click"""
        self.on_add_to_queue(self.video_data, self.selected_quality)
    
    def on_preview_click(self, e):
        """Handle preview button click"""
        # Will be implemented in main UI
        pass


class QueueItemCard(ft.Card):
    """Card component for displaying queue items"""
    
    def __init__(
        self,
        item: QueueItem,
        on_cancel: Optional[Callable] = None,
        on_retry: Optional[Callable] = None,
        on_remove: Optional[Callable] = None
    ):
        super().__init__()
        self.item = item
        self.on_cancel = on_cancel
        self.on_retry = on_retry
        self.on_remove = on_remove
        
        # Status colors
        self.status_colors = {
            DownloadStatus.WAITING: ft.Colors.GREY,
            DownloadStatus.PROCESSING: ft.Colors.BLUE,
            DownloadStatus.DOWNLOADING: ft.Colors.BLUE,
            DownloadStatus.CONVERTING: ft.Colors.ORANGE,
            DownloadStatus.DONE: ft.Colors.GREEN,
            DownloadStatus.ERROR: ft.Colors.RED,
            DownloadStatus.CANCELLED: ft.Colors.GREY
        }
        
        # Build card
        self.update_content()
    
    def update_content(self):
        """Update card content based on item status"""
        status_color = self.status_colors.get(self.item.status, ft.Colors.GREY)
        
        # Progress bar
        progress_bar = ft.ProgressBar(
            value=self.item.progress / 100,
            width=200,
            color=status_color
        )
        
        # Status text
        status_text = ft.Text(
            self.item.status.upper(),
            size=12,
            color=status_color,
            weight=ft.FontWeight.BOLD
        )
        
        # Progress percentage
        progress_text = ft.Text(
            f"{self.item.progress:.1f}%",
            size=12
        )
        
        # Speed and ETA
        info_text = ft.Text(
            f"{self.item.speed} {self.item.eta}",
            size=11,
            color=ft.Colors.GREY_400
        )
        
        # Action buttons
        buttons = []
        
        if self.item.status in [DownloadStatus.DOWNLOADING, DownloadStatus.PROCESSING]:
            buttons.append(
                ft.IconButton(
                    icon=ft.icons.CANCEL,
                    tooltip="Cancel",
                    on_click=self.on_cancel_click,
                    icon_color=ft.Colors.RED
                )
            )
        elif self.item.status == DownloadStatus.ERROR:
            buttons.append(
                ft.IconButton(
                    icon=ft.icons.REPLAY,
                    tooltip="Retry",
                    on_click=self.on_retry_click,
                    icon_color=ft.Colors.BLUE
                )
            )
            if self.item.error_message:
                buttons.append(
                    ft.IconButton(
                        icon=ft.icons.ERROR,
                        tooltip=self.item.error_message,
                        icon_color=ft.Colors.RED
                    )
                )
        elif self.item.status == DownloadStatus.DONE:
            buttons.append(
                ft.IconButton(
                    icon=ft.icons.CHECK_CIRCLE,
                    tooltip="Completed",
                    icon_color=ft.Colors.GREEN,
                    disabled=True
                )
            )
        
        buttons.append(
            ft.IconButton(
                icon=ft.icons.DELETE,
                tooltip="Remove from queue",
                on_click=self.on_remove_click
            )
        )
        
        # Build content
        content = ft.Container(
            content=ft.Row(
                [
                    # Thumbnail
                    ft.Container(
                        content=ft.Image(
                            src=self.item.thumbnail or "",
                            width=80,
                            height=60,
                            fit=ft.ImageFit.COVER,
                            border_radius=4
                        ),
                        border_radius=4
                    ),
                    
                    # Info
                    ft.Expanded(
                        child=ft.Column(
                            [
                                ft.Text(
                                    truncate_text(self.item.title, 40),
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    no_wrap=True
                                ),
                                ft.Text(
                                    self.item.channel,
                                    size=11,
                                    color=ft.Colors.GREY_400
                                ),
                                ft.Row(
                                    [
                                        ft.Text(
                                            AUDIO_QUALITIES.get(self.item.quality, {}).get('label', self.item.quality),
                                            size=10,
                                            color=ft.Colors.GREY_500
                                        )
                                    ]
                                )
                            ],
                            spacing=2
                        )
                    ),
                    
                    # Progress
                    ft.Column(
                        [
                            ft.Row([status_text, progress_text], spacing=8),
                            progress_bar,
                            info_text
                        ],
                        spacing=4,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        width=200
                    ),
                    
                    # Buttons
                    ft.Row(buttons, spacing=4)
                ],
                spacing=12
            ),
            padding=8
        )
        
        self.content = content
    
    def on_cancel_click(self, e):
        """Handle cancel button click"""
        if self.on_cancel:
            self.on_cancel(self.item.id)
    
    def on_retry_click(self, e):
        """Handle retry button click"""
        if self.on_retry:
            self.on_retry(self.item.id)
    
    def on_remove_click(self, e):
        """Handle remove button click"""
        if self.on_remove:
            self.on_remove(self.item.id)


class HistoryItemCard(ft.Card):
    """Card component for displaying download history"""
    
    def __init__(
        self,
        item: Dict[str, Any],
        on_play: Optional[Callable] = None,
        on_delete: Optional[Callable] = None
    ):
        super().__init__()
        self.item = item
        self.on_play = on_play
        self.on_delete = on_delete
        
        content = ft.Container(
            content=ft.Row(
                [
                    # Icon
                    ft.Icon(
                        ft.icons.AUDIO_FILE,
                        size=40,
                        color=ft.Colors.GREEN
                    ),
                    
                    # Info
                    ft.Expanded(
                        child=ft.Column(
                            [
                                ft.Text(
                                    truncate_text(item.get('title', ''), 40),
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    no_wrap=True
                                ),
                                ft.Text(
                                    item.get('channel', ''),
                                    size=11,
                                    color=ft.Colors.GREY_400
                                ),
                                ft.Row(
                                    [
                                        ft.Text(
                                            item.get('file_size', ''),
                                            size=10,
                                            color=ft.Colors.GREY_500
                                        ),
                                        ft.Text("•", size=10),
                                        ft.Text(
                                            item.get('quality', ''),
                                            size=10,
                                            color=ft.Colors.GREY_500
                                        )
                                    ]
                                )
                            ],
                            spacing=2
                        )
                    ),
                    
                    # Actions
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.icons.PLAY_ARROW,
                                tooltip="Play",
                                on_click=self.on_play_click
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                tooltip="Remove from history",
                                on_click=self.on_delete_click
                            )
                        ],
                        spacing=4
                    )
                ],
                spacing=12
            ),
            padding=8
        )
        
        self.content = content
    
    def on_play_click(self, e):
        """Handle play button click"""
        if self.on_play:
            self.on_play(self.item)
    
    def on_delete_click(self, e):
        """Handle delete button click"""
        if self.on_delete:
            self.on_delete(self.item)


class SettingsDialog(ft.AlertDialog):
    """Settings dialog"""
    
    def __init__(self, on_save: Callable, on_close: Callable):
        super().__init__()
        self.on_save = on_save
        self.on_close = on_close
        
        # Settings controls
        self.download_path_field = ft.TextField(
            label="Download Path",
            value=settings.download_path,
            read_only=True,
            suffix=ft.IconButton(
                icon=ft.icons.FOLDER_OPEN,
                tooltip="Browse",
                on_click=self.on_browse_click
            )
        )
        
        self.quality_dropdown = ft.Dropdown(
            label="Default Quality",
            value=settings.default_quality,
            options=[
                ft.dropdown.Option(key=k, text=v['label'])
                for k, v in AUDIO_QUALITIES.items()
            ]
        )
        
        self.concurrent_slider = ft.Slider(
            label="Max Concurrent Downloads: {value}",
            min=1,
            max=5,
            divisions=4,
            value=settings.max_concurrent_downloads
        )
        
        self.theme_dropdown = ft.Dropdown(
            label="Theme",
            value=settings.theme,
            options=[
                ft.dropdown.Option("dark", "Dark"),
                ft.dropdown.Option("light", "Light"),
                ft.dropdown.Option("auto", "Auto")
            ]
        )
        
        self.data_saver_switch = ft.Switch(
            label="Data Saver Mode (WiFi only)",
            value=settings.data_saver_mode
        )
        
        self.embed_thumbnail_switch = ft.Switch(
            label="Embed Thumbnails",
            value=settings.get('embed_thumbnail', True)
        )
        
        self.add_metadata_switch = ft.Switch(
            label="Add Metadata",
            value=settings.get('add_metadata', True)
        )
        
        self.remove_sponsors_switch = ft.Switch(
            label="Remove Sponsors/Intros/Outros",
            value=settings.get('remove_sponsors', True)
        )
        
        self.download_subtitles_switch = ft.Switch(
            label="Download Subtitles/Lyrics",
            value=settings.get('download_subtitles', True)
        )
        
        self.filename_template_field = ft.TextField(
            label="Filename Template",
            value=settings.get('filename_template', '{artist} - {title} [{quality}]'),
            hint_text="Available: {artist}, {title}, {quality}, {upload_date}, {id}"
        )
        
        # Actions
        self.actions = [
            ft.TextButton("Cancel", on_click=self.on_cancel),
            ft.ElevatedButton("Save", on_click=self.on_save_click),
            ft.TextButton("Reset to Defaults", on_click=self.on_reset_click)
        ]
        
        # Content
        self.content = ft.Column(
            [
                self.download_path_field,
                ft.Row([self.quality_dropdown, self.theme_dropdown], spacing=16),
                self.concurrent_slider,
                ft.Divider(),
                self.filename_template_field,
                ft.Divider(),
                self.data_saver_switch,
                self.embed_thumbnail_switch,
                self.add_metadata_switch,
                self.remove_sponsors_switch,
                self.download_subtitles_switch
            ],
            scroll=ft.ScrollMode.AUTO,
            height=400
        )
    
    def on_browse_click(self, e):
        """Handle browse button click"""
        # Platform-specific folder picker would go here
        pass
    
    def on_cancel(self, e):
        """Handle cancel button click"""
        self.on_close()
    
    def on_save_click(self, e):
        """Handle save button click"""
        new_settings = {
            'download_path': self.download_path_field.value,
            'default_quality': self.quality_dropdown.value,
            'max_concurrent_downloads': int(self.concurrent_slider.value),
            'theme': self.theme_dropdown.value,
            'data_saver_mode': self.data_saver_switch.value,
            'embed_thumbnail': self.embed_thumbnail_switch.value,
            'add_metadata': self.add_metadata_switch.value,
            'remove_sponsors': self.remove_sponsors_switch.value,
            'download_subtitles': self.download_subtitles_switch.value,
            'filename_template': self.filename_template_field.value
        }
        self.on_save(new_settings)
    
    def on_reset_click(self, e):
        """Handle reset button click"""
        settings.reset_to_defaults()
        self.on_close()


class PlaylistInputDialog(ft.AlertDialog):
    """Dialog for playlist URL input"""
    
    def __init__(self, on_confirm: Callable, on_cancel: Callable):
        super().__init__()
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        
        self.url_field = ft.TextField(
            label="Playlist URL",
            hint_text="https://www.youtube.com/playlist?list=...",
            prefix_icon=ft.icons.LINK
        )
        
        self.quality_dropdown = ft.Dropdown(
            label="Quality",
            value=settings.default_quality,
            options=[
                ft.dropdown.Option(key=k, text=v['label'])
                for k, v in AUDIO_QUALITIES.items()
            ]
        )
        
        self.content = ft.Column(
            [
                self.url_field,
                self.quality_dropdown
            ],
            tight=True
        )
        
        self.actions = [
            ft.TextButton("Cancel", on_click=lambda e: on_cancel()),
            ft.ElevatedButton("Add Playlist", on_click=self.on_add_click)
        ]
    
    def on_add_click(self, e):
        """Handle add button click"""
        url = self.url_field.value.strip()
        if url:
            self.on_confirm(url, self.quality_dropdown.value)


class ExportQueueDialog(ft.AlertDialog):
    """Dialog for exporting queue"""
    
    def __init__(self, on_export: Callable, on_cancel: Callable):
        super().__init__()
        self.on_export = on_export
        self.on_cancel = on_cancel
        
        self.filename_field = ft.TextField(
            label="Filename",
            hint_text="my_queue",
            prefix_icon=ft.icons.SAVE
        )
        
        self.content = self.filename_field
        self.actions = [
            ft.TextButton("Cancel", on_click=lambda e: on_cancel()),
            ft.ElevatedButton("Export", on_click=self.on_export_click)
        ]
    
    def on_export_click(self, e):
        """Handle export button click"""
        filename = self.filename_field.value.strip()
        if filename:
            self.on_export(filename)


class ImportQueueDialog(ft.AlertDialog):
    """Dialog for importing queue"""
    
    def __init__(self, files: List[Dict], on_import: Callable, on_cancel: Callable):
        super().__init__()
        self.on_import = on_import
        self.on_cancel = on_cancel
        
        self.file_dropdown = ft.Dropdown(
            label="Select Queue File",
            options=[
                ft.dropdown.Option(f['name'], f"{f['name']} ({f.get('modified', '')})")
                for f in files
            ]
        )
        
        self.content = self.file_dropdown
        self.actions = [
            ft.TextButton("Cancel", on_click=lambda e: on_cancel()),
            ft.ElevatedButton("Import", on_click=self.on_import_click)
        ]
    
    def on_import_click(self, e):
        """Handle import button click"""
        if self.file_dropdown.value:
            self.on_import(self.file_dropdown.value)
