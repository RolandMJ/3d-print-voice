# BlenderAI

AI-powered natural language interface for Blender. Type (or speak) what you
want in plain English, and it appears in Blender's 3D viewport. Fully local —
no cloud APIs, no internet required, no cost per use.

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
# One-time setup
curl -fsSL https://ollama.com/install.sh | sudo sh   # Install Ollama
pip install -r requirements.txt --break-system-packages
# Install addon/ai_bridge.py in Blender (Edit > Preferences > Add-ons > Install from Disk)

# Run
./launcher.sh    # or double-click BlenderAI desktop icon
```

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

## Requirements

- Blender 5.1+
- Python 3.11+
- NVIDIA GPU with 12GB+ VRAM (for local LLM + voice model)
- Ollama (installed via official script)
- Qwen2.5-Coder 14B-Instruct (pulled via Ollama, ~9GB)

## Project Status

- [x] Phase 1 — Text input to bpy execution (local LLM via Ollama)
- [ ] Phase 2 — Voice input via faster-whisper
- [ ] Phase 3 — Scene context awareness
- [ ] Phase 4 — 3D print intelligence

## License

Proprietary. All rights reserved. See [docs/IP_NOTICE.md](docs/IP_NOTICE.md).

## Author

Roland Preisach (rolandmj) — 2026
