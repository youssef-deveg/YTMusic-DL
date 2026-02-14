import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/constants/app_constants.dart';

class SettingsProvider extends ChangeNotifier {
  static const String _themeKey = 'theme_mode';
  static const String _equalizerPresetKey = 'equalizer_preset';
  static const String _equalizerBandsKey = 'equalizer_bands';
  static const String _bassBoostKey = 'bass_boost';
  static const String _virtualizerKey = 'virtualizer';
  static const String _crossfadeKey = 'crossfade_duration';
  static const String _sleepTimerKey = 'sleep_timer';
  static const String _volumeNormalizationKey = 'volume_normalization';
  static const String _lastFolderKey = 'last_folder';
  
  late SharedPreferences _prefs;
  
  ThemeMode _themeMode = ThemeMode.dark;
  String _equalizerPreset = 'Normal';
  List<double> _equalizerBands = List.filled(10, 0.0);
  double _bassBoost = 0.0;
  double _virtualizer = 0.0;
  int _crossfadeDuration = 0;
  int? _sleepTimerMinutes;
  bool _volumeNormalization = false;
  String? _lastFolder;
  
  // Getters
  ThemeMode get themeMode => _themeMode;
  String get equalizerPreset => _equalizerPreset;
  List<double> get equalizerBands => _equalizerBands;
  double get bassBoost => _bassBoost;
  double get virtualizer => _virtualizer;
  int get crossfadeDuration => _crossfadeDuration;
  int? get sleepTimerMinutes => _sleepTimerMinutes;
  bool get volumeNormalization => _volumeNormalization;
  String? get lastFolder => _lastFolder;
  
  List<String> get equalizerPresetNames => AppConstants.equalizerPresets.keys.toList();
  
  Future<void> initialize() async {
    _prefs = await SharedPreferences.getInstance();
    _loadSettings();
  }
  
  void _loadSettings() {
    final themeModeIndex = _prefs.getInt(_themeKey) ?? 2;
    _themeMode = ThemeMode.values[themeModeIndex];
    
    _equalizerPreset = _prefs.getString(_equalizerPresetKey) ?? 'Normal';
    
    final bandsString = _prefs.getString(_equalizerBandsKey);
    if (bandsString != null) {
      _equalizerBands = bandsString.split(',').map((e) => double.parse(e)).toList();
    }
    
    _bassBoost = _prefs.getDouble(_bassBoostKey) ?? 0.0;
    _virtualizer = _prefs.getDouble(_virtualizerKey) ?? 0.0;
    _crossfadeDuration = _prefs.getInt(_crossfadeKey) ?? 0;
    _sleepTimerMinutes = _prefs.getInt(_sleepTimerKey);
    _volumeNormalization = _prefs.getBool(_volumeNormalizationKey) ?? false;
    _lastFolder = _prefs.getString(_lastFolderKey);
    
    notifyListeners();
  }
  
  Future<void> setThemeMode(ThemeMode mode) async {
    _themeMode = mode;
    await _prefs.setInt(_themeKey, mode.index);
    notifyListeners();
  }
  
  Future<void> setEqualizerPreset(String preset) async {
    _equalizerPreset = preset;
    _equalizerBands = List.from(AppConstants.equalizerPresets[preset] ?? List.filled(10, 0.0));
    await _prefs.setString(_equalizerPresetKey, preset);
    await _prefs.setString(_equalizerBandsKey, _equalizerBands.join(','));
    notifyListeners();
  }
  
  Future<void> setEqualizerBand(int index, double value) async {
    if (index >= 0 && index < _equalizerBands.length) {
      _equalizerBands[index] = value.clamp(-12.0, 12.0);
      await _prefs.setString(_equalizerBandsKey, _equalizerBands.join(','));
      notifyListeners();
    }
  }
  
  Future<void> setBassBoost(double value) async {
    _bassBoost = value.clamp(0.0, 1.0);
    await _prefs.setDouble(_bassBoostKey, _bassBoost);
    notifyListeners();
  }
  
  Future<void> setVirtualizer(double value) async {
    _virtualizer = value.clamp(0.0, 1.0);
    await _prefs.setDouble(_virtualizerKey, _virtualizer);
    notifyListeners();
  }
  
  Future<void> setCrossfadeDuration(int seconds) async {
    _crossfadeDuration = seconds.clamp(0, 10);
    await _prefs.setInt(_crossfadeKey, _crossfadeDuration);
    notifyListeners();
  }
  
  Future<void> setSleepTimer(int? minutes) async {
    _sleepTimerMinutes = minutes;
    if (minutes != null) {
      await _prefs.setInt(_sleepTimerKey, minutes);
    } else {
      await _prefs.remove(_sleepTimerKey);
    }
    notifyListeners();
  }
  
  Future<void> setVolumeNormalization(bool enabled) async {
    _volumeNormalization = enabled;
    await _prefs.setBool(_volumeNormalizationKey, enabled);
    notifyListeners();
  }
  
  Future<void> setLastFolder(String? path) async {
    _lastFolder = path;
    if (path != null) {
      await _prefs.setString(_lastFolderKey, path);
    } else {
      await _prefs.remove(_lastFolderKey);
    }
    notifyListeners();
  }
  
  void clearSleepTimer() {
    _sleepTimerMinutes = null;
    _prefs.remove(_sleepTimerKey);
    notifyListeners();
  }
}
