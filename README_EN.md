# 📸 StockDescriptor

**Batch describer for Photo Stocks** — a powerful tool for preparing, AI-analyzing, and processing photos for stock platforms with automatic EXIF metadata management and Obsidian navigation.

**NEW v2.1:** Multilingual GUI (English / Русский) with language toggle, console logging, and persistent language setting.

Showcase: https://stock.adobe.com/contributor/202223264/willyam

---
## ✨ New Beautiful GUI (recommended)

![[./attachments/Sleekshot 2026-07-12 13-30-50.jpg]]
Launch the modern window with one click:

```batch
run_gui.bat
# or
python gui_launcher.py
```

### What the GUI can do:

1. **Folder path input** + **Browse** button
2. **Big «🚀 RUN PIPELINE» button** — runs the full cycle:
   - Resize (create THMBS/)
   - AI generation of Title / Description / Keywords
   - Inject metadata into originals (EXIF)
   - Create Obsidian navigation `METADATA-NAV.md`
3. **«⚙️ AI Settings» button**:
   - Switch **LM Studio (local)** ↔ **Google Gemini (online)**
   - Fields for LM Studio URL/model
   - Gemini API Key field (masked) + model
   - Batch size and delay sliders
   - Key saved to: `~/.stockdescriptor/config.json`
4. **Live execution log** with colored statuses
5. **Console logging** — all log messages are also printed to the terminal
6. **Language toggle** — switch between EN/RU at any time
7. Auto-save last folder

**GUI Advantages:**
- No need to remember commands and flags
- Easy choice between local and cloud AI
- API keys never go into the repository
- Beautiful modern interface (Dark + blue theme)

---

## 🎯 Main Features (CLI also works)

### 1. 🖼️ Resize for Vision API
`processing/resize_for_vision.ps1` — proportionally reduces to 1024px, saves to `THMBS/`

### 2. 🤖 AI Metadata Generation
`processing/batch_metadata.py` now supports **two providers**:
- **LM Studio** (default, local, OpenAI-compatible endpoint)
- **Google Gemini** (online, requires API key)

Supports resume, --check-errs, mock mode, incremental writing.

### 3. 🏷️ EXIF Injection + Obsidian nav
Full pipeline with one command.

---

## 🚀 Quick Start (GUI — the easiest way)

```batch
cd d:\projects\AI\stock-descriptor
run_gui.bat
```

1. Click **«Browse...»** → select folder with JPGs
2. (Optional) **«⚙️ AI Settings»** → choose Gemini and paste key
3. Click **«🚀 RUN PIPELINE»**
4. Watch the log — done!

---

## ⚙️ CLI (for scripts / advanced users)

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Full pipeline via bat (old way)
processing\run_pipeline.bat "C:\path\to\your\images"

# Direct launch with provider selection
python processing\batch_metadata.py "C:\path\to\images" --provider gemini --model gemini-1.5-flash-latest
```

**New batch_metadata.py flags:**
- `--provider lmstudio|gemini`
- `--model "model-name"`
- `--api-key "YOUR_KEY"` (for Gemini; better use GUI or env var)

---

## 📁 Project Structure (updated)

```
StockDescriptor/
├── gui_launcher.py          # ← NEW: beautiful GUI app
├── run_gui.bat              # ← NEW: easy GUI launch
├── requirements.txt         # + customtkinter
├── README_EN.md             # English documentation
├── README_RU.md             # Russian documentation
├── processing/
│   ├── config_manager.py    # ← NEW: config + API key management
│   ├── batch_metadata.py    # Updated: Gemini support + llm_config
│   ├── resize_for_vision.ps1
│   ├── write_exif.ps1
│   ├── create-metadata-nav-modified.ps1
│   ├── run_pipeline.bat
│   └── ...
├── templates/
└── README.md
```

---

## 🔐 API Key Storage

- On first Gemini key entry in GUI settings, it is saved to:
  `~/.stockdescriptor/config.json`
- File is created automatically in your home directory
- **Never commit this file to git** (it's in .gitignore logic)
- For security: keep your computer password-protected

---

## 🛠️ Installation / Update

```powershell
cd d:\projects\AI\stock-descriptor
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Done! Now you can run `run_gui.bat`

---

## 📝 Console Logging

All log messages from the GUI are now also printed to the terminal/console where you launched the application. This is useful for:
- Debugging and troubleshooting
- Running the GUI in headless/automated environments
- Keeping a terminal record of the pipeline execution

---

**Happy stock photo processing!** 🦈📸