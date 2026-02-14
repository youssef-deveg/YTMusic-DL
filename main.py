"""
YouTube Music Downloader - Main Application
Entry point for the Flet desktop and mobile application
"""

import flet as ft
from flet import Page, View
import asyncio
from datetime import datetime
from pathlib import Path

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
from ui import (
    SearchResultCard,
    QueueItemCard,
    HistoryItemCard,
    SettingsDialog,
    PlaylistInputDialog,
    ExportQueueDialog,
    ImportQueueDialog
)
from utils import (
    is_playlist_url,
    extract_playlist_id,
    get_video_id,
    format_duration,
    check_internet_connection,
    is_wifi_connected
)


class YouTubeMusicDownloader:
    """Main application class"""
    
    def __init__(self, page: Page):
        self.page = page
        self.searcher = None
        self.downloader = AudioDownloader()
        self.current_results = []
        
        # UI Components
        self.search_field = None
        self.search_button = None
        self.results_list = None
        self.queue_list = None
        self.history_list = None
        self.global_progress_bar = None
        self.global_status_text = None
        self.nav_bar = None
        self.tab_content = None
        self.audio_player = None
        
        # Setup
        self.setup_page()
        self.setup_ui()
        self.setup_event_handlers()
        
        # Start background tasks
        self.page.run_task(self.initialize)
    
    def setup_page(self):
        """Configure page settings"""
        self.page.title = "YouTube Music Downloader"
        self.page.theme_mode = ft.ThemeMode.DARK if settings.theme == "dark" else ft.ThemeMode.LIGHT
        self.page.padding = 0
        self.page.window_width = 1200
        self.page.window_height = 800
        
        # Apply theme colors
        theme = UI_CONFIG['theme_colors'][settings.theme]
        self.page.bgcolor = theme['bg']
    
    def setup_ui(self):
        """Setup UI components"""
        # Resolve theme colors for current theme
        theme = UI_CONFIG['theme_colors'][settings.theme]
        # App Bar
        self.page.appbar = ft.AppBar(
            title=ft.Text("YouTube Music Downloader", size=20, weight=ft.FontWeight.BOLD),
            center_title=False,
                bgcolor=theme.get('surface', None),
            actions=[
                    ft.IconButton(
                        icon=ft.Icons.SETTINGS,
                    tooltip="Settings",
                    on_click=self.on_settings_click
                ),
                    ft.IconButton(
                        icon=ft.Icons.UPDATE,
                    tooltip="Update yt-dlp",
                    on_click=self.on_update_ytdlp_click
                )
            ]
        )
        
        # Global Progress Bar
        self.global_progress_bar = ft.ProgressBar(
            value=0,
            width=400,
                    color=ft.Colors.GREEN
        )
        
        self.global_status_text = ft.Text(
            "Ready",
            size=12,
                    color=ft.Colors.GREY_400
        )
        
        # Search Tab
        search_tab = self.create_search_tab()
        
        # Queue Tab
        queue_tab = self.create_queue_tab()
        
        # History Tab
        history_tab = self.create_history_tab()
        
        # Settings Tab
        settings_tab = self.create_settings_tab()
        
        # Content container for tabs
        self.tab_content = ft.Container(content=search_tab, expand=True)
        
        # NavigationBar for tab switching
        self.nav_bar = ft.NavigationBar(
            selected_index=0,
            on_change=self.on_tab_change,
            destinations=[
                ft.NavigationBarDestination(
                    label="Search",
                    icon=ft.Icons.SEARCH
                ),
                ft.NavigationBarDestination(
                    label="Queue",
                    icon=ft.Icons.QUEUE_MUSIC
                ),
                ft.NavigationBarDestination(
                    label="History",
                    icon=ft.Icons.HISTORY
                ),
                ft.NavigationBarDestination(
                    label="Settings",
                    icon=ft.Icons.SETTINGS
                )
            ],
            bgcolor=theme.get('surface', None)
        )
        
        # Store tab contents
        self.tab_contents = [search_tab, queue_tab, history_tab, settings_tab]
        
        # Global Progress Row
        progress_row = ft.Container(
            content=ft.Row(
                [
                        ft.Icon(ft.Icons.DOWNLOAD, color=ft.Colors.GREEN),
                    self.global_progress_bar,
                    self.global_status_text
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12
            ),
            padding=ft.padding.all(8),
            bgcolor=theme.get('surface', None)
        )
        
        # Main Layout
        self.page.add(
            ft.Column(
                [
                    self.tab_content,
                    progress_row,
                    self.nav_bar
                ],
                expand=True,
                spacing=0
            )
        )
    
    def create_search_tab(self):
        """Create search tab content"""
        # Search bar
        self.search_field = ft.TextField(
            label="Search YouTube Music",
            hint_text="Enter song, artist, or album name...",
                prefix_icon=ft.Icons.SEARCH,
            on_submit=self.on_search_submit,
            expand=True
        )
        
        self.search_button = ft.ElevatedButton(
            "Search",
                icon=ft.Icons.SEARCH,
            on_click=self.on_search_click
        )
        
        # Filter controls
        sort_dropdown = ft.Dropdown(
            label="Sort By",
            value=settings.get('search_sort', 'relevance'),
            options=[ft.dropdown.Option(s['value'], s['label']) for s in SEARCH_SORT_OPTIONS],
            width=150,
        )
        sort_dropdown.on_select = self.on_sort_change
        
        duration_dropdown = ft.Dropdown(
            label="Duration",
            value=settings.get('search_duration_filter', ''),
            options=[ft.dropdown.Option(d['value'], d['label']) for d in DURATION_FILTERS],
            width=150,
        )
        duration_dropdown.on_select = self.on_duration_filter_change
        
        type_dropdown = ft.Dropdown(
            label="Type",
            value=settings.get('search_type_filter', ''),
            options=[ft.dropdown.Option(t['value'], t['label']) for t in VIDEO_TYPE_FILTERS],
            width=150,
        )
        type_dropdown.on_select = self.on_type_filter_change
        
        # Playlist button
        playlist_button = ft.ElevatedButton(
            "Add Playlist",
                icon=ft.Icons.PLAYLIST_ADD,
            on_click=self.on_add_playlist_click
        )
        
        # Download All button
        download_all_button = ft.ElevatedButton(
            "Download All Results",
                icon=ft.Icons.DOWNLOAD,
            on_click=self.on_download_all_click
        )
        
        # Search bar row
        search_row = ft.Row(
            [
                self.search_field,
                self.search_button,
                playlist_button
            ],
            spacing=12
        )
        
        # Filter row
        filter_row = ft.Row(
            [
                sort_dropdown,
                duration_dropdown,
                type_dropdown,
                download_all_button
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO
        )
        
        # Results list
        self.results_list = ft.ListView(
            expand=True,
            spacing=8,
            padding=ft.padding.all(16)
        )
        
        # Initial message
        self.results_list.controls.append(
            ft.Container(
                content=ft.Column(
                    [
                            ft.Icon(ft.Icons.SEARCH, size=64, color=ft.Colors.GREY_700),
                        ft.Text(
                            "Search for your favorite music",
                            size=18,
                                color=ft.Colors.GREY_500
                        ),
                        ft.Text(
                            "Enter a song name, artist, or paste a YouTube URL",
                            size=14,
                                color=ft.Colors.GREY_600
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                alignment=ft.Alignment.CENTER,
                expand=True
            )
        )
        
        return ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        [search_row, filter_row],
                        spacing=12
                    ),
                    padding=ft.padding.all(16)
                ),
                ft.Divider(height=1),
                self.results_list
            ],
            expand=True
        )
    
    def create_queue_tab(self):
        """Create queue tab content"""
        # Action buttons
        clear_completed_btn = ft.TextButton(
            "Clear Completed",
            icon=ft.Icons.CLEAR_ALL,
            on_click=self.on_clear_completed_click
        )
        
        retry_all_btn = ft.TextButton(
            "Retry All Failed",
            icon=ft.Icons.REPLAY,
            on_click=self.on_retry_all_click
        )
        
        cancel_all_btn = ft.TextButton(
            "Cancel All",
            icon=ft.Icons.CANCEL,
            on_click=self.on_cancel_all_click
        )
        
        export_btn = ft.IconButton(
            icon=ft.Icons.UPLOAD,
            tooltip="Export Queue",
            on_click=self.on_export_queue_click
        )
        
        import_btn = ft.IconButton(
            icon=ft.Icons.DOWNLOAD,
            tooltip="Import Queue",
            on_click=self.on_import_queue_click
        )
        
        # Header row
        header = ft.Row(
            [
                ft.Text("Download Queue", size=18, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [clear_completed_btn, retry_all_btn, cancel_all_btn, export_btn, import_btn],
                    spacing=8
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        
        # Queue list
        self.queue_list = ft.ListView(
            expand=True,
            spacing=8,
            padding=ft.padding.all(16)
        )
        
        return ft.Column(
            [
                ft.Container(content=header, padding=ft.padding.all(16)),
                ft.Divider(height=1),
                self.queue_list
            ],
            expand=True
        )
    
    def create_history_tab(self):
        """Create history tab content"""
        # Action buttons
        clear_history_btn = ft.TextButton(
            "Clear History",
            icon=ft.Icons.DELETE_SWEEP,
            on_click=self.on_clear_history_click
        )
        
        # Header
        header = ft.Row(
            [
                ft.Text("Download History", size=18, weight=ft.FontWeight.BOLD),
                clear_history_btn
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        
        # History list
        self.history_list = ft.ListView(
            expand=True,
            spacing=8,
            padding=ft.padding.all(16)
        )
        
        return ft.Column(
            [
                ft.Container(content=header, padding=ft.padding.all(16)),
                ft.Divider(height=1),
                self.history_list
            ],
            expand=True
        )
    
    def create_settings_tab(self):
        """Create settings tab content"""
        # Settings controls
        controls = []
        
        # Download path
        controls.append(
            ft.ListTile(
                title=ft.Text("Download Location"),
                subtitle=ft.Text(str(settings.download_path)),
                trailing=ft.IconButton(
                    icon=ft.Icons.EDIT,
                    on_click=self.on_change_download_path
                )
            )
        )
        
        # Default quality
        default_quality_dropdown = ft.Dropdown(
            value=settings.default_quality,
            options=[ft.dropdown.Option(k, v['label']) for k, v in AUDIO_QUALITIES.items()],
            width=180,
        )
        default_quality_dropdown.on_select = self.on_default_quality_change
        controls.append(
            ft.ListTile(
                title=ft.Text("Default Quality"),
                trailing=default_quality_dropdown
            )
        )
        
        # Concurrent downloads
        controls.append(
            ft.ListTile(
                title=ft.Text("Max Concurrent Downloads"),
                trailing=ft.Slider(
                    value=settings.max_concurrent_downloads,
                    min=1,
                    max=5,
                    divisions=4,
                    label="{value}",
                    width=200,
                    on_change=self.on_concurrent_change
                )
            )
        )
        
        # Theme
        theme_dropdown = ft.Dropdown(
            value=settings.theme,
            options=[
                ft.dropdown.Option("dark", "Dark"),
                ft.dropdown.Option("light", "Light"),
                ft.dropdown.Option("auto", "Auto")
            ],
            width=150,
        )
        theme_dropdown.on_select = self.on_theme_change
        controls.append(
            ft.ListTile(
                title=ft.Text("Theme"),
                trailing=theme_dropdown
            )
        )
        
        # Toggles
        toggles = [
            ("Data Saver Mode (WiFi only)", "data_saver_mode"),
            ("Embed Thumbnails", "embed_thumbnail"),
            ("Add Metadata", "add_metadata"),
            ("Remove Sponsors/Intros/Outros", "remove_sponsors"),
            ("Download Subtitles/Lyrics", "download_subtitles")
        ]
        
        for label, key in toggles:
            controls.append(
                ft.ListTile(
                    title=ft.Text(label),
                    trailing=ft.Switch(
                        value=settings.get(key, True),
                        on_change=lambda e, k=key: self.on_toggle_change(e, k)
                    )
                )
            )
        
        # Filename template
        controls.append(
            ft.ListTile(
                title=ft.Text("Filename Template"),
                subtitle=ft.Text(
                    "Available: {artist}, {title}, {quality}, {upload_date}, {id}",
                    size=12
                )
            )
        )
        
        template_field = ft.TextField(
            value=settings.get('filename_template', '{artist} - {title} [{quality}]'),
            on_change=self.on_template_change
        )
        
        controls.append(ft.Container(content=template_field, padding=ft.padding.symmetric(horizontal=16)))
        
        # Reset button
        controls.append(
            ft.Container(
                content=ft.ElevatedButton(
                    "Reset All Settings",
                    icon=ft.Icons.RESTORE,
                    color=ft.Colors.RED,
                    on_click=self.on_reset_settings
                ),
                padding=ft.padding.all(16),
                alignment=ft.Alignment.CENTER
            )
        )
        
        return ft.ListView(
            controls=controls,
            expand=True,
            spacing=4
        )
    
    def setup_event_handlers(self):
        """Setup event handlers"""
        queue_manager.add_callback(self.on_queue_update)
    
    async def initialize(self):
        """Initialize async components"""
        # Check internet
        has_internet = await check_internet_connection()
        if not has_internet:
            self.show_snackbar("No internet connection detected", ft.Colors.RED)
        
        # Initialize searcher
        self.searcher = YouTubeSearcher()
        
        # Start download worker
        await worker.start()
        
        # Load history
        self.refresh_history()
        
        # Start periodic updates
        asyncio.create_task(self.periodic_update())
    
    async def periodic_update(self):
        """Periodic UI update"""
        while True:
            try:
                await asyncio.sleep(1)
                self.update_global_progress()
                self.refresh_queue()
            except Exception as e:
                print(f"Periodic update error: {e}")
    
    def open_dialog(self, dialog):
        """Open a dialog properly"""
        dialog.open = True
        self.page.update()
    
    def close_dialog(self, dialog):
        """Close a dialog properly"""
        dialog.open = False
        self.page.update()
    
    def update_global_progress(self):
        """Update global progress bar"""
        progress, completed, failed = queue_manager.get_global_progress()
        self.global_progress_bar.value = progress / 100
        
        pending = queue_manager.get_pending_count()
        active = queue_manager.get_active_downloads()
        
        if active > 0:
            self.global_status_text.value = f"Downloading... {active} active, {pending} pending"
        elif pending > 0:
            self.global_status_text.value = f"{pending} items in queue"
        elif completed > 0:
            self.global_status_text.value = f"Completed: {completed}"
        else:
            self.global_status_text.value = "Ready"
        
        self.page.update()
    
    def on_tab_change(self, e):
        """Handle tab change"""
        selected_index = e.control.selected_index
        self.tab_content.content = self.tab_contents[selected_index]
        self.page.update()
    
    def switch_to_tab(self, index):
        """Switch to a specific tab"""
        if 0 <= index < len(self.tab_contents):
            self.nav_bar.selected_index = index
            self.tab_content.content = self.tab_contents[index]
            self.page.update()
    
    # Search handlers
    async def on_search_submit(self, e):
        """Handle search field submission"""
        await self.perform_search()
    
    async def on_search_click(self, e):
        """Handle search button click"""
        await self.perform_search()
    
    async def perform_search(self):
        """Perform search"""
        query = self.search_field.value.strip()
        if not query:
            return
        
        # Check if it's a URL
        if get_video_id(query):
            # Single video URL - get info and add
            await self.add_video_by_url(query)
            return
        
        # Show loading
        self.search_button.disabled = True
        self.results_list.controls = [
            ft.Container(
                content=ft.ProgressRing(),
                alignment=ft.Alignment.CENTER,
                expand=True
            )
        ]
        self.page.update()
        
        try:
            async with self.searcher:
                results = await self.searcher.search(
                    query=query,
                    max_results=25,
                    order=settings.get('search_sort', 'relevance'),
                    video_duration=settings.get('search_duration_filter', ''),
                    video_type=settings.get('search_type_filter', ''),
                    add_audio_keyword=settings.get('auto_add_audio_keyword', True)
                )
                
                self.current_results = results
                self.display_search_results(results)
                
        except Exception as e:
            self.show_snackbar(f"Search error: {str(e)}", ft.Colors.RED)
            self.results_list.controls = []
        
        finally:
            self.search_button.disabled = False
            self.page.update()
    
    def display_search_results(self, results: list):
        """Display search results"""
        self.results_list.controls = []
        
        if not results:
            self.results_list.controls.append(
                ft.Container(
                    content=ft.Text("No results found", color=ft.Colors.GREY_500),
                    alignment=ft.Alignment.CENTER,
                    expand=True
                )
            )
        else:
            for video in results:
                card = SearchResultCard(
                    video_data=video,
                    on_add_to_queue=self.on_add_to_queue,
                    default_quality=settings.default_quality
                )
                self.results_list.controls.append(card)
        
        self.page.update()
    
    async def add_video_by_url(self, url: str):
        """Add video by URL"""
        video_id = get_video_id(url)
        if not video_id:
            self.show_snackbar("Invalid YouTube URL", ft.Colors.RED)
            return
        
        async with self.searcher:
            video_info = await self.searcher.get_video_info(video_id)
            if video_info:
                self.on_add_to_queue(video_info, settings.default_quality)
                self.show_snackbar(f"Added: {video_info['title']}", ft.Colors.GREEN)
            else:
                self.show_snackbar("Could not fetch video info", ft.Colors.RED)
    
    def on_add_to_queue(self, video_data: dict, quality: str):
        """Add video to download queue"""
        item = QueueItem(
            video_id=video_data.get('id', ''),
            title=video_data.get('title', ''),
            channel=video_data.get('channel', ''),
            url=video_data.get('url', ''),
            thumbnail=video_data.get('thumbnail', ''),
            quality=quality,
            is_short=video_data.get('is_short', False)
        )
        
        queue_manager.add_item(item)
        self.show_snackbar(f"Added to queue: {video_data.get('title', '')}", ft.Colors.GREEN)
        
        # Switch to queue tab
        self.switch_to_tab(1)
    
    def on_add_playlist_click(self, e):
        """Handle add playlist button click"""
        def on_confirm(url, quality):
            self.close_dialog(dialog)
            asyncio.create_task(self.add_playlist(url, quality))
        
        def on_cancel():
            self.close_dialog(dialog)
        
        dialog = PlaylistInputDialog(on_confirm, on_cancel)
        self.open_dialog(dialog)
    
    async def add_playlist(self, url: str, quality: str):
        """Add playlist to queue"""
        playlist_id = extract_playlist_id(url)
        if not playlist_id:
            self.show_snackbar("Invalid playlist URL", ft.Colors.RED)
            return
        
        self.show_snackbar("Fetching playlist...", ft.Colors.BLUE)
        
        try:
            async with self.searcher:
                videos = await self.searcher.get_playlist_videos(playlist_id)
                
                if not videos:
                    self.show_snackbar("No videos found in playlist", ft.Colors.RED)
                    return
                
                items = []
                for video in videos:
                    item = QueueItem(
                        video_id=video.get('id', ''),
                        title=video.get('title', ''),
                        channel=video.get('channel', ''),
                        url=video.get('url', ''),
                        thumbnail=video.get('thumbnail', ''),
                        quality=quality,
                        is_short=video.get('is_short', False)
                    )
                    items.append(item)
                
                queue_manager.add_items(items)
                self.show_snackbar(f"Added {len(items)} videos from playlist", ft.Colors.GREEN)
                
                # Switch to queue tab
                self.switch_to_tab(1)
                
        except Exception as e:
            self.show_snackbar(f"Error: {str(e)}", ft.Colors.RED)
    
    def on_download_all_click(self, e):
        """Add all search results to queue"""
        if not self.current_results:
            return
        
        count = 0
        for video in self.current_results:
            self.on_add_to_queue(video, settings.default_quality)
            count += 1
        
        self.show_snackbar(f"Added {count} items to queue", ft.Colors.GREEN)
    
    # Queue handlers
    def on_queue_update(self):
        """Called when queue changes"""
        self.refresh_queue()
    
    def refresh_queue(self):
        """Refresh queue list display"""
        self.queue_list.controls = []
        
        items = queue_manager.get_queue()
        
        if not items:
            self.queue_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.QUEUE_MUSIC, size=64, color=ft.Colors.GREY_700),
                            ft.Text("Queue is empty", color=ft.Colors.GREY_500)
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    alignment=ft.Alignment.CENTER,
                    expand=True
                )
            )
        else:
            for item in items:
                card = QueueItemCard(
                    item=item,
                    on_cancel=self.on_cancel_download,
                    on_retry=self.on_retry_download,
                    on_remove=self.on_remove_from_queue
                )
                self.queue_list.controls.append(card)
        
        self.page.update()
    
    def on_cancel_download(self, item_id: str):
        """Cancel a download"""
        queue_manager.cancel_download(item_id)
        self.show_snackbar("Download cancelled", ft.Colors.ORANGE)
    
    def on_retry_download(self, item_id: str):
        """Retry a failed download"""
        queue_manager.retry_item(item_id)
        self.show_snackbar("Retrying download...", ft.Colors.BLUE)
    
    def on_remove_from_queue(self, item_id: str):
        """Remove item from queue"""
        queue_manager.remove_item(item_id)
        self.refresh_queue()
    
    def on_clear_completed_click(self, e):
        """Clear completed downloads"""
        queue_manager.clear_completed()
        self.refresh_queue()
    
    def on_retry_all_click(self, e):
        """Retry all failed downloads"""
        count = queue_manager.retry_all_failed()
        self.show_snackbar(f"Retrying {count} downloads", ft.Colors.BLUE)
    
    def on_cancel_all_click(self, e):
        """Cancel all downloads"""
        queue_manager.cancel_all()
        self.show_snackbar("All downloads cancelled", ft.Colors.ORANGE)
    
    def on_export_queue_click(self, e):
        """Export queue to file"""
        def on_export(filename):
            if queue_manager.export_queue(filename):
                self.show_snackbar(f"Queue exported to {filename}", ft.Colors.GREEN)
            else:
                self.show_snackbar("Failed to export queue", ft.Colors.RED)
            self.close_dialog(dialog)
        
        def on_cancel():
            self.close_dialog(dialog)
        
        dialog = ExportQueueDialog(on_export, on_cancel)
        self.open_dialog(dialog)
    
    def on_import_queue_click(self, e):
        """Import queue from file"""
        files = settings.list_exported_queues()
        
        if not files:
            self.show_snackbar("No saved queues found", ft.Colors.ORANGE)
            return
        
        def on_import(filename):
            count = queue_manager.import_queue(filename)
            if count > 0:
                self.show_snackbar(f"Imported {count} items", ft.Colors.GREEN)
                self.refresh_queue()
            else:
                self.show_snackbar("Failed to import queue", ft.Colors.RED)
            self.close_dialog(dialog)
        
        def on_cancel():
            self.close_dialog(dialog)
        
        dialog = ImportQueueDialog(files, on_import, on_cancel)
        self.open_dialog(dialog)
    
    # History handlers
    def refresh_history(self):
        """Refresh history list"""
        self.history_list.controls = []
        
        history = settings.get_history(100)
        
        if not history:
            self.history_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.HISTORY, size=64, color=ft.Colors.GREY_700),
                            ft.Text("No download history", color=ft.Colors.GREY_500)
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    alignment=ft.Alignment.CENTER,
                    expand=True
                )
            )
        else:
            for item in history:
                card = HistoryItemCard(
                    item=item,
                    on_play=self.on_play_history_item,
                    on_delete=self.on_delete_history_item
                )
                self.history_list.controls.append(card)
        
        self.page.update()
    
    def on_play_history_item(self, item: dict):
        """Play history item - audio playback not available in this version"""
        file_path = item.get('file_path')
        if file_path and Path(file_path).exists():
            self.show_snackbar(f"File location: {file_path}", ft.Colors.GREEN)
        else:
            self.show_snackbar("File not found", ft.Colors.RED)
    
    def on_delete_history_item(self, item: dict):
        """Delete history item"""
        # Remove from history list
        settings.history = [h for h in settings.history if h != item]
        settings.save_history()
        self.refresh_history()
    
    def on_clear_history_click(self, e):
        """Clear all history"""
        settings.clear_history()
        self.refresh_history()
        self.show_snackbar("History cleared", ft.Colors.GREEN)
    
    # Settings handlers
    def on_settings_click(self, e):
        """Open settings dialog"""
        def on_save(new_settings):
            settings.update(new_settings)
            self.apply_theme()
            self.close_dialog(dialog)
            self.show_snackbar("Settings saved", ft.Colors.GREEN)
        
        def on_close():
            self.close_dialog(dialog)
        
        dialog = SettingsDialog(on_save, on_close)
        self.open_dialog(dialog)
    
    def on_change_download_path(self, e):
        """Change download path"""
        # Would need platform-specific file picker
        self.show_snackbar("Feature not available on this platform", ft.Colors.ORANGE)
    
    def on_default_quality_change(self, e):
        """Change default quality"""
        settings.default_quality = e.control.value
    
    def on_concurrent_change(self, e):
        """Change concurrent downloads"""
        settings.max_concurrent_downloads = int(e.control.value)
    
    def on_theme_change(self, e):
        """Change theme"""
        settings.theme = e.control.value
        self.apply_theme()
    
    def on_toggle_change(self, e, key: str):
        """Handle toggle changes"""
        settings.set(key, e.control.value)
    
    def on_template_change(self, e):
        """Change filename template"""
        settings.set('filename_template', e.control.value)
    
    def on_reset_settings(self, e):
        """Reset settings to defaults"""
        settings.reset_to_defaults()
        self.apply_theme()
        self.show_snackbar("Settings reset to defaults", ft.Colors.GREEN)
    
    def apply_theme(self):
        """Apply current theme"""
        self.page.theme_mode = ft.ThemeMode.DARK if settings.theme == "dark" else ft.ThemeMode.LIGHT
        # Support 'auto' and unknown values by falling back to 'dark'
        theme_key = settings.theme if settings.theme in UI_CONFIG['theme_colors'] else 'dark'
        theme = UI_CONFIG['theme_colors'][theme_key]
        self.page.bgcolor = theme['bg']
        self.page.update()
    
    async def on_update_ytdlp_click(self, e):
        """Update yt-dlp"""
        self.show_snackbar("Updating yt-dlp...", ft.Colors.BLUE)
        
        success, message = update_ytdlp()
        
        if success:
            self.show_snackbar(message, ft.Colors.GREEN)
        else:
            self.show_snackbar(message, ft.Colors.RED)
    
    def on_sort_change(self, e):
        """Handle sort change"""
        settings.set('search_sort', e.control.value)
    
    def on_duration_filter_change(self, e):
        """Handle duration filter change"""
        settings.set('search_duration_filter', e.control.value)
    
    def on_type_filter_change(self, e):
        """Handle type filter change"""
        settings.set('search_type_filter', e.control.value)
    
    def show_snackbar(self, message: str, color: str = ft.Colors.GREEN):
        """Show snackbar message"""
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=color, duration=3000)
        # Support multiple Flet versions: prefer `show_snack_bar`, fallback
        # to assigning `page.snack_bar` and updating the page.
        try:
            if hasattr(self.page, 'show_snack_bar'):
                self.page.show_snack_bar(snack)
            else:
                self.page.snack_bar = snack
                self.page.update()
        except Exception:
            print(message)


