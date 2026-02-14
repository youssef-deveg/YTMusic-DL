import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/settings_provider.dart';
import '../../core/constants/app_constants.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: Consumer<SettingsProvider>(
        builder: (context, settings, _) {
          return ListView(
            children: [
              _buildSection(
                'Appearance',
                [
                  ListTile(
                    leading: const Icon(Icons.dark_mode),
                    title: const Text('Theme'),
                    subtitle: Text(_getThemeName(settings.themeMode)),
                    onTap: () => _showThemeDialog(context, settings),
                  ),
                ],
              ),
              
              _buildSection(
                'Audio',
                [
                  ListTile(
                    leading: const Icon(Icons.equalizer),
                    title: const Text('Equalizer'),
                    subtitle: Text(settings.equalizerPreset),
                    onTap: () => _showEqualizer(context),
                  ),
                  ListTile(
                    leading: const Icon(Icons.volume_up),
                    title: const Text('Bass Boost'),
                    subtitle: Slider(
                      value: settings.bassBoost,
                      onChanged: (value) => settings.setBassBoost(value),
                    ),
                  ),
                  ListTile(
                    leading: const Icon(Icons.surround_sound),
                    title: const Text('Virtualizer'),
                    subtitle: Slider(
                      value: settings.virtualizer,
                      onChanged: (value) => settings.setVirtualizer(value),
                    ),
                  ),
                  SwitchListTile(
                    secondary: const Icon(Icons.tune),
                    title: const Text('Volume Normalization'),
                    value: settings.volumeNormalization,
                    onChanged: (value) => settings.setVolumeNormalization(value),
                  ),
                  ListTile(
                    leading: const Icon(Icons.swap_horiz),
                    title: const Text('Crossfade'),
                    subtitle: Text('${settings.crossfadeDuration} seconds'),
                    onTap: () => _showCrossfadeDialog(context, settings),
                  ),
                ],
              ),
              
              _buildSection(
                'Playback',
                [
                  ListTile(
                    leading: const Icon(Icons.speed),
                    title: const Text('Default Playback Speed'),
                    subtitle: const Text('1.0x'),
                    onTap: () {},
                  ),
                  SwitchListTile(
                    secondary: const Icon(Icons.replay),
                    title: const Text('Remember Playback Position'),
                    value: true,
                    onChanged: (value) {},
                  ),
                ],
              ),
              
              _buildSection(
                'Library',
                [
                  ListTile(
                    leading: const Icon(Icons.folder),
                    title: const Text('Scan Folders'),
                    subtitle: const Text('Choose folders to scan'),
                    onTap: () {},
                  ),
                  ListTile(
                    leading: const Icon(Icons.refresh),
                    title: const Text('Rescan Library'),
                    onTap: () {},
                  ),
                ],
              ),
              
              _buildSection(
                'About',
                [
                  const ListTile(
                    leading: Icon(Icons.info),
                    title: Text('Version'),
                    subtitle: Text(AppConstants.appVersion),
                  ),
                  ListTile(
                    leading: const Icon(Icons.privacy_tip),
                    title: const Text('Privacy Policy'),
                    onTap: () {},
                  ),
                ],
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildSection(String title, List<Widget> children) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Text(
            title,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: Colors.grey,
            ),
          ),
        ),
        ...children,
        const Divider(),
      ],
    );
  }

  String _getThemeName(ThemeMode mode) {
    switch (mode) {
      case ThemeMode.light:
        return 'Light';
      case ThemeMode.dark:
        return 'Dark';
      case ThemeMode.system:
        return 'System';
    }
  }

  void _showThemeDialog(BuildContext context, SettingsProvider settings) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Theme'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: ThemeMode.values.map((mode) {
            return ListTile(
              title: Text(_getThemeName(mode)),
              trailing: settings.themeMode == mode
                  ? const Icon(Icons.check)
                  : null,
              onTap: () {
                settings.setThemeMode(mode);
                Navigator.pop(context);
              },
            );
          }).toList(),
        ),
      ),
    );
  }

  void _showEqualizer(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => const EqualizerSheet(),
    );
  }

  void _showCrossfadeDialog(BuildContext context, SettingsProvider settings) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Crossfade Duration'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: AppConstants.crossfadeDurations.map((seconds) {
            return ListTile(
              title: Text(seconds == 0 ? 'Off' : '$seconds seconds'),
              trailing: settings.crossfadeDuration == seconds
                  ? const Icon(Icons.check)
                  : null,
              onTap: () {
                settings.setCrossfadeDuration(seconds);
                Navigator.pop(context);
              },
            );
          }).toList(),
        ),
      ),
    );
  }
}

class EqualizerSheet extends StatelessWidget {
  const EqualizerSheet({super.key});

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.6,
      minChildSize: 0.4,
      maxChildSize: 0.9,
      expand: false,
      builder: (context, scrollController) {
        return Consumer<SettingsProvider>(
          builder: (context, settings, _) {
            return Container(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Equalizer',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close),
                        onPressed: () => Navigator.pop(context),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  
                  // Presets
                  DropdownButton<String>(
                    value: settings.equalizerPreset,
                    isExpanded: true,
                    items: settings.equalizerPresetNames.map((preset) {
                      return DropdownMenuItem(
                        value: preset,
                        child: Text(preset),
                      );
                    }).toList(),
                    onChanged: (value) {
                      if (value != null) {
                        settings.setEqualizerPreset(value);
                      }
                    },
                  ),
                  
                  const SizedBox(height: 24),
                  
                  // Band sliders
                  Expanded(
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: List.generate(10, (index) {
                        final frequencies = [
                          '32', '64', '125', '250', '500',
                          '1K', '2K', '4K', '8K', '16K'
                        ];
                        return Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(
                              '${settings.equalizerBands[index].toInt()}',
                              style: const TextStyle(fontSize: 10),
                            ),
                            Expanded(
                              child: RotatedBox(
                                quarterTurns: 3,
                                child: Slider(
                                  value: settings.equalizerBands[index],
                                  min: -12,
                                  max: 12,
                                  onChanged: (value) {
                                    settings.setEqualizerBand(index, value);
                                  },
                                ),
                              ),
                            ),
                            Text(
                              frequencies[index],
                              style: const TextStyle(fontSize: 10),
                            ),
                          ],
                        );
                      }),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }
}
