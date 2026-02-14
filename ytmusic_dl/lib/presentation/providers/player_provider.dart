import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import '../../data/models/media_item.dart';
import 'dart:io';

enum PlaybackRepeatMode { off, one, all }

class PlayerProvider extends ChangeNotifier {
  VideoPlayerController? _videoController;
  VideoPlayerController? _audioController;
  
  bool _isPlaying = false;
  bool _isVideo = false;
  Duration _position = Duration.zero;
  Duration _duration = Duration.zero;
  double _volume = 1.0;
  double _playbackSpeed = 1.0;
  bool _isBuffering = false;
  PlaybackRepeatMode _repeatMode = PlaybackRepeatMode.off;
  bool _shuffleEnabled = false;
  
  MediaItem? _currentItem;
  List<MediaItem> _queue = [];
  int _currentIndex = -1;
  
  Duration? _loopStart;
  Duration? _loopEnd;
  
  VideoPlayerController? get controller => _isVideo ? _videoController : _audioController;
  
  PlayerProvider() {
    _setupListeners();
  }
  
  void _setupListeners() {
    // Position listener
    _addPositionListener();
  }
  
  void _addPositionListener() {
    // Position updates will be handled in the UI via periodic calls
  }
  
  // Getters
  VideoPlayerController? get videoController => _videoController;
  VideoPlayerController? get audioController => _audioController;
  bool get isPlaying => _isPlaying;
  bool get isVideo => _isVideo;
  Duration get position => _position;
  Duration get duration => _duration;
  double get volume => _volume;
  double get playbackSpeed => _playbackSpeed;
  bool get isBuffering => _isBuffering;
  PlaybackRepeatMode get repeatMode => _repeatMode;
  bool get shuffleEnabled => _shuffleEnabled;
  MediaItem? get currentItem => _currentItem;
  List<MediaItem> get queue => _queue;
  int get currentIndex => _currentIndex;
  Duration? get loopStart => _loopStart;
  Duration? get loopEnd => _loopEnd;
  
  bool get hasPrevious => _currentIndex > 0 || _repeatMode == PlaybackRepeatMode.all;
  bool get hasNext => _currentIndex < _queue.length - 1 || _repeatMode == PlaybackRepeatMode.all;
  
  double get progress {
    if (_duration.inMilliseconds == 0) return 0;
    return _position.inMilliseconds / _duration.inMilliseconds;
  }
  
  Future<void> _initializeController(String path) async {
    // Dispose old controller
    await _videoController?.dispose();
    await _audioController?.dispose();
    
    final file = File(path);
    final uri = Uri.file(file.path);
    
    if (_isVideo) {
      _videoController = VideoPlayerController.file(file);
      await _videoController!.initialize();
      _duration = _videoController!.value.duration;
      _videoController!.addListener(_onVideoUpdate);
    } else {
      _audioController = VideoPlayerController.file(file);
      await _audioController!.initialize();
      _duration = _audioController!.value.duration;
      _audioController!.addListener(_onVideoUpdate);
    }
    
    notifyListeners();
  }
  
  void _onVideoUpdate() {
    final ctrl = controller;
    if (ctrl == null) return;
    
    _isPlaying = ctrl.value.isPlaying;
    _position = ctrl.value.position;
    _isBuffering = ctrl.value.isBuffering;
    
    if (ctrl.value.position >= ctrl.value.duration && ctrl.value.duration > Duration.zero) {
      _handleTrackComplete();
    }
    
    notifyListeners();
  }
  
  void _handleTrackComplete() {
    if (_repeatMode == PlaybackRepeatMode.one) {
      controller?.seekTo(Duration.zero);
      controller?.play();
    } else if (_repeatMode == PlaybackRepeatMode.all || _shuffleEnabled) {
      playNext();
    } else if (_currentIndex < _queue.length - 1) {
      playNext();
    }
  }
  
  // Playback controls
  Future<void> playMedia(MediaItem item, {List<MediaItem>? playlist}) async {
    _currentItem = item;
    _isVideo = false;
    
    if (playlist != null) {
      _queue = playlist;
      _currentIndex = playlist.indexOf(item);
    } else {
      _queue = [item];
      _currentIndex = 0;
    }
    
    await _initializeController(item.path);
    await controller?.play();
    _isPlaying = true;
    notifyListeners();
  }
  
  Future<void> playVideo(MediaItem item, {List<MediaItem>? playlist}) async {
    _currentItem = item;
    _isVideo = true;
    
    if (playlist != null) {
      _queue = playlist;
      _currentIndex = playlist.indexOf(item);
    } else {
      _queue = [item];
      _currentIndex = 0;
    }
    
    await _initializeController(item.path);
    await controller?.play();
    _isPlaying = true;
    notifyListeners();
  }
  
  Future<void> play() async {
    await controller?.play();
    _isPlaying = true;
    notifyListeners();
  }
  
  Future<void> pause() async {
    await controller?.pause();
    _isPlaying = false;
    notifyListeners();
  }
  
