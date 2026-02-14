/**
 * YouTube Music Downloader - Frontend JavaScript
 * Handles all UI interactions, API calls, and WebSocket updates
 */

// Global state
let currentSearchResults = [];
let socket = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeSocket();
    loadSettings();
    loadQueue();
    loadHistory();
    loadFiles();
    setupEventListeners();
});

// WebSocket Setup
function initializeSocket() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server');
        showToast('Connected to server', 'success');
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        showToast('Disconnected from server', 'warning');
    });
    
    socket.on('queue_update', function(data) {
        updateQueueDisplay(data.items);
    });
    
    socket.on('progress_update', function(data) {
        updateGlobalProgress(data);
    });
}

// Event Listeners
function setupEventListeners() {
    // Search input enter key
    document.getElementById('searchInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    
    // Max concurrent slider
    document.getElementById('maxConcurrent').addEventListener('input', function(e) {
        document.getElementById('maxConcurrentValue').textContent = e.target.value;
    });
}

// Search Functions
async function performSearch() {
    const query = document.getElementById('searchInput').value.trim();
    if (!query) {
        showToast('Please enter a search query', 'warning');
        return;
    }
    
    const sort = document.getElementById('sortSelect').value;
    const duration = document.getElementById('durationSelect').value;
    
    // Show loading
    document.getElementById('searchResults').innerHTML = `
        <div class="col-12 text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Searching...</p>
        </div>
    `;
    
    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                order: sort,
                video_duration: duration
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            showToast(data.error, 'danger');
            document.getElementById('searchResults').innerHTML = `
                <div class="col-12 text-center text-secondary py-5">
                    <i class="bi bi-exclamation-circle" style="font-size: 48px;"></i>
                    <p class="mt-3">${data.error}</p>
                </div>
            `;
            return;
        }
        
        currentSearchResults = data.results || [];
        displaySearchResults(currentSearchResults);
        
        // Show download all button if results exist
        if (currentSearchResults.length > 0) {
            document.getElementById('downloadAllBtn').style.display = 'inline-block';
            document.getElementById('resultsCount').textContent = `${currentSearchResults.length} results`;
        } else {
            document.getElementById('downloadAllBtn').style.display = 'none';
            document.getElementById('resultsCount').textContent = 'No results found';
        }
        
    } catch (error) {
        console.error('Search error:', error);
        showToast('Search failed: ' + error.message, 'danger');
    }
}

