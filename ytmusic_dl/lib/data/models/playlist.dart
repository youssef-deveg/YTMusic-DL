class Playlist {
  final int? id;
  final String name;
  final String? artworkPath;
  final DateTime createdAt;
  final List<int> mediaIds;

  Playlist({
    this.id,
    required this.name,
    this.artworkPath,
    DateTime? createdAt,
    List<int>? mediaIds,
  })  : createdAt = createdAt ?? DateTime.now(),
        mediaIds = mediaIds ?? [];

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'name': name,
      'artworkPath': artworkPath,
      'createdAt': createdAt.millisecondsSinceEpoch,
    };
  }

  factory Playlist.fromMap(Map<String, dynamic> map, {List<int>? mediaIds}) {
    return Playlist(
      id: map['id'] as int?,
      name: map['name'] as String,
      artworkPath: map['artworkPath'] as String?,
      createdAt: DateTime.fromMillisecondsSinceEpoch(map['createdAt'] as int),
      mediaIds: mediaIds ?? [],
    );
  }

  Playlist copyWith({
    int? id,
    String? name,
    String? artworkPath,
    DateTime? createdAt,
    List<int>? mediaIds,
  }) {
    return Playlist(
      id: id ?? this.id,
      name: name ?? this.name,
      artworkPath: artworkPath ?? this.artworkPath,
      createdAt: createdAt ?? this.createdAt,
      mediaIds: mediaIds ?? this.mediaIds,
    );
  }
}
