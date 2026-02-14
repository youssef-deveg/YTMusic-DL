String formatDuration(Duration duration) {
  String twoDigits(int n) => n.toString().padLeft(2, '0');
  final hours = duration.inHours;
  final minutes = duration.inMinutes.remainder(60);
  final seconds = duration.inSeconds.remainder(60);
  
  if (hours > 0) {
    return '${twoDigits(hours)}:${twoDigits(minutes)}:${twoDigits(seconds)}';
  }
  return '${twoDigits(minutes)}:${twoDigits(seconds)}';
}

String formatFileSize(int bytes) {
  if (bytes < 1024) return '$bytes B';
  if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
  if (bytes < 1024 * 1024 * 1024) return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  return '${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(2)} GB';
}

String getFileExtension(String path) {
  return path.split('.').last.toLowerCase();
}

bool isAudioFile(String path) {
  final ext = getFileExtension(path);
  return ['mp3', 'flac', 'aac', 'ogg', 'wav', 'm4a', 'wma', 'opus'].contains(ext);
}

bool isVideoFile(String path) {
  final ext = getFileExtension(path);
  return ['mp4', 'mkv', 'avi', 'flv', 'webm', 'mov', '3gp'].contains(ext);
}