def main(page: Page):
    """Main entry point"""
    YouTubeMusicDownloader(page)


if __name__ == "__main__":
    # Start the Flet app on an available port and bind to 0.0.0.0 by default
    # so the server is reachable from the host. If the chosen port is in use,
    # pick another free port and retry.
    import socket, os

    def _get_free_port(host: str = "0.0.0.0") -> int:
        family = socket.AF_INET6 if socket.has_ipv6 else socket.AF_INET
        s = socket.socket(family, socket.SOCK_STREAM)
        try:
            # bind to port 0 to let OS select an available port on the requested host
            if family == socket.AF_INET6:
                bind_addr = ('::', 0) if host in (None, '0.0.0.0') else (host, 0)
            else:
                bind_addr = (host if host else '127.0.0.1', 0)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(bind_addr)
            return s.getsockname()[1]
        finally:
            s.close()

    host = os.environ.get('FLET_SERVER_HOST', '0.0.0.0')

    # Ensure FLET_SERVER_PORT is set to a free port if not already provided
    if not os.environ.get('FLET_SERVER_PORT'):
        free_port = _get_free_port(host=host)
        os.environ['FLET_SERVER_PORT'] = str(free_port)

    chosen_port = int(os.environ.get('FLET_SERVER_PORT', '0'))
    print(f"Starting Flet on {host}:{chosen_port}")
    try:
        ft.run(main, view=ft.AppView.FLET_APP, host=host, port=chosen_port)
    except OSError as e:
        print(f"Port {chosen_port} bind failed: {e}. Picking a new free port.")
        free_port = _get_free_port(host=host)
        os.environ['FLET_SERVER_PORT'] = str(free_port)
        print(f"Retrying on {host}:{free_port}")
        ft.run(main, view=ft.AppView.FLET_APP, host=host, port=free_port)