  Future<void> togglePlayPause() async {
    if (_isPlaying) {
      await pause();
    } else {
      await play();
    }
  }
  
  Future<void> stop() async {
    await controller?.pause();
    await controller?.seekTo(Duration.zero);
    _currentItem = null;
    notifyListeners();
  }
  
  Future<void> seek(Duration position) async {
    await controller?.seekTo(position);
    _position = position;
    notifyListeners();
  }
  
  Future<void> seekRelative(Duration offset) async {
    final newPosition = _position + offset;
    if (newPosition < Duration.zero) {
      await seek(Duration.zero);
    } else if (newPosition > _duration) {
      await seek(_duration);
    } else {
      await seek(newPosition);
    }
  }
  
  Future<void> setVolume(double volume) async {
    _volume = volume;
    await controller?.setVolume(volume);
    notifyListeners();
  }
  
  Future<void> setPlaybackSpeed(double speed) async {
    _playbackSpeed = speed;
    await controller?.setPlaybackSpeed(speed);
    notifyListeners();
  }
  
  Future<void> playNext() async {
    if (_queue.isEmpty) return;
    
    int nextIndex;
    if (_shuffleEnabled) {
      nextIndex = _queue.length > 1 
          ? (_currentIndex + 1 + (_queue.length - 1)) % _queue.length
          : 0;
    } else {
      nextIndex = (_currentIndex + 1) % _queue.length;
    }
    
    if (nextIndex >= 0 && nextIndex < _queue.length) {
      _currentIndex = nextIndex;
      _currentItem = _queue[nextIndex];
      _isVideo = isVideoFile(_queue[nextIndex].path);
      await _initializeController(_currentItem!.path);
      await controller?.play();
      _isPlaying = true;
      notifyListeners();
    }
  }
  
  Future<void> playPrevious() async {
    if (_queue.isEmpty) return;
    
    if (_position.inSeconds > 3) {
      await seek(Duration.zero);
      return;
    }
    
    final prevIndex = (_currentIndex - 1 + _queue.length) % _queue.length;
    if (prevIndex >= 0 && prevIndex < _queue.length) {
      _currentIndex = prevIndex;
      _currentItem = _queue[prevIndex];
      _isVideo = isVideoFile(_queue[prevIndex].path);
      await _initializeController(_currentItem!.path);
      await controller?.play();
      _isPlaying = true;
      notifyListeners();
    }
  }
  
  void setQueue(List<MediaItem> items, {int startIndex = 0}) {
    _queue = items;
    _currentIndex = startIndex;
    if (items.isNotEmpty && startIndex >= 0 && startIndex < items.length) {
      _currentItem = items[startIndex];
      _isVideo = isVideoFile(items[startIndex].path);
    }
    notifyListeners();
  }
  
  void addToQueue(MediaItem item) {
    _queue.add(item);
    notifyListeners();
  }
  
  void removeFromQueue(int index) {
    if (index >= 0 && index < _queue.length) {
      _queue.removeAt(index);
      if (index < _currentIndex) {
        _currentIndex--;
      } else if (index == _currentIndex && _queue.isNotEmpty) {
        _currentIndex = _currentIndex.clamp(0, _queue.length - 1);
        _currentItem = _queue[_currentIndex];
      }
      notifyListeners();
    }
  }
  
  void clearQueue() {
    _queue.clear();
    _currentIndex = -1;
    _currentItem = null;
    notifyListeners();
  }
  
  void toggleRepeatMode() {
    switch (_repeatMode) {
      case PlaybackRepeatMode.off:
        _repeatMode = PlaybackRepeatMode.all;
        break;
      case PlaybackRepeatMode.all:
        _repeatMode = PlaybackRepeatMode.one;
        break;
      case PlaybackRepeatMode.one:
        _repeatMode = PlaybackRepeatMode.off;
        break;
    }
    notifyListeners();
  }
  
  void toggleShuffle() {
    _shuffleEnabled = !_shuffleEnabled;
    notifyListeners();
  }
  
  void setLoopStart() {
    _loopStart = _position;
    notifyListeners();
  }
  
  void setLoopEnd() {
    _loopEnd = _position;
    notifyListeners();
  }
  
  void clearLoop() {
    _loopStart = null;
    _loopEnd = null;
    notifyListeners();
  }
  
  Future<void> playAtIndex(int index) async {
    if (index >= 0 && index < _queue.length) {
      _currentIndex = index;
      _currentItem = _queue[index];
      _isVideo = isVideoFile(_queue[index].path);
      await _initializeController(_currentItem!.path);
      await controller?.play();
      _isPlaying = true;
      notifyListeners();
    }
  }
  
  @override
  void dispose() {
    _videoController?.dispose();
    _audioController?.dispose();
    super.dispose();
  }
}

bool isVideoFile(String path) {
  final ext = path.split('.').last.toLowerCase();
  return ['mp4', 'mkv', 'avi', 'flv', 'webm', 'mov', '3gp'].contains(ext);
}
