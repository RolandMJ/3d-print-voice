# Audit Remediation — Security, Error Handling, UX Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all critical/high/medium findings from the application audit: security hardening (exec sandbox, shell injection, tmpfile), error handling (timeouts, feedback), UX improvements (tooltips, history, progress), code quality, logging, and documentation.

**Architecture:** Fixes are grouped by file to minimize re-reads. Security fixes touch addon/ai_bridge.py (exec sandbox), launcher.sh (GUI error script), agent/voice.py (tmpfile). Error handling touches agent/app.py and agent/llm_client.py. UX touches agent/app.py (tooltips, history, progress). Documentation touches README.md, requirements.txt.

**Tech Stack:** Python 3.11+, tkinter, bash, bpy (Blender Python API)

---

### Task 1: Fix shell injection — create gui_error.py helper

**Files:**
- Create: `agent/gui_error.py`
- Modify: `launcher.sh`

**Step 1: Create agent/gui_error.py**

```python
#!/usr/bin/env python3
"""Show a GUI error dialog. Called from launcher.sh to avoid shell injection."""
import sys
import tkinter as tk
from tkinter import messagebox

def show_error(msg: str) -> None:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("3DPrintVoice", msg)
    root.destroy()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        show_error(sys.argv[1])
    else:
        show_error("An unknown error occurred.")
```

**Step 2: Update launcher.sh — replace _gui_error function**

Replace the `_gui_error()` function with:

```bash
_gui_error() {
    python3 "$PROJECT_DIR/agent/gui_error.py" "$1" 2>/dev/null \
        || echo "[3DPrintVoice] ERROR: $1"
}
```

This passes the message as a proper argument (sys.argv), never interpolated into Python source.

**Step 3: Verify syntax**

```bash
python3 -c "import ast; ast.parse(open('agent/gui_error.py').read()); print('OK')"
bash -n launcher.sh && echo "OK"
```

**Step 4: Commit**

```bash
git add agent/gui_error.py launcher.sh
git commit -m "security: fix shell injection — use gui_error.py helper instead of inline Python"
```

---

### Task 2: Sandbox exec() in Blender addon

**Files:**
- Modify: `addon/ai_bridge.py`

**Step 1: Add code validator and restricted exec**

Add above `_execute_bpy()`:

```python
_BLOCKED_PATTERNS = [
    "import os", "import sys", "import subprocess", "import socket",
    "import shutil", "import pathlib",
    "__import__", "eval(", "exec(", "compile(",
    "open(", "getattr(", "setattr(", "delattr(",
    "globals(", "locals(", "vars(",
    "os.system", "os.popen", "os.remove", "os.unlink",
    "subprocess.run", "subprocess.Popen", "subprocess.call",
]


def _validate_bpy_code(code: str) -> str | None:
    """Check code for dangerous patterns. Returns error string or None if safe."""
    for pattern in _BLOCKED_PATTERNS:
        if pattern in code:
            return f"Blocked: code contains forbidden pattern '{pattern}'"
    return None
```

Modify `_execute_bpy()`:

```python
def _execute_bpy(code):
    """Execute bpy code string in a restricted sandbox."""
    # Validate before executing
    violation = _validate_bpy_code(code)
    if violation:
        return {"status": "error", "error": violation}

    import math, mathutils
    restricted_globals = {
        "bpy": bpy,
        "math": math,
        "mathutils": mathutils,
        "__builtins__": {
            "range": range, "len": len, "int": int, "float": float,
            "str": str, "bool": bool, "list": list, "dict": dict,
            "tuple": tuple, "set": set, "print": print, "abs": abs,
            "min": min, "max": max, "round": round, "enumerate": enumerate,
            "zip": zip, "sorted": sorted, "reversed": reversed,
            "isinstance": isinstance, "type": type, "hasattr": hasattr,
            "True": True, "False": False, "None": None,
            "__import__": _blocked_import,
        },
    }
    try:
        bpy.ops.ed.undo_push(message="AI Bridge command")
        exec(code, restricted_globals)
        result_val = restricted_globals.get("result", "executed")
        return {"status": "ok", "result": result_val}
    except Exception:
        return {"status": "error", "error": traceback.format_exc()}
```

