# 3DPrintVoice Packaging, Rename & First-Launch Setup — Implementation Plan (v2)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rename project to 3DPrintVoice, add GPL-3.0 license, create a first-launch wizard (splash + system check + model selection), make it installable on Linux Mint with a desktop entry, and wire the model tier config through the launcher and LLM client.

**Architecture:** The launcher is split into two stages: a thin shell wrapper that starts the Python app (with PYTHONPATH set), and the Python app handles ALL prerequisite checks via GUI (no silent failures). First-launch wizard is a multi-screen tkinter dialog (same Blender dark theme). Config persisted to `~/.config/3d-print-voice/config.json`. Install script creates a venv in `/opt/3d-print-voice/venv/`. Model name flows from config → launcher.sh (pull/warmup) → llm_client.py (API calls).

**Tech Stack:** Python 3.11+, tkinter, bash, nvidia-smi, venv, standard Linux desktop integration (XDG .desktop files)

**Critical Design Decisions (from audit):**
1. **launcher.sh restructured** — wizard runs BEFORE Ollama/Blender startup, not after
2. **Terminal=false works** — all errors shown via tkinter dialogs, not stdout
3. **venv isolation** — pip installs into `/opt/3d-print-voice/venv/`, not system Python
4. **Version canonical source** — `agent/__init__.py` holds `__version__`
5. **All 15+ files with "BlenderAI" renamed** — exhaustive list below

---

### Task 0: Commit uncommitted work

The 3D print toggle button changes from the previous session (addon/ai_bridge.py, agent/app.py) are uncommitted.

**Step 1: Commit current changes**

```bash
git add agent/app.py addon/ai_bridge.py
git commit -m "feat: add 3D print mode toggle button + addon result passthrough"
```

---

### Task 1: Add canonical version to agent/__init__.py

**Files:**
- Modify: `agent/__init__.py`

**Step 1: Add version**

```python
# agent/__init__.py
__version__ = "0.4.0"
```

**Step 2: Commit**

```bash
git add agent/__init__.py
git commit -m "chore: add canonical __version__ to agent package"
```

---

### Task 2: Rename project — ALL occurrences

**Files to modify (exhaustive list):**
- `agent/app.py:2` (docstring), `:62` (window title)
- `agent/main.py:2` (docstring), `:83` (print statement)
- `addon/ai_bridge.py:6` (`"author": "BlenderAI"` → `"author": "3DPrintVoice"`)
- `launcher.sh` (~15 instances of `[BlenderAI]` log prefix)
- `README.md:1` (title), `:27` (reference)
- `CLAUDE.md:1` (project title)
- `docs/CHANGELOG.md:3` (title)
- `docs/SETUP_GUIDE.md:1,3,19,133,158,176` (6 occurrences)
- `docs/DEVELOPMENT_LOG.md:1,3` (title + reference)
- `docs/COMMAND_CHEATSHEET.md:1,166` (title + reference)
- `docs/GITHUB_SETUP.md:1` (title)
- `docs/PROJECT_OVERVIEW.md:1,10` (title + references)
- `docs/architecture.svg:24` (text in diagram)
- `docs/IP_NOTICE.md` (multiple references)

**Files to rename:**
- `blender-ai.desktop` → `3d-print-voice.desktop`

**Step 1: Global rename in all files**

Replace "BlenderAI" with "3DPrintVoice" as display name. Replace "blender-ai" with "3d-print-voice" in identifiers/paths. Do NOT change references to "Blender" (the software) or "AI Bridge" (the addon name in bl_info — keep that as the Blender addon display name).

Files to be careful with:
- `addon/ai_bridge.py`: change `"author"` field only, keep `"name": "AI Bridge"` — that's the addon name users see in Blender
- `docs/architecture.svg`: update the text label, preserve the SVG structure
- `launcher.sh`: `[BlenderAI]` → `[3DPrintVoice]` in all echo statements
- `agent/main.py:83`: `"BlenderAI — local mode..."` → `"3DPrintVoice — local mode..."`

**Step 2: Rename desktop file**

```bash
git mv blender-ai.desktop 3d-print-voice.desktop
```

