#!/usr/bin/env bash
# 3DPrintVoice — Vivobook Design Push Script
#
# Run this on your laptop after designing in FreeCAD.
# It pushes STL exports to the VPS with proper versioning.
#
# Setup (one-time on Vivobook):
#   1. Copy this script: scp scripts/vivobook-push.sh vivobook:~/
#   2. Make executable: chmod +x ~/vivobook-push.sh
#   3. Set up SSH key: ssh-copy-id user@your-vps-ip
#   4. Create FreeCAD export folder: mkdir -p ~/3dprintvoice-designs/outbox
#
# Usage:
#   ./vivobook-push.sh LEG THIGH R "Initial rough shape from footprint sketch"
#   ./vivobook-push.sh ARM UPPER L "Added shoulder socket mount point"
#   ./vivobook-push.sh TORSO CHEST C "Front chest plate basic form"
#
# FreeCAD workflow:
#   1. Design your part in FreeCAD
#   2. Export as STL: File > Export > select STL
#   3. Save to: ~/3dprintvoice-designs/outbox/
#   4. Run this script with part info
#   5. The script versions it and pushes to VPS

set -euo pipefail

VPS="user@your-vps-ip"
VPS_BASE="/home/user/3dprintvoice-designs"
VPS_ACTIVE="$VPS_BASE/active"
VPS_MANIFEST="$VPS_BASE/manifest.json"
LOCAL_OUTBOX="$HOME/3dprintvoice-designs/outbox"
LOCAL_SENT="$HOME/3dprintvoice-designs/sent"
SIZE_LIMIT_MB=5120

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# --- Args ---
if [ $# -lt 3 ]; then
    echo -e "${YELLOW}Usage:${NC} $0 REGION PART SIDE [\"notes\"]"
    echo ""
    echo "  REGION: HEAD, TORSO, ARM, LEG, HAND, FOOT, JOINT, PANEL, FRAME, CONNECTOR"
    echo "  PART:   descriptive name (THIGH, UPPER, CHEST, KNEE, etc.)"
    echo "  SIDE:   L (left), R (right), C (center)"
    echo "  notes:  optional description of this iteration"
    echo ""
    echo "Example:"
    echo "  $0 LEG THIGH R \"Initial shape from FreeCAD footprint sketch\""
    echo ""
    echo "FreeCAD STL files should be in: $LOCAL_OUTBOX/"
    exit 1
fi

REGION="${1^^}"  # uppercase
PART="${2^^}"
SIDE="${3^^}"
NOTES="${4:-FreeCAD export}"
PART_KEY="${REGION}_${PART}_${SIDE}"
DATE=$(date +%Y%m%d)
TIMESTAMP=$(date -Iseconds)

# --- Check outbox ---
mkdir -p "$LOCAL_OUTBOX" "$LOCAL_SENT"

STL_FILES=("$LOCAL_OUTBOX"/*.stl "$LOCAL_OUTBOX"/*.STL)
# Filter to only existing files
FOUND_FILES=()
for f in "${STL_FILES[@]}"; do
    [ -f "$f" ] && FOUND_FILES+=("$f")
done

if [ ${#FOUND_FILES[@]} -eq 0 ]; then
    echo -e "${RED}No STL files found in $LOCAL_OUTBOX/${NC}"
    echo "Export your FreeCAD design as STL to that folder first."
    exit 1
fi

if [ ${#FOUND_FILES[@]} -gt 1 ]; then
    echo -e "${YELLOW}Multiple STL files found. Select one:${NC}"
    select f in "${FOUND_FILES[@]}"; do
        [ -n "$f" ] && break
    done
    SOURCE_FILE="$f"
else
    SOURCE_FILE="${FOUND_FILES[0]}"
fi

echo -e "${GREEN}Source:${NC} $SOURCE_FILE"

# --- Check VPS connectivity ---
echo -n "Checking VPS connection... "
if ! ssh -o ConnectTimeout=5 "$VPS" "true" 2>/dev/null; then
    echo -e "${RED}FAILED${NC}"
    echo "Cannot reach VPS at $VPS. Check network and SSH key."
    exit 1
fi
echo -e "${GREEN}OK${NC}"

# --- Ensure VPS structure ---
ssh "$VPS" "mkdir -p $VPS_ACTIVE $VPS_BASE/archive"

# --- Check storage ---
USED_MB=$(ssh "$VPS" "du -sm $VPS_BASE 2>/dev/null | cut -f1" || echo "0")
echo "VPS storage: ${USED_MB}MB / ${SIZE_LIMIT_MB}MB"
if [ "$USED_MB" -gt "$SIZE_LIMIT_MB" ]; then
    echo -e "${RED}VPS storage full! Archive old drafts before pushing.${NC}"
    exit 1
fi

# --- Get next version from manifest ---
VERSION=$(ssh "$VPS" "
if [ -f $VPS_MANIFEST ]; then
    python3 -c \"
import json, sys
try:
    m = json.load(open('$VPS_MANIFEST'))
    parts = m.get('parts', {})
    key = '$PART_KEY'
    if key in parts:
        versions = parts[key].get('versions', [])
        print(max(v['version'] for v in versions) + 1 if versions else 1)
    else:
        print(1)
except:
    print(1)
\" 2>/dev/null
else
    echo 1
fi
")
VERSION=${VERSION:-1}

FILENAME="${PART_KEY}_DRAFT_v$(printf '%03d' "$VERSION")_${DATE}.stl"
echo -e "${GREEN}Version:${NC} v$(printf '%03d' "$VERSION") → ${FILENAME}"

# --- Push file ---
echo -n "Pushing to VPS... "
scp -O -q "$SOURCE_FILE" "$VPS:$VPS_ACTIVE/$FILENAME"
echo -e "${GREEN}OK${NC}"

# --- Update manifest on VPS ---
ssh "$VPS" "python3 -c \"
import json, os
manifest_path = '$VPS_MANIFEST'
if os.path.exists(manifest_path):
    with open(manifest_path) as f:
        m = json.load(f)
else:
    m = {'project': 'articulated-figure-01', 'author': 'Roland Preisach',
         'created': '$TIMESTAMP', 'parts': {}}

if 'parts' not in m:
    m['parts'] = {}
key = '$PART_KEY'
if key not in m['parts']:
    m['parts'][key] = {'versions': [], 'current_version': 0, 'current_status': 'DRAFT'}

m['parts'][key]['versions'].append({
    'version': $VERSION,
    'status': 'DRAFT',
    'date': '$TIMESTAMP',
    'source': 'freecad',
    'file': '$FILENAME',
    'notes': '$NOTES'
})
m['parts'][key]['current_version'] = $VERSION
m['parts'][key]['current_status'] = 'DRAFT'
m['last_updated'] = '$TIMESTAMP'

with open(manifest_path, 'w') as f:
    json.dump(m, f, indent=2)
print('Manifest updated')
\""

# --- Move source to sent folder ---
mv "$SOURCE_FILE" "$LOCAL_SENT/$(basename "$SOURCE_FILE")"

echo ""
echo -e "${GREEN}=== Push complete ===${NC}"
echo "  Part:    $PART_KEY"
echo "  Version: v$(printf '%03d' "$VERSION")"
echo "  Status:  DRAFT"
echo "  File:    $FILENAME"
echo "  Notes:   $NOTES"
echo "  Storage: ${USED_MB}MB / ${SIZE_LIMIT_MB}MB"
echo ""
echo "On your desktop, click SYNC or press F4 to pull this design into Blender."
