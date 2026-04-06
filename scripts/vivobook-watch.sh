#!/usr/bin/env bash
# 3DPrintVoice — Auto-watch FreeCAD export folder
#
# Runs in background. When a new STL appears in the outbox,
# prompts for part info and pushes to VPS automatically.
#
# Usage:
#   ./vivobook-watch.sh &
#
# Stop:
#   kill %1  (or close terminal)
#
# Requires: inotifywait (sudo apt install inotify-tools)

set -euo pipefail

OUTBOX="$HOME/3dprintvoice-designs/outbox"
PUSH_SCRIPT="$(dirname "$0")/vivobook-push.sh"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

mkdir -p "$OUTBOX"

if ! command -v inotifywait &>/dev/null; then
    echo "Install inotify-tools: sudo apt install inotify-tools"
    exit 1
fi

echo -e "${GREEN}Watching $OUTBOX for new STL files...${NC}"
echo "Save FreeCAD exports here. Auto-push on detection."
echo ""

inotifywait -m -e close_write --format '%f' "$OUTBOX" | while read -r FILE; do
    # Only process STL files
    if [[ "${FILE,,}" == *.stl ]]; then
        echo ""
        echo -e "${YELLOW}New file detected: $FILE${NC}"
        echo "Enter part info for versioned push:"
        read -p "  Region (HEAD/TORSO/ARM/LEG/HAND/FOOT/JOINT/PANEL/FRAME): " REGION
        read -p "  Part name (THIGH/UPPER/CHEST/etc.): " PART
        read -p "  Side (L/R/C): " SIDE
        read -p "  Notes: " NOTES

        "$PUSH_SCRIPT" "$REGION" "$PART" "$SIDE" "$NOTES"
    fi
done
