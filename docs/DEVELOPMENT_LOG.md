# 3DPrintVoice — Development Log

This log documents the development history of 3DPrintVoice (formerly BlenderAI), serving as evidence
of intellectual property creation, design decisions, and progressive development.

Each entry records what was built, why, and what decisions were made.

---

## Session Handoff — Where We Left Off (2026-04-05)

**Current version:** v0.3.0 (14 commits on main, pushed to GitHub)

**What works:**
- GUI control bar with Blender dark theme, text input, status panel
- Text commands → Ollama (Qwen2.5-Coder 14B) → Blender execution
- 30+ operation recipes (hollowing, booleans, bevels, shapes, tolerances)
- Undo support (Ctrl+Z in Blender)
- Error retry (auto-feeds errors back to model)
- Session logging
- One-click launcher (./launcher.sh)

**What needs testing next session:**
- Voice input end-to-end (mic → arecord → whisper → command). The arecord
  capture works (confirmed via wav analysis), whisper transcription works
  (confirmed via test), but the full GUI flow (click MIC → speak → auto-stop
  → transcribe → execute in Blender) has not been tested live yet.
- Complex multi-step operations (box with lid, boolean combinations)
- Tolerance-fit parts printed on Prusa MK3 (do clearances need adjustment?)

**What's next (Phase 3 — Context Awareness):**
- After each bpy execution, query scene state (object names, positions,
  dimensions) and feed back to the model as context
- This enables conversational modeling: "make it taller", "move it left",
  "add a hole through the Cube"
- Currently each command is independent — the model doesn't know what's
  in the scene

**Known issues:**
- sounddevice library incompatible with PipeWire on this system (replaced
  with arecord, but worth revisiting if PipeWire updates fix it)
- VRAM is tight: ~10.2GB used with model loaded, ~1.5GB free for Blender
  viewport. Complex scenes may cause GPU memory pressure.
- Whisper model downloads trigger HuggingFace warnings (cosmetic, not functional)

---

## 2026-04-05 — GUI Control Bar + Voice Input (v0.3.0)

### What Was Built

GUI control bar replacing the terminal interface. Blender-themed dark UI
(`#2D2D2D` background, orange `#E87D0D` accents) positioned at the top of
the screen, full width, always on top.

Voice input via faster-whisper (base.en model) on CPU. Toggle recording with
a mic button — auto-stops after 1.5 seconds of silence, transcribes speech
to text, and sends the command through the normal pipeline.

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| Tkinter for GUI | Built into Python, zero extra dependencies, lightweight |
| Top bar (not floating window) | Doesn't compete with Blender for screen space |
| Toggle mic (not hold-to-talk) | Hands-free once activated, auto-stop on silence |
| faster-whisper base.en on CPU | CUDA whisper + coding model exceeded 12GB VRAM; CPU transcription <1s for commands |
| arecord for mic capture | sounddevice returns silence due to PipeWire compat issue; arecord works reliably |
| Status panel with VRAM | User needs to know system health at a glance |
| Background whisper preload | First voice command is fast — model loaded at startup |
| F1 global hotkey | Can toggle mic even when Blender is focused |

### Bugs Found and Fixed During Testing

1. **VRAM exhaustion:** Whisper small.en on CUDA (~1GB) + Qwen2.5-Coder 14B
   (~9GB) + Blender + desktop exceeded 12GB. Fixed by moving whisper to CPU
   with base.en model. Transcription speed is still <1s for short commands.

2. **sounddevice silence bug:** Python sounddevice library returns all-zero
   audio on this system (PipeWire + Corsair VOID ELITE). Root cause: PipeWire
   compatibility issue with PortAudio's stream activation. Fix: replaced
   sounddevice with subprocess call to arecord (ALSA), which captures
   correctly. Confirmed with RMS 302 from arecord vs RMS 0 from sounddevice.

3. **Mic physically working:** Corsair VOID ELITE mic captures audio at the
   ALSA level (verified via `arecord` + wav analysis). Initial reports of
   "no audio" were due to the sounddevice library issue, not hardware.

### UX Layout

```
┌──────────────────────────────────────────────────────────────────────────┐
│ [MIC] [___________ command input field ___________] [SEND] │ ● Blender │
│       [___________ last command → result _________]        │ ● Ollama  │
│                                                            │ ● Mic     │
│                                                            │ VRAM 10/12│
└──────────────────────────────────────────────────────────────────────────┘
```

### Operation Vocabulary Expansion

System prompt expanded from 8 basic examples to 30+ operation recipes.
This was driven by a user test where "make this cylinder hollow" failed —
the local 14B model didn't know the Solidify modifier pattern. Adding
explicit recipes for all common operations resolved this class of failures.

Also added Prusa MK3 printer tolerance rules (0.25mm sliding fit, 0.15mm
snug, 0.05mm press fit, 0.40mm loose fit) so multi-part assemblies come
off the printer with correct clearances.

---

## 2026-04-05 — Project Inception and Phase 1 Implementation

### Concept Origin

The idea: control Blender entirely through natural language, bypassing the
steep learning curve of Blender's UI. Motivated by the desire to go from
spoken/typed intent to 3D-printed physical objects with zero Blender expertise.

