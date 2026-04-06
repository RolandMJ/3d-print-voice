#!/usr/bin/env bash
# 3DPrintVoice Launcher — starts all components, stops all on exit.
#
# Usage: ./launcher.sh
#   or double-click the 3DPrintVoice desktop icon
#
# What it does:
#   1. Runs first-launch wizard if needed (before anything else)
#   2. Starts Ollama if not already running
#   3. Warms up the LLM model
#   4. Launches Blender with the AI Bridge addon
#   5. Launches the 3DPrintVoice control bar
#   6. On exit: stops Blender and Ollama cleanly

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- Activate venv if installed to /opt ---
if [ -d "$PROJECT_DIR/venv" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
fi

# --- Check python3 exists ---
# (must come after venv activation so venv's python3 is found)
if ! command -v python3 &>/dev/null; then
    if command -v notify-send &>/dev/null; then
        notify-send "3DPrintVoice" "Python 3 is not installed. Please install python3." --icon=dialog-error
    fi
    echo "[3DPrintVoice] ERROR: python3 not found."
    exit 1
fi

# --- GUI error helper (shows tkinter messagebox when Terminal=false) ---
_gui_error() {
    python3 "$PROJECT_DIR/agent/gui_error.py" "$1" 2>/dev/null \
        || echo "[3DPrintVoice] ERROR: $1"
}

# --- Verify Python dependencies ---
if ! python3 -c "import faster_whisper" &>/dev/null 2>&1; then
    if [ -d "$PROJECT_DIR/venv" ]; then
        _gui_error "Python dependencies missing from venv. Run:\n$PROJECT_DIR/venv/bin/pip install -r $PROJECT_DIR/requirements.txt"
    else
        _gui_error "Python dependencies not installed. Run:\npip install -r $PROJECT_DIR/requirements.txt"
    fi
    exit 1
fi

# --- First-run check: launch wizard BEFORE starting any services ---
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
    python3 -m agent.setup_wizard_main || true

    # Re-check if setup completed
    COMPLETED=false
    if [ -f "$CONFIG_FILE" ]; then
        COMPLETED=$(python3 -c "
import json
try:
    cfg = json.load(open('$CONFIG_FILE'))
    print('true' if cfg.get('first_run_done', False) else 'false')
except: print('false')
" 2>/dev/null || echo "false")
    fi

    if [ "$COMPLETED" != "true" ]; then
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
    echo "  (This may download several GB on first run.)"
    ollama pull "$MODEL"
    # Verify model was actually downloaded
    if ! ollama list 2>/dev/null | grep -q "$MODEL"; then
        _gui_error "Model $MODEL failed to download.\n\nCheck internet connection and disk space."
        exit 1
    fi
fi

# --- Warm up the model ---
echo "[3DPrintVoice] Warming up LLM..."
curl -sf http://localhost:11434/api/chat -d "{
  \"model\": \"$MODEL\",
  \"messages\": [{\"role\": \"user\", \"content\": \"print hello\"}],
  \"stream\": false,
  \"options\": {\"num_predict\": 10}
}" >/dev/null 2>&1 || echo "[3DPrintVoice] Warning: model warm-up failed, first command may be slow."
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
