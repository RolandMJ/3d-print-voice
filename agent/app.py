#!/usr/bin/env python3
"""3DPrintVoice Control Bar — Blender-themed top bar GUI.

Provides text and voice input for controlling Blender via natural language.
Sits at the top of the screen, always on top, with status indicators.
"""

import datetime
import subprocess
import threading
import time
import tkinter as tk
from tkinter import font as tkfont
from pathlib import Path

from agent.llm_client import generate_bpy_code
from agent import blender_client
from agent.voice import VoiceRecorder, _get_whisper

# --- Theme (Blender dark UI) ---
BG = "#2D2D2D"
BG_FIELD = "#1D1D1D"
BG_STATUS = "#252525"
FG = "#E0E0E0"
FG_DIM = "#808080"
FG_RESULT = "#A0D0A0"
FG_ERROR = "#E08080"
ORANGE = "#E87D0D"
ORANGE_HOVER = "#F09030"
GREEN = "#4CAF50"
RED = "#E05050"
YELLOW = "#F0C040"
BORDER = "#3D3D3D"

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
BAR_HEIGHT = 100


class Tooltip:
    """Simple hover tooltip for tkinter widgets."""

    def __init__(self, widget, text=""):
        self._widget = widget
        self._text = text
        self._tip = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def update_text(self, text):
        self._text = text

    def _show(self, event=None):
        if not self._text:
            return
        try:
            if not self._widget.winfo_exists():
                return
            x = self._widget.winfo_rootx() + 20
            y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
            self._tip = tk.Toplevel(self._widget)
            self._tip.wm_overrideredirect(True)
            self._tip.wm_geometry(f"+{x}+{y}")
            lbl = tk.Label(self._tip, text=self._text, bg="#FFFFDD", fg="#333",
                           relief=tk.SOLID, borderwidth=1,
                           font=("sans-serif", 9), padx=6, pady=3)
            lbl.pack()
        except tk.TclError:
            pass

    def _hide(self, event=None):
        try:
            if self._tip:
                self._tip.destroy()
                self._tip = None
        except tk.TclError:
            self._tip = None


class StatusDot(tk.Canvas):
    """Small colored dot indicator."""

    def __init__(self, parent, label, **kwargs):
        super().__init__(parent, width=12, height=12, bg=BG_STATUS,
                         highlightthickness=0, **kwargs)
        self._dot = self.create_oval(2, 2, 10, 10, fill=RED, outline="")
        self._label = label

    def set_ok(self):
        self.itemconfig(self._dot, fill=GREEN)

    def set_error(self):
        self.itemconfig(self._dot, fill=RED)

    def set_warn(self):
        self.itemconfig(self._dot, fill=YELLOW)


