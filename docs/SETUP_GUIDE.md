# BlenderAI — Complete Setup Guide (Beginner-Friendly)

This guide walks you through every step needed to get BlenderAI running on your
machine. No prior experience with Python projects or Blender addons is assumed.

---

## What You Need Before Starting

| Requirement | You Have |
|------------|----------|
| Blender 5.1.0 | Installed (system-wide) |
| Python 3.12 | Installed |
| NVIDIA GPU with CUDA | RTX 5070 (ready) |
| Anthropic API key | You need one — see Step 1 |
| Terminal access | Yes (Bash on Linux) |

---

## Step 1: Get Your Anthropic API Key

The AI brain behind BlenderAI is Claude (made by Anthropic). To talk to Claude,
you need an API key — think of it as a password that lets your code use Claude.

1. Open your browser and go to: https://console.anthropic.com/
2. Log in (or create an account if you don't have one)
3. Click **"API Keys"** in the left sidebar
4. Click **"Create Key"**
5. Give it a name like "blender-ai"
6. Copy the key — it starts with `sk-ant-...`
7. **Keep this key secret.** Never share it, never commit it to git.

**Why:** Claude is a paid API. Each time you type a command, BlenderAI sends
your text to Claude, and Claude sends back Python code. The API key is how
Anthropic knows it's you and bills your account. Usage for this project is
very cheap — a few cents per session.

---

## Step 2: Create Your .env File

The `.env` file stores your API key locally so the code can use it without
you having to type it every time.

1. Open a terminal
2. Navigate to the project folder:
   ```bash
   cd ~/Documents/Claude\ Projects/blender-ai
   ```
3. Copy the example file:
   ```bash
   cp .env.example .env
   ```
4. Open the new `.env` file in a text editor:
   ```bash
   nano .env
   ```
   (or use any editor you prefer — `gedit .env`, `code .env`, etc.)
5. Replace the placeholder with your real key:
   ```
   ANTHROPIC_API_KEY=YOUR_API_KEY_HERE
   ```
6. Save and close (in nano: Ctrl+O, Enter, Ctrl+X)

**Why:** We keep the key in a separate `.env` file (not in the code) so it
never accidentally gets shared. The `.gitignore` file ensures `.env` is never
uploaded to GitHub.

---

## Step 3: Install Python Dependencies

The agent (the part that runs in your terminal) needs two Python libraries:
- `anthropic` — the official library to talk to Claude's API
- `python-dotenv` — reads your `.env` file automatically

1. In the terminal, make sure you're in the project folder:
   ```bash
   cd ~/Documents/Claude\ Projects/blender-ai
   ```
2. Install the dependencies:
   ```bash
   pip install -r requirements.txt --break-system-packages
   ```
   (The `--break-system-packages` flag is needed on Ubuntu/Mint because the
   system Python is managed by the OS. This is safe for our use case.)

**Why:** Python doesn't come with everything pre-installed. `pip` is Python's
package manager — like an app store for code libraries. The `requirements.txt`
file lists exactly what we need, so anyone can reproduce the setup.

---

## Step 4: Install the Blender Addon

The addon is a small Python script that runs *inside* Blender. It opens a
door (an HTTP server) so our external agent can send commands to Blender.

1. **Open Blender** (double-click the Blender icon, or type `blender` in terminal)

2. **Open Preferences:**
   - Look at the very top menu bar of Blender
   - Click **Edit** (second item from the left)
   - Click **Preferences...** (near the bottom of the dropdown)
   - A new window opens — this is Blender's settings panel

3. **Go to the Add-ons section:**
   - In the Preferences window, look at the left sidebar
   - Click **Get Extensions** (the puzzle piece icon, or it may say "Add-ons"
     depending on your Blender version)
   - If you see "Get Extensions", look for a dropdown/menu button (▾) near
     the top right and click **Install from Disk...**
   - If you see "Add-ons" directly, click the **Install...** button at the
     top right

4. **Navigate to the addon file:**
   - A file browser opens
   - Navigate to: `Documents/Claude Projects/blender-ai/addon/`
   - Select `ai_bridge.py`
   - Click **Install from Disk** (or **Install Add-on**)

5. **Enable the addon:**
   - After installing, you should see "AI Bridge" appear in the list
   - Make sure the **checkbox next to it is checked** (ticked)
   - You should see a message in Blender's terminal/console:
     ```
     [AI Bridge] HTTP server listening on 127.0.0.1:6789
     [AI Bridge] Addon registered
     ```

6. **Verify it works:**
   - Open a new terminal (separate from Blender)
   - Run:
     ```bash
     curl http://127.0.0.1:6789/health
     ```
   - You should see: `{"status": "ok"}`
   - If you see "Connection refused", the addon isn't running — go back and
     make sure it's enabled

**Why:** Blender has its own isolated Python environment. We can't import
Blender's `bpy` library from outside. Instead, we run a tiny web server
*inside* Blender that listens for commands. Our external agent sends HTTP
requests to this server, and the server executes the code in Blender's
context. It's like sending a letter to someone inside a building — the
HTTP server is the mailbox.

---

## Step 5: Run BlenderAI

Now the fun part — actually using it.

1. **Make sure Blender is open** with the AI Bridge addon enabled (Step 4)

2. Open a **separate terminal** (this is important — Blender runs in one
   terminal/window, the agent runs in another)

3. Navigate to the project:
   ```bash
   cd ~/Documents/Claude\ Projects/blender-ai
   ```

4. Start the agent:
   ```bash
   python3 -m agent.main
   ```

5. You should see:
   ```
   BlenderAI — Phase 1 (text mode)
   Type a command for Blender. 'quit' to exit.

   >>>
   ```

6. **Try your first command — type:**
   ```
   create a 40mm cube
   ```

7. **What happens next:**
   - The agent sends your text to Claude
   - Claude generates Python code (shown in your terminal)
   - The code is sent to Blender via HTTP
   - A cube appears in Blender's 3D viewport
   - Terminal shows "Done."

8. **Try more commands:**
   ```
   delete everything in the scene
   create a sphere with radius 20mm
   create a cylinder 10mm radius 50mm tall
   move the cylinder up by 30mm
   ```

9. **To quit:** type `quit`, `exit`, or `q` (or press Ctrl+C)

**Why:** We run the agent as a Python module (`python3 -m agent.main`) rather
than a script (`python3 agent/main.py`) because it properly handles the
package imports between files.

---

## Troubleshooting

### "Cannot reach Blender addon"
- Is Blender open?
- Is the addon enabled? (Check Edit → Preferences → Add-ons → AI Bridge is ticked)
- Try the health check: `curl http://127.0.0.1:6789/health`

### "Claude API error"
- Is your `.env` file in the project root (not inside `agent/`)?
- Does it contain `ANTHROPIC_API_KEY=sk-ant-...` (no quotes, no spaces)?
- Does your Anthropic account have credits?

### "No module named 'agent'"
- Make sure you're running from the project root directory
- Use `python3 -m agent.main`, not `python3 agent/main.py`

### Cube appears but in the wrong place
- Blender uses meters. 40mm = 0.04 meters in Blender. This is normal.
- Zoom in/out with the scroll wheel to see small objects.

### Nothing visible in Blender viewport
- Press Numpad `.` (period) to zoom to the selected object
- Press `Home` key to see everything in the scene
- Check if you're in the right view — press `Numpad 0` for camera view,
  or `Numpad 5` to toggle perspective/orthographic
