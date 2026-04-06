#!/usr/bin/env bash
# 3DPrintVoice Uninstaller
set -euo pipefail

APP_NAME="3d-print-voice"
INSTALL_DIR="/opt/$APP_NAME"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor"
CONFIG_DIR="$HOME/.config/$APP_NAME"

echo "==================================="
echo "  3DPrintVoice Uninstaller"
echo "==================================="
echo ""

read -p "Remove 3DPrintVoice? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

if [ -d "$INSTALL_DIR" ]; then
    echo "[uninstall] Removing $INSTALL_DIR..."
    sudo rm -rf "$INSTALL_DIR"
fi

if [ -f "$DESKTOP_DIR/$APP_NAME.desktop" ]; then
    echo "[uninstall] Removing desktop launcher..."
    rm "$DESKTOP_DIR/$APP_NAME.desktop"
fi

for size in 48x48 256x256; do
    rm -f "$ICON_DIR/$size/apps/$APP_NAME.png"
done
gtk-update-icon-cache "$ICON_DIR" 2>/dev/null || true

if [ -d "$CONFIG_DIR" ]; then
    read -p "Also remove settings in $CONFIG_DIR? [y/N] " rm_config
    if [[ "$rm_config" =~ ^[Yy]$ ]]; then
        rm -rf "$CONFIG_DIR"
        echo "[uninstall] Settings removed."
    else
        echo "[uninstall] Settings kept."
    fi
fi

echo ""
echo "3DPrintVoice has been uninstalled."