Add the blocked import helper:

```python
def _blocked_import(name, *args, **kwargs):
    allowed = {"math", "mathutils", "bmesh", "json"}
    if name in allowed:
        import importlib
        return importlib.import_module(name)
    raise ImportError(f"Import of '{name}' is not allowed in bpy code execution")
```

**Step 2: Add localhost-only origin check to do_POST**

In `CommandHandler.do_POST`, add at the top:

```python
if self.client_address[0] != "127.0.0.1":
    self._respond(403, {"status": "error", "error": "Only localhost connections allowed"})
    return
```

**Step 3: Add execution timeout (5 seconds)**

Wrap exec in a thread with timeout:

```python
import concurrent.futures

def _execute_bpy(code):
    violation = _validate_bpy_code(code)
    if violation:
        return {"status": "error", "error": violation}

    import math, mathutils
    restricted_globals = {
        "bpy": bpy,
        "math": math,
        "mathutils": mathutils,
        "__builtins__": {
            "range": range, "len": len, "int": int, "float": float,
            "str": str, "bool": bool, "list": list, "dict": dict,
            "tuple": tuple, "set": set, "print": print, "abs": abs,
            "min": min, "max": max, "round": round, "enumerate": enumerate,
            "zip": zip, "sorted": sorted, "reversed": reversed,
            "isinstance": isinstance, "type": type, "hasattr": hasattr,
            "True": True, "False": False, "None": None,
            "__import__": _blocked_import,
        },
    }
    try:
        bpy.ops.ed.undo_push(message="AI Bridge command")
        exec(code, restricted_globals)
        result_val = restricted_globals.get("result", "executed")
        return {"status": "ok", "result": result_val}
    except Exception:
        return {"status": "error", "error": traceback.format_exc()}
```

Note: We CANNOT use threading timeout around exec in Blender because bpy ops must run on main thread. The existing 30s HTTP timeout on the client side is the real safeguard. Instead, add a code length limit:

```python
MAX_CODE_LENGTH = 10000  # 10KB max

def _execute_bpy(code):
    if len(code) > MAX_CODE_LENGTH:
        return {"status": "error", "error": f"Code too long ({len(code)} chars, max {MAX_CODE_LENGTH})"}
    # ... rest of function
```

**Step 4: Verify syntax**

```bash
python3 -c "import ast; ast.parse(open('addon/ai_bridge.py').read()); print('OK')"
```

**Step 5: Commit**

```bash
git add addon/ai_bridge.py
git commit -m "security: sandbox exec() — restricted builtins, blocked patterns, localhost-only, code size limit"
```

---

### Task 3: Fix tempfile.mktemp() in voice.py

**Files:**
- Modify: `agent/voice.py`

**Step 1: Find and replace mktemp with mkstemp**

In `agent/voice.py`, find the line with `tempfile.mktemp(suffix=".wav")` and replace:

```python
# OLD:
self._wav_path = tempfile.mktemp(suffix=".wav")

# NEW:
fd, self._wav_path = tempfile.mkstemp(suffix=".wav")
os.close(fd)  # arecord will write to this path
```

Ensure `os` is imported at the top of the file (it likely already is).

**Step 2: Commit**

```bash
git add agent/voice.py
git commit -m "security: fix tmpfile race condition — use mkstemp instead of mktemp"
```

---

### Task 4: Fix desktop entry Exec line

**Files:**
- Modify: `3d-print-voice.desktop`
- Modify: `install.sh` (heredoc that generates desktop entry)

**Step 1: Update 3d-print-voice.desktop**

Change:
```
Exec=bash -c '/opt/3d-print-voice/launcher.sh'
```
to:
```
Exec=/opt/3d-print-voice/launcher.sh
```

**Step 2: Update install.sh heredoc**

Same change in the `cat > ... << DESKTOP` block.

**Step 3: Commit**

```bash
git add 3d-print-voice.desktop install.sh
git commit -m "fix: desktop entry — direct Exec path instead of bash -c wrapper"
```

