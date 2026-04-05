#!/usr/bin/env python3
"""BlenderAI — text input loop.

Type a natural language command, local LLM generates bpy code, the code is
sent to Blender via the AI Bridge addon, and the result appears in the viewport.
"""

import datetime
from pathlib import Path

from agent.llm_client import generate_bpy_code
from agent import blender_client

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
MAX_RETRIES = 1


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


def _try_generate_and_execute(user_text: str) -> None:
    """Generate bpy code and send to Blender. Retry once on execution error."""
    print("Generating code...")
    try:
        bpy_code = generate_bpy_code(user_text)
    except Exception as e:
        print(f"LLM error: {e}")
        return

    print(f"--- bpy code ---\n{bpy_code}\n---")

    if bpy_code.strip().startswith("# CANNOT_EXECUTE"):
        print(f"Declined: {bpy_code.strip()}")
        _log_session(user_text, bpy_code, {"status": "declined"})
        return

    print("Sending to Blender...")
    result = blender_client.execute(bpy_code)

    if result["status"] == "ok":
        print("Done.")
        _log_session(user_text, bpy_code, result)
        return

    error_msg = result.get("error", "unknown error")
    print(f"Error from Blender:\n{error_msg}")
    _log_session(user_text, bpy_code, result)

    # Retry once — feed the error back to the model
    print("Retrying with error context...")
    retry_prompt = (
        f"The previous code failed with this error:\n{error_msg}\n\n"
        f"Original request: {user_text}\n\n"
        f"Fix the code and try again."
    )
    try:
        bpy_code_retry = generate_bpy_code(retry_prompt)
    except Exception as e:
        print(f"LLM retry error: {e}")
        return

    print(f"--- retry bpy code ---\n{bpy_code_retry}\n---")
    result_retry = blender_client.execute(bpy_code_retry)

    if result_retry["status"] == "ok":
        print("Done (on retry).")
    else:
        print(f"Retry also failed:\n{result_retry.get('error', 'unknown error')}")

    _log_session(user_text, bpy_code_retry, result_retry)


def main():
    print("BlenderAI — local mode (Ollama + Qwen2.5-Coder)")
    print("Type a command for Blender. 'quit' to exit.\n")

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

        _try_generate_and_execute(user_text)


if __name__ == "__main__":
    main()
