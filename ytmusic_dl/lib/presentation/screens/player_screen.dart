import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:video_player/video_player.dart';
import '../providers/player_provider.dart';
import '../providers/library_provider.dart';
import '../../core/utils/formatters.dart';
import '../../core/constants/app_constants.dart';

class PlayerScreen extends StatefulWidget {
  const PlayerScreen({super.key});

  @override
  State<PlayerScreen> createState() => _PlayerScreenState();
}

class _PlayerScreenState extends State<PlayerScreen> {
  bool _showControls = true;
  bool _isDragging = false;
  double _dragValue = 0;

  @override
  void initState() {
    super.initState();
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
  }

  @override
  void dispose() {
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Consumer<PlayerProvider>(
        builder: (context, player, _) {
          if (player.currentItem == null) {
            return const Center(
              child: Text(
                'No media playing',
                style: TextStyle(color: Colors.white),
              ),
            );
          }

          return GestureDetector(
            onTap: () {
              setState(() {
                _showControls = !_showControls;
              });
            },
            onHorizontalDragStart: (_) => _isDragging = true,
            onHorizontalDragUpdate: (details) {
              _dragValue += details.delta.dx;
            },
            onHorizontalDragEnd: (_) {
              if (_isDragging) {
                final seekAmount = Duration(seconds: (_dragValue / 10).round());
                player.seekRelative(seekAmount);
              }
              _isDragging = false;
              _dragValue = 0;
            },
            child: Stack(
              fit: StackFit.expand,
              children: [
                // Video or Album Art
                if (player.isVideo && player.controller != null)
                  _buildVideoPlayer(player)
                else
                  _buildAlbumArt(player),

                // Controls overlay
                if (_showControls) _buildControls(context, player),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildVideoPlayer(PlayerProvider player) {
    final controller = player.controller;
    if (controller == null || !controller.value.isInitialized) {
      return const Center(
        child: CircularProgressIndicator(color: Colors.white),
      );
    }
    
    return Center(
      child: AspectRatio(
        aspectRatio: controller.value.aspectRatio,
        child: VideoPlayer(controller),
      ),
    );
  }

  Widget _buildAlbumArt(PlayerProvider player) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Colors.purple.shade800,
            Colors.black,
          ],
        ),
      ),
      child: Center(
        child: Icon(
          Icons.music_note,
          size: 150,
          color: Colors.white.withValues(alpha: 0.5),
        ),
      ),
    );
  }

  Widget _buildControls(BuildContext context, PlayerProvider player) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Colors.black54,
            Colors.transparent,
            Colors.transparent,
            Colors.black87,
          ],
          stops: const [0.0, 0.3, 0.7, 1.0],
        ),
      ),
      child: SafeArea(
        child: Column(
          children: [
            _buildTopBar(context, player),
            const Spacer(),
            _buildCenterControls(player),
            const Spacer(),
            _buildBottomControls(context, player),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildTopBar(BuildContext context, PlayerProvider player) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.keyboard_arrow_down, color: Colors.white),
            onPressed: () => Navigator.pop(context),
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Text(
                  player.currentItem?.title ?? '',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  player.currentItem?.artist ?? '',
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.7),
                    fontSize: 14,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert, color: Colors.white),
            onSelected: (value) => _handleMenuAction(context, player, value),
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'queue',
                child: ListTile(
                  leading: Icon(Icons.queue_music),
                  title: Text('Queue'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              const PopupMenuItem(
                value: 'favorite',
                child: ListTile(
                  leading: Icon(Icons.favorite),
                  title: Text('Add to Favorites'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              const PopupMenuItem(
                value: 'speed',
                child: ListTile(
                  leading: Icon(Icons.speed),
                  title: Text('Playback Speed'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildCenterControls(PlayerProvider player) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        IconButton(
          icon: Icon(
            Icons.shuffle,
            color: player.shuffleEnabled ? Colors.green : Colors.white,
          ),
          onPressed: player.toggleShuffle,
        ),
        IconButton(
          icon: const Icon(Icons.skip_previous, color: Colors.white, size: 36),
          onPressed: player.hasPrevious ? player.playPrevious : null,
        ),
        Container(
          decoration: const BoxDecoration(
            shape: BoxShape.circle,
            color: Colors.white,
          ),
          child: IconButton(
            icon: Icon(
              player.isPlaying ? Icons.pause : Icons.play_arrow,
              color: Colors.black,
              size: 36,
            ),
            onPressed: player.togglePlayPause,
            iconSize: 36,
            padding: const EdgeInsets.all(12),
          ),
        ),
        IconButton(
          icon: const Icon(Icons.skip_next, color: Colors.white, size: 36),
          onPressed: player.hasNext ? player.playNext : null,
        ),
        IconButton(
          icon: Icon(
            player.repeatMode == PlaybackRepeatMode.one
                ? Icons.repeat_one
                : Icons.repeat,
            color: player.repeatMode != PlaybackRepeatMode.off 
                ? Colors.green 
                : Colors.white,
          ),
          onPressed: player.toggleRepeatMode,
        ),
      ],
    );
  }

  Widget _buildBottomControls(BuildContext context, PlayerProvider player) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        children: [
          SliderTheme(
            data: SliderTheme.of(context).copyWith(
              trackHeight: 3,
              thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6),
            ),
            child: Slider(
              value: player.progress.clamp(0.0, 1.0),
              onChanged: (value) {
                final position = Duration(
                  milliseconds: (value * player.duration.inMilliseconds).round(),
                );
                player.seek(position);
              },
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  formatDuration(player.position),
                  style: const TextStyle(color: Colors.white, fontSize: 12),
                ),
                Text(
                  formatDuration(player.duration),
                  style: const TextStyle(color: Colors.white, fontSize: 12),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              const Icon(Icons.volume_down, color: Colors.white, size: 20),
              Expanded(
                child: Slider(
                  value: player.volume,
                  onChanged: (value) => player.setVolume(value),
                ),
              ),
              const Icon(Icons.volume_up, color: Colors.white, size: 20),
            ],
          ),
        ],
      ),
    );
  }

  void _handleMenuAction(BuildContext context, PlayerProvider player, String action) {
    switch (action) {
      case 'queue':
        _showQueue(context, player);
        break;
      case 'favorite':
        if (player.currentItem != null) {
          context.read<LibraryProvider>().toggleFavorite(player.currentItem!);
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Added to favorites')),
          );
        }
        break;
      case 'speed':
        _showSpeedSelector(context, player);
        break;
    }
  }

  void _showQueue(BuildContext context, PlayerProvider player) {
    showModalBottomSheet(
      context: context,
      builder: (context) => Container(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Queue',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: ListView.builder(
                itemCount: player.queue.length,
                itemBuilder: (context, index) {
                  final item = player.queue[index];
                  return ListTile(
                    leading: Icon(
                      index == player.currentIndex 
                          ? Icons.play_arrow 
                          : Icons.music_note,
                    ),
                    title: Text(item.title),
                    subtitle: Text(item.artist),
                    onTap: () => player.playAtIndex(index),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showSpeedSelector(BuildContext context, PlayerProvider player) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Playback Speed'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: AppConstants.playbackSpeeds.map((speed) {
            return ListTile(
              title: Text('${speed}x'),
              trailing: player.playbackSpeed == speed
                  ? const Icon(Icons.check)
                  : null,
              onTap: () {
                player.setPlaybackSpeed(speed);
                Navigator.pop(context);
              },
            );
          }).toList(),
        ),
      ),
    );
  }
}
