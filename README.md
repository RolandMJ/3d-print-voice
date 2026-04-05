# BlenderAI

AI-powered natural language interface for Blender. Type what you want in plain
English, and it appears in Blender's 3D viewport.

## How It Works

```
You type "create a 40mm cube"
    → Claude AI generates Python/bpy code
        → Code sent via HTTP to Blender addon
            → Cube appears in Blender viewport
```

## Quick Start

1. Install dependencies: `pip install -r requirements.txt --break-system-packages`
2. Copy `.env.example` to `.env` and add your Anthropic API key
3. Install `addon/ai_bridge.py` in Blender (Edit → Preferences → Add-ons → Install from Disk)
4. Run: `python3 -m agent.main`

See [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md) for detailed step-by-step instructions.

## Architecture

See [docs/architecture.svg](docs/architecture.svg) for a visual diagram.

| Component | Purpose |
|-----------|---------|
| `addon/ai_bridge.py` | Blender addon — HTTP server that executes bpy code |
| `agent/main.py` | Terminal input loop — orchestrates the pipeline |
| `agent/claude_client.py` | Sends text to Claude API, receives bpy code |
| `agent/blender_client.py` | HTTP client — sends code to Blender addon |
| `prompts/system.md` | System prompt — Claude's bpy expertise rules |

## Requirements

- Blender 5.1+
- Python 3.11+
- NVIDIA GPU with CUDA (for Phase 2 voice input)
- Anthropic API key

## Project Status

- [x] Phase 1 — Text input → bpy execution (current)
- [ ] Phase 2 — Voice input via faster-whisper
- [ ] Phase 3 — Scene context awareness
- [ ] Phase 4 — 3D print intelligence

## License

Proprietary. All rights reserved. See [docs/IP_NOTICE.md](docs/IP_NOTICE.md).

## Author

Roland Preisach (rolandmj) — 2026
