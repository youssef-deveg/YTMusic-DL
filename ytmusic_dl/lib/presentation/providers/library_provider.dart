import 'package:flutter/material.dart';
import '../../data/datasources/database_helper.dart';
import '../../data/datasources/media_scanner.dart';
import '../../data/models/media_item.dart';
import '../../data/models/playlist.dart';

enum LibraryTab { songs, albums, artists, playlists, videos }

class LibraryProvider extends ChangeNotifier {
  final DatabaseHelper _db = DatabaseHelper.instance;
  final MediaScanner _scanner = MediaScanner.instance;
  
  List<MediaItem> _allMedia = [];
  List<MediaItem> _songs = [];
  List<MediaItem> _videos = [];
  List<MediaItem> _favorites = [];
  List<MediaItem> _recentlyAdded = [];
  List<MediaItem> _mostPlayed = [];
  List<MediaItem> _recentlyPlayed = [];
  List<Playlist> _playlists = [];
  List<String> _artists = [];
  List<String> _albums = [];
  
  bool _isScanning = false;
  double _scanProgress = 0;
  String? _scanStatus;
  LibraryTab _currentTab = LibraryTab.songs;
  
  // Getters
  List<MediaItem> get allMedia => _allMedia;
  List<MediaItem> get songs => _songs;
  List<MediaItem> get videos => _videos;
  List<MediaItem> get favorites => _favorites;
  List<MediaItem> get recentlyAdded => _recentlyAdded;
  List<MediaItem> get mostPlayed => _mostPlayed;
  List<MediaItem> get recentlyPlayed => _recentlyPlayed;
  List<Playlist> get playlists => _playlists;
  List<String> get artists => _artists;
  List<String> get albums => _albums;
  bool get isScanning => _isScanning;
  double get scanProgress => _scanProgress;
  String? get scanStatus => _scanStatus;
  LibraryTab get currentTab => _currentTab;
  
  Future<void> initialize() async {
    await loadLibrary();
  }
  
  Future<void> loadLibrary() async {
    _allMedia = await _db.getAllMedia();
    _songs = _allMedia.where((m) => !isVideoFile(m.path)).toList();
    _videos = _allMedia.where((m) => isVideoFile(m.path)).toList();
    _favorites = await _db.getFavorites();
    _recentlyAdded = await _db.getRecentlyAdded();
    _mostPlayed = await _db.getMostPlayed();
    _recentlyPlayed = await _db.getRecentlyPlayed();
    _playlists = await _db.getAllPlaylists();
    _artists = await _db.getAllArtists();
    _albums = await _db.getAllAlbums();
    notifyListeners();
  }
  
  void setCurrentTab(LibraryTab tab) {
    _currentTab = tab;
    notifyListeners();
  }
  
  Future<bool> requestPermissions() async {
    return await _scanner.requestPermissions();
  }
  
  Future<void> scanMedia() async {
    if (_isScanning) return;
    
    _isScanning = true;
    _scanProgress = 0;
    _scanStatus = 'Requesting permissions...';
    notifyListeners();
    
    final hasPermission = await requestPermissions();
    if (!hasPermission) {
      _isScanning = false;
      _scanStatus = 'Permission denied';
      notifyListeners();
      return;
    }
    
    _scanStatus = 'Scanning for media files...';
    notifyListeners();
    
    final items = await _scanner.scanMediaFiles();
    final total = items.length;
    
    for (int i = 0; i < items.length; i++) {
      await _db.insertMedia(items[i]);
      _scanProgress = (i + 1) / total;
      _scanStatus = 'Scanning: ${i + 1}/$total';
      notifyListeners();
    }
    
    await loadLibrary();
    _isScanning = false;
    _scanStatus = 'Scan complete: ${items.length} files found';
    notifyListeners();
  }
  
  Future<List<MediaItem>> search(String query) async {
    if (query.isEmpty) return [];
    return await _db.searchMedia(query);
  }
  
  Future<List<MediaItem>> getMediaByArtist(String artist) async {
    return await _db.getMediaByArtist(artist);
  }
  
  Future<List<MediaItem>> getMediaByAlbum(String album) async {
    return await _db.getMediaByAlbum(album);
  }
  
  Future<void> toggleFavorite(MediaItem item) async {
    if (item.id == null) return;
    await _db.toggleFavorite(item.id!, !item.isFavorite);
    await loadLibrary();
  }
  
  Future<void> onMediaPlayed(MediaItem item) async {
    if (item.id == null) return;
    await _db.incrementPlayCount(item.id!);
    await _db.addToRecentlyPlayed(item.id!);
    await loadLibrary();
  }
  
  // Playlist operations
  Future<void> createPlaylist(String name) async {
    await _db.insertPlaylist(Playlist(name: name));
    await loadLibrary();
  }
  
  Future<void> deletePlaylist(int id) async {
    await _db.deletePlaylist(id);
    await loadLibrary();
  }
  
  Future<void> addToPlaylist(int playlistId, int mediaId) async {
    await _db.addToPlaylist(playlistId, mediaId);
    await loadLibrary();
  }
  
  Future<void> removeFromPlaylist(int playlistId, int mediaId) async {
    await _db.removeFromPlaylist(playlistId, mediaId);
    await loadLibrary();
  }
  
  Future<List<MediaItem>> getPlaylistMedia(int playlistId) async {
    return await _db.getPlaylistMedia(playlistId);
  }
}

bool isVideoFile(String path) {
  final ext = path.split('.').last.toLowerCase();
  return ['mp4', 'mkv', 'avi', 'flv', 'webm', 'mov', '3gp'].contains(ext);
}
