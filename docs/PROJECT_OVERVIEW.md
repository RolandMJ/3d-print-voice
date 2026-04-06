# 3DPrintVoice — What Is This and How Does It Work?

## The Big Idea

Blender is a powerful 3D modeling program — professionals use it to make
everything from movie special effects to 3D-printed objects. But it has a
steep learning curve. You need to learn dozens of menus, keyboard shortcuts,
and concepts just to make a simple box.

**3DPrintVoice lets you skip all that.** Instead of learning Blender's interface,
you just type (or say) what you want in plain English:

    "create a 40mm cube"
    "make it taller"
    "add a hole through the middle"
    "create a ball-and-socket joint for the shoulder"
    "add M3 heat-set insert pockets"
    "export all parts as STL"

And the object appears (or changes) in Blender, right in front of you.

Behind the scenes, a local AI model translates your English into Blender's
programming language (Python/bpy), and sends it to Blender to execute.
Everything runs on your computer — no internet, no cloud, no cost per use.

---

## How It Works — The Simple Version

Think of it like having a bilingual assistant sitting next to you:

1. **You** say what you want in English (type or speak in terminal)
2. **The AI assistant** (Qwen2.5-Coder, running on your GPU) converts that
   into Blender's language (Python code)
3. **A messenger** (HTTP connection) carries the code to Blender
4. **Blender** executes the code (creates/modifies the 3D object)
5. **You see the result** in Blender's viewport

The key insight: you never need to learn Blender's interface. The AI knows
how to speak Blender's language, so you don't have to.

The system includes 79 commands across 9 categories — from basic shapes to
articulation joints, hardware integration (screws, magnets, metal rods),
surface detail (panel lines, rivets), and batch STL export. It's built
specifically for designing complex multi-part 3D-printable assemblies.

---

## What We Built (Phase 1)

Phase 1 is the working skeleton — the minimum needed to prove the idea works.

### The Files and What They Do

```
3d-print-voice/
├── launcher.sh              ← Double-click to start everything
├── 3d-print-voice.desktop   ← App menu icon for Linux
├── addon/
│   └── ai_bridge.py         ← Lives INSIDE Blender (the door to send commands through)
├── agent/
│   ├── main.py              ← The front desk — where you type commands
│   ├── llm_client.py        ← Talks to local AI model (the translator)
│   └── blender_client.py    ← Sends code to Blender (the messenger)
├── prompts/
│   └── system.md            ← Instructions that tell the AI how to write Blender code
├── tests/
│   └── test_llm_client.py   ← Automated checks that the code works correctly
├── logs/                    ← Records of every command (auto-created)
└── requirements.txt         ← List of Python libraries needed
```

### Each Piece Explained

**launcher.sh** — The "one button" that starts everything. It boots up the AI
engine (Ollama), opens Blender, and launches the command terminal. When you
quit, it shuts everything down cleanly.

**addon/ai_bridge.py** — A Blender plugin. It opens a "door" (web server on
port 6789) so outside programs can send commands to Blender. Each command is
logged as an undo step, so you can Ctrl+Z to revert.

**agent/main.py** — The program you interact with. Shows the `>>>` prompt,
takes your text, orchestrates everything. If Blender reports an error, it
automatically asks the AI to fix the code and try again.

**agent/llm_client.py** — Talks to the local AI model through Ollama. It
sends your English text along with special instructions (the system prompt),
and extracts clean code from the response (stripping any markdown formatting
the model might add).

**agent/blender_client.py** — Handles the HTTP connection to Blender. Packages
the code, sends it, and brings back the result.

**prompts/system.md** — The AI's "job description." It tells the model about
Blender's coordinate system, measurement units, and includes many
request/response examples so the model knows exactly what format to use.

---

## What Comes Next

### Phase 2 — Voice Input
Instead of typing commands, you'll speak to Blender. A speech-to-text model
(faster-whisper, running locally on your GPU alongside the coding model)
hears what you say and converts it to text. Then everything works the same
as Phase 1 — just hands-free.

### Phase 3 — Context Awareness
Right now, each command is independent. Phase 3 feeds scene information back
to the AI after every command, enabling conversational modeling:

- "Create a box" → box appears
- "Make it taller" → AI knows which object, makes it taller
- "Put a hole through it" → AI understands context, does the boolean operation

### Phase 4 — 3D Print Intelligence
Before exporting for the Prusa MK3, the system checks for overhangs, wall
thickness, and manifold geometry. Then exports a print-ready STL.

---

## The Local Advantage

Everything runs on your machine:
- **No internet needed** after initial setup
- **No API costs** — you own the AI model
- **No data leaves your computer** — complete privacy
- **Works offline** — airplane, cabin, anywhere with power
- **Fast** — no network latency, just GPU computation
