"""Local LLM client — talks to Ollama API at localhost:11434."""
import json
import re
import urllib.request
import urllib.error
from pathlib import Path

SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system.md"
OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5-coder:14b-instruct"


def _load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text()


def _ollama_chat(system: str, user_message: str) -> str:
    """Send a chat request to Ollama and return the response text."""
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 1024},
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data["message"]["content"]


def extract_code(raw: str) -> str:
    """Extract executable Python from model output.

    Local models often wrap code in markdown fences or add explanations.
    This strips everything except the actual code.
    """
    fence_match = re.search(r"```(?:python)?\s*\n(.*?)```", raw, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    return raw.strip()


def generate_bpy_code(user_text: str, scene_context: str = "") -> str:
    """Generate bpy code from natural language via local Ollama model."""
    system = _load_system_prompt()

    user_message = user_text
    if scene_context:
        user_message = f"Current scene state:\n{scene_context}\n\nUser request: {user_text}"

    raw = _ollama_chat(system, user_message)
    return extract_code(raw)
