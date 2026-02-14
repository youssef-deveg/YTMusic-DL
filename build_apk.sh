#!/bin/bash
# Build script for YouTube Music Downloader Android APK

echo "====================================="
echo "YouTube Music Downloader APK Builder"
echo "====================================="

# Check if flet is installed
if ! command -v flet &> /dev/null; then
    echo "Flet is not installed. Installing..."
    pip install flet
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/

# Build APK
echo "Building APK..."
flet build apk --verbose

# Check if build succeeded
if [ $? -eq 0 ]; then
    echo ""
    echo "====================================="
    echo "Build successful!"
    echo "====================================="
    echo ""
    echo "APK location: build/apk/"
    ls -lh build/apk/
    echo ""
    echo "To install on device:"
    echo "  adb install build/apk/app-release.apk"
else
    echo ""
    echo "====================================="
    echo "Build failed!"
    echo "====================================="
    exit 1
fi
