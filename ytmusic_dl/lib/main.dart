import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import 'core/theme/app_theme.dart';
import 'presentation/providers/player_provider.dart';
import 'presentation/providers/library_provider.dart';
import 'presentation/providers/settings_provider.dart';
import 'presentation/screens/main_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Set preferred orientations
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);
  
  // Initialize providers
  final settingsProvider = SettingsProvider();
  await settingsProvider.initialize();
  
  final libraryProvider = LibraryProvider();
  await libraryProvider.initialize();
  
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider.value(value: settingsProvider),
        ChangeNotifierProvider.value(value: libraryProvider),
        ChangeNotifierProvider(create: (_) => PlayerProvider()),
      ],
      child: const YTMusicApp(),
    ),
  );
}

class YTMusicApp extends StatelessWidget {
  const YTMusicApp({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<SettingsProvider>(
      builder: (context, settings, _) {
        return MaterialApp(
          title: 'YTMusic DL',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.lightTheme,
          darkTheme: AppTheme.darkTheme,
          themeMode: settings.themeMode,
          home: const MainScreen(),
        );
      },
    );
  }
}
