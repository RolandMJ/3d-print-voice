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

Target hardware: Linux desktop with RTX 5070 GPU, Prusa MK3 3D printer.

### Architecture Decision

**Decision:** External agent process communicating with a Blender addon via HTTP.

**Alternatives considered:**
1. Blender addon that calls Claude directly — rejected because Blender's
   Python environment is isolated and cannot install pip packages (anthropic SDK)
2. Blender addon with bundled HTTP client — same isolation problem
3. Socket-based communication — HTTP is simpler, debuggable with curl, and
   doesn't require custom protocol handling

**Chosen approach rationale:** Keep Blender's addon minimal (stdlib only),
put all intelligence in the external agent. The HTTP boundary creates a clean
separation: addon handles bpy execution, agent handles AI and user interaction.

### Technical Decisions

| Decision | Rationale |
|----------|-----------|
| HTTP on localhost:6789 | Simple, debuggable, no auth needed for local-only |
| exec() for bpy code | Intentional — fully local, user-controlled, only way to run dynamic bpy |
| Timer queue pattern | bpy operations must run on main thread; HTTP handler runs on daemon thread |
| claude-sonnet-4-20250514 | Best balance of speed and code quality for real-time interaction |
| urllib instead of requests | blender_client.py could use stdlib; chose to minimize dependencies |
| Session logging | Every command + generated code logged for debugging and IP evidence |
| python-dotenv | Clean API key management without hardcoding secrets |

### Phase 1 Deliverables

| File | Purpose | Lines |
|------|---------|-------|
| addon/ai_bridge.py | Blender HTTP server addon | ~130 |
| agent/main.py | Terminal input loop | ~70 |
| agent/claude_client.py | Claude API integration | ~35 |
| agent/blender_client.py | HTTP client to Blender | ~40 |
| prompts/system.md | bpy system prompt | ~40 |
| requirements.txt | Python dependencies | 2 |
| .env.example | API key template | 1 |

### Validation Criteria

Phase 1 is complete when: typing "create a 40mm cube" in the terminal causes
a cube to appear in Blender's viewport.

---

## Development Roadmap

### Phase 2 — Voice Input (not started)
- faster-whisper with CUDA acceleration
- Microphone capture via sounddevice
- Push-to-talk and silence detection modes

### Phase 3 — Context Awareness (not started)
- Scene state query after each execution
- Feed object names/positions/dimensions back to Claude
- Enable relative commands ("make it taller", "move it left")

### Phase 4 — 3D Print Intelligence (not started)
- Overhang detection (>45 degrees)
- Wall thickness validation (minimum 1.2mm)
- STL export to slicer-ready files
