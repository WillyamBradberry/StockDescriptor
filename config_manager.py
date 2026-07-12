#!/usr/bin/env python3
"""
Config manager for StockDescriptor GUI + CLI
Stores user settings and API keys in ~/.stockdescriptor/config.json (user home)
"""

import json
from pathlib import Path
from typing import Dict, Any

CONFIG_DIR = Path.home() / ".stockdescriptor"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "provider": "lmstudio",                    # "lmstudio" or "gemini"
    "lmstudio_url": "http://localhost:1234/v1/chat/completions",
    "lmstudio_model": "qwen3.6-35b-a3b",
    "gemini_api_key": "",
    "gemini_model": "gemini-1.5-flash-latest",
    "exiftool_path": "D:\\PROGRAMS\\EXIFTOOL\\exiftool.exe",
    "batch_size": 3,
    "delay": 3,
    "last_folder": "",
    "theme": "dark",                           # for future GUI
    "language": "ru"                           # "ru" or "en"
}


def load_config() -> Dict[str, Any]:
    """Load config from user file, merge with defaults if partial."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            # Merge: keep user values, add missing defaults
            cfg = DEFAULT_CONFIG.copy()
            cfg.update(user_cfg)
            return cfg
        except Exception as e:
            print(f"Warning: could not load config ({e}), using defaults.")
    return DEFAULT_CONFIG.copy()


def save_config(cfg: Dict[str, Any]) -> bool:
    """Save config to user file. Creates dir if needed."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        # Never save empty key if not provided
        if "gemini_api_key" in cfg and not cfg["gemini_api_key"]:
            cfg["gemini_api_key"] = ""  # keep empty
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def get_api_key(provider: str, cfg: Dict[str, Any] = None) -> str:
    """Helper to get current API key for provider."""
    if cfg is None:
        cfg = load_config()
    if provider.lower() == "gemini":
        return cfg.get("gemini_api_key", "") or ""
    return ""  # lmstudio usually no key needed (local)


if __name__ == "__main__":
    print("StockDescriptor Config Manager")
    cfg = load_config()
    print(f"Config file: {CONFIG_FILE}")
    print(json.dumps(cfg, indent=2, ensure_ascii=False))