#!/usr/bin/env bash
# 3DPrintVoice Installer — installs to /opt and creates desktop entry
set -euo pipefail

APP_NAME="3d-print-voice"
INSTALL_DIR="/opt/$APP_NAME"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==================================="
echo "  3DPrintVoice Installer"
echo "==================================="
echo ""
echo "This will:"
echo "  - Install to $INSTALL_DIR"
echo "  - Create a Python virtual environment for dependencies"
echo "  - Add a desktop launcher to your application menu"
echo ""
read -p "Continue? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Check python3
if ! command -v python3 &>/dev/null; then
    echo "[install] ERROR: python3 is not installed."
    echo "  Install with: sudo apt install python3 python3-venv python3-tk"
    exit 1
fi

# Check python3-venv
if ! python3 -m venv --help &>/dev/null 2>&1; then
    echo "[install] ERROR: python3-venv is not installed."
    echo "  Install with: sudo apt install python3-venv"
    exit 1
fi

# Check tkinter
if ! python3 -c "import tkinter" &>/dev/null 2>&1; then
    echo "[install] ERROR: python3-tk is not installed."
    echo "  Install with: sudo apt install python3-tk"
    exit 1
fi

# Install app files
echo "[install] Copying files to $INSTALL_DIR..."
sudo mkdir -p "$INSTALL_DIR"
sudo cp -r "$SOURCE_DIR/agent" "$INSTALL_DIR/"
sudo cp -r "$SOURCE_DIR/addon" "$INSTALL_DIR/"
sudo cp -r "$SOURCE_DIR/prompts" "$INSTALL_DIR/"
sudo cp -r "$SOURCE_DIR/assets" "$INSTALL_DIR/"
sudo cp "$SOURCE_DIR/launcher.sh" "$INSTALL_DIR/"
sudo cp "$SOURCE_DIR/requirements.txt" "$INSTALL_DIR/"
sudo cp "$SOURCE_DIR/LICENSE" "$INSTALL_DIR/"
sudo chmod +x "$INSTALL_DIR/launcher.sh"

# Fix ownership so Python can write __pycache__
sudo chown -R "$USER:$USER" "$INSTALL_DIR"

# Create venv and install dependencies
echo "[install] Creating Python virtual environment..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"
echo "[install] Dependencies installed."

# Install desktop entry
echo "[install] Creating desktop launcher..."
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/$APP_NAME.desktop" << DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=3DPrintVoice
Comment=Voice & text command interface for 3D-printable objects in Blender
Exec=bash -c '$INSTALL_DIR/launcher.sh'
Icon=$APP_NAME
Terminal=false
Categories=Graphics;3DGraphics;Engineering;
Keywords=blender;3d;printing;voice;modeling;
StartupNotify=true
DESKTOP
chmod +x "$DESKTOP_DIR/$APP_NAME.desktop"

# Install icons
if [ -f "$SOURCE_DIR/assets/icon-48.png" ]; then
    mkdir -p "$ICON_DIR/48x48/apps"
    cp "$SOURCE_DIR/assets/icon-48.png" "$ICON_DIR/48x48/apps/$APP_NAME.png"
fi
if [ -f "$SOURCE_DIR/assets/icon-256.png" ]; then
    mkdir -p "$ICON_DIR/256x256/apps"
    cp "$SOURCE_DIR/assets/icon-256.png" "$ICON_DIR/256x256/apps/$APP_NAME.png"
fi
gtk-update-icon-cache "$ICON_DIR" 2>/dev/null || true

echo ""
echo "==================================="
echo "  Installation complete!"
echo "==================================="
echo ""
echo "Launch from:"
echo "  - Application menu -> Graphics -> 3DPrintVoice"
echo "  - Terminal: $INSTALL_DIR/launcher.sh"
echo ""
echo "First launch will guide you through setup."
