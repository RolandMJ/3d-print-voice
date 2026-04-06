# Changelog

All notable changes to 3DPrintVoice (formerly BlenderAI) are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.4.0] - 2026-04-06

### Added — Phase 3: Scene Context & Awareness
- Scene context: LLM sees all objects, dimensions, locations after each command
- Relative commands work: "make it taller", "create matching socket"
- Parametric properties: joints store radius/clearance as custom properties
- Print bed warning: yellow alert when part exceeds configured bed size
- Print bed presets: Prusa MK3, Prusa Mini, Ender 3, custom
- Organic geometry: bezier curve extrusion, subdivision mesh, loft, smooth, shrinkwrap
- DIN metric hardware: exact M3-M8 clearance holes, DIN 912/7991/934 dimensions
- Threaded rod (Gewindestange DIN 975) channels with correct OD clearance
- Spring pin (Spannhülse DIN 1481) and dowel pin (Zylinderstift DIN 7) recipes
- Curved armor panels: bmesh spin, tapered, overlap lip
- Articulation joints: ball-socket (S/M/L), ratchet, double-hinge, swivel, friction peg

### Added — Setup & Packaging
- First-launch setup wizard with system check and model tier selection (Full/Medium)
- GPL-3.0 license (replaces proprietary)
- Linux installer (install.sh) with venv isolation and desktop entry
- Linux uninstaller (uninstall.sh) with optional config removal
- App icon (SVG + PNG)
- Config module (~/.config/3d-print-voice/config.json)
- 3D print mode toggle button in control bar
- Command history (up/down arrows, max 50)
- Hover tooltips on status dots and 3D Print button
- Elapsed time display during LLM generation
- GUI error dialogs when launcher fails (works with Terminal=false)
- 79 commands/recipes across 9 categories in system prompt (983 lines)
- Articulation joint recipes: ball-and-socket (S/M/L), ratchet, double-hinge,
  swivel, friction peg — for poseable multi-part figure assemblies
- Hardware integration: metal rod sleeves (3/4/6/8mm), countersunk screws,
  magnet pockets, spring clip detents
- Surface detail: panel line engraving, raised rivet/bolt details
- Assembly features: keyed D-pin alignment, part splitting with zigzag interlock
- Batch STL export (individual file per mesh object)
- Part naming convention: REGION_PART_SIDE_NUMBER (e.g., ARM_UPPER_L_01)
- Bilingual command reference poster (HTML, EN/DE, print-optimized A2)
- REF button + F2 hotkey opens command reference in browser
- PrusaSlicer integration: SLICE button (F3), status dot, smart instance management
- VPS design sync: versioned FreeCAD → Blender workflow with manifest audit trail
- Assembly testing: load full assembly, interference check, clearance measurement,
  cross-section view, range-of-motion test, center-of-gravity balance check
- Dropped 3B lite tier — minimum 6GB VRAM (7B medium) required

### Changed
- Project renamed: BlenderAI → 3DPrintVoice
- Launcher restructured: setup wizard runs before services
- LLM model name read from config (configurable via wizard)
- Blender addon: exec() sandboxed with restricted builtins and blocked patterns
- LLM timeout reduced from 120s to 30s
- Error messages display up to 120 chars (was 80)
- Log rotation: max 10 session files
- Embedded bpy code moved to external files in prompts/
- Dependency versions pinned in requirements.txt

### Fixed
- Shell injection vulnerability in launcher error display
- Unrestricted exec() with full __builtins__ access
- tempfile.mktemp() race condition in voice recording
- MIC button now disabled when no microphone detected
- Threading race condition on _processing flag
- Desktop entry uses direct Exec path instead of bash -c wrapper
- Launcher verifies Python dependencies after venv activation
- Launcher verifies model download after ollama pull

### Security
- Blocked dangerous patterns in bpy code execution (os, subprocess, eval, etc.)
- Restricted __builtins__ in exec scope (only safe builtins allowed)
- Localhost-only origin check on addon HTTP endpoint
- Code size limit (10KB) on bpy execution
- Input length cap (2000 chars) on LLM requests
- GUI error helper prevents shell injection (gui_error.py)
- Sandbox: tightened blocked patterns (getattr/setattr without parens)
- Sandbox: removed type/hasattr from restricted builtins
- Launcher: CONFIG_FILE passed via sys.argv, not string interpolation
- Tooltip: graceful shutdown handling (TclError protection)
- Sanitized f-string interpolation in 3D print mode restore (enum whitelist validation)

## [0.3.0] - 2026-04-05

### Added
- GUI control bar (agent/app.py) — Blender-themed top bar with text and voice input
- Voice input module (agent/voice.py) — faster-whisper base.en on CPU with silence detection
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

### Fixed
- VRAM exhaustion: moved whisper from CUDA (small.en) to CPU (base.en)
  to avoid exceeding 12GB alongside coding model
- Mic capture silence: replaced sounddevice with arecord subprocess due
  to PipeWire compatibility issue (sounddevice returns zeros, arecord works)

## [0.2.0] - 2026-04-05

### Added
- Local LLM client (llm_client.py) using Ollama + Qwen2.5-Coder 14B
- Code extractor to strip markdown fences from local model output
- Error retry: automatic re-generation when Blender reports execution errors
- Undo support: each AI command is undoable via Ctrl+Z in Blender
- One-click launcher (launcher.sh) that starts/stops all components
- Linux desktop entry for app menu integration
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
