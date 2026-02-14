#!/bin/bash
# Build script for YT Music Downloader
# Works on Linux, macOS, and can be adapted for Windows

set -e  # Exit on error

echo "====================================="
echo "YT Music Downloader - Build Script"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="YT Music Downloader"
PACKAGE_NAME="com.exapps.ytdownload"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$PROJECT_DIR/build"
RELEASE_DIR="$PROJECT_DIR/release"

# Parse arguments
BUILD_TYPE="release"
CLEAN=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --debug)
            BUILD_TYPE="debug"
            shift
            ;;
        --release)
            BUILD_TYPE="release"
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --debug       Build debug APK (default: release)"
            echo "  --release     Build release APK"
            echo "  --clean       Clean build directory before building"
            echo "  --verbose     Enable verbose output"
            echo "  --help        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo ""
echo "Configuration:"
echo "  Build Type: $BUILD_TYPE"
echo "  Clean Build: $CLEAN"
echo "  Verbose: $VERBOSE"
echo ""

# Clean build directory if requested
if [ "$CLEAN" = true ]; then
    echo -e "${YELLOW}Cleaning build directory...${NC}"
    rm -rf "$BUILD_DIR"
    rm -rf "$RELEASE_DIR"
    echo -e "${GREEN}✓ Clean complete${NC}"
fi

# Check Python installation
echo ""
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Check if running in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "${GREEN}✓ Running in virtual environment: $VIRTUAL_ENV${NC}"
else
    echo -e "${YELLOW}! Not running in a virtual environment${NC}"
    echo "  Consider creating one: python3 -m venv venv"
fi

# Install/update dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install flet
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Verify flet installation
echo ""
echo "Verifying Flet installation..."
if ! command -v flet &> /dev/null; then
    echo -e "${RED}✗ Flet is not installed properly${NC}"
    exit 1
fi

FLET_VERSION=$(flet --version 2>&1)
echo -e "${GREEN}✓ Flet $FLET_VERSION found${NC}"

# Check Java installation (required for Android builds)
echo ""
echo "Checking Java installation..."
if ! command -v java &> /dev/null; then
    echo -e "${RED}✗ Java is not installed${NC}"
    echo "  Please install Java JDK 17 or higher"
    echo "  Ubuntu/Debian: sudo apt install openjdk-17-jdk"
    echo "  macOS: brew install openjdk@17"
    exit 1
fi

JAVA_VERSION=$(java -version 2>&1 | awk -F '"' '/version/ {print $2}')
echo -e "${GREEN}✓ Java $JAVA_VERSION found${NC}"

# Check Android SDK
echo ""
echo "Checking Android SDK..."
if [ -z "$ANDROID_HOME" ] && [ -z "$ANDROID_SDK_ROOT" ]; then
    echo -e "${YELLOW}! Android SDK not found in environment variables${NC}"
    echo "  Please set ANDROID_HOME or ANDROID_SDK_ROOT"
    
    # Try to find common Android SDK locations
    if [ -d "$HOME/Android/Sdk" ]; then
        export ANDROID_HOME="$HOME/Android/Sdk"
        echo -e "${GREEN}✓ Found Android SDK at: $ANDROID_HOME${NC}"
    elif [ -d "/usr/lib/android-sdk" ]; then
        export ANDROID_HOME="/usr/lib/android-sdk"
        echo -e "${GREEN}✓ Found Android SDK at: $ANDROID_HOME${NC}"
    else
        echo -e "${RED}✗ Cannot find Android SDK${NC}"
        echo "  Please install Android SDK or set ANDROID_HOME"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Android SDK found${NC}"
fi

# Build the APK
echo ""
echo "====================================="
echo "Building $BUILD_TYPE APK..."
echo "====================================="
echo ""

mkdir -p "$RELEASE_DIR"

# Prepare build arguments
BUILD_ARGS=""

if [ "$VERBOSE" = true ]; then
    BUILD_ARGS="$BUILD_ARGS --verbose"
fi

# Get version from git or use default
if command -v git &> /dev/null && [ -d ".git" ]; then
    VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "1.0.0")
    BUILD_NUMBER=$(git rev-list --count HEAD 2>/dev/null || echo "1")
else
    VERSION="1.0.0"
    BUILD_NUMBER="1"
fi

echo "Build Information:"
echo "  Version: $VERSION"
echo "  Build Number: $BUILD_NUMBER"
echo "  Package: $PACKAGE_NAME"
echo ""

# Run Flet build
echo "Starting Flet build process..."
echo ""

cd "$PROJECT_DIR"

# Build APK
flet build apk \
    $BUILD_ARGS \
    --project "YT-Music-Downloader" \
    --product "$APP_NAME" \
    --company "ExApps" \
    --copyright "Copyright (c) 2024 ExApps" \
    --build-version "$VERSION" \
    --build-number "$BUILD_NUMBER" \
    --module "main"

# Check build result
echo ""
echo "Checking build output..."

if [ -d "$BUILD_DIR/apk" ]; then
    echo -e "${GREEN}✓ Build directory exists${NC}"
    ls -la "$BUILD_DIR/apk/"
    
    # Find and copy APK
    APK_FILE=$(find "$BUILD_DIR/apk" -name "*.apk" -type f | head -1)
    
    if [ -n "$APK_FILE" ]; then
        APK_BASENAME=$(basename "$APK_FILE")
        OUTPUT_NAME="YT-Music-Downloader-v${VERSION}-${BUILD_TYPE}.apk"
        
        cp "$APK_FILE" "$RELEASE_DIR/$OUTPUT_NAME"
        echo -e "${GREEN}✓ APK copied to: $RELEASE_DIR/$OUTPUT_NAME${NC}"
        
        # Get file size
        FILE_SIZE=$(du -h "$RELEASE_DIR/$OUTPUT_NAME" | cut -f1)
        echo -e "${GREEN}✓ File size: $FILE_SIZE${NC}"
        
        # Generate checksums
        cd "$RELEASE_DIR"
        sha256sum "$OUTPUT_NAME" > "${OUTPUT_NAME}.sha256"
        md5sum "$OUTPUT_NAME" > "${OUTPUT_NAME}.md5"
        echo -e "${GREEN}✓ Checksums generated${NC}"
        
    else
        echo -e "${RED}✗ No APK file found in build output${NC}"
        echo "  Build directory contents:"
        find "$BUILD_DIR" -type f
        exit 1
    fi
else
    echo -e "${RED}✗ Build directory not found${NC}"
    echo "  Contents of project directory:"
    ls -la "$PROJECT_DIR"
    exit 1
fi

# Success message
echo ""
echo "====================================="
echo -e "${GREEN}Build Successful!${NC}"
echo "====================================="
echo ""
echo "Output Files:"
echo "  APK: $RELEASE_DIR/$OUTPUT_NAME"
echo "  SHA256: $RELEASE_DIR/${OUTPUT_NAME}.sha256"
echo "  MD5: $RELEASE_DIR/${OUTPUT_NAME}.md5"
echo ""
echo "Next Steps:"
echo "  1. Install on device: adb install $RELEASE_DIR/$OUTPUT_NAME"
echo "  2. Or manually transfer to Android device"
echo ""
echo "Package Info:"
echo "  Name: $APP_NAME"
echo "  Package: $PACKAGE_NAME"
echo "  Version: $VERSION"
echo "  Build: $BUILD_NUMBER"
echo ""
