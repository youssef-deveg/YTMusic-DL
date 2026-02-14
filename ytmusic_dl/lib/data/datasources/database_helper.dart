import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../models/media_item.dart';
import '../models/playlist.dart';
import '../../core/constants/app_constants.dart';

class DatabaseHelper {
  static Database? _database;
  static final DatabaseHelper instance = DatabaseHelper._();

  DatabaseHelper._();

  Future<Database> get database async {
    _database ??= await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    final path = join(await getDatabasesPath(), AppConstants.databaseName);
    return await openDatabase(
      path,
      version: AppConstants.databaseVersion,
      onCreate: _onCreate,
    );
  }

  Future<void> _onCreate(Database db, int version) async {
    await db.execute('''
      CREATE TABLE media (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        artist TEXT NOT NULL,
        album TEXT NOT NULL,
        path TEXT NOT NULL UNIQUE,
        duration INTEGER NOT NULL,
        artworkPath TEXT,
        dateAdded INTEGER NOT NULL,
        playCount INTEGER DEFAULT 0,
        isFavorite INTEGER DEFAULT 0
      )
    ''');

    await db.execute('''
      CREATE TABLE playlists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        artworkPath TEXT,
        createdAt INTEGER NOT NULL
      )
    ''');

    await db.execute('''
      CREATE TABLE playlist_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        playlistId INTEGER NOT NULL,
        mediaId INTEGER NOT NULL,
        position INTEGER NOT NULL,
        FOREIGN KEY (playlistId) REFERENCES playlists(id) ON DELETE CASCADE,
        FOREIGN KEY (mediaId) REFERENCES media(id) ON DELETE CASCADE
      )
    ''');

    await db.execute('''
      CREATE TABLE recently_played (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mediaId INTEGER NOT NULL,
        playedAt INTEGER NOT NULL,
        FOREIGN KEY (mediaId) REFERENCES media(id) ON DELETE CASCADE
      )
    ''');

    await db.execute('CREATE INDEX idx_media_artist ON media(artist)');
    await db.execute('CREATE INDEX idx_media_album ON media(album)');
    await db.execute('CREATE INDEX idx_media_favorite ON media(isFavorite)');
  }