---

### Task 5: LLM timeout feedback + elapsed time display

**Files:**
- Modify: `agent/llm_client.py`
- Modify: `agent/app.py`

**Step 1: Reduce urllib timeout and add input length cap in llm_client.py**

Change timeout from 120 to 30 seconds. Add input length cap:

```python
MAX_INPUT_LENGTH = 2000

def generate_bpy_code(user_text: str, scene_context: str = "") -> str:
    if len(user_text) > MAX_INPUT_LENGTH:
        return f"# CANNOT_EXECUTE: input too long ({len(user_text)} chars, max {MAX_INPUT_LENGTH})"
    # ... rest unchanged
```

In `_ollama_chat`, change `timeout=120` to `timeout=30`.

**Step 2: Add elapsed time display in app.py**

In `_process_command()`, record start time. In `_run_pipeline()`, update status every second with elapsed time. Add a timer-based updater:

In `_process_command`:
```python
import time
self._cmd_start = time.monotonic()
self._elapsed_timer = self.root.after(1000, self._update_elapsed, text)
```

Add method:
```python
def _update_elapsed(self, text):
    if not self._processing:
        return
    elapsed = int(time.monotonic() - self._cmd_start)
    self._set_result(f'"{text}" — generating... ({elapsed}s)', YELLOW)
    self._elapsed_timer = self.root.after(1000, self._update_elapsed, text)
```

In `_run_pipeline` finally block, cancel the timer:
```python
if hasattr(self, '_elapsed_timer'):
    self.root.after_cancel(self._elapsed_timer)
```

**Step 3: Run existing tests**

```bash
pytest tests/ -v
```

**Step 4: Commit**

```bash
git add agent/llm_client.py agent/app.py
git commit -m "fix: LLM timeout reduced to 30s, input length cap, elapsed time display"
```

---

### Task 6: Threading safety + MIC button disable

**Files:**
- Modify: `agent/app.py`

**Step 1: Add threading lock for _processing flag**

In `__init__`:
```python
self._lock = threading.Lock()
```

In `_process_command`:
```python
def _process_command(self, text):
    with self._lock:
        if self._processing:
            return
        self._processing = True
    # ... rest unchanged
```

In `_run_pipeline` finally block:
```python
with self._lock:
    self._processing = False
```

**Step 2: Disable MIC button when mic unavailable**

In `_update_status`, after the mic check:

```python
# Mic
try:
    import sounddevice as sd
    sd.query_devices(kind="input")
    if self._whisper_loaded:
        self.root.after(0, self._dot_mic.set_ok)
        self.root.after(0, self._mic_btn.configure, {"state": tk.NORMAL})
    else:
        self.root.after(0, self._dot_mic.set_warn)
except Exception:
    self.root.after(0, self._dot_mic.set_error)
    self.root.after(0, self._mic_btn.configure, {"state": tk.DISABLED})
```

**Step 3: Commit**

```bash
git add agent/app.py
git commit -m "fix: add threading lock for processing flag, disable MIC when unavailable"
```

---

### Task 7: Launcher robustness — dependency check, model verification

**Files:**
- Modify: `launcher.sh`

**Step 1: Add dependency verification after venv activation**

After the venv activation block, add:

```bash
# --- Verify Python dependencies ---
if ! python3 -c "import faster_whisper" &>/dev/null 2>&1; then
    if [ -d "$PROJECT_DIR/venv" ]; then
        _gui_error "Python dependencies are missing from the virtual environment.\n\nRun: $PROJECT_DIR/venv/bin/pip install -r $PROJECT_DIR/requirements.txt"
    else
        _gui_error "Python dependencies are not installed.\n\nRun: pip install -r $PROJECT_DIR/requirements.txt"
    fi
    exit 1
fi
```

**Step 2: Add model verification after pull**

After `ollama pull "$MODEL"`, add:

```bash
if ! ollama list 2>/dev/null | grep -q "$MODEL"; then
    _gui_error "Model $MODEL failed to download. Check your internet connection and disk space."
    exit 1
fi
```

**Step 3: Verify syntax**

