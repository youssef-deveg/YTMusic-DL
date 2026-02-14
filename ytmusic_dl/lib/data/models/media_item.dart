class MediaItem {
  final int? id;
  final String title;
  final String artist;
  final String album;
  final String path;
  final int duration;
  final String? artworkPath;
  final DateTime dateAdded;
  final int playCount;
  final bool isFavorite;

  MediaItem({
    this.id,
    required this.title,
    required this.artist,
    required this.album,
    required this.path,
    required this.duration,
    this.artworkPath,
    DateTime? dateAdded,
    this.playCount = 0,
    this.isFavorite = false,
  }) : dateAdded = dateAdded ?? DateTime.now();

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'title': title,
      'artist': artist,
      'album': album,
      'path': path,
      'duration': duration,
      'artworkPath': artworkPath,
      'dateAdded': dateAdded.millisecondsSinceEpoch,
      'playCount': playCount,
      'isFavorite': isFavorite ? 1 : 0,
    };
  }

  factory MediaItem.fromMap(Map<String, dynamic> map) {
    return MediaItem(
      id: map['id'] as int?,
      title: map['title'] as String,
      artist: map['artist'] as String,
      album: map['album'] as String,
      path: map['path'] as String,
      duration: map['duration'] as int,
      artworkPath: map['artworkPath'] as String?,
      dateAdded: DateTime.fromMillisecondsSinceEpoch(map['dateAdded'] as int),
      playCount: map['playCount'] as int? ?? 0,
      isFavorite: (map['isFavorite'] as int?) == 1,
    );
  }

  MediaItem copyWith({
    int? id,
    String? title,
    String? artist,
    String? album,
    String? path,
    int? duration,
    String? artworkPath,
    DateTime? dateAdded,
    int? playCount,
    bool? isFavorite,
  }) {
    return MediaItem(
      id: id ?? this.id,
      title: title ?? this.title,
      artist: artist ?? this.artist,
      album: album ?? this.album,
      path: path ?? this.path,
      duration: duration ?? this.duration,
      artworkPath: artworkPath ?? this.artworkPath,
      dateAdded: dateAdded ?? this.dateAdded,
      playCount: playCount ?? this.playCount,
      isFavorite: isFavorite ?? this.isFavorite,
    );
  }
}