class PrintVoiceApp:
    """Main application — Blender-themed control bar."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("3DPrintVoice")
        self.root.configure(bg=BG)
        self.root.attributes("-topmost", True)

        # Position at top of screen, full width
        screen_w = self.root.winfo_screenwidth()
        self.root.geometry(f"{screen_w}x{BAR_HEIGHT}+0+0")
        self.root.resizable(True, False)
        self.root.minsize(800, BAR_HEIGHT)

        # Remove window decorations for a clean bar look, but keep close button
        self.root.overrideredirect(False)

        # Fonts
        self._font_input = tkfont.Font(family="monospace", size=14)
        self._font_result = tkfont.Font(family="monospace", size=12)
        self._font_status = tkfont.Font(family="sans-serif", size=9)
        self._font_btn = tkfont.Font(family="sans-serif", size=12, weight="bold")

        # State
        self._lock = threading.Lock()
        self._processing = False
        self._cmd_count = 0
        self._print_mode = False
        self._saved_blender_settings = None
        self._cmd_history = []
        self._history_idx = -1
        self._scene_context = ""

        # Voice
        self._recorder = VoiceRecorder(on_auto_stop=self._on_voice_result)
        self._whisper_loaded = False

        # Build UI
        self._build_ui()

        # Start status checker
        self._check_status()

        # Preload whisper in background
        threading.Thread(target=self._preload_whisper, daemon=True).start()

        # Bind close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Global key binding
        self.root.bind_all("<F1>", lambda e: self._toggle_mic())
        self.root.bind_all("<F2>", lambda e: self._open_reference())

    def _build_ui(self):
        """Build the two-row control bar."""
        # Main container
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Left side (controls) — takes most width
        left = tk.Frame(main, bg=BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Right side (status) — fixed width
        right = tk.Frame(main, bg=BG_STATUS, width=160, padx=8, pady=4)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        right.pack_propagate(False)

        # Separator (right of middle)
        sep = tk.Frame(main, bg=BORDER, width=1)
        sep.pack(side=tk.RIGHT, fill=tk.Y, padx=4)

        # Middle section — 3D Print toggle
        mid = tk.Frame(main, bg=BG, padx=8)
        mid.pack(side=tk.RIGHT, fill=tk.Y)

        self._print_btn = tk.Button(
            mid, text="3D PRINT\n   OFF", font=self._font_status,
            bg=BG_FIELD, fg=FG_DIM, activebackground=GREEN,
            activeforeground="white", relief=tk.FLAT,
            cursor="hand2", command=self._toggle_print_mode,
            padx=10, pady=6, width=10,
        )
        self._print_btn.pack(side=tk.TOP, expand=True)
        Tooltip(self._print_btn, "Toggle 3D print view: metric units, mm, snap to grid")

        self._ref_btn = tk.Button(
            mid, text=" REF ", font=self._font_status,
            bg=BG_FIELD, fg=FG_DIM, activebackground=ORANGE,
            activeforeground="white", relief=tk.FLAT,
            cursor="hand2", command=self._open_reference,
            padx=10, pady=4,
        )
        self._ref_btn.pack(side=tk.BOTTOM, expand=True)
        Tooltip(self._ref_btn, "Command reference: 79 commands across 9 categories (EN/DE)")

        # Separator (left of middle)
        sep2 = tk.Frame(main, bg=BORDER, width=1)
        sep2.pack(side=tk.RIGHT, fill=tk.Y, padx=4)

        # --- Row 1: Mic + Input + Send ---
        row1 = tk.Frame(left, bg=BG)
        row1.pack(fill=tk.X, pady=(0, 2))

        # Mic button
        self._mic_btn = tk.Button(
            row1, text=" MIC ", font=self._font_btn,
            bg=BG_FIELD, fg=FG, activebackground=ORANGE,
            activeforeground="white", relief=tk.FLAT,
            cursor="hand2", command=self._toggle_mic,
            padx=12, pady=4,
        )
        self._mic_btn.pack(side=tk.LEFT, padx=(0, 6))

        # Text input
        self._input = tk.Entry(
            row1, font=self._font_input,
            bg=BG_FIELD, fg=FG, insertbackground=ORANGE,
            relief=tk.FLAT, borderwidth=0,
            selectbackground=ORANGE, selectforeground="white",
        )
        self._input.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
        self._input.bind("<Return>", lambda e: self._send_command())
        self._input.bind("<Up>", self._history_prev)
        self._input.bind("<Down>", self._history_next)
        self._input.focus_set()

        # Send button
        self._send_btn = tk.Button(
            row1, text=" SEND ", font=self._font_btn,
            bg=ORANGE, fg="white", activebackground=ORANGE_HOVER,
            activeforeground="white", relief=tk.FLAT,
            cursor="hand2", command=self._send_command,
            padx=12, pady=4,
        )
        self._send_btn.pack(side=tk.RIGHT, padx=(6, 0))

        # --- Row 2: Last command result ---
        row2 = tk.Frame(left, bg=BG)
        row2.pack(fill=tk.X)

        lbl = tk.Label(row2, text="Last:", font=self._font_status,
                        bg=BG, fg=FG_DIM, anchor="w")
        lbl.pack(side=tk.LEFT, padx=(0, 4))

        self._result_var = tk.StringVar(value="No commands yet")
        self._result_label = tk.Label(
            row2, textvariable=self._result_var,
            font=self._font_result, bg=BG_FIELD, fg=FG_DIM,
            anchor="w", relief=tk.FLAT, padx=8, pady=4,
        )
        self._result_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # --- Right side: Status indicators ---
        self._dot_blender = self._add_status_row(right, "Blender")
        self._dot_ollama = self._add_status_row(right, "Ollama")
        self._dot_mic = self._add_status_row(right, "Mic")

        self._tip_blender = Tooltip(self._dot_blender, "Blender: checking...")
        self._tip_ollama = Tooltip(self._dot_ollama, "Ollama: checking...")
        self._tip_mic = Tooltip(self._dot_mic, "Mic: checking...")

        # VRAM label
        self._vram_var = tk.StringVar(value="VRAM: --")
        tk.Label(right, textvariable=self._vram_var, font=self._font_status,
                 bg=BG_STATUS, fg=FG_DIM, anchor="w").pack(anchor="w", pady=(4, 0))

        # Command count
        self._count_var = tk.StringVar(value="Cmds: 0")
        tk.Label(right, textvariable=self._count_var, font=self._font_status,
                 bg=BG_STATUS, fg=FG_DIM, anchor="w").pack(anchor="w")

    def _add_status_row(self, parent, label):
        """Add a status dot + label row."""
        row = tk.Frame(parent, bg=BG_STATUS)
        row.pack(anchor="w", pady=1)
        dot = StatusDot(row, label)
        dot.pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(row, text=label, font=self._font_status,
                 bg=BG_STATUS, fg=FG_DIM, anchor="w").pack(side=tk.LEFT)
        return dot

    # --- 3D Print Mode ---

    _PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

    def _toggle_print_mode(self):
        """Toggle between normal and 3D-print-optimized Blender settings."""
        if self._processing:
            return
        if not self._print_mode:
            threading.Thread(target=self._apply_print_mode, daemon=True).start()
        else:
            threading.Thread(target=self._restore_normal_mode, daemon=True).start()

    def _apply_print_mode(self):
        """Capture current settings, then apply 3D print config."""
        self.root.after(0, self._set_result, "Capturing Blender settings...", YELLOW)
        # Capture current settings
        capture_result = blender_client.execute((self._PROMPTS_DIR / "print_mode_capture.py").read_text())
        if capture_result["status"] == "ok":
            try:
                import json
                self._saved_blender_settings = json.loads(
                    capture_result.get("result", "{}"))
            except Exception:
                self._saved_blender_settings = None

        # Apply 3D print settings
        self.root.after(0, self._set_result, "Applying 3D print settings...", YELLOW)
        result = blender_client.execute((self._PROMPTS_DIR / "print_mode_apply.py").read_text())
        if result["status"] == "ok":
            self._print_mode = True
            self.root.after(0, self._print_btn.configure,
                            {"bg": GREEN, "fg": "white", "text": "3D PRINT\n    ON"})
            self.root.after(0, self._set_result,
                            "3D Print mode ON — metric, mm, snap to grid", FG_RESULT)
        else:
            err = result.get("error", "unknown")[:60]
            self.root.after(0, self._set_result,
                            f"3D Print mode failed: {err}", FG_ERROR)

    def _restore_normal_mode(self):
        """Restore previously captured Blender settings."""
        if not self._saved_blender_settings:
            # No saved settings — just reset to Blender defaults
            reset_code = """\