```bash
bash -n launcher.sh && echo "OK"
```

**Step 4: Commit**

```bash
git add launcher.sh
git commit -m "fix: launcher verifies dependencies and model after pull"
```

---

### Task 8: UX — Tooltips for status dots and 3D Print button

**Files:**
- Modify: `agent/app.py`

**Step 1: Add Tooltip helper class**

Add near the top of app.py, after the StatusDot class:

```python
class Tooltip:
    """Simple hover tooltip for tkinter widgets."""

    def __init__(self, widget, text):
        self._widget = widget
        self._text = text
        self._tip = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def update_text(self, text):
        self._text = text

    def _show(self, event=None):
        x = self._widget.winfo_rootx() + 20
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        self._tip = tk.Toplevel(self._widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(self._tip, text=self._text, bg="#FFFFDD", fg="#333",
                       relief=tk.SOLID, borderwidth=1,
                       font=("sans-serif", 9), padx=6, pady=3)
        lbl.pack()

    def _hide(self, event=None):
        if self._tip:
            self._tip.destroy()
            self._tip = None
```

**Step 2: Add tooltips to status dots**

In `_build_ui`, after creating the dots, add:

```python
self._tip_blender = Tooltip(self._dot_blender, "Blender: checking...")
self._tip_ollama = Tooltip(self._dot_ollama, "Ollama: checking...")
self._tip_mic = Tooltip(self._dot_mic, "Mic: checking...")
```

In `_update_status`, update tooltip text alongside the dot color:

```python
# Blender
if blender_client.health_check():
    self.root.after(0, self._dot_blender.set_ok)
    self.root.after(0, self._tip_blender.update_text, "Blender: connected (localhost:6789)")
else:
    self.root.after(0, self._dot_blender.set_error)
    self.root.after(0, self._tip_blender.update_text, "Blender: not responding")
```

Similar for Ollama and Mic.

**Step 3: Add tooltip to 3D Print button**

After creating `self._print_btn`:

```python
Tooltip(self._print_btn, "Toggle 3D print view: metric units, mm, snap to grid")
```

**Step 4: Commit**

```bash
git add agent/app.py
git commit -m "feat: add hover tooltips to status dots and 3D Print button"
```

---

### Task 9: UX — Command history (up/down arrows)

**Files:**
- Modify: `agent/app.py`

**Step 1: Add history state in __init__**

```python
self._cmd_history = []
self._history_idx = -1
```

**Step 2: Record commands in _send_command**

At the start of `_send_command`, after `text = ...`:

```python
if text:
    self._cmd_history.append(text)
    if len(self._cmd_history) > 50:
        self._cmd_history.pop(0)
    self._history_idx = len(self._cmd_history)
```

**Step 3: Bind up/down arrow keys**

In `_build_ui`, after `self._input.bind("<Return>", ...)`:

```python
self._input.bind("<Up>", self._history_prev)
self._input.bind("<Down>", self._history_next)
```

**Step 4: Add history navigation methods**

```python
def _history_prev(self, event=None):
    if not self._cmd_history:
        return "break"
    if self._history_idx > 0:
        self._history_idx -= 1
    self._input.delete(0, tk.END)
    self._input.insert(0, self._cmd_history[self._history_idx])
    return "break"

def _history_next(self, event=None):
    if not self._cmd_history:
        return "break"
    if self._history_idx < len(self._cmd_history) - 1:
        self._history_idx += 1
        self._input.delete(0, tk.END)
        self._input.insert(0, self._cmd_history[self._history_idx])
    else:
        self._history_idx = len(self._cmd_history)
        self._input.delete(0, tk.END)
    return "break"
```

**Step 5: Commit**

```bash
git add agent/app.py
git commit -m "feat: command history with up/down arrow keys (max 50)"
```

---

### Task 10: UX — Wizard completion confirmation

**Files:**
- Modify: `agent/setup_wizard.py`

**Step 1: Add completion screen in _finish**

Replace the immediate `self.root.destroy()` with a brief confirmation:

```python
def _finish(self):
    tier = self._tier_var.get()
    config = load_config()
    config["model_tier"] = tier
    config["model"] = MODEL_TIERS[tier]
    config["first_run_done"] = True
    save_config(config)
    self._completed = True

    # Show brief confirmation
    self._clear()
    frame = tk.Frame(self.root, bg=BG, padx=40, pady=60)
    frame.pack(fill=tk.BOTH, expand=True)
    tk.Label(frame, text="Setup complete!", font=self._font_title,
             bg=BG, fg=GREEN).pack(pady=(0, 16))
    tk.Label(frame, text="Starting 3DPrintVoice...", font=self._font_body,
             bg=BG, fg=FG_DIM).pack()
    self.root.after(2000, self.root.destroy)
```

**Step 2: Commit**

```bash
git add agent/setup_wizard.py
git commit -m "feat: wizard shows completion confirmation before closing"
```

---

### Task 11: Move embedded bpy code to external files

**Files:**
- Create: `prompts/print_mode_capture.py`
- Create: `prompts/print_mode_apply.py`
- Modify: `agent/app.py`

**Step 1: Create prompts/print_mode_capture.py**

Move the content of `_BPY_CAPTURE_SETTINGS` to this file (the raw bpy code, not as a Python string).

**Step 2: Create prompts/print_mode_apply.py**

Move the content of `_BPY_APPLY_PRINT_MODE` to this file.

**Step 3: Update app.py to load from files**

Replace the class-level string constants with file loading:

```python
_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

# In _apply_print_mode and _restore_normal_mode, load the files:
def _apply_print_mode(self):
    capture_code = (_PROMPTS_DIR / "print_mode_capture.py").read_text()
    apply_code = (_PROMPTS_DIR / "print_mode_apply.py").read_text()
    # ... use capture_code and apply_code instead of self._BPY_CAPTURE_SETTINGS etc.
```

Remove the `_BPY_CAPTURE_SETTINGS` and `_BPY_APPLY_PRINT_MODE` class constants.

**Step 4: Commit**

```bash
git add prompts/print_mode_capture.py prompts/print_mode_apply.py agent/app.py
git commit -m "refactor: move embedded bpy code to external files in prompts/"
```

---

### Task 12: Log rotation + error message expansion

**Files:**
- Modify: `agent/app.py`

**Step 1: Add log rotation in _log method**

Before writing, check and rotate:

```python
def _log(self, user_text, bpy_code, result):
    LOG_DIR.mkdir(exist_ok=True)
    # Rotate: keep max 10 session logs
    logs = sorted(LOG_DIR.glob("session_*.log"))
    while len(logs) > 9:
        logs.pop(0).unlink()
    # ... rest of existing log code
```

**Step 2: Increase error display length**

Change error truncation from 80 to 120 chars:

```python
# In _run_pipeline, change:
short_err = error.split("\n")[-2] if "\n" in error else error[:80]
# To:
short_err = error.split("\n")[-2] if "\n" in error else error[:120]
```

**Step 3: Commit**

```bash
git add agent/app.py
git commit -m "fix: log rotation (max 10 files), longer error display (120 chars)"
```

---

### Task 13: Pin requirements.txt versions

**Files:**
- Modify: `requirements.txt`

**Step 1: Check installed versions**

```bash
pip show faster-whisper numpy 2>/dev/null | grep -E "^(Name|Version)"
```

**Step 2: Pin to current versions**

Update requirements.txt with exact pins, e.g.:

```
faster-whisper==1.1.1
numpy==1.26.4
```

(Use actual versions from step 1.)

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: pin dependency versions in requirements.txt"
```

---

### Task 14: Update README.md — document platform, limitations

**Files:**
- Modify: `README.md`

**Step 1: Add platform section and update requirements**

After the existing Requirements section, add/update:

```markdown
## Platform

Linux only (Ubuntu 22.04+, Linux Mint 21+). Not compatible with macOS or Windows.

Voice input requires ALSA (`arecord`). The MIC button is automatically disabled
if no microphone is detected.
```

Update the Requirements section to mention configurable model tiers:

```markdown
## Requirements