function displaySearchResults(results) {
    const container = document.getElementById('searchResults');
    
    if (!results || results.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center text-secondary py-5">
                <i class="bi bi-search" style="font-size: 48px;"></i>
                <p class="mt-3">No results found</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = results.map(video => `
        <div class="col-md-6 col-lg-4">
            <div class="card search-result-card h-100">
                <div class="position-relative">
                    <img src="${video.thumbnail}" class="card-img-top" alt="${video.title}" style="height: 180px; object-fit: cover;">
                    ${video.is_short ? '<span class="playlist-badge">SHORT</span>' : ''}
                    <span class="playlist-badge" style="left: 5px; right: auto; bottom: 5px; top: auto;">${video.duration}</span>
                </div>
                <div class="card-body">
                    <h6 class="card-title text-truncate" title="${video.title}">${video.title}</h6>
                    <p class="card-text text-secondary small">${video.channel}</p>
                    <p class="card-text text-secondary small">${video.views_formatted}</p>
                    <div class="d-flex justify-content-between align-items-center mt-3">
                        <select class="form-select form-select-sm w-auto" id="quality-${video.id}">
                            <option value="best_opus">Opus (~160kbps)</option>
                            <option value="mp3_320">MP3 320kbps</option>
                            <option value="flac">FLAC Lossless</option>
                            <option value="aac_256">AAC 256kbps</option>
                        </select>
                        <button class="btn btn-success btn-sm" onclick="addToQueue('${video.id}')">
                            <i class="bi bi-plus"></i> Add
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

// Queue Functions
async function addToQueue(videoId) {
    const video = currentSearchResults.find(v => v.id === videoId);
    if (!video) return;
    
    const quality = document.getElementById(`quality-${videoId}`).value;
    
    try {
        const response = await fetch('/api/queue/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                video_id: video.id,
                title: video.title,
                channel: video.channel,
                url: video.url,
                thumbnail: video.thumbnail,
                quality: quality,
                is_short: video.is_short
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`Added to queue: ${video.title}`, 'success');
            // Switch to queue tab
            document.getElementById('queue-tab').click();
        } else {
            showToast(data.error || 'Failed to add to queue', 'danger');
        }
    } catch (error) {
        showToast('Error adding to queue: ' + error.message, 'danger');
    }
}

async function downloadAllResults() {
    if (currentSearchResults.length === 0) return;
    
    const quality = document.getElementById('defaultQuality').value;
    
    try {
        const response = await fetch('/api/queue/add-batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                videos: currentSearchResults,
                quality: quality
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`Added ${data.count} items to queue`, 'success');
            document.getElementById('queue-tab').click();
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'danger');
    }
}

async function loadQueue() {
    try {
        const response = await fetch('/api/queue');
        const data = await response.json();
        updateQueueDisplay(data.items);
    } catch (error) {
        console.error('Error loading queue:', error);
    }
}

function updateQueueDisplay(items) {
    const container = document.getElementById('queueList');
    document.getElementById('queueCount').textContent = items.length;
    
    if (!items || items.length === 0) {
        container.innerHTML = `
            <div class="text-center text-secondary py-5">
                <i class="bi bi-list-task" style="font-size: 48px;"></i>
                <p class="mt-3">Queue is empty</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = items.map(item => `
        <div class="queue-item">
            <div class="row align-items-center">
                <div class="col-auto">
                    <img src="${item.thumbnail || ''}" class="thumbnail" alt="">
                </div>
                <div class="col">
                    <h6 class="mb-1 text-truncate">${item.title}</h6>
                    <p class="mb-0 text-secondary small">${item.channel}</p>
                    <p class="mb-0 text-secondary small">Quality: ${item.quality}</p>
                </div>
                <div class="col-md-3">
                    <div class="progress" style="height: 6px;">
                        <div class="progress-bar" style="width: ${item.progress || 0}%"></div>
                    </div>
                    <div class="d-flex justify-content-between mt-1">
                        <small class="status-${item.status}">${item.status.toUpperCase()}</small>
                        <small>${(item.progress || 0).toFixed(1)}%</small>
                    </div>
                    ${item.speed ? `<small class="text-secondary">${item.speed} ${item.eta}</small>` : ''}
                </div>
                <div class="col-auto">
                    ${getQueueActions(item)}
                </div>
            </div>
        </div>
    `).join('');
}

function getQueueActions(item) {
    if (item.status === 'downloading' || item.status === 'processing') {
        return `
            <button class="btn btn-outline-danger btn-sm action-btn" onclick="cancelDownload('${item.id}')">
                <i class="bi bi-x"></i>
            </button>
        `;
    } else if (item.status === 'error') {
        return `
            <button class="btn btn-outline-warning btn-sm action-btn" onclick="retryDownload('${item.id}')">
                <i class="bi bi-arrow-clockwise"></i>
            </button>
            <button class="btn btn-outline-danger btn-sm action-btn" onclick="removeFromQueue('${item.id}')">
                <i class="bi bi-trash"></i>
            </button>
        `;
    } else if (item.status === 'done') {
        return `
            <button class="btn btn-outline-success btn-sm action-btn" disabled>
                <i class="bi bi-check"></i>
            </button>
            <button class="btn btn-outline-danger btn-sm action-btn" onclick="removeFromQueue('${item.id}')">
                <i class="bi bi-trash"></i>
            </button>
        `;
    } else {
        return `
            <button class="btn btn-outline-danger btn-sm action-btn" onclick="removeFromQueue('${item.id}')">
                <i class="bi bi-trash"></i>
            </button>
        `;
    }
}

async function cancelDownload(itemId) {
    try {
        await fetch(`/api/queue/cancel/${itemId}`, { method: 'POST' });
        showToast('Download cancelled', 'info');
    } catch (error) {
        showToast('Error: ' + error.message, 'danger');
    }
}

async function retryDownload(itemId) {
    try {
        await fetch(`/api/queue/retry/${itemId}`, { method: 'POST' });
        showToast('Retrying download', 'info');
    } catch (error) {
        showToast('Error: ' + error.message, 'danger');
    }
}

async function removeFromQueue(itemId) {
    try {
        await fetch(`/api/queue/remove/${itemId}`, { method: 'POST' });
        showToast('Removed from queue', 'info');
    } catch (error) {
        showToast('Error: ' + error.message, 'danger');
    }
}

async function clearCompleted() {
    try {
        await fetch('/api/queue/clear-completed', { method: 'POST' });
        showToast('Completed downloads cleared', 'info');
    } catch (error) {
        showToast('Error: ' + error.message, 'danger');
    }
}

async function retryAll() {
    try {
        const response = await fetch('/api/queue/retry-all', { method: 'POST' });
        const data = await response.json();
        showToast(`Retrying ${data.count} downloads`, 'info');
    } catch (error) {
        showToast('Error: ' + error.message, 'danger');
    }
}

async function cancelAll() {
    try {
        await fetch('/api/queue/cancel-all', { method: 'POST' });
        showToast('All downloads cancelled', 'info');
    } catch (error) {
        showToast('Error: ' + error.message, 'danger');
    }
}

// Global Progress
function updateGlobalProgress(data) {
    const progressBar = document.getElementById('globalProgressBar');
    const status = document.getElementById('globalStatus');
    
    progressBar.style.width = data.progress + '%';
    
    if (data.active > 0) {
        status.textContent = `Downloading... ${data.active} active, ${data.pending} pending`;
    } else if (data.pending > 0) {
        status.textContent = `${data.pending} items in queue`;
    } else if (data.completed > 0) {
        status.textContent = `Completed: ${data.completed}`;
    } else {
        status.textContent = 'Ready';
    }
}

// History Functions
async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        displayHistory(data.history);
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

function displayHistory(history) {
    const container = document.getElementById('historyList');
    
    if (!history || history.length === 0) {
        container.innerHTML = `
            <div class="text-center text-secondary py-5">
                <i class="bi bi-clock-history" style="font-size: 48px;"></i>
                <p class="mt-3">No download history</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = history.map(item => `
        <div class="card mb-2">
            <div class="card-body py-2">
                <div class="row align-items-center">
                    <div class="col">
                        <h6 class="mb-1 text-truncate">${item.title}</h6>
                        <p class="mb-0 text-secondary small">${item.channel} • ${item.quality} • ${item.file_size || 'Unknown size'}</p>
                    </div>
                    <div class="col-auto">
                        ${item.file_path ? `
                            <a href="/api/download/${encodeURIComponent(item.file_path.split('/').pop())}" 
                               class="btn btn-outline-success btn-sm" download>
                                <i class="bi bi-download"></i>
                            </a>
                        ` : ''}
                        <button class="btn btn-outline-danger btn-sm" onclick="deleteHistoryItem(${JSON.stringify(item).replace(/"/g, '&quot;')})">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

async function clearHistory() {
    try {
        await fetch('/api/history/clear', { method: 'POST' });
        showToast('History cleared', 'info');
        loadHistory();
    } catch (error) {
        showToast('Error: ' + error.message, 'danger');
    }
}

async function deleteHistoryItem(item) {
    try {
        await fetch('/api/history/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item: item })
        });
        loadHistory();
    } catch (error) {
        showToast('Error: ' + error.message, 'danger');
    }
}

