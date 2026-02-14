# GitHub Actions Workflow Documentation

## Workflows Overview

This repository includes several GitHub Actions workflows for automated building, testing, and releasing.

## Workflows

### 1. Build Android APK (`build-android.yml`)
**File:** `.github/workflows/build-android.yml`

**Triggers:**
- Push to `main` or `master` branches
- Tag push (e.g., `v1.0.0`)
- Pull requests to `main` or `master`
- Manual workflow dispatch

**Purpose:**
Builds the Android APK from the Flet application.

**Features:**
- Builds debug and release APKs
- Automatically generates version numbers
- Creates SHA256 checksums
- Uploads artifacts
- Supports Android API 21-34 (Android 5.0 to 14)

**Android Configuration:**
- Package name: `com.exapps.ytdownload`
- Minimum SDK: 21 (Android 5.0)
- Target SDK: 34 (Android 14)
- All necessary permissions included

### 2. Release APK (`release.yml`)
**File:** `.github/workflows/release.yml`

**Triggers:**
- Tag push matching `v*.*.*`
- Manual workflow dispatch

**Purpose:**
Creates a GitHub Release with the built APK.

**Features:**
- Automatically creates GitHub Releases
- Generates release notes
- Includes checksums
- Attaches APK to release

### 3. Test and Lint (`test.yml`)
**File:** `.github/workflows/test.yml`

**Triggers:**
- Push to `main`, `master`, or `develop`
- Pull requests

**Purpose:**
Ensures code quality before building.

**Features:**
- Tests Python 3.8-3.12
- Runs flake8 linting
- Checks code formatting with black
- Verifies imports
- Optional type checking with mypy

### 4. Dependency Cache (`cache-deps.yml`)
**File:** `.github/workflows/cache-deps.yml`

**Triggers:**
- Changes to `requirements.txt` or `pyproject.toml`
- Manual dispatch

**Purpose:**
Caches Python dependencies for faster builds.

## Build Configuration

### Environment Variables

```yaml
PYTHON_VERSION: '3.11'      # Python version for builds
FLUTTER_VERSION: '3.19.0'   # Flutter SDK version
JAVA_VERSION: '17'          # Java JDK version
ANDROID_COMPILE_SDK: '34'   # Android compile SDK
ANDROID_TARGET_SDK: '34'    # Android target SDK
ANDROID_MIN_SDK: '21'       # Android minimum SDK
```

### APK Build Process

1. **Checkout Code**
   - Uses `actions/checkout@v4`
   - Fetches full git history

2. **Setup Environment**
   - Python 3.11
   - Java JDK 17
   - Flutter 3.19.0
   - Android SDK 34

3. **Install Dependencies**
   - Upgrade pip
   - Install flet
   - Install requirements.txt

4. **Build APK**
   - Uses `flet build apk` command
   - Configures with pyproject.toml
   - Sets package name and permissions
   - Generates version from git tags

5. **Upload Artifacts**
   - Uploads APK to workflow artifacts
   - Creates checksums
   - Available for 30 days

## Required Secrets

No secrets are required for basic builds. For signed release builds:

- `ANDROID_KEY_ALIAS` - Key alias for signing
- `ANDROID_KEY_PASSWORD` - Key password
- `ANDROID_STORE_FILE` - Base64 encoded keystore
- `ANDROID_STORE_PASSWORD` - Keystore password

## Permissions

The workflows require these permissions:

```yaml
permissions:
  contents: write  # For creating releases
  actions: read    # For accessing workflow info
```

## Build Outputs

### APK Location
```
build/apk/
├── app-release.apk      # Release build
├── app-debug.apk        # Debug build
└── ...
```

### Release Assets
```
release/
├── YT-Music-Downloader-v1.0.0.apk
├── YT-Music-Downloader-v1.0.0.apk.sha256
└── checksums.txt
```

## Troubleshooting

### Build Failures

1. **Android SDK not found**
   - Ensure `ANDROID_HOME` or `ANDROID_SDK_ROOT` is set
   - Check that build-tools are installed

2. **Java version mismatch**
   - Requires Java 17
   - Check with `java -version`

3. **Dependency errors**
   - Clear pip cache
   - Update `requirements.txt`

4. **Flet build errors**
   - Ensure `pyproject.toml` is properly configured
   - Check that `main.py` exists

### Debug Builds

For debug builds with more output:
```bash
flet build apk --verbose --build-version "1.0.0-debug"
```

## Android Permissions

The APK requests these permissions:

- `INTERNET` - Download audio from YouTube
- `ACCESS_NETWORK_STATE` - Check network connectivity
- `ACCESS_WIFI_STATE` - WiFi detection for data saver
- `WRITE_EXTERNAL_STORAGE` - Save downloaded files
- `READ_EXTERNAL_STORAGE` - Access downloaded files
- `MANAGE_EXTERNAL_STORAGE` - Full storage access (Android 11+)
- `FOREGROUND_SERVICE` - Background downloads
- `POST_NOTIFICATIONS` - Download progress notifications
- `WAKE_LOCK` - Prevent sleep during downloads
- `READ_MEDIA_AUDIO/IMAGES/VIDEO` - Media access (Android 13+)

## Compatibility

### Android Versions
- **Minimum:** Android 5.0 (API 21)
- **Target:** Android 14 (API 34)
- **Tested:** Android 10, 11, 12, 13, 14

### Screen Sizes
- Small phones (320dp)
- Normal phones (360dp+)
- Large tablets (600dp+)
- Extra large tablets (720dp+)

## Performance Tips

1. **Enable caching**
   - Dependencies are cached between runs
   - Flutter SDK is cached

2. **Use matrix builds**
   - Test multiple Python versions
   - Build different configurations

3. **Artifact retention**
   - APKs kept for 30 days
   - Build logs kept for 7 days (on failure)

## Customization

### Change Package Name
Edit `pyproject.toml`:
```toml
[tool.flet.android]
package = "com.yourcompany.yourapp"
```

### Change App Name
Edit `pyproject.toml`:
```toml
[project]
name = "Your App Name"
```

### Add More Permissions
Edit `pyproject.toml`:
```toml
[tool.flet.android]
permissions = [
    "android.permission.INTERNET",
    # Add more permissions here
]
```

## Support

For issues with GitHub Actions:
1. Check workflow logs in Actions tab
2. Review error messages
3. Verify all environment variables
4. Test locally with `act` tool

For Flet build issues:
1. Check [Flet documentation](https://flet.dev/docs/)
2. Review build output logs
3. Test locally with `flet build apk --verbose`
