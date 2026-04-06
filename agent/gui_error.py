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
