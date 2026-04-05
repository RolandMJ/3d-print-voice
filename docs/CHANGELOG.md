# Changelog

All notable changes to BlenderAI are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.3.0] - 2026-04-05

### Added
- GUI control bar (agent/app.py) — Blender-themed top bar with text and voice input
- Voice input module (agent/voice.py) — faster-whisper on CUDA with silence detection
- Mic toggle: click to record, auto-stops after 1.5s silence, transcribes, sends
- Live status panel: Blender/Ollama/Mic connection dots, VRAM usage, command count
- F1 global hotkey for mic toggle
- Prusa MK3 tolerance rules for multi-part assemblies (sliding/snug/press/loose fit)
- 30+ bpy operation recipes in system prompt (hollowing, booleans, bevels, shapes)
- Command cheat sheet (docs/COMMAND_CHEATSHEET.md)
- Full bpy operations reference (docs/bpy_operations_reference.md)

### Changed
- Launcher now starts GUI control bar instead of terminal loop
- Terminal mode (agent/main.py) preserved as fallback for headless use
- System prompt expanded from 8 to 30+ operation examples
- Desktop file updated for GUI mode

## [0.2.0] - 2026-04-05

### Added
- Local LLM client (llm_client.py) using Ollama + Qwen2.5-Coder 14B
- Code extractor to strip markdown fences from local model output
- Error retry: automatic re-generation when Blender reports execution errors
- Undo support: each AI command is undoable via Ctrl+Z in Blender
- One-click launcher (launcher.sh) that starts/stops all components
- Linux desktop entry (blender-ai.desktop) for app menu integration
- Test suite with 12 tests for code extraction and LLM client
- Implementation plan document

### Changed
- System prompt rewritten with 8 request/response examples and stricter
  output format rules for local model reliability
- main.py rewritten for local architecture (no API key, error retry loop)
- requirements.txt updated: sounddevice + faster-whisper only
- All documentation updated for fully local architecture

### Removed
- Anthropic Claude API dependency (claude_client.py deleted)
- python-dotenv dependency
- .env.example file (no API keys needed)

## [0.1.0] - 2026-04-05

### Added
- Blender addon (ai_bridge.py) with HTTP server on port 6789
- POST /execute endpoint for receiving and executing bpy code
- GET /health endpoint for connection verification
- Thread-safe command queue with bpy.app.timers for main thread execution
- Claude API client (claude_client.py) using claude-sonnet-4-20250514
- System prompt (prompts/system.md) with bpy expertise and output contract
- Blender HTTP client (blender_client.py) with health check and error handling
- Terminal input loop (main.py) for text-based interaction
- Session logging to logs/ directory
- Project documentation (setup guide, architecture diagram, IP notice)
