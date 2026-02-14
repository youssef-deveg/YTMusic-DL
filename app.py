"""
YouTube Music Downloader - Flask Web Application
A complete web-based YouTube Music downloader with real-time updates
"""

import os
import sys
import json
import asyncio
import threading
from datetime import datetime
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, request, jsonify, send_file, Response
from flask_socketio import SocketIO, emit

# Import backend modules
from config import AUDIO_QUALITIES, DownloadStatus, UI_CONFIG
from settings import settings
from queue_manager import queue_manager, QueueItem
from downloader import AudioDownloader, update_ytdlp, worker
from search import YouTubeSearcher
from utils import (
    is_playlist_url, 
    extract_playlist_id, 
    get_video_id,
    format_duration,
    format_file_size
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global state
searcher = None
downloader = AudioDownloader()
worker_thread = None

# WebSocket event handlers for real-time updates
def notify_queue_update():
    """Notify all clients of queue update"""
    try:
        items = [item.to_dict() for item in queue_manager.get_queue()]
        socketio.emit('queue_update', {'items': items})
    except Exception as e:
        print(f"Queue update notification error: {e}")

def notify_progress_update():
    """Notify all clients of progress update"""
    try:
        progress, completed, failed = queue_manager.get_global_progress()
        active = queue_manager.get_active_downloads()
        pending = queue_manager.get_pending_count()
        
        socketio.emit('progress_update', {
            'progress': progress,
            'completed': completed,
            'failed': failed,
            'active': active,
            'pending': pending
        })
    except Exception as e:
        print(f"Progress update notification error: {e}")

# Register callbacks
queue_manager.add_callback(lambda: (notify_queue_update(), notify_progress_update()))

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    """Search YouTube Music"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Check if it's a URL
        video_id = get_video_id(query)
        
        async def do_search():
            async with YouTubeSearcher() as s:
                if video_id:
                    # Single video URL
                    video_info = await s.get_video_info(video_id)
                    return {'results': [video_info] if video_info else [], 'is_url': True}
                else:
                    # Search query
                    order = data.get('order', settings.get('search_sort', 'relevance'))
                    video_duration = data.get('video_duration', settings.get('search_duration_filter', ''))
                    video_type = data.get('video_type', settings.get('search_type_filter', ''))
                    
                    results = await s.search(
                        query=query,
                        max_results=25,
                        order=order,
                        video_duration=video_duration,
                        video_type=video_type,
                        add_audio_keyword=settings.get('auto_add_audio_keyword', True)
                    )
                    return {'results': results, 'is_url': False}
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(do_search())
        return jsonify(result)
            
    except Exception as e:
        print(f"Search error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/queue', methods=['GET'])
def get_queue():
    """Get download queue"""
    items = [item.to_dict() for item in queue_manager.get_queue()]
    return jsonify({'items': items})

@app.route('/api/queue/add', methods=['POST'])
def add_to_queue():
    """Add video to download queue"""
    try:
        data = request.get_json()
        
        item = QueueItem(
            video_id=data.get('video_id', ''),
            title=data.get('title', ''),
            channel=data.get('channel', ''),
            url=data.get('url', ''),
            thumbnail=data.get('thumbnail', ''),
            quality=data.get('quality', settings.default_quality),
            is_short=data.get('is_short', False)
        )
        
        queue_manager.add_item(item)
        
        # Start worker if not running
        start_worker()
        
        return jsonify({'success': True, 'item_id': item.id})
        
    except Exception as e:
        print(f"Add to queue error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/queue/add-batch', methods=['POST'])
def add_batch_to_queue():
    """Add multiple videos to queue"""
    try:
        data = request.get_json()
        videos = data.get('videos', [])
        quality = data.get('quality', settings.default_quality)
        
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
        
        # Start worker if not running
        start_worker()
        
        return jsonify({'success': True, 'count': len(items)})
        
    except Exception as e:
        print(f"Batch add error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/queue/cancel/<item_id>', methods=['POST'])
def cancel_download(item_id):
    """Cancel a download"""
    success = queue_manager.cancel_download(item_id)
    return jsonify({'success': success})

@app.route('/api/queue/retry/<item_id>', methods=['POST'])
def retry_download(item_id):
    """Retry a failed download"""
    success = queue_manager.retry_item(item_id)
    if success:
        start_worker()
    return jsonify({'success': success})

@app.route('/api/queue/remove/<item_id>', methods=['POST'])
def remove_from_queue(item_id):
    """Remove item from queue"""
    success = queue_manager.remove_item(item_id)
    return jsonify({'success': success})

@app.route('/api/queue/clear-completed', methods=['POST'])
def clear_completed():
    """Clear completed downloads from queue"""
    queue_manager.clear_completed()
    return jsonify({'success': True})

@app.route('/api/queue/cancel-all', methods=['POST'])
def cancel_all():
    """Cancel all downloads"""
    queue_manager.cancel_all()
    return jsonify({'success': True})

@app.route('/api/queue/retry-all', methods=['POST'])
def retry_all():
    """Retry all failed downloads"""
    count = queue_manager.retry_all_failed()
    if count > 0:
        start_worker()
    return jsonify({'success': True, 'count': count})

@app.route('/api/queue/export', methods=['POST'])
def export_queue():
    """Export queue to file"""
    try:
        data = request.get_json()
        filename = data.get('filename', 'queue')
        success = queue_manager.export_queue(filename)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/queue/import', methods=['POST'])
def import_queue():
    """Import queue from file"""
    try:
        data = request.get_json()
        filename = data.get('filename', '')
        count = queue_manager.import_queue(filename)
        if count > 0:
            start_worker()
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/queue/exported-files', methods=['GET'])
def get_exported_files():
    """Get list of exported queue files"""
    files = settings.list_exported_queues()
    return jsonify({'files': files})

@app.route('/api/playlist', methods=['POST'])
def get_playlist():
    """Get playlist videos"""
    try:
        data = request.get_json()
        url = data.get('url', '')
        
        playlist_id = extract_playlist_id(url)
        if not playlist_id:
            return jsonify({'error': 'Invalid playlist URL'}), 400
        
        async def get_playlist():
            async with YouTubeSearcher() as s:
                return await s.get_playlist_videos(playlist_id)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        videos = loop.run_until_complete(get_playlist())
        return jsonify({'videos': videos})
            
    except Exception as e:
        print(f"Playlist error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get download history"""
    limit = request.args.get('limit', 100, type=int)
    history = settings.get_history(limit)
    return jsonify({'history': history})

@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    """Clear download history"""
    settings.clear_history()
    return jsonify({'success': True})

@app.route('/api/history/delete', methods=['POST'])
def delete_history_item():
    """Delete history item"""
    try:
        data = request.get_json()
        item = data.get('item', {})
        settings.history = [h for h in settings.history if h != item]
        settings.save_history()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current settings"""
    return jsonify({
        'download_path': str(settings.download_path),
        'default_quality': settings.default_quality,
        'max_concurrent_downloads': settings.max_concurrent_downloads,
        'theme': settings.theme,
        'data_saver_mode': settings.data_saver_mode,
        'audio_qualities': AUDIO_QUALITIES
    })

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update settings"""
    try:
        data = request.get_json()
        settings.update(data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings/reset', methods=['POST'])
def reset_settings():
    """Reset settings to defaults"""
    settings.reset_to_defaults()
    return jsonify({'success': True})

@app.route('/api/download-path', methods=['POST'])
def change_download_path():
    """Change download path"""
    try:
        data = request.get_json()
        path = data.get('path', '')
        if path:
            settings.download_path = path
            return jsonify({'success': True})
        return jsonify({'error': 'Path is required'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-ytdlp', methods=['POST'])
def update_ytdlp_endpoint():
    """Update yt-dlp"""
    try:
        success, message = update_ytdlp()
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress', methods=['GET'])
def get_progress():
    """Get current progress"""
    progress, completed, failed = queue_manager.get_global_progress()
    active = queue_manager.get_active_downloads()
    pending = queue_manager.get_pending_count()
    
    return jsonify({
        'progress': progress,
        'completed': completed,
        'failed': failed,
        'active': active,
        'pending': pending
    })

@app.route('/api/download/<path:filename>')
def download_file(filename):
    """Download a file"""
    try:
        file_path = Path(settings.download_path) / filename
        if file_path.exists():
            return send_file(file_path, as_attachment=True)
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/downloaded-files')
def get_downloaded_files():
    """Get list of downloaded files"""
    try:
        download_dir = Path(settings.download_path)
        if not download_dir.exists():
            return jsonify({'files': []})
        
        files = []
        for f in download_dir.iterdir():
            if f.is_file():
                files.append({
                    'name': f.name,
                    'size': format_file_size(f.stat().st_size),
                    'modified': f.stat().st_mtime
                })
        
        files.sort(key=lambda x: x['modified'], reverse=True)
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stream/<item_id>')
def stream_audio(item_id):
    """Stream audio file"""
    try:
        item = queue_manager.get_item(item_id)
        if item and item.file_path and Path(item.file_path).exists():
            return send_file(item.file_path)
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def start_worker():
    """Start the download worker if not already running"""
    global worker_thread
    
    if worker_thread is None or not worker_thread.is_alive():
        def run_worker():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(worker.start())
        
        worker_thread = threading.Thread(target=run_worker, daemon=True)
        worker_thread.start()
        print("Download worker started")

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connected', {'data': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

if __name__ == '__main__':
    print("Starting YouTube Music Downloader (Flask version)...")
    print(f"Download path: {settings.download_path}")
    print(f"Access the app at: http://localhost:5000")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
