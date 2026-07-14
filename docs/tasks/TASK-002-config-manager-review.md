# TASK-002: Config Manager — Security & Robustness Review

**Spec:** SPEC-002  
**Key File:** `config_manager.py`  
**Priority:** P2  
**Status:** ✅ Working, minor improvements identified

---

## Description

The config manager works correctly with encrypted secrets. Minor improvements identified:

1. **Error recovery**: If `secrets.enc` is corrupted, user must re-enter all credentials. Consider adding a "reset secrets" function.
2. **Key rotation**: No mechanism to rotate encryption key.
3. **Validation**: No validation of config values on load (e.g., port numbers, URLs).

---

## Proposed Improvements

1. Add `reset_secrets()` function to clear and regenerate secrets file
2. Add basic validation for critical fields (port range, non-empty hostnames)
3. Add `get_upload_config(platform)` helper for cleaner access

---

## Files

- `config_manager.py` — source
- `gui_launcher.py` — may need minor updates for new helpers

---

## Dependencies

- None