// Files Functions
async function loadFiles() {
    try {
        const response = await fetch('/api/downloaded-files');
        const data = await response.json();
        displayFiles(data.files);
    } catch (error) {
        console.error('Error loading files:', error);
    }
}

function displayFiles(files) {
    const container = document.getElementById('filesList');
    
    if (!files || files.length === 0) {
        container.innerHTML = `
            <div class="text-center text-secondary py-5">
                <i class="bi bi-folder" style="font-size: 48px;"></i>
                <p class="mt-3">No downloaded files</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = `
        <div class="table-responsive">
            <table class="table table-dark table-hover">
                <thead>
                    <tr>
                        <th>Filename</th>
                        <th>Size</th>
                        <th>Downloaded</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${files.map(file => `
                        <tr>
                            <td class="text-truncate" style="max-width: 300px;">${file.name}</td>
                            <td>${file.size}</td>
                            <td>${new Date(file.modified * 1000).toLocaleDateString()}</td>
                            <td>
                                <a href="/api/download/${encodeURIComponent(file.name)}" 
                                   class="btn btn-outline-success btn-sm" download>
                                    <i class="bi bi-download"></i>
                                </a>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// Playlist Functions
function showPlaylistModal() {
    const modal = new bootstrap.Modal(document.getElementById('playlistModal'));
    modal.show();
}

async function addPlaylist() {
    const url = document.getElementById('playlistUrl').value.trim();
    const quality = document.getElementById('playlistQuality').value;
    
    if (!url) {
        showToast('Please enter a playlist URL', 'warning');
        return;
    }
    
    document.getElementById('playlistLoading').style.display = 'block';
    
    try {
        // Get playlist videos
        const response = await fetch('/api/playlist', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });
        
        const data = await response.json();
        
        if (data.error) {
            showToast(data.error, 'danger');
            document.getElementById('playlistLoading').style.display = 'none';
            return;
        }
        
        // Add all videos to queue
        const batchResponse = await fetch('/api/queue/add-batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                videos: data.videos,
                quality: quality
            })
        });
        
        const batchData = await batchResponse.json();
        
        if (batchData.success) {
            showToast(`Added ${batchData.count} videos from playlist`, 'success');
            bootstrap.Modal.getInstance(document.getElementById('playlistModal')).hide();
            document.getElementById('queue-tab').click();
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'danger');
    } finally {
        document.getElementById('playlistLoading').style.display = 'none';
    }
}

// Export/Import Functions
async function exportQueue() {
    document.getElementById('queueActionTitle').textContent = 'Export Queue';
    document.getElementById('exportSection').style.display = 'block';
    document.getElementById('importSection').style.display = 'none';
    document.getElementById('queueActionBtn').textContent = 'Export';
    document.getElementById('queueActionBtn').onclick = performExport;
    
    const modal = new bootstrap.Modal(document.getElementById('queueActionModal'));
    modal.show();
}

async function showImportModal() {
    document.getElementById('queueActionTitle').textContent = 'Import Queue';
    document.getElementById('exportSection').style.display = 'none';
    document.getElementById('importSection').style.display = 'block';
    document.getElementById('queueActionBtn').textContent = 'Import';
    document.getElementById('queueActionBtn').onclick = performImport;
    
    // Load exported files
    try {
        const response = await fetch('/api/queue/exported-files');
        const data = await response.json();
        
        const select = document.getElementById('importFileSelect');
        select.innerHTML = '<option value="">Select a file...</option>' +
            data.files.map(f => `<option value="${f.name}">${f.name}</option>`).join('');
    } catch (error) {
        console.error('Error loading exported files:', error);
    }
    
    const modal = new bootstrap.Modal(document.getElementById('queueActionModal'));
    modal.show();
}

async function performExport() {
    const filename = document.getElementById('exportFilename').value.trim() || 'queue';
    
    try {
        const response = await fetch('/api/queue/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: filename })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Queue exported successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('queueActionModal')).hide();
        } else {
            showToast(data.error || 'Export failed', 'danger');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'danger');
    }
}

async function performImport() {
    const filename = document.getElementById('importFileSelect').value;
    
    if (!filename) {
        showToast('Please select a file', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/queue/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: filename })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`Imported ${data.count} items`, 'success');
            bootstrap.Modal.getInstance(document.getElementById('queueActionModal')).hide();
        } else {
            showToast(data.error || 'Import failed', 'danger');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'danger');
    }
}

// Settings Functions
async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        const data = await response.json();
        
        document.getElementById('downloadPath').value = data.download_path;
        document.getElementById('defaultQuality').value = data.default_quality;
        document.getElementById('maxConcurrent').value = data.max_concurrent_downloads;
        document.getElementById('maxConcurrentValue').textContent = data.max_concurrent_downloads;
        document.getElementById('themeSelect').value = data.theme;
        document.getElementById('embedThumbnail').checked = data.embed_thumbnail !== false;
        document.getElementById('addMetadata').checked = data.add_metadata !== false;
        document.getElementById('removeSponsors').checked = data.remove_sponsors !== false;
        document.getElementById('downloadSubtitles').checked = data.download_subtitles !== false;
        document.getElementById('filenameTemplate').value = data.filename_template || '{artist} - {title} [{quality}]';
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

async function saveSettings() {
    const settings = {
        download_path: document.getElementById('downloadPath').value,
        default_quality: document.getElementById('defaultQuality').value,
        max_concurrent_downloads: parseInt(document.getElementById('maxConcurrent').value),
        theme: document.getElementById('themeSelect').value,
        embed_thumbnail: document.getElementById('embedThumbnail').checked,
        add_metadata: document.getElementById('addMetadata').checked,
        remove_sponsors: document.getElementById('removeSponsors').checked,
        download_subtitles: document.getElementById('downloadSubtitles').checked,
        filename_template: document.getElementById('filenameTemplate').value
    };
    
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Settings saved', 'success');
            bootstrap.Modal.getInstance(document.getElementById('settingsModal')).hide();
        } else {
            showToast(data.error || 'Failed to save settings', 'danger');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'danger');
    }
}

async function resetSettings() {
    try {
        await fetch('/api/settings/reset', { method: 'POST' });
        showToast('Settings reset to defaults', 'info');
        loadSettings();
    } catch (error) {
        showToast('Error: ' + error.message, 'danger');
    }
}

async function changeDownloadPath() {
    const newPath = prompt('Enter new download path:', document.getElementById('downloadPath').value);
    if (newPath) {
        try {
            const response = await fetch('/api/download-path', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: newPath })
            });
            
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('downloadPath').value = newPath;
                showToast('Download path updated', 'success');
            } else {
                showToast(data.error || 'Failed to update path', 'danger');
            }
        } catch (error) {
            showToast('Error: ' + error.message, 'danger');
        }
    }
}

// Update yt-dlp
async function updateYtDlp() {
    try {
        showToast('Updating yt-dlp...', 'info');
        const response = await fetch('/api/update-ytdlp', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'danger');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'danger');
    }
}

// Utility Functions
function showToast(message, type = 'info') {
    const container = document.querySelector('.toast-container');
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'danger' ? 'danger' : type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'primary'}`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    container.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}