- Blender 4.0+ (5.1+ recommended)
- Python 3.11+
- NVIDIA GPU with 3GB+ VRAM (determines model tier):
  - 12GB+: Full (Qwen2.5-Coder 14B) — best quality
  - 6-11GB: Medium (Qwen2.5-Coder 7B) — good quality
  - 3-5GB: Lite (Qwen2.5-Coder 3B) — basic commands
- Ollama (installed via official script)
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: document Linux-only platform, model tiers, voice requirements"
```

---

### Task 15: Update CHANGELOG, DEVELOPMENT_LOG, commit plan

**Files:**
- Modify: `docs/CHANGELOG.md`
- Modify: `docs/DEVELOPMENT_LOG.md`

**Step 1: Add v0.4.0 entry to CHANGELOG**

Prepend before the [0.3.0] entry:

```markdown
## [0.4.0] - 2026-04-06

### Added
- First-launch setup wizard with system check and model tier selection (Full/Medium/Lite)
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

### Changed
- Project renamed: BlenderAI → 3DPrintVoice
- Launcher restructured: setup wizard runs before services
- LLM model name read from config (configurable via wizard)
- Blender addon: exec() sandboxed with restricted builtins and blocked patterns
- LLM timeout reduced from 120s to 30s
- Error messages display up to 120 chars (was 80)
- Log rotation: max 10 session files

### Fixed
- Shell injection vulnerability in launcher error display
- Unrestricted exec() with full __builtins__ access
- tempfile.mktemp() race condition in voice recording
- MIC button now disabled when no microphone detected
- Threading race condition on _processing flag
- Desktop entry uses direct Exec path instead of bash -c wrapper

### Security
- Blocked dangerous patterns in bpy code execution (os, subprocess, eval, etc.)
- Restricted __builtins__ in exec scope (only safe builtins allowed)
- Localhost-only origin check on addon HTTP endpoint
- Code size limit (10KB) on bpy execution
- Input length cap (2000 chars) on LLM requests
```

**Step 2: Update DEVELOPMENT_LOG session handoff**

Add a new session entry at the top documenting what was done.

**Step 3: Commit**

```bash
git add docs/CHANGELOG.md docs/DEVELOPMENT_LOG.md docs/plans/2026-04-06-audit-remediation.md
git commit -m "docs: v0.4.0 changelog, development log, audit remediation plan"
```

---

### Task 16: End-to-end verification

**Step 1: Run all tests**

```bash
pytest tests/ -v
```

**Step 2: Syntax check all Python files**

```bash
python3 -c "
import ast
for f in ['agent/__init__.py', 'agent/config.py', 'agent/setup_wizard.py',
          'agent/setup_wizard_main.py', 'agent/app.py', 'agent/llm_client.py',
          'agent/main.py', 'agent/blender_client.py', 'agent/voice.py',
          'agent/gui_error.py', 'addon/ai_bridge.py']:
    ast.parse(open(f).read())
    print(f'OK: {f}')
"
```

**Step 3: Verify bash scripts**

```bash
bash -n install.sh && bash -n uninstall.sh && bash -n launcher.sh && echo "All bash OK"
```

**Step 4: Verify addon sandbox blocks dangerous code**

```bash
python3 -c "
import ast
code = open('addon/ai_bridge.py').read()
tree = ast.parse(code)
# Check _BLOCKED_PATTERNS exists
assert '_BLOCKED_PATTERNS' in code, 'Missing blocked patterns'
assert '_validate_bpy_code' in code, 'Missing validator'
assert '_blocked_import' in code, 'Missing import blocker'
print('Addon sandbox verified')
"
```

**Step 5: Verify no shell injection in launcher**

```bash
grep -c "messagebox.showerror" launcher.sh | grep -q "^0$" && echo "No inline Python in launcher — PASS" || echo "FAIL: inline Python still present"
```

**Step 6: Final commit if fixes needed**

```bash
git add -A && git commit -m "fix: address issues found during verification" || echo "Nothing to fix"
```

---

### Task 17: Push to remote

**Step 1: Push all commits**

```bash
git push origin main
```
