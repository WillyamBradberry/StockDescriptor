# SPEC-007: Multilingual UI (EN / RU)

**Status:** ✅ Done  
**Priority:** P1  
**Key File:** `gui_launcher.py` (embedded LANGUAGES dict)  
**Dependencies:** SPEC-001 (GUI Application)

---

## 1. Purpose

Support two languages in the GUI: **English** and **Русский**. All UI strings switch instantly via a toggle button in the header.

---

## 2. Implementation

### 2.1 String Storage

- All UI strings stored in `LANGUAGES` dict inside `gui_launcher.py`
- Two top-level keys: `"en"` and `"ru"`
- Each key contains ~160 string mappings

### 2.2 Language Detection

- Default language from config: `config["language"]` (default `"ru"`)
- Fallback to Russian if config value is invalid

### 2.3 String Resolution

```python
def tr(self, key: str, *args) -> str:
    val = LANGUAGES.get(self.lang, LANGUAGES["ru"]).get(key, key)
    if args:
        return val.format(*args)
    return val
```

- Unknown keys → return the key itself (graceful fallback)
- Format args support for dynamic values

---

## 3. UI Integration

### 3.1 Toggle Button

- Located in header row (right side)
- Text shows "EN" when current language is Russian, "RU" when current language is English
- On click: switch `self.lang`, update config, refresh all UI text

### 3.2 Refresh Logic

The `_refresh_ui_text()` method updates every visible UI element:
- Window title
- All labels (app title, subtitle, folder, run button, etc.)
- Execution log status messages
- Upload section labels
- Provider/model info row
- Status bar

---

## 4. Scope

All user-facing strings are covered:
- Window titles and buttons
- Labels and placeholders
- Log messages (step names, status messages)
- Warning/error dialogs
- Upload platform names and status texts
- Settings windows (AI Settings + Upload FTP Settings)

---

## 5. Not Translated

- Console output from PowerShell scripts (English only)
- AI model responses (always English — stock platform requirement)
- METADATA.md / METADATA-NAV.md content (AI-generated, English)

---

*Last updated: 2026-07-14*