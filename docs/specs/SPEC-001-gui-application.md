# SPEC-001: GUI Application

**Status:** ✅ Done  
**Priority:** P0  
**Key File:** `gui_launcher.py`  
**Dependencies:** SPEC-002 (Config), SPEC-003 (Pipeline), SPEC-005 (Upload)

---

## 1. Purpose

Provide a modern desktop GUI for the StockDescriptor pipeline, eliminating the need for CLI commands. The user selects a folder with JPGs, configures AI provider, and runs the full pipeline with one click.

---

## 2. UI Structure

### 2.1 Main Window

| Element | Description |
|---------|-------------|
| Title bar | "📸 StockDescriptor — AI Metadata for Stock Photos" |
| Header | App title + subtitle + language toggle (EN/RU) + "⚙️ AI Settings" button |
| Folder selection | Label + text entry + "Browse..." button |
| Run button | "🚀 RUN PIPELINE" — large green button |
| Info row | Current provider name + model name |
| Execution log | Scrollable text area (Consolas font, dark background) |
| Auto-upload checkbox | Next to log header — triggers upload after pipeline |
| Upload section | Platform checkboxes (Shutterstock/Adobe/Pond5) + progress bars + "📤 Upload Selected" button + gear icon for FTP settings |
| Status bar | Bottom bar with status text + hint |

### 2.2 Settings Window (modal)

| Element | Description |
|---------|-------------|
| Provider selector | Segmented button: "LM Studio (local)" / "Google Gemini (online)" |
| LM Studio fields | Endpoint URL + Model name |
| Gemini fields | API Key (masked) + Model name |
| ExifTool path | Text entry + "Browse..." button |
| Common params | Batch size slider (1-6) + Delay slider (0-10s) |
| Save/Cancel | Buttons at bottom |
| Warning | "API keys stored in plain text" notice |

### 2.3 Upload FTP Settings Window (modal)

| Element | Description |
|---------|-------------|
| Per-platform frames | Shutterstock, Adobe Stock, Pond5 |
| Fields per platform | Host, Port, Username, Password (with eye toggle 👁/🙈), Remote path |
| Save/Cancel | Buttons at bottom |

---

## 3. Behavior

### 3.1 Pipeline Execution

1. User selects folder → path saved to config (`last_folder`)
2. User clicks "🚀 RUN PIPELINE"
3. Validation:
   - Folder must exist
   - If Gemini selected → API key must be set (prompt to open settings if missing)
   - If already running → show warning
4. Pipeline runs in background thread:
   - **Step 1:** Resize images (PowerShell script)
   - **Step 2:** AI metadata generation (batch_metadata.py)
   - **Step 3:** EXIF injection (write_exif.ps1)
   - **Step 4:** Obsidian navigation (create-metadata-nav-modified.ps1)
5. Log messages streamed via queue → UI updates in real-time
6. On completion:
   - Button re-enabled
   - Status shows "✅ Pipeline complete"
   - If auto-upload enabled → triggers upload

### 3.2 Upload Execution

1. User selects platforms via checkboxes
2. Clicks "📤 Upload Selected"
3. Each platform uploads in its own thread
4. Progress bars update per-file
5. Files moved to `_UPLOADED/` only after ALL selected platforms finish

### 3.3 Language Toggle

- Button in header toggles between EN/RU
- All UI strings updated immediately
- Preference saved to config

### 3.4 Window Behavior

- Centered on screen, 85% of screen size (capped at 1100×850)
- Minimum size: 900×700
- Settings windows: resizable, ESC to close, clamped to screen bounds

---

## 4. Data Flow

```
User clicks RUN
  → validate inputs
  → start worker thread
  → thread calls:
      resize_for_vision.ps1
      batch_metadata.generate_metadata_for_folder()
      batch_metadata.run_write_exif()
      batch_metadata.run_nav_script()
  → progress via queue → poll_log_queue() → UI update
  → on done: re-enable UI, optionally trigger upload
```

---

## 5. Error Handling

- Pipeline errors → logged in execution log with ❌ prefix
- Critical errors → status bar shows "❌ Execution error"
- Missing THMBS folder → abort with error message
- Missing scripts → skip step with warning
- Upload errors → per-platform error shown on progress bar

---

## 6. Configuration Persistence

- `last_folder` — auto-saved on folder selection
- `language` — saved on toggle
- `auto_upload` — saved on checkbox change
- All other settings saved via Settings window → `config_manager.save_config()`

---

*Last updated: 2026-07-14*