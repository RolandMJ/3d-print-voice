#!/usr/bin/env bash
# 3DPrintVoice Launcher — starts all components, stops all on exit.
#
# Usage: ./launcher.sh
#   or double-click the 3DPrintVoice desktop icon
#
# What it does:
#   1. Starts Ollama if not already running
#   2. Warms up the LLM model (first request is slow, this gets it ready)
#   3. Launches Blender with the AI Bridge addon
#   4. Launches the 3DPrintVoice control bar
#   5. On exit: stops Blender and Ollama cleanly

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BLENDER_PID=""
OLLAMA_STARTED_BY_US=false

# --- Cleanup on exit ---
cleanup() {
    echo ""
    echo "[3DPrintVoice] Shutting down..."

    # Stop Blender if we started it
    if [ -n "$BLENDER_PID" ] && kill -0 "$BLENDER_PID" 2>/dev/null; then
        echo "[3DPrintVoice] Stopping Blender (PID $BLENDER_PID)..."
        kill "$BLENDER_PID" 2>/dev/null || true
        wait "$BLENDER_PID" 2>/dev/null || true
    fi

    # Stop Ollama only if we started it
    if [ "$OLLAMA_STARTED_BY_US" = true ]; then
        echo "[3DPrintVoice] Stopping Ollama..."
        ollama stop qwen2.5-coder:14b-instruct 2>/dev/null || true
    fi

    echo "[3DPrintVoice] All components stopped. Goodbye."
}
trap cleanup EXIT INT TERM

# --- Check prerequisites ---
if ! command -v ollama &>/dev/null; then
    echo "[3DPrintVoice] ERROR: Ollama is not installed."
    echo "  Install it with: curl -fsSL https://ollama.com/install.sh | sudo sh"
    exit 1
fi

if ! command -v blender &>/dev/null; then
    echo "[3DPrintVoice] ERROR: Blender is not installed or not in PATH."
    exit 1
fi

# --- Start Ollama if not running ---
echo "[3DPrintVoice] Checking Ollama..."
if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "[3DPrintVoice] Starting Ollama..."
    ollama serve &>/dev/null &
    OLLAMA_STARTED_BY_US=true
    # Wait for Ollama to be ready
    for i in $(seq 1 30); do
        if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "[3DPrintVoice] ERROR: Ollama failed to start after 30 seconds."
        exit 1
    fi
fi
echo "[3DPrintVoice] Ollama is running."

# --- Check model is available ---
if ! ollama list 2>/dev/null | grep -q "qwen2.5-coder:14b-instruct"; then
    echo "[3DPrintVoice] Model not found. Pulling qwen2.5-coder:14b-instruct..."
    echo "  (This downloads ~9GB on first run. Grab a coffee.)"
    ollama pull qwen2.5-coder:14b-instruct
fi

# --- Warm up the model ---
echo "[3DPrintVoice] Warming up LLM (first load takes 10-20 seconds)..."
curl -sf http://localhost:11434/api/chat -d '{
  "model": "qwen2.5-coder:14b-instruct",
  "messages": [{"role": "user", "content": "print hello"}],
  "stream": false,
  "options": {"num_predict": 10}
}' >/dev/null 2>&1 || echo "[3DPrintVoice] Warning: model warm-up failed, first command may be slow."
echo "[3DPrintVoice] LLM ready."

# --- Launch Blender ---
echo "[3DPrintVoice] Starting Blender..."
blender --python "$PROJECT_DIR/addon/ai_bridge.py" &>/dev/null &
BLENDER_PID=$!

# Wait for addon HTTP server
echo "[3DPrintVoice] Waiting for Blender addon..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:6789/health >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

if ! curl -sf http://localhost:6789/health >/dev/null 2>&1; then
    echo "[3DPrintVoice] ERROR: Blender addon did not start after 30 seconds."
    echo "  Make sure the AI Bridge addon is enabled in Blender preferences."
    exit 1
fi
echo "[3DPrintVoice] Blender is ready."

# --- Launch the control bar ---
echo "[3DPrintVoice] Starting control bar..."
cd "$PROJECT_DIR"

# Use GUI mode by default, fall back to terminal if no display
if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
    python3 -m agent.app
else
    echo "[3DPrintVoice] No display found, falling back to terminal mode."
    python3 -m agent.main
fi
