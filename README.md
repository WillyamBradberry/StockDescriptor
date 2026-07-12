# 📸 StockDescriptor

**Batch describer for Photo Stocks** — мощный инструмент для подготовки, AI-анализа и обработки фотографий для стоковых платформ с автоматическим управлением метаданными EXIF и Obsidian-навигацией.

**NEW v2.1:** Multilingual GUI (English / Русский) with language toggle, console logging, and persistent language setting.

Showcase: https://stock.adobe.com/contributor/202223264/willyam

---

## 🌐 Language / Язык

The GUI now supports **English** and **Russian**. Switch between them with the **EN/RU** button in the top-right corner of the header. Your choice is saved to `~/.stockdescriptor/config.json`.

GUI теперь поддерживает **английский** и **русский**. Переключайтесь кнопкой **EN/RU** в правом верхнем углу. Выбор сохраняется в `~/.stockdescriptor/config.json`.

---

## ✨ New Beautiful GUI (recommended) / Новый красивый GUI (рекомендуется)

Launch the modern window with one click / Запустите современное окно одним кликом:

```batch
run_gui.bat
# or / или
python gui_launcher.py
```

### What the GUI can do / Что умеет GUI:

1. **Folder path input** + **Browse** button / **Поле ввода пути к папке** + кнопка **«Обзор...»**
2. **Big «🚀 RUN PIPELINE» button** — runs the full cycle / **Большая кнопка «🚀 ЗАПУСТИТЬ ПАЙПЛАЙН»** — выполняет полный цикл:
   - Resize (create THMBS/)
   - AI generation of Title / Description / Keywords
   - Inject metadata into originals (EXIF)
   - Create Obsidian navigation `METADATA-NAV.md`
3. **«⚙️ AI Settings» button** / **Кнопка «⚙️ Настройки AI»**:
   - Switch **LM Studio (local)** ↔ **Google Gemini (online)** / Переключатель **LM Studio (локально)** ↔ **Google Gemini (онлайн)**
   - Fields for LM Studio URL/model / Поля для URL/модели LM Studio
   - Gemini API Key field (masked) + model / Поле для Gemini API Key (маскируется) + модель
   - Batch size and delay sliders / Слайдеры размера батча и задержки
   - Key saved to: `~/.stockdescriptor/config.json` / Ключ сохраняется в `~/.stockdescriptor/config.json`
4. **Live execution log** with colored statuses / **Живой журнал выполнения** с цветными статусами
5. **Console logging** — all log messages are also printed to the terminal / **Вывод в консоль** — все сообщения дублируются в терминал
6. **Language toggle** — switch between EN/RU at any time / **Переключатель языка** — переключение между EN/RU в любой момент
7. Auto-save last folder / Автоматическое сохранение последней папки

**GUI Advantages / Преимущества GUI:**
- No need to remember commands and flags / Не нужно помнить команды и флаги
- Easy choice between local and cloud AI / Удобный выбор между локальной и облачной нейросетью
- API keys never go into the repository / API ключи не попадают в репозиторий
- Beautiful modern interface (Dark + blue theme) / Красивый современный интерфейс (Dark + blue theme)

---

## 🎯 Main Features / Основные возможности (CLI тоже работает)

### 1. 🖼️ Resize for Vision API / Масштабирование для Vision API
`processing/resize_for_vision.ps1` — proportionally reduces to 1024px, saves to `THMBS/` / пропорционально уменьшает до 1024px, сохраняет в `THMBS/`

### 2. 🤖 AI Metadata Generation / AI-генерация метаданных
`processing/batch_metadata.py` now supports **two providers** / теперь поддерживает **два провайдера**:
- **LM Studio** (default, local, OpenAI-compatible endpoint / по умолчанию, локально, OpenAI-совместимый эндпоинт)
- **Google Gemini** (online, requires API key / онлайн, требуется API ключ)

