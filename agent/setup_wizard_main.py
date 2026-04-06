"""Standalone entry point for the setup wizard (called by launcher.sh on first run)."""
import sys
from agent.setup_wizard import run_setup

if __name__ == "__main__":
    completed = run_setup()
    sys.exit(0 if completed else 1)