**Step 3: Update desktop entry contents**

```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=3DPrintVoice
Comment=Voice & text command interface for 3D-printable objects in Blender
Exec=bash -c '/opt/3d-print-voice/launcher.sh'
Icon=3d-print-voice
Terminal=false
Categories=Graphics;3DGraphics;Engineering;
Keywords=blender;3d;printing;voice;modeling;
StartupNotify=true
```

**Step 4: Update docs/SETUP_GUIDE.md path references**

Replace `~/Documents/Claude\ Projects/blender-ai` with `/opt/3d-print-voice` throughout. Replace `blender-ai.desktop` with `3d-print-voice.desktop`. Update model name references to note they are configurable.

**Step 5: Commit**

```bash
git add -A
git commit -m "rename: BlenderAI → 3DPrintVoice across all files"
```

---

### Task 3: Add GPL-3.0 license

**Files:**
- Create: `LICENSE`
- Modify: `docs/IP_NOTICE.md` (replace proprietary notice with GPL-3.0)
- Modify: `README.md` (update license section)

**Step 1: Create LICENSE file**

Write the full GPL-3.0 license text. Source from https://www.gnu.org/licenses/gpl-3.0.txt (the standard text). Use `WebFetch` to get the exact text.

**Step 2: Update IP_NOTICE.md**

Replace lines 3-9 (the "Copyright" section with "proprietary" and "Unauthorized copying" language) with:

```markdown
## Copyright & License

Copyright (c) 2026 Roland Preisach.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see <https://www.gnu.org/licenses/>.
```

