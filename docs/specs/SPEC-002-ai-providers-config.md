# SPEC-002: AI Providers & Config Manager

**Status:** ✅ Done  
**Priority:** P0  
**Key Files:** `config_manager.py`, Settings UI in `gui_launcher.py`  
**Dependencies:** None

---

## 1. Purpose

Manage application configuration, API keys, and credentials securely. Support two AI providers: **LM Studio** (local, OpenAI-compatible) and **Google Gemini** (online). All secrets (API keys, FTP passwords) stored encrypted on disk.

---

## 2. Configuration Storage

### 2.1 File Structure

| File | Path | Content |
|------|------|---------|
| `config.json` | `~/.stockdescriptor/config.json` | Plain JSON — public settings only (provider, model, paths, etc.) |
| `secrets.enc` | `~/.stockdescriptor/secrets.enc` | Encrypted JSON — API keys and passwords |
| `.key` | `~/.stockdescriptor/.key` | Fernet encryption key (auto-generated, chmod 600) |

### 2.2 Secret Fields (always encrypted)

- `gemini_api_key`
- `upload_config.shutterstock.password`
- `upload_config.adobe.password`
- `upload_config.pond5.password`

### 2.3 Default Config

```json
{
  "provider": "lmstudio",
  "lmstudio_url": "http://localhost:1234/v1/chat/completions",
  "lmstudio_model": "qwen3.6-35b-a3b",
  "gemini_model": "gemini-1.5-flash-latest",
  "exiftool_path": "D:\\PROGRAMS\\EXIFTOOL\\exiftool.exe",
  "batch_size": 3,
  "delay": 3,
  "last_folder": "",
  "theme": "dark",
  "language": "ru",
  "auto_upload": false,
  "upload_config": {
    "shutterstock": { "host": "ftps.shutterstock.com", "port": 21, "username": "", "remote_path": "/" },
    "adobe": { "host": "sftp.contributor.adobestock.com", "port": 22, "username": "", "remote_path": "/" },
    "pond5": { "host": "ftp.pond5.com", "port": 21, "username": "", "remote_path": "/" }
  }
}
```

---

## 3. API Behavior

### 3.1 `load_config()`

1. Reads `~/.stockdescriptor/config.json` (plain settings)
2. Merges with `DEFAULT_CONFIG` (fills missing keys)
3. Reads `~/.stockdescriptor/secrets.enc` → decrypts each field
4. Injects decrypted secrets into config
5. Returns full config dict

### 3.2 `save_config(cfg)`

1. Extracts secret fields from config
2. Encrypts each secret value with Fernet
3. Writes encrypted secrets to `secrets.enc`
4. Strips secrets from config → writes plain JSON to `config.json`

### 3.3 Encryption

- Algorithm: **Fernet** (symmetric AES-128-CBC + HMAC-SHA256)
- Key: auto-generated on first `save_config()` call, stored in `.key`
- Permission: `.key` and `secrets.enc` set to `0o600` (user-only read)

---

## 4. AI Provider Switching

### 4.1 LM Studio (local)

- Endpoint: configurable URL (default `http://localhost:1234/v1/chat/completions`)
- Model: configurable name (default `qwen3.6-35b-a3b`)
- Protocol: OpenAI-compatible chat completions API
- Authentication: none (local)

### 4.2 Google Gemini (online)

- Endpoint: `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`
- Model: configurable (default `gemini-1.5-flash-latest`)
- Authentication: API key in URL query parameter
- Key source: encrypted config (via GUI or `--api-key` flag)

---

## 5. GUI Settings Window

See SPEC-001 §2.2 for UI layout. The Settings window reads/writes config via `config_manager.py`.

---

## 6. Edge Cases

- **Corrupted config file** → fall back to defaults with warning
- **Missing encryption key** → auto-generate on first save
- **Decryption failure** → secrets reset to empty, user re-enters credentials
- **Empty Gemini key** → warning on save, blocked on pipeline start

---

*Last updated: 2026-07-14*