Target hardware: Linux desktop with RTX 5070 GPU (12GB VRAM), Prusa MK3
3D printer, Corsair VOID ELITE wireless headset with microphone.

### Architecture Decision

**Decision:** External agent process communicating with a Blender addon via HTTP.

**Alternatives considered:**
1. Blender addon that calls LLM directly — rejected because Blender's
   Python environment is isolated and cannot install pip packages
2. Blender addon with bundled HTTP client — same isolation problem
3. Socket-based communication — HTTP is simpler, debuggable with curl, and
   doesn't require custom protocol handling

**Chosen approach rationale:** Keep Blender's addon minimal (stdlib only),
put all intelligence in the external agent. The HTTP boundary creates a clean
separation: addon handles bpy execution, agent handles AI and user interaction.

### Initial Implementation (v0.1.0)

First working skeleton using Anthropic Claude API (cloud-based). Proved the
architecture works end-to-end. This version was immediately superseded by
the local architecture decision (see below).

---

## 2026-04-05 — Local Architecture Decision and Rebuild (v0.2.0)

### The Pivot

**Decision:** Replace cloud-based Claude API with fully local LLM inference.

**Motivation:** The original design required an Anthropic API key, internet
connection, and incurred per-request costs. The user's vision was always a
fully local, self-contained system. The RTX 5070's 12GB VRAM is sufficient
to run capable local coding models.

### Model Selection

**Research conducted:** Evaluated all major open-source coding models
available as of April 2026.

| Model | Size | Fits 12GB? | Code Quality | Decision |
|-------|------|-----------|-------------|----------|
| Qwen2.5-Coder 14B | 9GB Q4 | Yes | Excellent | **Selected** |
| Qwen2.5-Coder 7B | 4.7GB | Yes | Good | Backup option |
| Qwen3-Coder 30B-A3B | 19GB | No | Excellent | Too large |
| Gemma 4 E4B | 9.6GB | Yes | Good (general) | Not code-specialized |
| Gemma 4 26B | 18GB | No | Very good | Too large |
| Devstral 24B | 14GB | No | Excellent | Too large |
| DeepSeek-Coder | various | Yes | Outdated | Superseded by Qwen |

**Chosen: Qwen2.5-Coder 14B-Instruct (Q4_K_M)**
- 9GB VRAM — fits with headroom for Blender + faster-whisper (~1GB each)
- Purpose-built for code generation (not general-purpose)
- 14B active parameters — 3x more than Gemma 4 E4B's effective 4.5B
- Proven Python quality, widely benchmarked

**Infrastructure: Ollama**
- One-line install, automatic GPU detection
- HTTP API at localhost:11434 (same pattern as the Blender addon)
- Automatic VRAM management
- Model scheduling handles GPU memory pressure

### VRAM Budget

| Component | VRAM | Notes |
|-----------|------|-------|
| Linux desktop (Xorg + Cinnamon) | ~0.7GB | Measured via nvidia-smi |
| Qwen2.5-Coder 14B (Q4_K_M) | ~9.0GB | Via Ollama |
| faster-whisper (small.en) | ~1.0GB | Phase 2, brief usage |
| Blender viewport | ~0.5-1.5GB | Varies with scene |
| **Total** | **~11-12GB** | Fits 12GB with Ollama's model scheduling |

System RAM (30GB) provides safety net — Ollama spills to CPU RAM if needed.

### Technical Changes from v0.1.0

| Change | Rationale |
|--------|-----------|
| claude_client.py → llm_client.py | Ollama API replaces Anthropic API |
| Added code extractor (extract_code) | Local models wrap output in markdown; need to strip it |
| Added error retry in main.py | Local models generate more errors; auto-retry with error context |
| Hardened system prompt (8 examples) | Local 14B model needs more explicit instruction than Claude |
| Added undo_push to addon | Each AI command becomes undoable via Ctrl+Z |
| Removed .env/dotenv dependency | No API key needed for local operation |
| Added launcher.sh | One script starts/stops Ollama + Blender + agent |
| Added .desktop file | Linux desktop integration for double-click launch |
| Added test suite (12 tests) | TDD for code extractor and LLM client |

### Voice System Design (for Phase 2)

Two-model approach:
- **Speech-to-text:** faster-whisper (small.en) — dedicated speech model, ~1GB
- **Text-to-code:** Qwen2.5-Coder 14B — dedicated coding model, ~9GB
- These are different model types (speech recognition vs language model)
  and cannot be combined into one
- Both fit simultaneously on RTX 5070 with Ollama's model scheduling

Hardware verified: Corsair VOID ELITE wireless headset detected as default
audio input (48kHz mono), PortAudio system library installed, audio subsystem
operational via PipeWire.

---

## Development Roadmap

### Phase 2 — Voice Input (not started)
- faster-whisper with CUDA acceleration on RTX 5070
- Microphone capture via sounddevice (Corsair VOID ELITE)
- Push-to-talk and silence detection modes

### Phase 3 — Context Awareness (not started)
- Scene state query after each execution
- Feed object names/positions/dimensions back to LLM
- Enable relative commands ("make it taller", "move it left")

### Phase 4 — 3D Print Intelligence (not started)
- Overhang detection (>45 degrees)
- Wall thickness validation (minimum 1.2mm)
- STL export to slicer-ready files for Prusa MK3
