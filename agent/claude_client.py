import os
from pathlib import Path
import anthropic

SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system.md"
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1024


def _load_system_prompt():
    return SYSTEM_PROMPT_PATH.read_text()


_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY env var
    return _client


def generate_bpy_code(user_text: str, scene_context: str = "") -> str:
    """Send user text to Claude and return raw bpy code string."""
    client = _get_client()
    system = _load_system_prompt()

    user_message = user_text
    if scene_context:
        user_message = f"Current scene state:\n{scene_context}\n\nUser request: {user_text}"

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )

    return response.content[0].text
