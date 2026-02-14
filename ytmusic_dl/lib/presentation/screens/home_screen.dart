import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/library_provider.dart';
import '../providers/player_provider.dart';
import '../widgets/media_list_tile.dart';
import '../widgets/section_header.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('YTMusic DL'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              context.read<LibraryProvider>().scanMedia();
            },
          ),
        ],
      ),
      body: Consumer<LibraryProvider>(
        builder: (context, library, _) {
          if (library.isScanning) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const CircularProgressIndicator(),
                  const SizedBox(height: 16),
                  Text(library.scanStatus ?? 'Scanning...'),
                  const SizedBox(height: 8),
                  LinearProgressIndicator(value: library.scanProgress),
                ],
              ),
            );
          }

          if (library.allMedia.isEmpty) {
            return _buildEmptyState(context);
          }

          return RefreshIndicator(
            onRefresh: () => library.scanMedia(),
            child: ListView(
              children: [
                // Quick actions
                _buildQuickActions(context, library),
                
                // Recently Played
                if (library.recentlyPlayed.isNotEmpty) ...[
                  SectionHeader(
                    title: 'Recently Played',
                    onSeeAll: () => _showSection(context, 'Recently Played', library.recentlyPlayed),
                  ),
                  _buildHorizontalList(context, library.recentlyPlayed),
                ],
                
                // Recently Added
                if (library.recentlyAdded.isNotEmpty) ...[
                  SectionHeader(
                    title: 'Recently Added',
                    onSeeAll: () => _showSection(context, 'Recently Added', library.recentlyAdded),
                  ),
                  _buildHorizontalList(context, library.recentlyAdded),
                ],
                
                // Most Played
                if (library.mostPlayed.isNotEmpty) ...[
                  SectionHeader(
                    title: 'Most Played',
                    onSeeAll: () => _showSection(context, 'Most Played', library.mostPlayed),
                  ),
                  _buildHorizontalList(context, library.mostPlayed),
                ],
                
                // Favorites
                if (library.favorites.isNotEmpty) ...[
                  SectionHeader(
                    title: 'Favorites',
                    onSeeAll: () => _showSection(context, 'Favorites', library.favorites),
                  ),
                  _buildHorizontalList(context, library.favorites),
                ],
                
                // Songs
                SectionHeader(
                  title: 'Songs (${library.songs.length})',
                  onSeeAll: () => _showSection(context, 'All Songs', library.songs),
                ),
                ...library.songs.take(10).map((item) => MediaListTile(
                  item: item,
                  onTap: () {
                    context.read<PlayerProvider>().playMedia(
                      item,
                      playlist: library.songs,
                    );
                    library.onMediaPlayed(item);
                  },
                )),
                
                // Videos
                if (library.videos.isNotEmpty) ...[
                  SectionHeader(
                    title: 'Videos (${library.videos.length})',
                    onSeeAll: () => _showSection(context, 'All Videos', library.videos),
                  ),
                  ...library.videos.take(5).map((item) => MediaListTile(
                    item: item,
                    isVideo: true,
                    onTap: () {
                      context.read<PlayerProvider>().playVideo(
                        item,
                        playlist: library.videos,
                      );
                      library.onMediaPlayed(item);
                    },
                  )),
                ],
                
                const SizedBox(height: 100),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.library_music,
            size: 80,
            color: Colors.grey,
          ),
          const SizedBox(height: 16),
          const Text(
            'No media files found',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          const Text(
            'Scan your device to find music and videos',
            style: TextStyle(color: Colors.grey),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: () {
              context.read<LibraryProvider>().scanMedia();
            },
            icon: const Icon(Icons.refresh),
            label: const Text('Scan for Media'),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickActions(BuildContext context, LibraryProvider library) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _buildActionButton(
            context,
            Icons.shuffle,
            'Shuffle All',
            () {
              if (library.songs.isNotEmpty) {
                final shuffled = List.of(library.songs)..shuffle();
                context.read<PlayerProvider>().playMedia(
                  shuffled.first,
                  playlist: shuffled,
                );
              }
            },
          ),
          _buildActionButton(
            context,
            Icons.play_arrow,
            'Play All',
            () {
              if (library.songs.isNotEmpty) {
                context.read<PlayerProvider>().playMedia(
                  library.songs.first,
                  playlist: library.songs,
                );
              }
            },
          ),
        ],
      ),
    );
  }

  Widget _buildActionButton(
    BuildContext context,
    IconData icon,
    String label,
    VoidCallback onTap,
  ) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        decoration: BoxDecoration(
          border: Border.all(color: Theme.of(context).colorScheme.primary),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            Icon(icon, color: Theme.of(context).colorScheme.primary),
            const SizedBox(width: 8),
            Text(
              label,
              style: TextStyle(
                color: Theme.of(context).colorScheme.primary,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHorizontalList(BuildContext context, List items) {
    return SizedBox(
      height: 180,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: items.length,
        itemBuilder: (context, index) {
          final item = items[index];
          return Container(
            width: 140,
            margin: const EdgeInsets.only(right: 12),
            child: GestureDetector(
              onTap: () {
                final isVideo = isVideoFile(item.path);
                if (isVideo) {
                  context.read<PlayerProvider>().playVideo(item, playlist: items.cast());
                } else {
                  context.read<PlayerProvider>().playMedia(item, playlist: items.cast());
                }
                context.read<LibraryProvider>().onMediaPlayed(item);
              },
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    height: 140,
                    decoration: BoxDecoration(
                      color: Colors.grey[800],
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Center(
                      child: Icon(
                        isVideoFile(item.path) ? Icons.video_library : Icons.music_note,
                        size: 48,
                        color: Colors.grey,
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    item.title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w500),
                  ),
                  Text(
                    item.artist,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(fontSize: 12, color: Colors.grey[400]),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  void _showSection(BuildContext context, String title, List items) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => SectionScreen(title: title, items: items),
      ),
    );
  }
}

class SectionScreen extends StatelessWidget {
  final String title;
  final List items;

  const SectionScreen({super.key, required this.title, required this.items});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: ListView.builder(
        itemCount: items.length,
        itemBuilder: (context, index) {
          final item = items[index];
          return MediaListTile(
            item: item,
            onTap: () {
              final isVideo = isVideoFile(item.path);
              if (isVideo) {
                context.read<PlayerProvider>().playVideo(item, playlist: items.cast());
              } else {
                context.read<PlayerProvider>().playMedia(item, playlist: items.cast());
              }
              context.read<LibraryProvider>().onMediaPlayed(item);
            },
          );
        },
      ),
    );
  }
}

bool isVideoFile(String path) {
  final ext = path.split('.').last.toLowerCase();
  return ['mp4', 'mkv', 'avi', 'flv', 'webm', 'mov', '3gp'].contains(ext);
}
