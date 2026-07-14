# TASK-001: GUI Application — Maintenance & Improvements

**Spec:** SPEC-001  
**Key File:** `gui_launcher.py`  
**Priority:** P1  
**Status:** 🔧 Identified for refactoring

---

## Description

The `gui_launcher.py` file is **1339 lines** — exceeding maintainability threshold. The file contains:

- `StockDescriptorGUI` class (~600 lines) — main window logic
- `UploadSettingsWindow` class (~170 lines) — FTP settings modal
- `SettingsWindow` class (~200 lines) — AI settings modal
- `LANGUAGES` dict (265 lines) — multilingual strings

---

## Proposed Refactoring

1. **Extract `LANGUAGES`** → separate file `gui_strings.py`
2. **Extract `UploadSettingsWindow`** → separate file `gui_upload_settings.py`
3. **Extract `SettingsWindow`** → separate file `gui_settings.py`
4. **Reduce `StockDescriptorGUI`** to under 500 lines

---

## Files

- `gui_launcher.py` — source (to be split)
- `gui_strings.py` — extracted strings
- `gui_settings.py` — extracted settings window
- `gui_upload_settings.py` — extracted upload settings window

---

## Dependencies

- None (self-contained refactoring)