Also update the "What This Covers" section — remove the word "proprietary." The items covered are still valid (they're copyrighted under GPL-3.0, just not proprietary).

**Step 3: Update README.md license section**

```markdown
## License

GPL-3.0 — free to use, modify, and distribute. See [LICENSE](LICENSE) and [docs/IP_NOTICE.md](docs/IP_NOTICE.md).
```

**Step 4: Commit**

```bash
git add LICENSE docs/IP_NOTICE.md README.md
git commit -m "license: switch from proprietary to GPL-3.0"
```

---

### Task 4: Create app icon

**Files:**
- Create: `assets/icon.svg`
- Create: `assets/icon-48.png`
- Create: `assets/icon-256.png`

**Step 1: Create assets directory and SVG**

```bash
mkdir -p assets
```

Create `assets/icon.svg` with a simple design: dark rounded square background (#2D2D2D), a 3D cube wireframe in orange (#E87D0D), and a microphone silhouette in white. Use only basic SVG elements (rect, path, polygon) — no external fonts or images.

The SVG should be a valid 256x256 viewBox.

**Step 2: Render PNGs**

Try in order of availability:
1. `rsvg-convert` (from `librsvg2-bin`, common on Mint)
2. `inkscape --export-filename` (if Inkscape installed)
3. Python `cairosvg` library
4. If none available: create PNGs directly using Python PIL/Pillow with basic shapes

```bash
# Install rsvg-convert if missing (it's in librsvg2-bin, standard on Mint)
which rsvg-convert || sudo apt-get install -y librsvg2-bin

rsvg-convert -w 48 -h 48 assets/icon.svg -o assets/icon-48.png
rsvg-convert -w 256 -h 256 assets/icon.svg -o assets/icon-256.png
```

Verify the PNGs exist and are valid:
```bash
file assets/icon-48.png assets/icon-256.png
```

**Step 3: Commit**

```bash
git add assets/
git commit -m "feat: add app icon (SVG + PNG renders)"
```

---

### Task 5: Create config module

**Files:**
- Create: `agent/config.py`
- Create: `tests/test_config.py`

**Step 1: Write tests**

```python
# tests/test_config.py
"""Tests for config module."""
import json
from unittest.mock import patch
from agent.config import load_config, save_config, DEFAULT_CONFIG


class TestConfig:
    def test_default_config_has_required_keys(self):
        assert "model" in DEFAULT_CONFIG
        assert "first_run_done" in DEFAULT_CONFIG
        assert DEFAULT_CONFIG["first_run_done"] is False

    def test_load_returns_defaults_when_no_file(self, tmp_path):
        with patch("agent.config.CONFIG_FILE", tmp_path / "nonexistent.json"):
            cfg = load_config()
            assert cfg["first_run_done"] is False
            assert cfg["model"] == "qwen2.5-coder:14b-instruct"

    def test_save_and_load_roundtrip(self, tmp_path):
        config_file = tmp_path / "config.json"
        with patch("agent.config.CONFIG_DIR", tmp_path), \
             patch("agent.config.CONFIG_FILE", config_file):
            save_config({"model": "qwen2.5-coder:7b-instruct", "first_run_done": True})
            cfg = load_config()
            assert cfg["model"] == "qwen2.5-coder:7b-instruct"
            assert cfg["first_run_done"] is True
```

**Step 2: Run tests — expect failure**

```bash
pytest tests/test_config.py -v
```

**Step 3: Implement config.py**

```python
# agent/config.py
"""Config management — ~/.config/3d-print-voice/config.json."""
import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "3d-print-voice"
CONFIG_FILE = CONFIG_DIR / "config.json"

MODEL_TIERS = {
    "full":   "qwen2.5-coder:14b-instruct",
    "medium": "qwen2.5-coder:7b-instruct",
    "lite":   "qwen2.5-coder:3b-instruct",
}

DEFAULT_CONFIG = {
    "model": "qwen2.5-coder:14b-instruct",
    "model_tier": "full",
    "first_run_done": False,
}


def load_config() -> dict:
    """Load config, returning defaults if missing or corrupt."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    """Save config to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
```

Note: No `chmod 600` — this file contains a model name string and a boolean. No secrets.

**Step 4: Run tests — expect pass**

```bash
pytest tests/test_config.py -v
```

**Step 5: Commit**

```bash
git add agent/config.py tests/test_config.py
git commit -m "feat: add config module with model tier support"
```

---

### Task 6: Create first-launch wizard

**Files:**
- Create: `agent/setup_wizard.py`

The wizard is a two-screen tkinter dialog using the same Blender dark theme.

**Screen 1 — Welcome + License:**
- "3DPrintVoice" title + version (imported from `agent.__version__`)
- Description one-liner
- GPL-3.0 notice
- "Created by Roland Preisach, 2026"
- "Got it" button → screen 2

**Screen 2 — System Check + Model Selection:**
- Static list: Python 3.11+, Blender 5.1+, Ollama, NVIDIA GPU
- "Run System Check" button (consent-based — nothing runs until clicked)
- After click, each requirement checked and shown green/red with detail text:
  - Python: version number
  - Blender: `blender --version` output
  - Ollama: `which ollama`
  - GPU: `nvidia-smi` → name + VRAM
- VRAM-based auto-recommendation:
  - ≥12GB → Full (14B) pre-selected
  - 6–11GB → Medium (7B) pre-selected
  - 3–5GB → Lite (3B) pre-selected, warning about limitations
  - <3GB or no GPU → STOP screen: "Your hardware cannot run a local LLM. Minimum: 3GB VRAM." Only "Close" button, no continue.
- Radiobuttons for tiers the hardware can run (disabled for tiers it can't)
- Missing software shown as red with install instructions (doesn't block — user can install and re-run check)
- "Continue with [tier]" button → saves to config, closes wizard

**Key implementation details:**
- Version imported from `agent.__version__`
- System checks run in background thread, UI updates via `root.after()`
- `needs_setup()` and `run_setup()` exported as public API
- Returns True/False for whether setup completed

See full implementation in the v1 plan — the code is correct, just needs:
1. Import `__version__` from `agent` instead of hardcoding VERSION
2. Remove `chmod 600` from save_config (already fixed in Task 5)

**Step 1: Create agent/setup_wizard.py**

(Full implementation as in v1 plan, with the two fixes above applied)

**Step 2: Verify syntax**

```bash
python3 -c "import ast; ast.parse(open('agent/setup_wizard.py').read()); print('OK')"
```

**Step 3: Commit**

```bash
git add agent/setup_wizard.py
git commit -m "feat: first-launch wizard with system check and model selection"
```

---

### Task 7: Restructure launcher.sh — wizard BEFORE services

**Files:**
- Modify: `launcher.sh` (major restructure)

This is the critical fix from the audit. The current flow is:

```
launcher.sh: check ollama → start ollama → pull model → start blender → python app
```

The new flow is:

```
launcher.sh: check first_run → if first run, launch wizard only → exit
             if not first run: read config → start ollama → pull model → start blender → python app
```

**The key insight:** On first run, the wizard runs STANDALONE (no Ollama, no Blender). The wizard checks what's installed and tells the user what to do. After the wizard completes, the user re-launches (or the script continues to normal startup).

**Step 1: Rewrite launcher.sh**

```bash
#!/usr/bin/env bash
# 3DPrintVoice Launcher — starts all components, stops all on exit.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- Activate venv if installed to /opt ---
if [ -d "$PROJECT_DIR/venv" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
fi

# --- Check python3 exists ---
if ! command -v python3 &>/dev/null; then
    if command -v notify-send &>/dev/null; then
        notify-send "3DPrintVoice" "Python 3 is not installed. Please install python3." --icon=dialog-error
    fi
    echo "[3DPrintVoice] ERROR: python3 not found."
    exit 1
fi

# --- First-run check: launch wizard before anything else ---
CONFIG_FILE="$HOME/.config/3d-print-voice/config.json"
FIRST_RUN=true
if [ -f "$CONFIG_FILE" ]; then
    FIRST_RUN=$(python3 -c "
import json
try:
    cfg = json.load(open('$CONFIG_FILE'))
    print('false' if cfg.get('first_run_done', False) else 'true')
except: print('true')
" 2>/dev/null || echo "true")
fi

if [ "$FIRST_RUN" = "true" ]; then
    echo "[3DPrintVoice] First run detected — launching setup wizard..."
    cd "$PROJECT_DIR"
    python3 -m agent.setup_wizard_main
    # Re-check if setup completed
    if [ -f "$CONFIG_FILE" ]; then
        COMPLETED=$(python3 -c "
import json
try:
    cfg = json.load(open('$CONFIG_FILE'))
    print('true' if cfg.get('first_run_done', False) else 'false')
except: print('false')
" 2>/dev/null || echo "false")
        if [ "$COMPLETED" != "true" ]; then
            echo "[3DPrintVoice] Setup not completed. Exiting."
            exit 0
        fi
    else
        echo "[3DPrintVoice] Setup not completed. Exiting."
        exit 0
    fi
    echo "[3DPrintVoice] Setup complete. Starting application..."
fi

# --- Read model from config ---
MODEL="qwen2.5-coder:14b-instruct"
if [ -f "$CONFIG_FILE" ]; then
    MODEL=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('model', 'qwen2.5-coder:14b-instruct'))" 2>/dev/null || echo "$MODEL")
fi

BLENDER_PID=""
OLLAMA_STARTED_BY_US=false

# --- Cleanup on exit ---
cleanup() {
    echo ""
    echo "[3DPrintVoice] Shutting down..."
    if [ -n "$BLENDER_PID" ] && kill -0 "$BLENDER_PID" 2>/dev/null; then
        echo "[3DPrintVoice] Stopping Blender (PID $BLENDER_PID)..."
        kill "$BLENDER_PID" 2>/dev/null || true
        wait "$BLENDER_PID" 2>/dev/null || true
    fi
    if [ "$OLLAMA_STARTED_BY_US" = true ]; then
        echo "[3DPrintVoice] Stopping Ollama..."
        ollama stop "$MODEL" 2>/dev/null || true
    fi
    echo "[3DPrintVoice] Goodbye."
}
trap cleanup EXIT INT TERM

# --- Check prerequisites (with GUI error fallback) ---
_gui_error() {
    # Show error via tkinter if no terminal, or print to stdout
    python3 -c "
import tkinter as tk
from tkinter import messagebox
root = tk.Tk(); root.withdraw()
messagebox.showerror('3DPrintVoice', '''$1''')
root.destroy()
" 2>/dev/null || echo "[3DPrintVoice] ERROR: $1"
}

if ! command -v ollama &>/dev/null; then
    _gui_error "Ollama is not installed.\n\nInstall with:\ncurl -fsSL https://ollama.com/install.sh | sudo sh\n\nThen re-launch 3DPrintVoice."
    exit 1
fi

if ! command -v blender &>/dev/null; then
    _gui_error "Blender is not installed or not in PATH.\n\nInstall from: https://www.blender.org/download/\n\nThen re-launch 3DPrintVoice."
    exit 1
fi

# --- Start Ollama if not running ---
echo "[3DPrintVoice] Checking Ollama..."
if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "[3DPrintVoice] Starting Ollama..."
    ollama serve &>/dev/null &
    OLLAMA_STARTED_BY_US=true
    for i in $(seq 1 30); do
        if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then break; fi
        sleep 1
    done
    if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
        _gui_error "Ollama failed to start after 30 seconds."
        exit 1
    fi
fi
echo "[3DPrintVoice] Ollama is running."

# --- Check/pull model ---
if ! ollama list 2>/dev/null | grep -q "$MODEL"; then
    echo "[3DPrintVoice] Model not found. Pulling $MODEL..."
    ollama pull "$MODEL"
fi

# --- Warm up the model ---
echo "[3DPrintVoice] Warming up LLM..."
curl -sf http://localhost:11434/api/chat -d "{
  \"model\": \"$MODEL\",
  \"messages\": [{\"role\": \"user\", \"content\": \"print hello\"}],
  \"stream\": false,
  \"options\": {\"num_predict\": 10}
}" >/dev/null 2>&1 || echo "[3DPrintVoice] Warning: model warm-up failed."
echo "[3DPrintVoice] LLM ready."

# --- Launch Blender ---
echo "[3DPrintVoice] Starting Blender..."
blender --python "$PROJECT_DIR/addon/ai_bridge.py" &>/dev/null &
BLENDER_PID=$!

echo "[3DPrintVoice] Waiting for Blender addon..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:6789/health >/dev/null 2>&1; then break; fi
    sleep 1
done
if ! curl -sf http://localhost:6789/health >/dev/null 2>&1; then
    _gui_error "Blender addon did not start after 30 seconds.\n\nMake sure the AI Bridge addon is enabled."
    exit 1
fi
echo "[3DPrintVoice] Blender is ready."

# --- Launch the control bar ---
echo "[3DPrintVoice] Starting control bar..."
cd "$PROJECT_DIR"
if [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; then
    python3 -m agent.app
else
    echo "[3DPrintVoice] No display found, falling back to terminal mode."
    python3 -m agent.main
fi
```

**Step 2: Create agent/setup_wizard_main.py — standalone entry point**

```python
# agent/setup_wizard_main.py
"""Standalone entry point for the setup wizard (called by launcher.sh on first run)."""
from agent.setup_wizard import run_setup
import sys

if __name__ == "__main__":
    completed = run_setup()
    sys.exit(0 if completed else 1)
```

This allows `python3 -m agent.setup_wizard_main` to work as a standalone invocation.

**Step 3: Remove first-run check from app.py main()**

The wizard no longer runs inside `app.py`. The launcher handles it. Remove any first-run logic from `app.py`'s `main()` — it should remain a simple:

```python
def main():
    app = BlenderAIApp()
    app.run()
```

**Step 4: Verify launcher syntax**

```bash
bash -n launcher.sh && echo "OK"
```

**Step 5: Commit**

```bash
git add launcher.sh agent/setup_wizard_main.py agent/app.py
git commit -m "feat: restructure launcher — wizard before services, GUI error dialogs"
```

---

### Task 8: Wire model config into llm_client.py

**Files:**
- Modify: `agent/llm_client.py`

**Step 1: Replace hardcoded MODEL constant**

Replace lines 9-10:
```python
OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5-coder:14b-instruct"
```
with:
```python
from agent.config import load_config

OLLAMA_URL = "http://localhost:11434"
_cached_model = None

def _get_model() -> str:
    """Get model name from config (cached after first read)."""
    global _cached_model
    if _cached_model is None:
        _cached_model = load_config().get("model", "qwen2.5-coder:14b-instruct")
    return _cached_model
```

In `_ollama_chat`, replace `"model": MODEL` with `"model": _get_model()`.

**Step 2: Run existing tests — they should still pass**

The existing tests mock `_ollama_chat` entirely, so `_get_model()` is never reached in the mocked path. No test changes needed.

```bash
pytest tests/test_llm_client.py -v
```

**Step 3: Commit**

```bash
git add agent/llm_client.py
git commit -m "feat: read model name from config instead of hardcoded constant"
```

---

### Task 9: Create install.sh and uninstall.sh with venv

**Files:**
- Create: `install.sh`
- Create: `uninstall.sh`

**Key audit fix:** Uses a Python venv instead of `pip install --break-system-packages`.

**Step 1: Create install.sh**

```bash
#!/usr/bin/env bash
# 3DPrintVoice Installer
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
    echo "  Install with: sudo apt install python3 python3-venv"
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
echo "  - Application menu → Graphics → 3DPrintVoice"
echo "  - Terminal: $INSTALL_DIR/launcher.sh"
echo ""
echo "First launch will guide you through setup."
```

**Step 2: Create uninstall.sh**

```bash
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
```

**Step 3: Make executable and commit**

```bash
chmod +x install.sh uninstall.sh
git add install.sh uninstall.sh
git commit -m "feat: add install/uninstall scripts with venv isolation"
```

---

### Task 10: Update .gitignore, remove old files, update CLAUDE.md

**Files:**
- Delete: `blender-ai.desktop` (already git mv'd in Task 2, verify gone)
- Modify: `.gitignore`
- Modify: `CLAUDE.md` (update project structure, name, architecture notes)

**Step 1: Update .gitignore**

Add:
```
# Virtual environment (created by install.sh)
venv/
```

**Step 2: Update CLAUDE.md**

- Change project title to "3DPrintVoice"
- Update architecture section — it still references Claude API from v0.1.0, should reflect Ollama
- Update project structure to include new files (config.py, setup_wizard.py, install.sh, etc.)
- Update Stack section — change model reference to "configurable via setup wizard (Full/Medium/Lite)"

**Step 3: Commit**

```bash
git add .gitignore CLAUDE.md
git commit -m "chore: update project docs and gitignore for v0.4.0"
```

---

### Task 11: End-to-end verification

**Step 1: Run all tests**

```bash
cd /path/to/blender-ai
pytest tests/ -v
```

**Step 2: Syntax check all Python files**

```bash
python3 -c "
import ast
for f in ['agent/__init__.py', 'agent/config.py', 'agent/setup_wizard.py',
          'agent/setup_wizard_main.py', 'agent/app.py', 'agent/llm_client.py',
          'agent/main.py', 'agent/blender_client.py', 'agent/voice.py',
          'addon/ai_bridge.py']:
    ast.parse(open(f).read())
    print(f'OK: {f}')
"
```

**Step 3: Verify bash scripts**

```bash
bash -n install.sh && echo "install.sh OK"
bash -n uninstall.sh && echo "uninstall.sh OK"
bash -n launcher.sh && echo "launcher.sh OK"
```

**Step 4: Verify no "BlenderAI" remnants in source code**

```bash
grep -ri "BlenderAI" agent/ addon/ launcher.sh prompts/ README.md CLAUDE.md docs/ 2>/dev/null || echo "Clean — no BlenderAI remnants"
```

Exceptions allowed: git history references, CHANGELOG.md (historical entries), DEVELOPMENT_LOG.md (historical entries). These document what was — not what is.

**Step 5: Visual test — launch the setup wizard**

```bash
python3 -c "from agent.setup_wizard import SetupWizard; SetupWizard().run()"
```

Verify:
- Screen 1: title, version, description, license, "Got it" button
- Screen 2: requirements list, "Run System Check" button
- After check: GPU detected, model tier recommended, radio buttons work
- "Continue" saves config and closes

**Step 6: Check config was written**

```bash
cat ~/.config/3d-print-voice/config.json
```

Should show model tier selection from Step 5.

**Step 7: Commit if fixes needed**

```bash
git add -A
git commit -m "fix: address issues found during verification"
```
