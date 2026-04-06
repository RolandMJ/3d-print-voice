# 3DPrintVoice

Voice & text command interface for creating 3D-printable objects in Blender.
Fully local — no cloud APIs, no internet required, no cost per use.

## How It Works

```
You type "create a 40mm cube"
    → Local LLM generates Python/bpy code (Ollama + Qwen2.5-Coder 14B)
        → Code sent via HTTP to Blender addon
            → Cube appears in Blender viewport
```

Everything runs on your machine. Your GPU handles both the AI model and Blender.

## Quick Start

```bash
# Install (copies to /opt, creates venv, adds desktop entry)
./install.sh

# Run
# Launch from app menu (Graphics → 3DPrintVoice) or:
/opt/3d-print-voice/launcher.sh
```

First launch opens a setup wizard that checks your system and selects the right
model for your GPU.

See [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md) for detailed step-by-step instructions.

## Architecture

See [docs/architecture.svg](docs/architecture.svg) for a visual diagram.

| Component | Purpose |
|-----------|---------|
| `addon/ai_bridge.py` | Blender addon — HTTP server that executes bpy code |
| `agent/main.py` | Terminal input loop — orchestrates the pipeline |
| `agent/llm_client.py` | Talks to local Ollama, extracts code from model output |
| `agent/blender_client.py` | HTTP client — sends code to Blender addon |
| `prompts/system.md` | System prompt — LLM's bpy expertise rules |
| `launcher.sh` | One-click launcher — starts/stops all components |

## Platform

Linux only (Ubuntu 22.04+, Linux Mint 21+). Not compatible with macOS or Windows.

Voice input requires ALSA (`arecord`). The MIC button is automatically disabled
if no microphone is detected.

## Requirements

- Blender 4.0+ (5.1+ recommended)
- Python 3.11+
- NVIDIA GPU with 3GB+ VRAM (determines model tier):
  - 12GB+: Full (Qwen2.5-Coder 14B) — best quality
  - 6-11GB: Medium (Qwen2.5-Coder 7B) — good quality
  - 3-5GB: Lite (Qwen2.5-Coder 3B) — basic commands
- Ollama (installed via official script)

The first-launch wizard auto-detects your GPU and recommends the best model tier.

## Project Status

- [x] Phase 1 — Text input to bpy execution (local LLM via Ollama)
- [x] Phase 2 — Voice input via faster-whisper
- [x] Phase 2.5 — GUI control bar, installer, setup wizard
- [ ] Phase 3 — Scene context awareness
- [ ] Phase 4 — 3D print intelligence

## License

GPL-3.0 — free to use, modify, and distribute. See [LICENSE](LICENSE) and [docs/IP_NOTICE.md](docs/IP_NOTICE.md).

## Author

Roland Preisach (rolandmj) — 2026
