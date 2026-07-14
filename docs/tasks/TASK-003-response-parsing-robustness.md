# TASK-003: Response Parsing — Robustness Improvements

**Spec:** SPEC-003  
**Key File:** `processing/batch_metadata.py`  
**Priority:** P1  
**Status:** ✅ Working, parsing is multi-strategy

---

## Description

The metadata extraction from LLM responses uses a 4-strategy approach that works well. However, as LLM outputs become more complex, the parser may need:

1. **JSON wrapper handling** — Some LLMs wrap metadata in JSON `{ "results": [...] }`
2. **Language filtering** — Ensure English output only (stock platform requirement)
3. **Duplicate keyword removal** — Case-insensitive dedup of keywords

---

## Proposed Improvements

1. Add JSON detection + extraction before markdown parsing
2. Add optional language filter (warn if non-English detected)
3. Add keyword deduplication step (case-insensitive)

---

## Files

- `processing/batch_metadata.py` — `extract_metadata_block()` and `_extract_field()`

---

## Dependencies

- None (self-contained improvements)