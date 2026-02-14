@echo off
REM Build script for YouTube Music Downloader Android APK (Windows)

echo =====================================
echo YouTube Music Downloader APK Builder
echo =====================================
echo.

REM Check if flet is installed
flet --version >nul 2>&1
if errorlevel 1 (
    echo Flet is not installed. Installing...
    pip install flet
)

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build

REM Build APK
echo Building APK...
flet build apk --verbose

REM Check if build succeeded
if %errorlevel% == 0 (
    echo.
    echo =====================================
    echo Build successful!
    echo =====================================
    echo.
    echo APK location: build\apk\
    dir /b build\apk\
    echo.
    echo To install on device:
    echo   adb install build\apk\app-release.apk
) else (
    echo.
    echo =====================================
    echo Build failed!
    echo =====================================
    exit /b 1
)

pause
