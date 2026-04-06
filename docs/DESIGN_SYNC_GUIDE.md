# Design Sync Guide — FreeCAD to Blender Workflow

## Overview

Design rough structural parts in FreeCAD on your laptop (Vivobook), push to VPS,
then import into Blender on your desktop (ROG Strix) for detailing with 3DPrintVoice.
Every iteration is versioned and tracked with timestamps for IP documentation.

## Architecture

```
Vivobook (FreeCAD)          VPS (your-vps-ip)           Desktop (3DPrintVoice)
    │                            │                            │
    ├─ Design in FreeCAD         │                            │
    ├─ Export STL to outbox/     │                            │
    ├─ vivobook-push.sh ───────►│ active/                    │
    │                            │ manifest.json              │
    │                            │◄────── SYNC button (F4) ──┤
    │                            │                            ├─ Import into Blender
    │                            │                            ├─ Detail with voice
    │                            │◄──── "save iteration" ────┤
    │                            │ new version auto-created   │
```

## One-Time Setup

### On the VPS (run once from desktop)

```bash
ssh user@your-vps-ip "mkdir -p /home/user/3dprintvoice-designs/{active,archive}"
```

### On the Vivobook (laptop)

1. Copy the push scripts:

```bash
# From your desktop, send scripts to Vivobook
scp scripts/vivobook-push.sh scripts/vivobook-watch.sh vivobook:~/
```

2. On the Vivobook, make executable and create folders:

```bash
chmod +x ~/vivobook-push.sh ~/vivobook-watch.sh
mkdir -p ~/3dprintvoice-designs/{outbox,sent}
```

3. Set up SSH key to VPS (if not already):

```bash
ssh-copy-id user@your-vps-ip
```

4. Install inotify-tools (for auto-watch mode):

```bash
sudo apt install inotify-tools
```

### On the Desktop (ROG Strix)

No extra setup needed. The SYNC button (F4) in 3DPrintVoice handles everything.

## Daily Workflow

### Step 1: Design in FreeCAD (Vivobook)

1. Open FreeCAD
2. Design your part using parametric tools (sketches, pads, pockets, fillets)
3. Export as STL:
   - Select part in model tree
   - File > Export
   - Format: STL Mesh (*.stl)
   - Save to: `~/3dprintvoice-designs/outbox/`
   - Use any filename (the push script renames it)

### Step 2: Push to VPS

**Option A: Manual push (recommended when starting)**

```bash
./vivobook-push.sh LEG THIGH R "Initial rough shape from footprint sketch"
```

**Option B: Auto-watch (for rapid iteration)**

```bash
./vivobook-watch.sh &
# Now every STL saved to outbox/ triggers a push prompt
```

### Step 3: Import into Blender (Desktop)

1. Click **SYNC** button (or press F4) in 3DPrintVoice
2. Status shows "Pulled X design files from VPS"
3. Say or type: **"import LEG_THIGH_R"**
   - Tool finds latest version in sync folder
   - Imports STL into Blender
   - Auto-cleans mesh (remove doubles, tris-to-quads, recalculate normals)
   - Applies naming convention

### Step 4: Detail in Blender

Use 3DPrintVoice voice/text commands:
- "add ball-and-socket joint at top"
- "engrave panel lines"
- "add M4 rod channel through center"
- "round edges 1mm"

### Step 5: Save Iteration

Say: **"save iteration"** or type it
- Exports current state as STL
- Bumps version number (v001 → v002)
- Pushes to VPS with timestamp
- Updates manifest with notes

### Step 6: Evaluate in PrusaSlicer

Click **SLICE** (F3) to send to PrusaSlicer for print evaluation.

### Step 7: Mark as Final

Say: **"mark LEG THIGH R as final"**
- Creates a FINAL version
- Manifest records approval timestamp

### Step 8: Reopen if Needed

Say: **"reopen LEG THIGH R for changes"**
- Creates new DRAFT version from latest FINAL
- Back to iteration cycle

## Naming Convention

```
{REGION}_{PART}_{SIDE}_{STATUS}_v{VERSION}_{DATE}.stl
```

**Regions:** HEAD, TORSO, ARM, LEG, HAND, FOOT, JOINT, PANEL, FRAME, CONNECTOR, ACCESSORY

**Statuses:** DRAFT → REVIEW → FINAL → PRINTED

**Examples:**
```
LEG_THIGH_R_DRAFT_v001_20260406.stl    ← first from FreeCAD
LEG_THIGH_R_DRAFT_v002_20260406.stl    ← after Blender detailing
LEG_THIGH_R_FINAL_v003_20260407.stl    ← approved for print
LEG_THIGH_R_DRAFT_v004_20260408.stl    ← reopened for changes
```

## Storage Management

- **Limit:** 5GB on VPS
- **Warning:** at 4GB
- **Archive:** old DRAFT versions auto-compressed (`.stl.gz`)
- **Kept uncompressed:** all FINAL versions + latest DRAFT per part
- **Cleanup command:** say "archive old drafts" to compress old iterations

## IP Documentation Trail

The `manifest.json` on VPS serves as legal evidence of authorship:

- Every version includes: timestamp, author, source tool, notes
- Git history on VPS provides additional timestamped proof
- Design decisions documented in notes field
- Full version chain shows original development progression

**Best practice:** Always add descriptive notes when pushing:
```bash
./vivobook-push.sh LEG SHIN R "Shin guard shape — 3mm wall, based on calf circumference measurement"
```

## FreeCAD Export Settings

For best results when importing into Blender:

1. **Mesh quality:** In FreeCAD export dialog:
   - Surface deviation: 0.1mm (good balance of quality vs file size)
   - Angular deviation: 10 degrees

2. **Scale:** FreeCAD defaults to mm. Blender import handles conversion.

3. **One part per file:** Export each body/part as a separate STL.

4. **Apply all operations:** Make sure all FreeCAD operations (pads, pockets,
   fillets) are computed before export. Check for errors in the model tree.
