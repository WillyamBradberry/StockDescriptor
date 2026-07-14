# TASK-005: CLI Pipeline — Improvements & Testing

**Spec:** SPEC-003  
**Key File:** `processing/batch_metadata.py`  
**Priority:** P2  
**Status:** ✅ Working, polish identified

---

## Description

The CLI pipeline works but has areas for improvement:

1. **Progress output** — Console output mixes English and Russian text
2. **Timeout handling** — 300s timeout is hardcoded; should be configurable
3. **Logging** — Currently uses `print()` statements; should use Python's `logging` module

---

## Proposed Improvements

1. Unify console output language (use config language setting)
2. Make API timeout configurable via `--timeout` flag
3. Replace `print()` with structured logging (`logging.DEBUG` / `logging.INFO`)

---

## Files

- `processing/batch_metadata.py`

---

## Dependencies

- SPEC-002 (language setting from config)