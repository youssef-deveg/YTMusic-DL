import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/player_provider.dart';
import '../providers/library_provider.dart';
import '../screens/home_screen.dart';
import '../screens/settings_screen.dart';
import '../widgets/mini_player.dart';

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _currentIndex = 0;
  
  final List<Widget> _screens = [
    const HomeScreen(),
    const SizedBox(), // Placeholder for search
    const SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex == 1 ? 0 : _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Consumer<PlayerProvider>(
            builder: (context, player, _) {
              if (player.currentItem == null) {
                return const SizedBox.shrink();
              }
              return const MiniPlayer();
            },
          ),
          BottomNavigationBar(
            currentIndex: _currentIndex,
            onTap: (index) {
              if (index == 1) {
                // Show search
                showSearch(
                  context: context,
                  delegate: MediaSearchDelegate(),
                );
              } else {
                setState(() {
                  _currentIndex = index;
                });
              }
            },
            items: const [
              BottomNavigationBarItem(
                icon: Icon(Icons.home),
                label: 'Home',
              ),
              BottomNavigationBarItem(
                icon: Icon(Icons.search),
                label: 'Search',
              ),
              BottomNavigationBarItem(
                icon: Icon(Icons.settings),
                label: 'Settings',
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class MediaSearchDelegate extends SearchDelegate<String> {
  @override
  List<Widget> buildActions(BuildContext context) {
    return [
      IconButton(
        icon: const Icon(Icons.clear),
        onPressed: () {
          query = '';
        },
      ),
    ];
  }

  @override
  Widget buildLeading(BuildContext context) {
    return IconButton(
      icon: const Icon(Icons.arrow_back),
      onPressed: () {
        close(context, '');
      },
    );
  }

  @override
  Widget buildResults(BuildContext context) {
    return _buildSearchResults(context);
  }

  @override
  Widget buildSuggestions(BuildContext context) {
    return _buildSearchResults(context);
  }

  Widget _buildSearchResults(BuildContext context) {
    if (query.isEmpty) {
      return const Center(
        child: Text('Search for songs, artists, or albums'),
      );
    }
    
    return FutureBuilder(
      future: context.read<LibraryProvider>().search(query),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        
        final results = snapshot.data ?? [];
        
        if (results.isEmpty) {
          return Center(
            child: Text('No results found for "$query"'),
          );
        }
        
        return ListView.builder(
          itemCount: results.length,
          itemBuilder: (context, index) {
            final item = results[index];
            return ListTile(
              leading: const Icon(Icons.music_note),
              title: Text(item.title),
              subtitle: Text('${item.artist} - ${item.album}'),
              onTap: () {
                close(context, item.path);
                context.read<PlayerProvider>().playMedia(
                  item,
                  playlist: results,
                );
              },
            );
          },
        );
      },
    );
  }
}
