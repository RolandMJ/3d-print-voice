# BlenderAI — Development Log

This log documents the development history of BlenderAI, serving as evidence
of intellectual property creation, design decisions, and progressive development.

Each entry records what was built, why, and what decisions were made.

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
