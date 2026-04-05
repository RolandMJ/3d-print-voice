#!/usr/bin/env python3
"""BlenderAI Phase 1 — text input loop.

Type a natural language command, Claude generates bpy code, the code is sent
to Blender via the AI Bridge addon, and the result appears in the viewport.
"""

import sys
import os
import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from agent.claude_client import generate_bpy_code
from agent import blender_client

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def _log_session(user_text: str, bpy_code: str, result: dict):
    """Append command + generated code + result to today's session log."""
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / f"session_{datetime.date.today().isoformat()}.log"
    with open(log_file, "a") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"[{datetime.datetime.now().isoformat()}]\n")
        f.write(f"USER: {user_text}\n")
        f.write(f"--- generated bpy code ---\n{bpy_code}\n")
        f.write(f"--- result ---\n{result}\n")


def main():
    print("BlenderAI — Phase 1 (text mode)")
    print("Type a command for Blender. 'quit' to exit.\n")

    # Check connection to Blender
    if not blender_client.health_check():
        print("WARNING: Cannot reach Blender addon at http://127.0.0.1:6789")
        print("Make sure Blender is running with the AI Bridge addon enabled.\n")

    while True:
        try:
            user_text = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not user_text:
            continue
        if user_text.lower() in ("quit", "exit", "q"):
            print("Exiting.")
            break

        # Generate bpy code via Claude
        print("Generating code...")
        try:
            bpy_code = generate_bpy_code(user_text)
        except Exception as e:
            print(f"Claude API error: {e}")
            continue

        # Show the generated code
        print(f"--- bpy code ---\n{bpy_code}\n---")

        # Check for CANNOT_EXECUTE
        if bpy_code.strip().startswith("# CANNOT_EXECUTE"):
            print(f"Claude declined: {bpy_code.strip()}")
            _log_session(user_text, bpy_code, {"status": "declined"})
            continue

        # Send to Blender
        print("Sending to Blender...")
        result = blender_client.execute(bpy_code)

        if result["status"] == "ok":
            print("Done.")
        else:
            print(f"Error from Blender:\n{result.get('error', 'unknown error')}")

        _log_session(user_text, bpy_code, result)


if __name__ == "__main__":
    main()
