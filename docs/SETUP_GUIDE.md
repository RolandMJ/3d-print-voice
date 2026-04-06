# 3DPrintVoice — Complete Setup Guide (Beginner-Friendly)

This guide walks you through every step needed to get 3DPrintVoice running on
your machine. No prior experience with Python projects or Blender addons
is assumed.

---

## What You Need Before Starting

| Requirement | Status |
|------------|--------|
| Blender 5.1.0 | Installed (system-wide) |
| Python 3.12 | Installed |
| NVIDIA GPU with CUDA (RTX 5070) | Ready |
| Corsair VOID ELITE headset w/ mic | Connected |
| Internet connection | Only needed for first-time setup (downloads) |

After setup, 3DPrintVoice runs completely offline. No cloud services, no API
keys, no ongoing costs.

---

## Step 1: Install Ollama (the Local AI Engine)

Ollama is a program that runs AI models on your computer. Think of it as a
"server" for AI — it loads the model into your GPU and answers questions.

1. Open a terminal
2. Run:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sudo sh
   ```
3. Enter your password when asked
4. Verify it installed:
   ```bash
   ollama --version
   ```
   You should see a version number.

**Why Ollama?** It handles all the complexity of running AI models locally —
GPU memory management, model loading, API compatibility. Without it, you'd
need to manually set up CUDA libraries, model formats, and inference servers.

---

## Step 2: Download the AI Model

The AI model is the "brain" that translates your English into Blender code.
We use Qwen2.5-Coder 14B — a model specifically trained for writing code.

1. Run:
   ```bash
   ollama pull qwen2.5-coder:14b-instruct
   ```
2. This downloads about **9GB**. It only happens once — after that, the model
   lives on your hard drive.
3. Verify it's there:
   ```bash
   ollama list
   ```
   You should see `qwen2.5-coder:14b-instruct` in the list.

**Why this model?** It's the strongest coding model that fits in your GPU's
12GB of memory. It was specifically trained on code (not just general text),
so it writes better Python than general-purpose models of the same size.

---

## Step 3: Install 3DPrintVoice

The installer handles everything automatically:

```bash
./install.sh
```

This will:
1. Copy the project to `/opt/3d-print-voice`
2. Create a Python virtual environment (isolated, won't affect system packages)
3. Install dependencies (faster-whisper, numpy)
4. Create a desktop entry (appears in Graphics menu)

**On first launch,** a setup wizard will:
1. Detect your GPU and VRAM
2. Recommend the best model tier (Full/Medium/Lite) for your hardware
3. Check that Ollama and Blender are installed
4. Save your settings

---

## Step 4: Install the Blender Addon

The addon is a plugin that runs inside Blender. It creates a "door" (HTTP
server) that lets our AI agent send commands to Blender.

1. **Open Blender** (type `blender` in terminal, or use the app menu)

2. **Open Preferences:**
   - Top menu bar → click **Edit**
   - Click **Preferences...** (near the bottom)

3. **Go to Add-ons:**
   - In the Preferences window, left sidebar → **Get Extensions**
   - Look for a dropdown/menu button (▾) near top right
   - Click **Install from Disk...**

4. **Navigate to the addon file:**
   - Go to: `/opt/3d-print-voice/addon/`
   - Select `ai_bridge.py`
   - Click **Install from Disk**

5. **Enable the addon:**
   - Find "AI Bridge" in the list
   - Check the **checkbox** next to it
   - You should see in Blender's console:
     ```
     [AI Bridge] HTTP server listening on 127.0.0.1:6789
     [AI Bridge] Addon registered
     ```

6. **Verify:**
   ```bash
   curl http://127.0.0.1:6789/health
   ```
   Should return: `{"status": "ok"}`

**Why an addon?** Blender has its own isolated Python environment. We can't
control Blender from outside without this bridge. The addon is the mailbox —
our agent sends letters (code), and the addon delivers them to Blender.

---

## Step 5: Run 3DPrintVoice

### Option A: The Launcher (Recommended)

The launcher starts everything automatically:

```bash
cd /opt/3d-print-voice
./launcher.sh
```

It will:
1. Start Ollama (if not running)
2. Warm up the AI model
3. Open Blender with the addon
4. Show the `>>>` command prompt

### Option B: Desktop Icon

For double-click launch from your desktop:

```bash
cp /opt/3d-print-voice/3d-print-voice.desktop ~/.local/share/applications/
```

Now "3DPrintVoice" appears in your app menu.

### Option C: Manual Start (each component separately)

If you prefer to control each piece:

1. Start Ollama: `ollama serve` (or it may already be running as a service)
2. Open Blender with addon enabled
3. In a separate terminal:
   ```bash
   cd /opt/3d-print-voice
   python3 -m agent.main
   ```

---

## Step 6: Try Your First Command

With 3DPrintVoice running, type at the `>>>` prompt:

```
create a 40mm cube
```

What happens:
1. Your text goes to the local AI model
2. The model generates: `bpy.ops.mesh.primitive_cube_add(size=0.04)`
3. The code is sent to Blender
4. A cube appears in the 3D viewport

Try more:
```
delete everything in the scene
create a sphere with radius 20mm
create a cylinder 10mm radius 50mm tall
move the cylinder up by 30mm
```

To quit: type `quit`, `exit`, or press Ctrl+C.

---

## Troubleshooting

### "Cannot reach Blender addon"
- Is Blender open?
- Is the addon enabled? (Edit → Preferences → Add-ons → AI Bridge is ticked)
- Test: `curl http://127.0.0.1:6789/health`

### "LLM error: Connection refused"
- Is Ollama running? Test: `curl http://localhost:11434/api/tags`
- Start it: `ollama serve`
- Is the model pulled? `ollama list` should show `qwen2.5-coder:14b-instruct`

### Model generates bad code / code fails
- This is expected occasionally with local models
- The system automatically retries once with error context
- Try rephrasing your command more specifically
- Simple commands work best: "create a cube", "move it up"

### First command is very slow
- Normal — the model takes 10-20 seconds to load into GPU on first request
- Subsequent commands are much faster (2-5 seconds)
- The launcher pre-warms the model to avoid this

### Nothing visible in Blender viewport
- Press `Home` key to see everything in the scene
- Press Numpad `.` to zoom to selected object
- Objects are in meters — a 40mm cube is small. Zoom in.

### Undo a command
- Press **Ctrl+Z** in Blender — each AI command is an undoable step