import bpy
s = bpy.context.scene
s.unit_settings.system = 'METRIC'
s.unit_settings.length_unit = 'ADAPTIVE'
s.unit_settings.scale_length = 1.0
for a in bpy.context.screen.areas:
    if a.type == 'VIEW_3D':
        for sp in a.spaces:
            if sp.type == 'VIEW_3D':
                sp.clip_start = 0.1
                sp.clip_end = 1000
                break
        break
ts = s.tool_settings
ts.use_snap = False
"""
        else:
            s = self._saved_blender_settings
            # Validate all values before interpolation to prevent injection
            VALID_SYSTEMS = {"METRIC", "IMPERIAL", "NONE"}
            VALID_LENGTHS = {"ADAPTIVE", "MILLIMETERS", "CENTIMETERS", "METERS",
                             "KILOMETERS", "MICROMETERS", "MILES", "FEET",
                             "INCHES", "THOU"}
            VALID_SNAP = {"INCREMENT", "VERTEX", "EDGE", "FACE", "VOLUME",
                          "EDGE_MIDPOINT", "EDGE_PERPENDICULAR", "GRID"}

            unit_sys = s.get("unit_system", "METRIC")
            if unit_sys not in VALID_SYSTEMS:
                unit_sys = "METRIC"
            length_unit = s.get("length_unit", "ADAPTIVE")
            if length_unit not in VALID_LENGTHS:
                length_unit = "ADAPTIVE"
            scale = float(s.get("scale_length", 1.0))
            clip_s = float(s.get("clip_start", 0.1))
            clip_e = float(s.get("clip_end", 1000))
            use_snap = bool(s.get("snap", False))
            snap_els = [e for e in s.get("snap_elements", ["INCREMENT"])
                        if e in VALID_SNAP]
            if not snap_els:
                snap_els = ["INCREMENT"]
            snap_set = "{" + ", ".join(f"'{e}'" for e in snap_els) + "}"

            reset_code = f"""\
