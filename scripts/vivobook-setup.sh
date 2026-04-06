#!/usr/bin/env bash
# ============================================
# 3DPrintVoice — Vivobook One-Time Setup
# ============================================
# Transfer this file to Vivobook via USB stick.
# Then run: bash vivobook-setup.sh
# It does EVERYTHING — SSH keys, folders, repo clone, VPS connection.
# ============================================

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "==========================================="
echo "  3DPrintVoice — Vivobook Setup"
echo "==========================================="
echo ""

# --- 1. SSH key ---
echo -e "${YELLOW}[1/6] SSH Key${NC}"
if [ -f "$HOME/.ssh/id_ed25519" ]; then
    echo -e "${GREEN}SSH key exists.${NC}"
else
    echo "Creating SSH key (just press Enter 3 times)..."
    ssh-keygen -t ed25519 -C "vivobook" -f "$HOME/.ssh/id_ed25519"
fi

echo ""
echo "========================================================"
echo -e "${YELLOW}ACTION REQUIRED:${NC} Copy the key below and add it to GitHub."
echo "Open this URL on any device: https://github.com/settings/ssh/new"
echo "Title: vivobook"
echo "Key:"
echo "========================================================"
cat "$HOME/.ssh/id_ed25519.pub"
echo "========================================================"
echo ""
read -p "Press Enter AFTER you added the key to GitHub..."

# --- 2. Test GitHub ---
echo -e "${YELLOW}[2/6] Testing GitHub connection${NC}"
if ssh -o StrictHostKeyChecking=accept-new -T git@github.com 2>&1 | grep -qi "success\|hi "; then
    echo -e "${GREEN}GitHub OK.${NC}"
else
    echo -e "${RED}GitHub connection failed. Check the key was added correctly.${NC}"
    echo "Try again later: ssh -T git@github.com"
fi

# --- 3. Clone repo ---
echo -e "${YELLOW}[3/6] Cloning repository${NC}"
if [ -d "$HOME/3d-print-voice" ]; then
    echo "Repo already exists, pulling latest..."
    cd "$HOME/3d-print-voice" && git pull origin main
else
    git clone git@github.com:RolandMJ/blender-ai.git "$HOME/3d-print-voice"
fi

# --- 4. Copy scripts and create folders ---
echo -e "${YELLOW}[4/6] Setting up scripts and folders${NC}"
cp "$HOME/3d-print-voice/scripts/vivobook-push.sh" "$HOME/"
cp "$HOME/3d-print-voice/scripts/vivobook-watch.sh" "$HOME/"
chmod +x "$HOME/vivobook-push.sh" "$HOME/vivobook-watch.sh"
mkdir -p "$HOME/3dprintvoice-designs/outbox"
mkdir -p "$HOME/3dprintvoice-designs/sent"
echo -e "${GREEN}Scripts and folders ready.${NC}"

# --- 5. VPS SSH setup ---
echo -e "${YELLOW}[5/6] Setting up VPS connection${NC}"
echo "Adding SSH key to VPS (enter VPS password if prompted)..."
ssh-copy-id -o StrictHostKeyChecking=accept-new user@your-vps-ip 2>/dev/null || true

echo -n "Testing VPS connection... "
if ssh -o ConnectTimeout=10 user@your-vps-ip "echo OK" 2>/dev/null; then
    echo -e "${GREEN}VPS OK.${NC}"
    # Create VPS folder structure
    ssh user@your-vps-ip "mkdir -p /home/user/3dprintvoice-designs/{active,archive}"
    echo -e "${GREEN}VPS folders created.${NC}"
else
    echo -e "${RED}VPS connection failed.${NC}"
    echo "You may need to run: ssh-copy-id user@your-vps-ip"
fi

# --- 6. Install optional tools ---
echo -e "${YELLOW}[6/6] Optional tools${NC}"
if command -v inotifywait &>/dev/null; then
    echo -e "${GREEN}inotify-tools already installed.${NC}"
else
    read -p "Install inotify-tools for auto-watch mode? [y/N] " yn
    if [[ "$yn" =~ ^[Yy]$ ]]; then
        sudo apt install -y inotify-tools
    fi
fi

echo ""
echo "==========================================="
echo -e "${GREEN}  Setup complete!${NC}"
echo "==========================================="
echo ""
echo "HOW TO USE:"
echo ""
echo "  1. Design in FreeCAD"
echo "  2. Export STL to: ~/3dprintvoice-designs/outbox/"
echo "  3. Push to VPS:"
echo "     ~/vivobook-push.sh LEG THIGH R \"description\""
echo ""
echo "  Or start auto-watch:"
echo "     ~/vivobook-watch.sh"
echo ""
echo "  Then on desktop: press F4 (SYNC) in 3DPrintVoice."
echo ""
