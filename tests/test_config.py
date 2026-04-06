"""Tests for config module."""
import json
from unittest.mock import patch
from agent.config import load_config, save_config, DEFAULT_CONFIG


class TestConfig:
    def test_default_config_has_required_keys(self):
        assert "model" in DEFAULT_CONFIG
        assert "first_run_done" in DEFAULT_CONFIG
        assert DEFAULT_CONFIG["first_run_done"] is False

    def test_load_returns_defaults_when_no_file(self, tmp_path):
        with patch("agent.config.CONFIG_FILE", tmp_path / "nonexistent.json"):
            cfg = load_config()
            assert cfg["first_run_done"] is False
            assert cfg["model"] == "qwen2.5-coder:14b-instruct"

    def test_save_and_load_roundtrip(self, tmp_path):
        config_file = tmp_path / "config.json"
        with patch("agent.config.CONFIG_DIR", tmp_path), \
             patch("agent.config.CONFIG_FILE", config_file):
            save_config({"model": "qwen2.5-coder:7b-instruct", "first_run_done": True})
            cfg = load_config()
            assert cfg["model"] == "qwen2.5-coder:7b-instruct"
            assert cfg["first_run_done"] is True