Supports resume, --check-errs, mock mode, incremental writing / Поддерживает resume, --check-errs, mock-режим, инкрементальную запись.

### 3. 🏷️ EXIF Injection + Obsidian nav / Инжекция EXIF + Obsidian nav
Full pipeline with one command / Полный пайплайн одной командой.

---

## 🚀 Quick Start / Быстрый старт (GUI — самый простой способ)

```batch
cd d:\projects\AI\stock-descriptor
run_gui.bat
```

1. Click **«Browse...» / «Обзор...»** → select folder with JPGs / выберите папку с JPG
2. (Optional) **«⚙️ AI Settings» / «⚙️ Настройки AI»** → choose Gemini and paste key / выберите Gemini и вставьте ключ
3. Click **«🚀 RUN PIPELINE» / «🚀 ЗАПУСТИТЬ ПАЙПЛАЙН»**
4. Watch the log — done! / Следите за журналом — готово!

---

## ⚙️ CLI (for scripts / advanced users / для скриптов / продвинутых пользователей)

```powershell
# Activate venv / Активировать venv
.\venv\Scripts\Activate.ps1

# Full pipeline via bat (old way) / Полный пайплайн через bat (старый способ)
processing\run_pipeline.bat "C:\path\to\your\images"

# Direct launch with provider selection / Прямой запуск с выбором провайдера
python processing\batch_metadata.py "C:\path\to\images" --provider gemini --model gemini-1.5-flash-latest
```

**New batch_metadata.py flags / Новые флаги batch_metadata.py:**
- `--provider lmstudio|gemini`
- `--model "model-name" / "название-модели"`
- `--api-key "YOUR_KEY"` (for Gemini; better use GUI or env var / для Gemini; лучше использовать GUI или переменную окружения)

---

## 📁 Project Structure / Структура проекта (обновлённая)

```
StockDescriptor/
├── gui_launcher.py          # ← NEW: beautiful GUI app / красивое GUI-приложение
├── run_gui.bat              # ← NEW: easy GUI launch / удобный запуск GUI
├── requirements.txt         # + customtkinter
├── processing/
│   ├── config_manager.py    # ← NEW: config + API key management / загрузка/сохранение настроек
│   ├── batch_metadata.py    # Updated: Gemini support + llm_config / Обновлён: поддержка Gemini
│   ├── resize_for_vision.ps1
│   ├── write_exif.ps1
│   ├── create-metadata-nav-modified.ps1
│   ├── run_pipeline.bat
│   └── ...
├── templates/
└── README.md
```

---

## 🔐 API Key Storage / Хранение API ключей

- On first Gemini key entry in GUI settings, it is saved to / При первом вводе ключа Gemini в настройках GUI он сохраняется в:
  `~/.stockdescriptor/config.json`
- File is created automatically in your home directory / Файл создаётся автоматически в вашем домашнем каталоге
- **Never commit this file to git** / **Никогда не коммитьте этот файл в git** (it's in .gitignore logic / он уже в .gitignore логике)
- For security: keep your computer password-protected / Для безопасности: храните компьютер под паролем

---

## 🛠️ Installation / Update / Установка / Обновление

```powershell
cd d:\projects\AI\stock-descriptor
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Done! Now you can run `run_gui.bat` / Готово! Теперь можно запускать `run_gui.bat`

---

## 📝 Console Logging / Вывод логов в консоль

All log messages from the GUI are now also printed to the terminal/console where you launched the application. This is useful for:
- Debugging and troubleshooting
- Running the GUI in headless/automated environments
- Keeping a terminal record of the pipeline execution

Все сообщения из GUI теперь также выводятся в терминал/консоль, из которой вы запустили приложение. Это полезно для:
- Отладки и поиска проблем
- Запуска GUI в автоматизированных средах
- Ведения терминальной записи выполнения пайплайна

---

**Happy stock photo processing! / Приятной работы с вашими стоковыми фотографиями!** 🦈📸