#!/usr/bin/env python3
"""
Config manager for StockDescriptor GUI + CLI
- API keys and passwords stored ENCRYPTED in ~/.stockdescriptor/secrets.enc
- Other settings stored as plain editable JSON in ~/.stockdescriptor/config.json
"""

import json
import base64
import os
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet

CONFIG_DIR = Path.home() / ".stockdescriptor"
CONFIG_FILE = CONFIG_DIR / "config.json"
SECRETS_FILE = CONFIG_DIR / "secrets.enc"
KEY_FILE = CONFIG_DIR / ".key"

# Fields that MUST be encrypted (never appear in plain config.json)
SECRET_FIELDS = {
    "gemini_api_key",
    "upload_config.shutterstock.password",
    "upload_config.adobe.password",
    "upload_config.pond5.password",
}

DEFAULT_CONFIG: Dict[str, Any] = {
    "provider": "lmstudio",
    "lmstudio_url": "http://localhost:1234/v1/chat/completions",
    "lmstudio_model": "qwen3.6-35b-a3b",
    "gemini_api_key": "",          # stored in secrets.enc
    "gemini_model": "gemini-1.5-flash-latest",
    "exiftool_path": "D:\\PROGRAMS\\EXIFTOOL\\exiftool.exe",
    "batch_size": 3,
    "delay": 3,
    "last_folder": "",
    "theme": "dark",
    "language": "ru",
    "auto_upload": False,
    "upload_config": {
        "shutterstock": {
            "host": "ftps.shutterstock.com",
            "port": 21,
            "username": "",
            "password": "",          # stored in secrets.enc
            "remote_path": "/"
        },
        "adobe": {
            "host": "sftp.contributor.adobestock.com",
            "port": 22,
            "username": "",
            "password": "",          # stored in secrets.enc
            "remote_path": "/"
        },
        "pond5": {
            "host": "ftp.pond5.com",
            "port": 21,
            "username": "",
            "password": "",          # stored in secrets.enc
            "remote_path": "/"
        }
    }
}


def _ensure_key() -> bytes:
    """Get or create encryption key."""
    if KEY_FILE.exists():
        return base64.urlsafe_b64decode(KEY_FILE.read_bytes())
    key = Fernet.generate_key()
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    KEY_FILE.write_bytes(base64.urlsafe_b64encode(key))
    os.chmod(KEY_FILE, 0o600)
    return key


def _get_fernet() -> Fernet:
    return Fernet(_ensure_key())


def _encrypt(data: str) -> str:
    """Encrypt string, return base64-encoded ciphertext."""
    f = _get_fernet()
    return f.encrypt(data.encode("utf-8")).decode("utf-8")


def _decrypt(ciphertext: str) -> str:
    """Decrypt base64-encoded ciphertext."""
    f = _get_fernet()
    return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")


def _get_nested(cfg: Dict, path: str) -> Any:
    """Get value by dot-path like 'upload_config.shutterstock.password'."""
    parts = path.split(".")
    for p in parts[:-1]:
        cfg = cfg.setdefault(p, {})
    return cfg.get(parts[-1], "")


def _set_nested(cfg: Dict, path: str, value: Any):
    """Set value by dot-path."""
    parts = path.split(".")
    for p in parts[:-1]:
        cfg = cfg.setdefault(p, {})
    cfg[parts[-1]] = value


def _extract_secrets(cfg: Dict[str, Any]) -> Dict[str, str]:
    """Extract all secret fields from config into flat dict."""
    secrets = {}
    for field in SECRET_FIELDS:
        val = _get_nested(cfg, field)
        if val and isinstance(val, str):
            secrets[field] = val
    return secrets


def _strip_secrets(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Return config with secret fields replaced by empty strings."""
    result = json.loads(json.dumps(cfg))  # deep copy
    for field in SECRET_FIELDS:
        _set_nested(result, field, "")
    return result


def _inject_secrets(cfg: Dict[str, Any], secrets: Dict[str, str]) -> Dict[str, Any]:
    """Inject decrypted secrets back into config."""
    for field, val in secrets.items():
        if val:
            _set_nested(cfg, field, val)
    return cfg


def load_config() -> Dict[str, Any]:
    """Load config: plain JSON + encrypted secrets merged together."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Load plain config
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            cfg = DEFAULT_CONFIG.copy()
            cfg.update(user_cfg)
        except Exception as e:
            print(f"Warning: could not load config ({e}), using defaults.")
            cfg = DEFAULT_CONFIG.copy()
    else:
        cfg = DEFAULT_CONFIG.copy()

    # Load and inject encrypted secrets
    if SECRETS_FILE.exists():
        try:
            with open(SECRETS_FILE, "r", encoding="utf-8") as f:
                encrypted_secrets = json.load(f)
            secrets = {k: _decrypt(v) for k, v in encrypted_secrets.items()}
            cfg = _inject_secrets(cfg, secrets)
        except Exception as e:
            print(f"Warning: could not decrypt secrets ({e}). Secrets may need re-entry.")

    return cfg


def save_config(cfg: Dict[str, Any]) -> bool:
    """Save config: plain JSON (editable) + encrypted secrets (protected)."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Extract and encrypt secrets
        secrets = _extract_secrets(cfg)
        encrypted_secrets = {k: _encrypt(v) for k, v in secrets.items() if v}

        # Save encrypted secrets
        with open(SECRETS_FILE, "w", encoding="utf-8") as f:
            json.dump(encrypted_secrets, f, indent=2)
        os.chmod(SECRETS_FILE, 0o600)

        # Save plain config (without secrets)
        plain_cfg = _strip_secrets(cfg)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(plain_cfg, f, indent=2, ensure_ascii=False)

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
    return ""


if __name__ == "__main__":
    print("StockDescriptor Config Manager (Encrypted Secrets)")
    print(f"Config file:    {CONFIG_FILE}")
    print(f"Secrets file:   {SECRETS_FILE}")
    print(f"Key file:       {KEY_FILE}")
    cfg = load_config()
    print("\n--- Plain config (editable) ---")
    print(json.dumps(_strip_secrets(cfg), indent=2, ensure_ascii=False))
    print("\n--- Secrets loaded (decrypted in memory) ---")
    for field in SECRET_FIELDS:
        val = _get_nested(cfg, field)
        print(f"  {field}: {'***SET***' if val else '(empty)'}")
