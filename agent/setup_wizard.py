"""First-launch setup wizard — splash screen + system requirements check."""
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import font as tkfont

from agent import __version__
from agent.config import load_config, save_config, MODEL_TIERS

# Theme — matches app.py
BG = "#2D2D2D"
BG_FIELD = "#1D1D1D"
FG = "#E0E0E0"
FG_DIM = "#808080"
GREEN = "#4CAF50"
RED = "#E05050"
YELLOW = "#F0C040"
ORANGE = "#E87D0D"
BORDER = "#3D3D3D"

WELCOME_TEXT = (
    "Voice & text command interface for creating\n"
    "3D-printable objects in Blender.\n\n"
    "Fully local \u2014 no cloud APIs, no internet required."
)

LICENSE_TEXT = (
    "Licensed under the GNU General Public License v3.0.\n"
    "Free to use, modify, and distribute.\n"
    "See LICENSE file for full terms."
)


class SetupWizard:
    """Two-screen first-launch wizard."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("3DPrintVoice \u2014 Setup")
        self.root.configure(bg=BG)
        self.root.geometry("600x520")
        self.root.resizable(False, False)

        self._font_title = tkfont.Font(family="sans-serif", size=22, weight="bold")
        self._font_body = tkfont.Font(family="sans-serif", size=11)
        self._font_small = tkfont.Font(family="sans-serif", size=9)
        self._font_btn = tkfont.Font(family="sans-serif", size=12, weight="bold")
        self._font_mono = tkfont.Font(family="monospace", size=10)

        self._selected_tier = None
        self._check_results = {}
        self._completed = False

        self._show_welcome()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    # --- Screen 1: Welcome + License ---

    def _show_welcome(self):
        self._clear()
        frame = tk.Frame(self.root, bg=BG, padx=40, pady=30)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="3DPrintVoice", font=self._font_title,
                 bg=BG, fg=ORANGE).pack(pady=(0, 4))

        tk.Label(frame, text=f"v{__version__}", font=self._font_small,
                 bg=BG, fg=FG_DIM).pack(pady=(0, 20))

        tk.Label(frame, text=WELCOME_TEXT, font=self._font_body,
                 bg=BG, fg=FG, justify=tk.CENTER).pack(pady=(0, 30))

        # License box
        lic_frame = tk.Frame(frame, bg=BG_FIELD, padx=16, pady=12)
        lic_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(lic_frame, text="License", font=self._font_btn,
                 bg=BG_FIELD, fg=FG, anchor="w").pack(anchor="w")
        tk.Label(lic_frame, text=LICENSE_TEXT, font=self._font_small,
                 bg=BG_FIELD, fg=FG_DIM, justify=tk.LEFT).pack(anchor="w", pady=(4, 0))

        tk.Label(frame, text="Created by Roland Preisach, 2026",
                 font=self._font_small, bg=BG, fg=FG_DIM).pack(pady=(10, 20))

        tk.Button(frame, text="  Got it  ", font=self._font_btn,
                  bg=ORANGE, fg="white", activebackground="#F09030",
                  activeforeground="white", relief=tk.FLAT, cursor="hand2",
                  command=self._show_system_check, padx=20, pady=8).pack()

    # --- Screen 2: System Check + Model Selection ---

    def _show_system_check(self):
        self._clear()
        frame = tk.Frame(self.root, bg=BG, padx=40, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="System Requirements", font=self._font_title,
                 bg=BG, fg=FG).pack(pady=(0, 10))

        tk.Label(frame, text=(
            "3DPrintVoice needs the following software installed.\n"
            "Click the button below to check your system."
        ), font=self._font_body, bg=BG, fg=FG_DIM, justify=tk.CENTER).pack(pady=(0, 16))

        # Requirements list
        self._req_frame = tk.Frame(frame, bg=BG_FIELD, padx=16, pady=12)
        self._req_frame.pack(fill=tk.X, pady=(0, 12))

        self._req_labels = {}
        for name in ["Python 3.11+", "Blender 5.1+", "Ollama", "NVIDIA GPU"]:
            row = tk.Frame(self._req_frame, bg=BG_FIELD)
            row.pack(fill=tk.X, pady=2)
            dot = tk.Canvas(row, width=12, height=12, bg=BG_FIELD, highlightthickness=0)
            dot.pack(side=tk.LEFT, padx=(0, 8))
            oval = dot.create_oval(2, 2, 10, 10, fill=FG_DIM, outline="")
            lbl = tk.Label(row, text=name, font=self._font_mono,
                           bg=BG_FIELD, fg=FG_DIM, anchor="w")
            lbl.pack(side=tk.LEFT)
            detail = tk.Label(row, text="", font=self._font_small,
                              bg=BG_FIELD, fg=FG_DIM, anchor="e")
            detail.pack(side=tk.RIGHT)
            self._req_labels[name] = (dot, oval, lbl, detail)

        # Model recommendation area (shown after check)
        self._model_frame = tk.Frame(frame, bg=BG)
        self._model_frame.pack(fill=tk.X, pady=(0, 12))

        # Buttons area
        self._btn_frame = tk.Frame(frame, bg=BG)
        self._btn_frame.pack(fill=tk.X)

        self._check_btn = tk.Button(
            self._btn_frame, text="  Run System Check  ", font=self._font_btn,
            bg=ORANGE, fg="white", activebackground="#F09030",
            activeforeground="white", relief=tk.FLAT, cursor="hand2",
            command=self._run_check, padx=20, pady=8,
        )
        self._check_btn.pack()

        self._continue_btn = None

    def _run_check(self):
        self._check_btn.configure(state=tk.DISABLED, text="  Checking...  ", bg=BG_FIELD)
        threading.Thread(target=self._do_checks, daemon=True).start()

    def _do_checks(self):
        import sys
        results = {}

        # Python
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        py_ok = sys.version_info >= (3, 11)
        results["Python 3.11+"] = (py_ok, py_ver)
        self.root.after(0, self._update_req, "Python 3.11+", py_ok, py_ver)

        # Blender
        blender_path = shutil.which("blender")
        if blender_path:
            try:
                out = subprocess.check_output(
                    ["blender", "--version"], timeout=10, text=True,
                    stderr=subprocess.DEVNULL).strip()
                ver_line = [l for l in out.split("\n") if "Blender" in l]
                ver = ver_line[0].split()[-1] if ver_line else "unknown"
                major = int(ver.split(".")[0]) if ver[0].isdigit() else 0
                blender_ok = major >= 4
                results["Blender 5.1+"] = (blender_ok, ver)
                self.root.after(0, self._update_req, "Blender 5.1+", blender_ok, f"v{ver}")
            except Exception:
                results["Blender 5.1+"] = (False, "error")
                self.root.after(0, self._update_req, "Blender 5.1+", False, "error checking version")
        else:
            results["Blender 5.1+"] = (False, "not found")
            self.root.after(0, self._update_req, "Blender 5.1+", False,
                            "not found \u2014 install from blender.org")

        # Ollama
        ollama_path = shutil.which("ollama")
        if ollama_path:
            results["Ollama"] = (True, "installed")
            self.root.after(0, self._update_req, "Ollama", True, "installed")
        else:
            results["Ollama"] = (False, "not found")
            self.root.after(0, self._update_req, "Ollama", False,
                            "not found \u2014 curl -fsSL https://ollama.com/install.sh | sh")

        # GPU + VRAM
        vram_gb = 0
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,memory.total",
                 "--format=csv,noheader,nounits"],
                timeout=5, text=True, stderr=subprocess.DEVNULL).strip()
            parts = out.split(", ")
            if len(parts) == 2:
                gpu_name = parts[0].strip()
                vram_gb = int(parts[1].strip()) / 1024
                gpu_ok = vram_gb >= 3
                results["NVIDIA GPU"] = (gpu_ok, gpu_name, vram_gb)
                self.root.after(0, self._update_req, "NVIDIA GPU", gpu_ok,
                                f"{gpu_name} \u2014 {vram_gb:.0f}GB VRAM")
            else:
                results["NVIDIA GPU"] = (False, "parse error", 0)
                self.root.after(0, self._update_req, "NVIDIA GPU", False, "detection error")
        except FileNotFoundError:
            results["NVIDIA GPU"] = (False, "no nvidia-smi", 0)
            self.root.after(0, self._update_req, "NVIDIA GPU", False, "no NVIDIA GPU detected")
        except Exception:
            results["NVIDIA GPU"] = (False, "error", 0)
            self.root.after(0, self._update_req, "NVIDIA GPU", False, "detection error")

        self._check_results = results
        self.root.after(0, self._show_recommendation, vram_gb)

    def _update_req(self, name, ok, detail):
        dot, oval, lbl, detail_lbl = self._req_labels[name]
        color = GREEN if ok else RED
        dot.itemconfig(oval, fill=color)
        lbl.configure(fg=FG)
        detail_lbl.configure(text=detail, fg=GREEN if ok else YELLOW)

    def _show_recommendation(self, vram_gb):
        for w in self._model_frame.winfo_children():
            w.destroy()
        self._check_btn.pack_forget()

        if vram_gb < 3:
            tk.Label(self._model_frame, text=(
                "Your GPU does not have enough VRAM to run a local LLM.\n"
                "Minimum requirement: 3GB VRAM (dedicated NVIDIA GPU).\n\n"
                "3DPrintVoice cannot function without a local model.\n"
                "Consider upgrading your GPU or using a machine with more VRAM."
            ), font=self._font_body, bg=BG, fg=RED, justify=tk.CENTER).pack(pady=12)

            tk.Button(self._btn_frame, text="  Close  ", font=self._font_btn,
                      bg=RED, fg="white", relief=tk.FLAT, cursor="hand2",
                      command=self._on_close, padx=20, pady=8).pack()
            return

        # Determine recommended tier
        if vram_gb >= 12:
            rec = "full"
        elif vram_gb >= 6:
            rec = "medium"
        else:
            rec = "lite"

        tier_info = {
            "full": ("Full (14B)", "12GB+ VRAM", "Best quality \u2014 handles complex operations"),
            "medium": ("Medium (7B)", "6GB+ VRAM", "Good quality \u2014 covers most commands"),
            "lite": ("Lite (3B)", "3GB+ VRAM", "Basic \u2014 simple primitives only"),
        }

        tk.Label(self._model_frame, text="Recommended model based on your GPU:",
                 font=self._font_body, bg=BG, fg=FG).pack(anchor="w", pady=(8, 6))

        self._tier_var = tk.StringVar(value=rec)

        for tier_key in ["full", "medium", "lite"]:
            name, vram_req, desc = tier_info[tier_key]
            can_run = (
                (tier_key == "full" and vram_gb >= 12) or
                (tier_key == "medium" and vram_gb >= 6) or
                (tier_key == "lite" and vram_gb >= 3)
            )
            state = tk.NORMAL if can_run else tk.DISABLED

            row = tk.Frame(self._model_frame, bg=BG)
            row.pack(fill=tk.X, pady=1)

            rb = tk.Radiobutton(
                row, text=f"{name}  ({vram_req})", font=self._font_mono,
                variable=self._tier_var, value=tier_key,
                bg=BG, fg=FG if can_run else FG_DIM,
                selectcolor=BG_FIELD, activebackground=BG,
                activeforeground=ORANGE, state=state,
                highlightthickness=0,
            )
            rb.pack(side=tk.LEFT)

            tk.Label(row, text=f"  {desc}", font=self._font_small,
                     bg=BG, fg=FG_DIM if can_run else BORDER).pack(side=tk.LEFT)

        # Continue button
        self._continue_btn = tk.Button(
            self._btn_frame,
            text=f"  Continue with {tier_info[rec][0]}  ",
            font=self._font_btn,
            bg=GREEN, fg="white", activebackground="#5CBF60",
            activeforeground="white", relief=tk.FLAT, cursor="hand2",
            command=self._finish, padx=20, pady=8,
        )
        self._continue_btn.pack()

        # Update button text on radio change
        def _on_tier_change(*_):
            t = self._tier_var.get()
            self._continue_btn.configure(text=f"  Continue with {tier_info[t][0]}  ")
        self._tier_var.trace_add("write", _on_tier_change)

    def _finish(self):
        tier = self._tier_var.get()
        config = load_config()
        config["model_tier"] = tier
        config["model"] = MODEL_TIERS[tier]
        config["first_run_done"] = True
        save_config(config)
        self._completed = True

        # Show brief confirmation before closing
        self._clear()
        frame = tk.Frame(self.root, bg=BG, padx=40, pady=60)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text="Setup complete!", font=self._font_title,
                 bg=BG, fg=GREEN).pack(pady=(0, 16))
        tk.Label(frame, text="Starting 3DPrintVoice...", font=self._font_body,
                 bg=BG, fg=FG_DIM).pack()
        self.root.after(2000, self.root.destroy)

    def _on_close(self):
        self.root.destroy()

    def run(self) -> bool:
        """Run the wizard. Returns True if setup was completed."""
        self.root.mainloop()
        return self._completed


def needs_setup() -> bool:
    """Check if first-launch setup is needed."""
    config = load_config()
    return not config.get("first_run_done", False)


def run_setup() -> bool:
    """Run the setup wizard. Returns True if completed."""
    wizard = SetupWizard()
    return wizard.run()
