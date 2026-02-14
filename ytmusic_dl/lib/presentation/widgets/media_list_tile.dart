import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../data/models/media_item.dart';
import '../../core/utils/formatters.dart';
import '../providers/library_provider.dart';

class MediaListTile extends StatelessWidget {
  final MediaItem item;
  final VoidCallback onTap;
  final bool isVideo;

  const MediaListTile({
    super.key,
    required this.item,
    required this.onTap,
    this.isVideo = false,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Container(
        width: 48,
        height: 48,
        decoration: BoxDecoration(
          color: Colors.grey[800],
          borderRadius: BorderRadius.circular(4),
        ),
        child: Icon(
          isVideo ? Icons.video_library : Icons.music_note,
          color: Colors.grey,
        ),
      ),
      title: Text(
        item.title,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      subtitle: Text(
        '${item.artist} • ${item.album}',
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: TextStyle(color: Colors.grey[400]),
      ),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (item.isFavorite)
            const Icon(Icons.favorite, color: Colors.red, size: 18),
          const SizedBox(width: 8),
          Text(
            formatDuration(Duration(milliseconds: item.duration)),
            style: TextStyle(color: Colors.grey[400]),
          ),
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert, size: 20),
            onSelected: (value) => _handleMenuAction(context, value),
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'play',
                child: ListTile(
                  leading: Icon(Icons.play_arrow),
                  title: Text('Play'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              const PopupMenuItem(
                value: 'queue',
                child: ListTile(
                  leading: Icon(Icons.queue_music),
                  title: Text('Add to Queue'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              PopupMenuItem(
                value: 'favorite',
                child: ListTile(
                  leading: Icon(item.isFavorite ? Icons.favorite : Icons.favorite_border),
                  title: Text(item.isFavorite ? 'Remove from Favorites' : 'Add to Favorites'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
              const PopupMenuItem(
                value: 'info',
                child: ListTile(
                  leading: Icon(Icons.info),
                  title: Text('Info'),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
            ],
          ),
        ],
      ),
      onTap: onTap,
    );
  }

  void _handleMenuAction(BuildContext context, String action) {
    switch (action) {
      case 'play':
        onTap();
        break;
      case 'queue':
        // Add to queue
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Added to queue')),
        );
        break;
      case 'favorite':
        context.read<LibraryProvider>().toggleFavorite(item);
        break;
      case 'info':
        _showInfoDialog(context);
        break;
    }
  }

  void _showInfoDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(item.title),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _infoRow('Artist', item.artist),
            _infoRow('Album', item.album),
            _infoRow('Duration', formatDuration(Duration(milliseconds: item.duration))),
            _infoRow('Path', item.path),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}
