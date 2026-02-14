# YouTube Music Downloader

[![Build Android APK](https://github.com/20Youssef10/YT-DL/actions/workflows/build-android.yml/badge.svg)](https://github.com/20Youssef10/YT-DL/actions/workflows/build-android.yml)
[![Release](https://github.com/20Youssef10/YT-DL/actions/workflows/release.yml/badge.svg)](https://github.com/20Youssef10/YT-DL/releases)
[![Tests](https://github.com/20Youssef10/YT-DL/actions/workflows/test.yml/badge.svg)](https://github.com/20Youssef10/YT-DL/actions/workflows/test.yml)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Flet](https://img.shields.io/badge/Built%20with-Flet-00B4AB?logo=flutter)](https://flet.dev)

A complete, feature-rich YouTube Music Downloader application built with Flet (Flutter for Python) and yt-dlp. Download music, songs, albums, and playlists from YouTube with ease.

## 📱 Download APK

Get the latest APK from GitHub Releases:

**[⬇️ Download Latest APK](https://github.com/20Youssef10/YT-DL/releases/latest)**

### APK Information
- **Package Name:** `com.exapps.ytdownload`
- **App Name:** YT Music Downloader
- **Minimum Android:** 5.0 (API 21)
- **Target Android:** 14 (API 34)

## ✨ Features

### Core Features
- 🔍 Search YouTube Music via YouTube Data API v3
- 🖼️ Display search results with thumbnails, titles, channels, and duration
- 🎵 Select audio quality (Opus 160kbps, MP3 320kbps, FLAC, AAC/M4A 256kbps)
- 📥 Download queue with progress tracking
- ⚡ Sequential and parallel downloads (up to 5 concurrent)
- 📋 Full playlist support
- 📜 Download history
- 🌙 Dark theme by default with responsive design

### Advanced Features
1. **Parallel Downloads** - Download up to 5 files simultaneously
2. **Playlist Support** - Download entire playlists with one click
3. **Download All** - Add all search results to queue at once
4. **Settings Page** - Customize download path, quality, theme, and more
5. **Persistent Settings** - Settings saved across sessions
6. **Subtitles/Lyrics** - Download and embed subtitles when available
7. **Audio Preview** - Preview tracks before downloading
8. **Sort Results** - Sort by relevance, views, date, or rating
9. **Advanced Filters** - Filter by duration and video type
10. **Download History** - Track all downloaded files
11. **Retry Failed** - Automatically or manually retry failed downloads
12. **System Notifications** - Get notified when downloads complete
13. **Data Saver Mode** - Download only on WiFi
14. **YouTube Shorts Support** - Download Shorts as audio
15. **Custom Filenames** - Use templates like "{artist} - {title}"
16. **Metadata Embedding** - Full metadata and thumbnail embedding
17. **SponsorBlock** - Remove sponsors, intros, and outros
18. **Queue Export/Import** - Save and load download queues
19. **Auto-update yt-dlp** - Keep yt-dlp up to date
20. **Background Downloads** - Downloads continue when app is minimized

## 📁 Project Structure

```
Youtube Music Downloader/
├── main.py              # Application entry point
├── config.py            # Configuration and constants
├── settings.py          # Settings management
├── search.py            # YouTube API search
├── downloader.py        # yt-dlp download logic
├── queue_manager.py     # Download queue management
├── ui.py                # Flet UI components
├── utils.py             # Utility functions
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Flet build configuration
├── build.sh             # Linux/macOS build script
├── build_windows.bat    # Windows build script
├── .github/
│   └── workflows/
│       ├── build-android.yml  # GitHub Actions build
│       ├── release.yml        # GitHub Actions release
│       └── test.yml           # GitHub Actions tests
└── README.md            # This file
```

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Step 1: Install Dependencies

```bash
cd "/storage/emulated/0/Python Projects/Youtube Music Downloader"
pip install -r requirements.txt
```

### Step 2: Run the Application

```bash
python main.py
```

The application will open in a desktop window.

## 📦 Building Android APK

### Option 1: GitHub Actions (Recommended)

The easiest way to build the APK is using GitHub Actions:

1. Fork this repository
2. Push a tag: `git tag v1.0.0 && git push origin v1.0.0`
3. GitHub Actions will automatically build and release the APK
4. Download from the [Releases](https://github.com/20Youssef10/YT-DL/releases) page

### Option 2: Local Build

#### Prerequisites
- Flet CLI: `pip install flet`
- Android SDK
- Java JDK 17+

#### Build Commands

**Linux/macOS:**
```bash
./build.sh --release
```

**Windows:**
```bash
build_windows.bat --release
```

**Manual:**
```bash
flet build apk --release
```

The APK will be generated in the `build/apk` directory.

### Build Options

```bash
# Build debug APK
./build.sh --debug

# Build release APK
./build.sh --release

# Clean build
./build.sh --clean --release

# Verbose output
./build.sh --verbose --release
```

### Install on Android

```bash
# Install via ADB
adb install build/apk/app-release.apk

# Or transfer the APK to your device and install manually
```

## ⚙️ Configuration

### YouTube API Key
The application uses YouTube Data API v3 for searching. The API key is already configured in `config.py`:

```python
YOUTUBE_API_KEY = "AIzaSyBcoHE4l3UtUTS9EjcrmHHMluDWxhREPzE"
```

**Note:** For production use, consider using your own API key to avoid rate limits.

### Customizing Build Settings

Edit `pyproject.toml` to customize the app:

```toml
[project]
name = "YT-Music-Downloader"
version = "1.0.0"

[tool.flet]
product = "YT Music Downloader"
company = "ExApps"

[tool.flet.android]
package = "com.exapps.ytdownload"
min_sdk_version = 21
target_sdk_version = 34
```

### Android Permissions

The APK includes these permissions:
- `INTERNET` - Download audio
- `ACCESS_NETWORK_STATE` - Check connectivity
- `WRITE_EXTERNAL_STORAGE` - Save files
- `POST_NOTIFICATIONS` - Show progress
- `FOREGROUND_SERVICE` - Background downloads

## 📖 Usage

### Search and Download
1. Open the Search tab
2. Enter a song name, artist, or paste a YouTube URL
3. Click Search
4. Select quality from dropdown
5. Click "Add to Queue" or "Download All Results"

### Download Playlists
1. Click "Add Playlist" button
2. Paste YouTube playlist URL
3. Select quality
4. All videos will be added to queue automatically

### Manage Queue
1. Switch to Queue tab
2. View download progress for each item
3. Cancel, retry, or remove items as needed
4. Export queue to save for later

### Settings
1. Go to Settings tab or click Settings icon
2. Change download location, default quality, theme
3. Enable/disable features like SponsorBlock, metadata embedding
4. Customize filename templates

### Download History
1. Open History tab
2. View all previously downloaded files
3. Play files directly from app
4. Clear history when needed

## ⌨️ Keyboard Shortcuts

- **Enter** - Submit search
- **Ctrl+Q** - Quit application
- **Ctrl+S** - Open settings

## 🔧 Troubleshooting

### Download Failed
- Check internet connection
- Verify YouTube video is available
- Try different quality setting
- Check if download path has write permissions

### API Rate Limit
YouTube API has quota limits. If you hit the limit:
- Wait a few minutes before searching again
- Use direct video URLs instead of search
- Consider using your own API key

### APK Build Fails
- Ensure Java JDK 17+ is installed
- Check Android SDK is properly configured
- Run `flet doctor` to diagnose issues
- Check GitHub Actions logs for CI/CD issues

### No Audio Output
- Check system volume
- Verify audio file downloaded correctly
- Try playing file in external player

## 🚀 GitHub Actions Workflows

This repository includes automated CI/CD pipelines:

### Build Android APK
- **Trigger:** Push to main, tags, or manual
- **Output:** Signed APK uploaded to artifacts
- **File:** `.github/workflows/build-android.yml`

### Release APK
- **Trigger:** Tag push (v*.*.*)
- **Output:** GitHub Release with APK
- **File:** `.github/workflows/release.yml`

### Test and Lint
- **Trigger:** Pull requests, push to main
- **Checks:** Python syntax, imports, formatting
- **File:** `.github/workflows/test.yml`

### Workflow Documentation
See `.github/workflows/README.md` for detailed workflow documentation.

## 👨‍💻 Development

### Adding New Features

1. **Add new setting:**
   - Add to `DEFAULT_SETTINGS` in `config.py`
   - Add UI control in `ui.py` SettingsDialog
   - Handle in `main.py` event handlers

2. **Add new download option:**
   - Extend `AudioDownloader.get_ydl_options()` in `downloader.py`
   - Add toggle in settings

3. **Add new search filter:**
   - Add to `config.py` filter lists
   - Add dropdown in UI
   - Pass to `YouTubeSearcher.search()` in `search.py`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Note:** This project is for educational purposes. Respect YouTube's Terms of Service and copyright laws when using this application.

## 🙏 Credits

- [Flet](https://flet.dev/) - Flutter for Python
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Media downloader
- [YouTube Data API](https://developers.google.com/youtube/v3) - Search functionality
- [Flutter](https://flutter.dev/) - UI framework

## 📧 Support

For issues, questions, or contributions:
- [GitHub Issues](https://github.com/20Youssef10/YT-DL/issues)
- [GitHub Discussions](https://github.com/20Youssef10/YT-DL/discussions)

## 📊 Project Stats

![GitHub stars](https://img.shields.io/github/stars/20Youssef10/YT-DL?style=social)
![GitHub forks](https://img.shields.io/github/forks/20Youssef10/YT-DL?style=social)
![GitHub issues](https://img.shields.io/github/issues/20Youssef10/YT-DL)
![GitHub pull requests](https://img.shields.io/github/issues-pr/20Youssef10/YT-DL)

---

**Happy Downloading! 🎵**

<p align="center">
  Made with ❤️ using <a href="https://flet.dev">Flet</a>
</p>
