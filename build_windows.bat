@echo off
REM Build script for YT Music Downloader (Windows)
REM Works on Windows 10/11 with PowerShell

echo =====================================
echo YT Music Downloader - Build Script
echo =====================================
echo.

REM Configuration
set APP_NAME=YT Music Downloader
set PACKAGE_NAME=com.exapps.ytdownload
set BUILD_TYPE=release
set CLEAN=false
set VERBOSE=false

REM Parse arguments
:parse_args
if "%~1"=="" goto :done_parsing
if "%~1"=="--debug" (
    set BUILD_TYPE=debug
    shift
    goto :parse_args
)
if "%~1"=="--release" (
    set BUILD_TYPE=release
    shift
    goto :parse_args
)
if "%~1"=="--clean" (
    set CLEAN=true
    shift
    goto :parse_args
)
if "%~1"=="--verbose" (
    set VERBOSE=true
    shift
    goto :parse_args
)
if "%~1"=="--help" (
    echo Usage: %0 [OPTIONS]
    echo.
    echo Options:
    echo   --debug       Build debug APK ^(default: release^)
    echo   --release     Build release APK
    echo   --clean       Clean build directory before building
    echo   --verbose     Enable verbose output
    echo   --help        Show this help message
    exit /b 0
)
shift
goto :parse_args
:done_parsing

echo Configuration:
echo   Build Type: %BUILD_TYPE%
echo   Clean Build: %CLEAN%
echo   Verbose: %VERBOSE%
echo.

REM Get script directory
set PROJECT_DIR=%~dp0
set BUILD_DIR=%PROJECT_DIR%build
set RELEASE_DIR=%PROJECT_DIR%release

REM Clean build directory if requested
if "%CLEAN%"=="true" (
    echo Cleaning build directory...
    if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
    if exist "%RELEASE_DIR%" rmdir /s /q "%RELEASE_DIR%"
    echo [OK] Clean complete
)

REM Check Python installation
echo.
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% found

REM Check if running in virtual environment
if defined VIRTUAL_ENV (
    echo [OK] Running in virtual environment: %VIRTUAL_ENV%
) else (
    echo [!] Not running in a virtual environment
    echo     Consider creating one: python -m venv venv
)

REM Install dependencies
echo.
echo Installing dependencies...
python -m pip install --upgrade pip
pip install flet
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    exit /b 1
)
echo [OK] Dependencies installed

REM Verify flet installation
echo.
echo Verifying Flet installation...
flet --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Flet is not installed properly
    exit /b 1
)
for /f %%i in ('flet --version 2^>^&1') do set FLET_VERSION=%%i
echo [OK] Flet %FLET_VERSION% found

REM Check Java installation
echo.
echo Checking Java installation...
java -version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Java is not installed
    echo     Please install Java JDK 17 or higher
    exit /b 1
)
echo [OK] Java found

REM Check Android SDK
echo.
echo Checking Android SDK...
if defined ANDROID_HOME (
    echo [OK] Android SDK found at: %ANDROID_HOME%
) else if defined ANDROID_SDK_ROOT (
    echo [OK] Android SDK found at: %ANDROID_SDK_ROOT%
    set ANDROID_HOME=%ANDROID_SDK_ROOT%
) else (
    echo [!] Android SDK not found in environment variables
    
    REM Check common locations
    if exist "%LOCALAPPDATA%\Android\Sdk" (
        set ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk
        echo [OK] Found Android SDK at: %ANDROID_HOME%
    ) else if exist "%USERPROFILE%\AppData\Local\Android\Sdk" (
        set ANDROID_HOME=%USERPROFILE%\AppData\Local\Android\Sdk
        echo [OK] Found Android SDK at: %ANDROID_HOME%
    ) else (
        echo [ERROR] Cannot find Android SDK
        echo     Please install Android Studio or set ANDROID_HOME
        exit /b 1
    )
)

REM Build the APK
echo.
echo =====================================
echo Building %BUILD_TYPE% APK...
echo =====================================
echo.

if not exist "%RELEASE_DIR%" mkdir "%RELEASE_DIR%"

REM Get version from git or use default
git describe --tags --always >nul 2>&1
if not errorlevel 1 (
    for /f %%i in ('git describe --tags --always 2^>nul') do set VERSION=%%i
    for /f %%i in ('git rev-list --count HEAD 2^>nul') do set BUILD_NUMBER=%%i
) else (
    set VERSION=1.0.0
    set BUILD_NUMBER=1
)

echo Build Information:
echo   Version: %VERSION%
echo   Build Number: %BUILD_NUMBER%
echo   Package: %PACKAGE_NAME%
echo.

REM Prepare build arguments
set BUILD_ARGS=
if "%VERBOSE%"=="true" set BUILD_ARGS=--verbose

REM Run Flet build
echo Starting Flet build process...
echo.

cd /d "%PROJECT_DIR%"

flet build apk ^
    %BUILD_ARGS% ^
    --project "YT-Music-Downloader" ^
    --product "%APP_NAME%" ^
    --company "ExApps" ^
    --copyright "Copyright (c) 2024 ExApps" ^
    --build-version "%VERSION%" ^
    --build-number %BUILD_NUMBER% ^
    --module "main"

if errorlevel 1 (
    echo [ERROR] Build failed
    exit /b 1
)

REM Check build result
echo.
echo Checking build output...

if exist "%BUILD_DIR%\apk" (
    echo [OK] Build directory exists
    dir "%BUILD_DIR%\apk\