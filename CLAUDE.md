# 3DPrintVoice — Voice & Text Command Interface for 3D Printing in Blender

## Project Goal
A local AI-driven interface that lets the user control Blender via voice or
typed natural language. A local LLM (Ollama) generates bpy (Blender Python API)
code, sends it to a Blender addon via HTTP, and the result appears live in
Blender's viewport. No custom 3D engine. No custom viewport. Blender IS the tool.

## Architecture

Microphone → arecord (ALSA)
    ↓
faster-whisper (local, CPU, base.en) → text
    ↓
agent/app.py (GUI control bar)
    ↓
Ollama (localhost:11434) → configurable model (Full/Medium)
    ↓  system prompt: bpy expert → returns executable bpy Python code
HTTP POST → localhost:6789
    ↓
Blender addon (addon/ai_bridge.py) — runs HTTPServer inside Blender
    ↓
exec(bpy_code) → result visible in Blender viewport
    ↓
Response (result, error if any) → back to agent

## Stack
- Blender 5.1.0 (installed system, not modified)
- Blender addon: stdlib + bpy only (Blender's isolated Python env)
- External agent: Python 3.11+, faster-whisper, numpy
- Voice: faster-whisper with model "base.en", device="cpu" (avoids VRAM exhaustion)
- LLM: Ollama + configurable model tier (Full: 14B, Medium: 7B)
- System prompt: 1556 lines, 110+ commands/recipes across 12 categories

## Project Structure

3d-print-voice/
├── CLAUDE.md
├── README.md
├── LICENSE                  ← GPL-3.0
├── requirements.txt
├── install.sh               ← Linux installer (copies to /opt, creates venv)
├── uninstall.sh             ← Linux uninstaller
├── launcher.sh              ← One-click launcher (wizard → ollama → blender → GUI)
├── 3d-print-voice.desktop   ← Desktop entry template
├── assets/
│   ├── icon.svg             ← App icon source
│   ├── icon-48.png          ← Desktop entry icon
│   └── icon-256.png         ← Splash screen icon
├── addon/
│   └── ai_bridge.py         ← Blender addon: HTTP server + bpy exec
├── agent/
│   ├── __init__.py           ← Package init + __version__
│   ├── app.py                ← GUI control bar (tkinter)
│   ├── config.py             ← Config management (~/.config/3d-print-voice/)
│   ├── setup_wizard.py       ← First-launch wizard (splash + system check)
│   ├── setup_wizard_main.py  ← Standalone wizard entry point
│   ├── main.py               ← Terminal fallback input loop
│   ├── llm_client.py         ← Ollama API with model tier support
│   ├── blender_client.py     ← HTTP client: POST commands to addon
│   └── voice.py              ← faster-whisper mic capture + transcription
├── prompts/
│   └── system.md             ← LLM bpy expertise and behavior rules
└── tests/
    ├── test_config.py
    └── test_llm_client.py

## Critical Technical Constraints

### Blender Addon Python Environment
- Blender ships with its own Python interpreter — isolated from system Python
- The addon (ai_bridge.py) can ONLY use stdlib modules + bpy
- Do NOT import requests, anthropic, or any third-party lib inside the addon
- HTTPServer runs in a daemon thread so it doesn't block Blender's UI thread
- All bpy calls must happen on Blender's main thread — use a queue and
  bpy.app.timers to pull from the queue on the main thread

### bpy Code Execution
- The addon receives bpy code as a string and executes via exec()
- This is intentional and safe — fully local, user-controlled
- Always wrap exec() in try/except and return structured error info
- The exec() context must include: {"bpy": bpy, "__builtins__": __builtins__}

### LLM Code Generation Rules
- The LLM must return ONLY executable bpy Python — no markdown, no
  explanation, no triple backticks
- If the model cannot fulfill a request safely, return a comment string:
  # CANNOT_EXECUTE: reason
- Enforce this in the system prompt with an explicit output format contract
- Local models may wrap code in markdown fences — extract_code() strips these

### Voice Input
- faster-whisper runs on CPU (base.en) to avoid VRAM competition with LLM
- Capture audio via arecord (ALSA) — sounddevice had PipeWire issues
- Silence detection auto-stops recording after 1.5s of quiet

## Phases

### Phase 1 — Working Skeleton (start here)
Goal: typed command → bpy executes → result in Blender viewport

Deliverables:
- addon/ai_bridge.py: HTTP server on port 6789, /execute endpoint, bpy exec
- agent/blender_client.py: POST to addon, return response
- agent/llm_client.py: send user text to Ollama, receive bpy code
- prompts/system.md: bpy system prompt (primitives, transforms, booleans)
- agent/main.py: text input loop → claude → blender → print result
- requirements.txt

Validation: type "create a 40mm cube" in terminal → cube appears in Blender

### Phase 2 — Voice Input
- agent/voice.py: mic capture + faster-whisper transcription
- Integrate into main.py loop
- Add push-to-talk (spacebar) and silence-detection modes

### Phase 3 — Context Awareness
- After each bpy execution, query scene state (object names, positions,
  dimensions) and feed back to Claude as context for follow-up commands
- Enables: "make it taller" / "move it left" / "hollow it out"

### Phase 4 — Print Intelligence
- Overhang detection (flag > 45° without support)
- Wall thickness check (minimum 1.2mm for 0.4mm nozzle)
- STL export via bpy to target directory for slicer

## User Hardware
- OS: Linux Mint, kernel 6.14, desktop build
- GPU: ASUS TUF RTX 5070 (CUDA available, use for Whisper)
- Blender: system-installed (run blender --version to confirm before first session)
- 3D Printer: Prusa MK3 (target export: STL)

## Rules for This Project
- Never suggest the user learn Blender's UI — the whole point is to bypass it
- Keep the GUI control bar minimal — no complex UI, no settings dialogs
- Before adding any dependency, check if stdlib or bpy already covers it
- Phase 1 must work before Phase 2 starts — no skipping ahead
- All bpy code generated by the LLM must be logged to a session file
  for debugging and learning
