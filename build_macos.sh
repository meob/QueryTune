#!/bin/bash

# Build script for QueryTune macOS Application

APP_NAME="QueryTune"
MAIN_SCRIPT="main.py"
ICON_FILE="assets/QTune.icns" # User provided icon

echo "--- Starting Build Process for $APP_NAME ---"

# 1. Clean previous builds
echo "Cleaning old build files..."
rm -rf build dist

# 2. Check for icon
if [ ! -f "$ICON_FILE" ]; then
    echo "Warning: Icon file $ICON_FILE not found. Using default Python icon."
    ICON_ARG=""
else
    ICON_ARG="--icon=$ICON_FILE"
fi

# 3. Run PyInstaller
echo "Running PyInstaller..."
pyinstaller --noconfirm --onedir --windowed \
    $ICON_ARG \
    --add-data "assets:assets" \
    --add-data "$(python3 -c 'import customtkinter; print(customtkinter.__path__[0])'):customtkinter" \
    --name "$APP_NAME" \
    "$MAIN_SCRIPT"

echo "--- Build Finished ---"
echo "The application can be found in dist/$APP_NAME.app"

# 4. Create DMG (requires 'create-dmg' installed via brew)
if command -v create-dmg &> /dev/null; then
    echo "Creating DMG..."
    
    # Prepare a clean source folder for DMG
    DMG_SOURCE="dist/dmg_source"
    mkdir -p "$DMG_SOURCE"
    cp -r "dist/$APP_NAME.app" "$DMG_SOURCE/"

    mkdir -p dist/dmg
    create-dmg \
        --volname "$APP_NAME Installer" \
        --window-pos 200 120 \
        --window-size 800 400 \
        --icon-size 100 \
        --icon "$APP_NAME.app" 200 190 \
        --hide-extension "$APP_NAME.app" \
        --app-drop-link 600 185 \
        "dist/$APP_NAME.dmg" \
        "$DMG_SOURCE/"
    
    echo "DMG created: dist/$APP_NAME.dmg"
    
    # Cleanup source folder
    rm -rf "$DMG_SOURCE"
else
    echo "Info: 'create-dmg' not found. Skipping DMG creation."
    echo "To install it: brew install create-dmg"
fi
