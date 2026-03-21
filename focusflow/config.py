"""
Config persistence for FocusFlow.
Stores window position, opacity, last schedule path, and always-on-top state.
All config is saved to %APPDATA%/FocusFlow/config.json on Windows,
or ~/.config/FocusFlow/config.json on other platforms.
"""

import json
import os
import sys

# Determine config directory based on platform
if sys.platform == "win32":
    _CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "FocusFlow")
else:
    _CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "FocusFlow")

CONFIG_PATH = os.path.join(_CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "last_schedule_path": "",
    "window_x": 100,
    "window_y": 50,
    "opacity": 1.0,
    "always_on_top": True,
}


def load_config() -> dict:
    """Load config from disk, returning defaults for any missing keys."""
    config = DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            saved = json.load(f)
        if isinstance(saved, dict):
            for key in DEFAULT_CONFIG:
                if key in saved:
                    config[key] = saved[key]
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return config


def save_config(config: dict) -> None:
    """Persist config dict to disk, creating the directory if needed."""
    try:
        os.makedirs(_CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except OSError:
        pass
