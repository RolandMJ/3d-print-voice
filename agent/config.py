"""Config management — ~/.config/3d-print-voice/config.json."""
import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "3d-print-voice"
CONFIG_FILE = CONFIG_DIR / "config.json"

MODEL_TIERS = {
    "full":   "qwen2.5-coder:14b-instruct",
    "medium": "qwen2.5-coder:7b-instruct",
    "lite":   "qwen2.5-coder:3b-instruct",
}

DEFAULT_CONFIG = {
    "model": "qwen2.5-coder:14b-instruct",
    "model_tier": "full",
    "first_run_done": False,
}


def load_config() -> dict:
    """Load config, returning defaults if missing or corrupt."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    """Save config to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
