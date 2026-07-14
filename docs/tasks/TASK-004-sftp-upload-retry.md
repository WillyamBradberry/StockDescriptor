# TASK-004: SFTP Upload — Retry & Resilience

**Spec:** SPEC-005  
**Key File:** `scripts/upload_to_stocks.py`  
**Priority:** P2  
**Status:** ✅ Working, resilience can be improved

---

## Description

The upload module handles basic errors but lacks retry logic for transient failures (network timeouts, connection drops).

---

## Proposed Improvements

1. **Retry on connection drop** — Auto-reconnect and resume upload
2. **Exponential backoff** — Wait 1s, 2s, 4s before giving up
3. **Configurable timeout** — Make connection timeout configurable
4. **Dry-run mode** — `--dry-run` flag to list files without uploading

---

## Files

- `scripts/upload_to_stocks.py`
- `gui_launcher.py` — may need minor UI for retry config

---

## Dependencies

- None