import bpy
s = bpy.context.scene
s.unit_settings.system = '{unit_sys}'
s.unit_settings.length_unit = '{length_unit}'
s.unit_settings.scale_length = {scale}
for a in bpy.context.screen.areas:
    if a.type == 'VIEW_3D':
        for sp in a.spaces:
            if sp.type == 'VIEW_3D':
                sp.clip_start = {clip_s}
                sp.clip_end = {clip_e}
                break
        break
ts = s.tool_settings
ts.use_snap = {use_snap}
ts.snap_elements = {snap_set}
"""
        self.root.after(0, self._set_result, "Restoring original settings...", YELLOW)
        result = blender_client.execute(reset_code)
        if result["status"] == "ok":
            self._print_mode = False
            self.root.after(0, self._print_btn.configure,
                            {"bg": BG_FIELD, "fg": FG_DIM, "text": "3D PRINT\n   OFF"})
            self.root.after(0, self._set_result,
                            "Original Blender settings restored", FG_RESULT)
        else:
            err = result.get("error", "unknown")[:60]
            self.root.after(0, self._set_result,
                            f"Restore failed: {err}", FG_ERROR)

    # --- Actions ---

    def _open_reference(self):
        """Open the command reference HTML in the default browser."""
        ref_path = Path(__file__).resolve().parent.parent / "docs" / "command-reference.html"
        if ref_path.exists():
            subprocess.Popen(["xdg-open", str(ref_path)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            self._set_result("Reference file not found", FG_ERROR)

    def _send_command(self):
        """Send typed text to LLM → Blender."""
        text = self._input.get().strip()
        if not text or self._processing:
            return
        self._cmd_history.append(text)
        if len(self._cmd_history) > 50:
            self._cmd_history.pop(0)
        self._history_idx = len(self._cmd_history)
        self._input.delete(0, tk.END)
        self._process_command(text)

    def _history_prev(self, event=None):
        """Navigate to previous command in history."""
        if not self._cmd_history:
            return "break"
        if self._history_idx > 0:
            self._history_idx -= 1
        self._input.delete(0, tk.END)
        self._input.insert(0, self._cmd_history[self._history_idx])
        return "break"

    def _history_next(self, event=None):
        """Navigate to next command in history."""
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

    def _toggle_mic(self):
        """Toggle voice recording on/off."""
        if self._recorder.is_recording:
            # Stop and transcribe
            self._mic_btn.configure(bg=BG_FIELD, fg=FG, text=" MIC ")
            self._set_result("Transcribing...", FG_DIM)
            threading.Thread(target=self._stop_and_transcribe, daemon=True).start()
        else:
            # Start recording
            self._recorder.start()
            self._mic_btn.configure(bg=ORANGE, fg="white", text=" REC ")
            self._set_result("Recording... (speak now, auto-stops on silence)", YELLOW)

    def _stop_and_transcribe(self):
        """Stop recording and transcribe (runs in background thread)."""
        text = self._recorder.stop()
        self.root.after(0, self._mic_btn.configure,
                        {"bg": BG_FIELD, "fg": FG, "text": " MIC "})
        if text:
            self.root.after(0, self._input.delete, 0, tk.END)
            self.root.after(0, self._input.insert, 0, text)
            self.root.after(0, self._process_command, text)
        else:
            self.root.after(0, self._set_result,
                            "No speech detected. Try again.", FG_ERROR)

    def _on_voice_result(self, text):
        """Called from voice auto-stop (background thread)."""
        self.root.after(0, self._mic_btn.configure,
                        {"bg": BG_FIELD, "fg": FG, "text": " MIC "})
        if text:
            self.root.after(0, self._input.delete, 0, tk.END)
            self.root.after(0, self._input.insert, 0, text)
            self.root.after(0, self._process_command, text)

    def _process_command(self, text):
        """Full pipeline: text → LLM → Blender. Runs in background."""
        with self._lock:
            if self._processing:
                return
            self._processing = True
        self._cmd_start = time.monotonic()
        self._send_btn.configure(state=tk.DISABLED, bg=BG_FIELD)
        self._set_result(f'"{text}" — generating code...', YELLOW)
        self._elapsed_timer = self.root.after(1000, self._update_elapsed, text)
        threading.Thread(target=self._run_pipeline, args=(text,),
                         daemon=True).start()

    def _update_elapsed(self, text):
        """Show elapsed seconds during processing."""
        if not self._processing:
            return
        elapsed = int(time.monotonic() - self._cmd_start)
        self._set_result(f'"{text}" — generating... ({elapsed}s)', YELLOW)
        self._elapsed_timer = self.root.after(1000, self._update_elapsed, text)

    def _run_pipeline(self, text):
        """Execute the full command pipeline (background thread)."""
        try:
            # Generate bpy code with scene context
            bpy_code = generate_bpy_code(text, scene_context=self._scene_context)

            if bpy_code.strip().startswith("# CANNOT_EXECUTE"):
                self.root.after(0, self._set_result,
                                f'"{text}" — declined: {bpy_code.strip()}', FG_ERROR)
                self._log(text, bpy_code, {"status": "declined"})
                return

            # Send to Blender
            self.root.after(0, self._set_result,
                            f'"{text}" — sending to Blender...', YELLOW)
            result = blender_client.execute(bpy_code)

            if result["status"] == "ok":
                self._cmd_count += 1
                self.root.after(0, self._count_var.set, f"Cmds: {self._cmd_count}")
                self.root.after(0, self._set_result,
                                f'"{text}" — Done.', FG_RESULT)
                self._log(text, bpy_code, result)
                self._update_scene_context()
            else:
                error = result.get("error", "unknown")
                # Try retry
                self.root.after(0, self._set_result,
                                f'"{text}" — error, retrying...', YELLOW)
                retry_prompt = (
                    f"The previous code failed with this error:\n{error}\n\n"
                    f"Original request: {text}\n\nFix the code."
                )
                bpy_retry = generate_bpy_code(retry_prompt)
                result_retry = blender_client.execute(bpy_retry)

                if result_retry["status"] == "ok":
                    self._cmd_count += 1
                    self.root.after(0, self._count_var.set,
                                    f"Cmds: {self._cmd_count}")
                    self.root.after(0, self._set_result,
                                    f'"{text}" — Done (retry).', FG_RESULT)
                    self._log(text, bpy_retry, result_retry)
                    self._update_scene_context()
                else:
                    short_err = error.split("\n")[-2] if "\n" in error else error[:120]
                    self.root.after(0, self._set_result,
                                    f'"{text}" — Failed: {short_err}', FG_ERROR)
                    self._log(text, bpy_retry, result_retry)

        except Exception as e:
            self.root.after(0, self._set_result,
                            f'Error: {str(e)[:80]}', FG_ERROR)
        finally:
            with self._lock:
                self._processing = False
            # _update_elapsed self-terminates when _processing is False
            self.root.after(0, self._send_btn.configure,
                            {"state": tk.NORMAL, "bg": ORANGE})

    def _update_scene_context(self):
        """Query Blender scene state for context-aware next command."""
        try:
            scene = blender_client.query_scene()
            if scene.get("objects"):
                import json
                self._scene_context = json.dumps(scene, indent=None)
            else:
                self._scene_context = ""
            # Check print bed limits
            self._check_print_bed(scene)
        except Exception:
            self._scene_context = ""

    def _check_print_bed(self, scene):
        """Warn if any object exceeds print bed dimensions."""
        from agent.config import load_config
        cfg = load_config()
        bed = cfg.get("print_bed", {"x": 250, "y": 210, "z": 210})
        for obj in scene.get("objects", []):
            dims = obj.get("dimensions_mm", [0, 0, 0])
            name = obj.get("name", "?")
            for axis, limit, val in [("X", bed["x"], dims[0]),
                                      ("Y", bed["y"], dims[1]),
                                      ("Z", bed["z"], dims[2])]:
                if val > limit:
                    self.root.after(0, self._set_result,
                        f"Warning: {name} ({val:.0f}mm {axis}) exceeds bed ({limit}mm) — consider splitting",
                        YELLOW)
                    return  # Show first warning only

    def _set_result(self, text, color=FG_DIM):
        """Update the last-command result label."""
        self._result_var.set(text)
        self._result_label.configure(fg=color)

    # --- Status ---

    def _check_status(self):
        """Periodically check Blender, Ollama, Mic status."""
        threading.Thread(target=self._update_status, daemon=True).start()
        self.root.after(5000, self._check_status)

    def _update_status(self):
        """Check all services (background thread)."""
        # Blender
        if blender_client.health_check():
            self.root.after(0, self._dot_blender.set_ok)
            self.root.after(0, self._tip_blender.update_text, "Blender: connected (localhost:6789)")
        else:
            self.root.after(0, self._dot_blender.set_error)
            self.root.after(0, self._tip_blender.update_text, "Blender: not responding")

        # Ollama
        try:
            import urllib.request
            req = urllib.request.Request("http://localhost:11434/api/tags")
            with urllib.request.urlopen(req, timeout=2):
                self.root.after(0, self._dot_ollama.set_ok)
                self.root.after(0, self._tip_ollama.update_text, "Ollama: running (localhost:11434)")
        except Exception:
            self.root.after(0, self._dot_ollama.set_error)
            self.root.after(0, self._tip_ollama.update_text, "Ollama: not running")

        # Mic
        try:
            import sounddevice as sd
            sd.query_devices(kind="input")
            if self._whisper_loaded:
                self.root.after(0, self._dot_mic.set_ok)
                self.root.after(0, self._mic_btn.configure, {"state": tk.NORMAL})
                self.root.after(0, self._tip_mic.update_text, "Mic: ready (whisper loaded)")
            else:
                self.root.after(0, self._dot_mic.set_warn)
                self.root.after(0, self._tip_mic.update_text, "Mic: loading whisper model...")
        except Exception:
            self.root.after(0, self._dot_mic.set_error)
            self.root.after(0, self._mic_btn.configure, {"state": tk.DISABLED})
            self.root.after(0, self._tip_mic.update_text, "Mic: no microphone detected")

        # VRAM
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=memory.used,memory.total",
                 "--format=csv,noheader,nounits"],
                timeout=3, text=True,
            ).strip()
            used, total = out.split(", ")
            used_gb = int(used) / 1024
            total_gb = int(total) / 1024
            self.root.after(0, self._vram_var.set,
                            f"VRAM: {used_gb:.1f}/{total_gb:.0f}GB")
        except Exception:
            self.root.after(0, self._vram_var.set, "VRAM: --")

    def _preload_whisper(self):
        """Preload whisper model in background so first voice command is fast."""
        try:
            _get_whisper()
            self._whisper_loaded = True
        except Exception:
            pass

    # --- Logging ---

    def _log(self, user_text, bpy_code, result):
        """Log command to session file. Rotates to keep max 10 log files."""
        LOG_DIR.mkdir(exist_ok=True)
        logs = sorted(LOG_DIR.glob("session_*.log"))
        while len(logs) > 9:
            logs.pop(0).unlink()
        log_file = LOG_DIR / f"session_{datetime.date.today().isoformat()}.log"
        with open(log_file, "a") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"[{datetime.datetime.now().isoformat()}]\n")
            f.write(f"USER: {user_text}\n")
            f.write(f"--- bpy code ---\n{bpy_code}\n")
            f.write(f"--- result ---\n{result}\n")

    # --- Lifecycle ---

    def _on_close(self):
        """Clean shutdown."""
        if self._recorder.is_recording:
            self._recorder.stop()
        self.root.destroy()

    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    app = PrintVoiceApp()
    app.run()


if __name__ == "__main__":
    main()