  // Media operations
  Future<int> insertMedia(MediaItem item) async {
    final db = await database;
    return await db.insert(
      'media',
      item.toMap(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<MediaItem>> getAllMedia() async {
    final db = await database;
    final maps = await db.query('media', orderBy: 'title ASC');
    return maps.map((map) => MediaItem.fromMap(map)).toList();
  }

  Future<List<MediaItem>> getMediaByArtist(String artist) async {
    final db = await database;
    final maps = await db.query(
      'media',
      where: 'artist = ?',
      whereArgs: [artist],
      orderBy: 'album ASC',
    );
    return maps.map((map) => MediaItem.fromMap(map)).toList();
  }

  Future<List<MediaItem>> getMediaByAlbum(String album) async {
    final db = await database;
    final maps = await db.query(
      'media',
      where: 'album = ?',
      whereArgs: [album],
      orderBy: 'title ASC',
    );
    return maps.map((map) => MediaItem.fromMap(map)).toList();
  }

  Future<List<MediaItem>> getFavorites() async {
    final db = await database;
    final maps = await db.query(
      'media',
      where: 'isFavorite = 1',
      orderBy: 'title ASC',
    );
    return maps.map((map) => MediaItem.fromMap(map)).toList();
  }

  Future<List<MediaItem>> getRecentlyAdded({int limit = 50}) async {
    final db = await database;
    final maps = await db.query(
      'media',
      orderBy: 'dateAdded DESC',
      limit: limit,
    );
    return maps.map((map) => MediaItem.fromMap(map)).toList();
  }

  Future<List<MediaItem>> getMostPlayed({int limit = 50}) async {
    final db = await database;
    final maps = await db.query(
      'media',
      where: 'playCount > 0',
      orderBy: 'playCount DESC',
      limit: limit,
    );
    return maps.map((map) => MediaItem.fromMap(map)).toList();
  }

  Future<List<MediaItem>> searchMedia(String query) async {
    final db = await database;
    final maps = await db.query(
      'media',
      where: 'title LIKE ? OR artist LIKE ? OR album LIKE ?',
      whereArgs: ['%$query%', '%$query%', '%$query%'],
      orderBy: 'title ASC',
    );
    return maps.map((map) => MediaItem.fromMap(map)).toList();
  }

  Future<int> updateMedia(MediaItem item) async {
    final db = await database;
    return await db.update(
      'media',
      item.toMap(),
      where: 'id = ?',
      whereArgs: [item.id],
    );
  }

  Future<int> deleteMedia(int id) async {
    final db = await database;
    return await db.delete('media', where: 'id = ?', whereArgs: [id]);
  }

  Future<int> toggleFavorite(int id, bool isFavorite) async {
    final db = await database;
    return await db.update(
      'media',
      {'isFavorite': isFavorite ? 1 : 0},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<int> incrementPlayCount(int id) async {
    final db = await database;
    return await db.rawUpdate(
      'UPDATE media SET playCount = playCount + 1 WHERE id = ?',
      [id],
    );
  }

  // Playlist operations
  Future<int> insertPlaylist(Playlist playlist) async {
    final db = await database;
    return await db.insert('playlists', playlist.toMap());
  }

  Future<List<Playlist>> getAllPlaylists() async {
    final db = await database;
    final maps = await db.query('playlists', orderBy: 'name ASC');
    final playlists = <Playlist>[];
    for (final map in maps) {
      final mediaIds = await getPlaylistMediaIds(map['id'] as int);
      playlists.add(Playlist.fromMap(map, mediaIds: mediaIds));
    }
    return playlists;
  }

  Future<List<int>> getPlaylistMediaIds(int playlistId) async {
    final db = await database;
    final maps = await db.query(
      'playlist_items',
      where: 'playlistId = ?',
      whereArgs: [playlistId],
      orderBy: 'position ASC',
    );
    return maps.map((m) => m['mediaId'] as int).toList();
  }

  Future<List<MediaItem>> getPlaylistMedia(int playlistId) async {
    final db = await database;
    final maps = await db.rawQuery('''
      SELECT media.* FROM media
      INNER JOIN playlist_items ON media.id = playlist_items.mediaId
      WHERE playlist_items.playlistId = ?
      ORDER BY playlist_items.position ASC
    ''', [playlistId]);
    return maps.map((map) => MediaItem.fromMap(map)).toList();
  }

  Future<int> addToPlaylist(int playlistId, int mediaId) async {
    final db = await database;
    final count = Sqflite.firstIntValue(
      await db.rawQuery('SELECT COUNT(*) FROM playlist_items WHERE playlistId = ?', [playlistId]),
    ) ?? 0;
    return await db.insert('playlist_items', {
      'playlistId': playlistId,
      'mediaId': mediaId,
      'position': count,
    });
  }

  Future<int> removeFromPlaylist(int playlistId, int mediaId) async {
    final db = await database;
    return await db.delete(
      'playlist_items',
      where: 'playlistId = ? AND mediaId = ?',
      whereArgs: [playlistId, mediaId],
    );
  }

  Future<int> deletePlaylist(int id) async {
    final db = await database;
    await db.delete('playlist_items', where: 'playlistId = ?', whereArgs: [id]);
    return await db.delete('playlists', where: 'id = ?', whereArgs: [id]);
  }

  // Recently played
  Future<void> addToRecentlyPlayed(int mediaId) async {
    final db = await database;
    await db.insert('recently_played', {
      'mediaId': mediaId,
      'playedAt': DateTime.now().millisecondsSinceEpoch,
    });
    await db.rawDelete('''
      DELETE FROM recently_played WHERE id NOT IN (
        SELECT id FROM recently_played ORDER BY playedAt DESC LIMIT 100
      )
    ''');
  }

  Future<List<MediaItem>> getRecentlyPlayed({int limit = 50}) async {
    final db = await database;
    final maps = await db.rawQuery('''
      SELECT media.* FROM media
      INNER JOIN recently_played ON media.id = recently_played.mediaId
      ORDER BY recently_played.playedAt DESC
      LIMIT ?
    ''', [limit]);
    return maps.map((map) => MediaItem.fromMap(map)).toList();
  }

  // Get unique artists
  Future<List<String>> getAllArtists() async {
    final db = await database;
    final maps = await db.rawQuery('SELECT DISTINCT artist FROM media ORDER BY artist ASC');
    return maps.map((m) => m['artist'] as String).toList();
  }

  // Get unique albums
  Future<List<String>> getAllAlbums() async {
    final db = await database;
    final maps = await db.rawQuery('SELECT DISTINCT album FROM media ORDER BY album ASC');
    return maps.map((m) => m['album'] as String).toList();
  }
}
