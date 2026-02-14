import 'dart:io';
import 'package:permission_handler/permission_handler.dart';
import '../models/media_item.dart';
import '../../core/utils/formatters.dart';

class MediaScanner {
  static final MediaScanner instance = MediaScanner._();
  MediaScanner._();

  Future<bool> requestPermissions() async {
    if (Platform.isAndroid) {
      final storageStatus = await Permission.storage.request();
      if (storageStatus.isGranted) {
        return true;
      }
      // Try audio permission for Android 13+
      final audioStatus = await Permission.audio.request();
      if (audioStatus.isGranted) {
        return true;
      }
      // Try manage external storage for older Android
      final manageStatus = await Permission.manageExternalStorage.request();
      return manageStatus.isGranted;
    }
    return true;
  }

  Future<List<MediaItem>> scanMediaFiles() async {
    final mediaItems = <MediaItem>[];
    
    // Common directories to scan on Android
    final directories = [
      Directory('/storage/emulated/0/Music'),
      Directory('/storage/emulated/0/Download'),
      Directory('/storage/emulated/0/DCIM'),
      Directory('/storage/emulated/0'),
    ];

    for (final dir in directories) {
      if (await dir.exists()) {
        await _scanDirectory(dir, mediaItems);
      }
    }

    // Also scan external storage if available
    final externalDirs = await _getExternalStorageDirectories();
    for (final path in externalDirs) {
      final dir = Directory(path);
      if (await dir.exists()) {
        await _scanDirectory(dir, mediaItems);
      }
    }

    return mediaItems;
  }

  Future<List<String>> _getExternalStorageDirectories() async {
    final directories = <String>[];
    final storageDir = Directory('/storage');
    
    if (await storageDir.exists()) {
      await for (final entity in storageDir.list()) {
        if (entity is Directory && !entity.path.contains('emulated')) {
          directories.add(entity.path);
        }
      }
    }
    return directories;
  }

  Future<void> _scanDirectory(Directory dir, List<MediaItem> mediaItems) async {
    try {
      await for (final entity in dir.list(recursive: true, followLinks: false)) {
        if (entity is File) {
          final path = entity.path;
          final ext = getFileExtension(path);
          
          if (isAudioFile(path) || isVideoFile(path)) {
            final mediaItem = await _createMediaItem(entity, ext);
            if (mediaItem != null) {
              mediaItems.add(mediaItem);
            }
          }
        }
      }
    } catch (e) {
      // Permission denied or other error - skip this directory
    }
  }

  Future<MediaItem?> _createMediaItem(File file, String extension) async {
    try {
      final fileName = file.path.split('/').last;
      final nameWithoutExt = fileName.replaceAll('.$extension', '');
      
      // Try to extract artist - title from filename
      String title = nameWithoutExt;
      String artist = 'Unknown Artist';
      String album = 'Unknown Album';
      
      // Common patterns: "Artist - Title" or "Title"
      if (nameWithoutExt.contains(' - ')) {
        final parts = nameWithoutExt.split(' - ');
        if (parts.length >= 2) {
          artist = parts[0].trim();
          title = parts.sublist(1).join(' - ').trim();
        }
      }
      
      // Get file stats for duration estimate
      final stat = await file.stat();
      
      // Estimate duration based on file size (very rough estimate)
      // This would ideally use a proper metadata reader
      final estimatedDuration = _estimateDuration(file.path, stat.size);
      
      return MediaItem(
        title: title,
        artist: artist,
        album: album,
        path: file.path,
        duration: estimatedDuration,
        dateAdded: stat.modified,
      );
    } catch (e) {
      return null;
    }
  }

  int _estimateDuration(String path, int fileSize) {
    // Very rough estimation based on file extension
    final ext = getFileExtension(path).toLowerCase();
    
    // Bitrate estimates (bytes per second)
    final bitrateMap = {
      'mp3': 16000,  // ~128kbps
      'aac': 16000,
      'm4a': 16000,
      'flac': 88000, // ~705kbps
      'wav': 176400, // ~1411kbps
      'ogg': 16000,
      'wma': 16000,
      'mp4': 80000,  // video estimate
      'mkv': 80000,
      'avi': 80000,
      'webm': 80000,
      'mov': 80000,
    };
    
    final bitrate = bitrateMap[ext] ?? 16000;
    final durationSeconds = fileSize ~/ bitrate;
    return durationSeconds * 1000; // Convert to milliseconds
  }
}
