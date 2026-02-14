class AppConstants {
  static const String appName = 'YTMusic DL';
  static const String appVersion = '1.0.0';
  
  // Supported formats
  static const List<String> audioFormats = ['mp3', 'flac', 'aac', 'ogg', 'wav', 'm4a', 'wma'];
  static const List<String> videoFormats = ['mp4', 'mkv', 'avi', 'flv', 'webm', 'mov', '3gp'];
  
  // Playback speeds
  static const List<double> playbackSpeeds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0];
  
  // Database
  static const String databaseName = 'ytmusic_dl.db';
  static const int databaseVersion = 1;
  
  // Equalizer presets
  static const Map<String, List<double>> equalizerPresets = {
    'Normal': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    'Rock': [4.0, 3.0, 2.0, 0.0, -1.0, -1.0, 0.0, 2.0, 3.0, 4.0],
    'Jazz': [3.0, 2.0, 1.0, 2.0, -1.0, -1.0, 0.0, 1.0, 2.0, 3.0],
    'Classical': [4.0, 3.0, 2.0, 1.0, -1.0, -1.0, 0.0, 2.0, 3.0, 4.0],
    'Pop': [-1.0, -1.0, 0.0, 3.0, 4.0, 4.0, 3.0, 0.0, -1.0, -1.0],
    'Bass Boost': [5.0, 4.0, 3.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    'Treble Boost': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 3.0, 4.0, 5.0],
    'Electronic': [4.0, 3.0, 1.0, 0.0, -2.0, -2.0, 0.0, 2.0, 4.0, 5.0],
  };
  
  // Sleep timer durations (in minutes)
  static const List<int> sleepTimerDurations = [15, 30, 45, 60, 90, 120];
  
  // Crossfade durations (in seconds)
  static const List<int> crossfadeDurations = [0, 2, 3, 4, 5, 6, 8, 10];
}
