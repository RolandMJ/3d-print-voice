# BlenderAI — What Is This and How Does It Work?

## The Big Idea

Blender is a powerful 3D modeling program — professionals use it to make
everything from movie special effects to 3D-printed objects. But it has a
steep learning curve. You need to learn dozens of menus, keyboard shortcuts,
and concepts just to make a simple box.

**BlenderAI lets you skip all that.** Instead of learning Blender's interface,
you just type what you want in plain English:

    "create a 40mm cube"
    "make it taller"
    "add a hole through the middle"

And the object appears (or changes) in Blender, right in front of you.

Behind the scenes, an AI (Claude) translates your English into Blender's
programming language (Python/bpy), and sends it to Blender to execute.

---

## How It Works — The Simple Version

Think of it like a translator at a restaurant in a foreign country:

1. **You** say what you want in English (type in terminal)
2. **The translator** (Claude AI) converts that into the local language
   (Blender Python code)
3. **The waiter** (HTTP connection) carries the order to the kitchen
4. **The kitchen** (Blender) prepares your dish (creates/modifies the 3D object)
5. **You see the result** on your plate (in Blender's viewport)

The key insight: you never need to learn Blender's interface. The AI knows
how to speak Blender's language, so you don't have to.

---

## What We Built (Phase 1)

Phase 1 is the working skeleton — the minimum needed to prove the idea works.

### The Files and What They Do

```
blender-ai/
├── addon/
│   └── ai_bridge.py         ← Lives INSIDE Blender (the kitchen door)
├── agent/
│   ├── main.py              ← The front desk — where you type commands
│   ├── claude_client.py     ← Talks to Claude AI (the translator)
│   └── blender_client.py    ← Sends code to Blender (the waiter)
├── prompts/
│   └── system.md            ← Instructions that tell Claude how to write Blender code
├── logs/                    ← Records of every command (auto-created)
├── .env                     ← Your secret API key (never shared)
├── .env.example             ← Template showing what the .env file should look like
└── requirements.txt         ← List of Python libraries needed
```

### Each Piece Explained

**addon/ai_bridge.py** — This is a Blender "addon" (plugin). When you enable
it in Blender, it starts a tiny web server on your computer (port 6789). This
server waits for commands. When it receives Python code, it runs that code
inside Blender. Think of it as a door — without it, there's no way to send
commands to Blender from outside.

**agent/main.py** — This is what you actually run. It shows the `>>>` prompt,
takes your typed text, sends it to Claude, gets code back, sends that code to
Blender, and shows you the result. It's the "conductor" that coordinates
everything.

**agent/claude_client.py** — This file talks to the Claude API. It sends your
English text along with special instructions (the system prompt) that tell
Claude: "You are a Blender expert. Return only executable Python code."
Claude reads your request, understands what you want, and writes the code.

**agent/blender_client.py** — This file handles the HTTP connection to Blender.
It packages the code Claude generated, sends it to the addon's web server,
and brings back the result (success or error).

**prompts/system.md** — These are Claude's "job instructions." They tell Claude
about Blender's coordinate system, measurement units, common patterns, and
rules. Without this, Claude would generate code that might not work correctly
in Blender.

---

## What Comes Next

### Phase 2 — Voice Input
Instead of typing commands, you'll be able to **speak** to Blender. The system
will use your microphone and a speech-to-text AI (faster-whisper, running
locally on your GPU) to hear what you say and convert it to text. Then
everything works the same as Phase 1 — just hands-free.

Think of it: you're looking at your 3D model and say "make it wider" — and
it happens.

### Phase 3 — Context Awareness
Right now, each command is independent — the AI doesn't remember what's already
in your scene. Phase 3 fixes that. After every command, the system will look
at what's in the Blender scene (object names, positions, sizes) and feed that
information back to Claude. This enables conversational modeling:

- "Create a box" → box appears
- "Make it taller" → the AI knows which object you mean, makes it taller
- "Put a hole through the center" → the AI understands context, creates the hole

### Phase 4 — 3D Print Intelligence
The final phase adds intelligence specific to 3D printing. Before you export
a model for your Prusa MK3 printer, the system will:

- Check for **overhangs** (parts that stick out and would need support material)
- Check **wall thickness** (too thin = breaks during printing)
- **Export STL files** ready for your slicer software

---

## Why This Matters

This project is a bridge between human intent and technical execution.
Instead of spending weeks learning a complex tool, you can start creating
immediately. The AI handles the translation layer, and you focus on what
you actually want to build.

For 3D printing specifically, this means going from idea to physical object
with nothing more than a conversation.
