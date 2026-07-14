#!/usr/bin/env python3
"""
StockDescriptor GUI Launcher
Beautiful modern GUI for batch stock photo metadata generation.
Supports LM Studio (local) and Google Gemini (online) with persistent user config.
Multilingual: English / Русский

CHANGELOG:
- Main window now uses grid layout with proper weight for auto-resize
- Upload settings window is scalable and clamps to screen bounds
- Password fields have eye toggle (👁/🙈) in upload settings
- ESC closes SettingsWindow and UploadSettingsWindow
- Gear icon (⚙️) aligned in one row with "Upload to Stock Platforms" header
- Auto-upload checkbox moved next to Execution Log header, state saved to config
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import queue
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json
import time

# Add processing and scripts to path
ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT / "processing"))
sys.path.insert(0, str(ROOT / "scripts"))

try:
    from config_manager import load_config, save_config
    from batch_metadata import (
        generate_metadata_for_folder,
        generate_preview_file,
        run_write_exif,
        run_nav_script
    )
    from upload_to_stocks import (
        upload_shutterstock,
        upload_adobe,
        upload_pond5,
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you run from project root and venv has dependencies (including paramiko).")
    sys.exit(1)


# ================== MULTILINGUAL STRINGS ==================
LANGUAGES = {
    "en": {
        "window_title": "📸 StockDescriptor — AI Metadata for Stock Photos",
        "settings_title": "⚙️ AI Settings — StockDescriptor",
        "settings_header": "Select AI provider and configure connection",
        "app_title": "📸 StockDescriptor",
        "app_subtitle": "Batch AI Metadata Generator for Stock Photography",
        "settings_btn": "⚙️  AI Settings",
        "folder_label": "📁  Folder with original photos",
        "folder_placeholder": "Select folder with JPG files...",
        "browse_btn": "Browse...",
        "browse_title": "Select folder with JPG photos for stock",
        "run_btn": "🚀  RUN PIPELINE",
        "run_btn_running": "⏳  RUNNING... (see log)",
        "provider_label": "🤖 Provider: {}",
        "model_label": "Model: {}",
        "log_label": "📋  Execution Log",
        "status_ready": "✅ Ready. Select a folder and click «RUN PIPELINE»",
        "status_running": "🚀 Pipeline started...",
        "status_done": "✅ Pipeline complete. Ready for next run.",
        "status_error": "❌ Execution error",
        "status_no_thumbs": "❌ Error: no THMBS folder",
        "hint": "API keys stored locally in ~/.stockdescriptor/config.json",
        "step_resize": "=== STEP 1/4: Creating thumbnails (resize_for_vision) ===",
        "step_metadata": "\n=== STEP 2/4: AI Metadata Generation ===",
        "step_exif": "\n=== STEP 3/4: Injecting metadata into originals (EXIF) ===",
        "step_nav": "\n=== STEP 4/4: Creating Obsidian navigation ===",
        "pipeline_done": "\n═══════════════════════════════════════════\n🎉 PIPELINE COMPLETED SUCCESSFULLY!",
        "log_loaded_folder": "📂 Loaded last folder from config.",
        "log_welcome": "👋 Welcome! Select a folder with photos.",
        "log_folder_selected": "📁 Folder selected: {}",
        "log_settings_saved": "⚙️ Settings saved. API keys written to user file.",
        "log_thumbs_ok": "Thumbnails successfully created in THMBS/",
        "log_thumbs_skip": "resize_for_vision.ps1 not found — skipping (ensure THMBS already exists)",
        "log_metadata_ok": "METADATA.md created: {}",
        "log_metadata_warn": "Metadata generation completed with issues.",
        "log_preview_ok": "METADATA_PREVIEW.md created for quick review.",
        "log_preview_err": "Failed to create preview: {}",
        "log_exif_ok": "EXIF metadata successfully written to original files.",
        "log_exif_err": "Error executing write_exif.ps1",
        "log_exif_skip": "write_exif.ps1 not found — skipping EXIF injection.",
        "log_exif_skip_errors": "\n⚠️ Skipped EXIF injection due to errors in metadata_error.md",
        "log_exif_fix": "Fix errors and run again with --check-errs or via GUI.",
        "log_nav_ok": "METADATA-NAV.md successfully created for Obsidian.",
        "log_critical": "CRITICAL ERROR: {}",
        "settings_provider": "Provider:",
        "seg_lmstudio": "LM Studio (local)",
        "seg_gemini": "Google Gemini (online)",
        "lm_frame_title": "LM Studio (OpenAI-compatible)",
        "lm_url_label": "Endpoint URL:",
        "lm_model_label": "Model name:",
        "gemini_frame_title": "Google Gemini Vision",
        "gemini_key_label": "API Key (stored locally):",
        "gemini_model_label": "Model (recommended: gemini-1.5-flash-latest or gemini-2.0-flash):",
        "exiftool_label": "ExifTool path:",
        "exiftool_browse": "Browse...",
        "common_params": "Common processing parameters",
        "batch_label": "Batch size (recommended 2-4):",
        "delay_label": "Delay between batches (sec):",
        "save_btn": "💾 Save settings",
        "cancel_btn": "Cancel",
        "warn_text": "🔒 API keys are stored in plain text in ~/.stockdescriptor/config.json\nKeep your computer secure. Do not share this file.",
        "msg_running": "In progress",
        "msg_running_text": "Pipeline is already running. Please wait for completion.",
        "msg_no_folder": "Error",
        "msg_no_folder_text": "First select a folder with photos!",
        "msg_folder_not_found": "Error",
        "msg_folder_not_found_text": "Folder not found:\n{}",
        "msg_no_key_title": "No Gemini Key",
        "msg_no_key_text": "No API key set for Gemini.\n\nOpen settings now?",
        "msg_empty_key_title": "Empty Key",
        "msg_empty_key_text": "You selected Gemini but didn't enter an API key.\nSaving without key — you'll get a warning on launch.",
        "msg_save_ok_title": "Done",
        "msg_save_ok_text": "Settings saved successfully!\n\nOn first Gemini use, the key will be saved in your profile.",
        "msg_save_err_title": "Error",
        "msg_save_err_text": "Failed to save config.",
        "resize_warn": "Warning during resize: {}",
        "resize_script_missing": "resize_for_vision.ps1 not found — skipping (ensure THMBS already exists)",
        "resize_no_thumbs": "ERROR: THMBS folder not created. Check JPG files exist.",
        "upload_btn": "📤 Upload to Stocks",
        "upload_section": "📤  Upload to Stock Platforms",
        "upload_shutterstock": "Shutterstock",
        "upload_adobe": "Adobe Stock",
        "upload_pond5": "Pond5",
        "upload_start_btn": "📤 Upload Selected",
        "upload_started": "📤 Starting parallel upload to stocks...",
        "upload_running": "📤 Parallel upload to stocks...",
        "upload_done": "✅ Upload complete. Ready for next run.",
        "upload_no_folder": "Select folder with JPG files for stock upload",
        "upload_platform_start": "▶️ Starting upload to {}...",
        "upload_platform_done": "✅ {} completed.",
        "upload_platform_error": "❌ Error on {}: {}",
        "upload_settings_title": "📤 Upload FTP Settings — StockDescriptor",
        "upload_settings_header": "Configure FTP/SFTP credentials for stock platforms",
        "upload_host_label": "Host:",
        "upload_port_label": "Port:",
        "upload_user_label": "Username:",
        "upload_pass_label": "Password:",
        "upload_path_label": "Remote path:",
        "upload_save_ok": "Upload settings saved successfully!",
        "upload_save_err": "Failed to save upload config.",
        "auto_upload": "Auto-upload to stocks after EXIF injection",
        "show_password": "Show password",
        "hide_password": "Hide password",
        "lang_toggle": "EN",
    },
    "ru": {
        "window_title": "📸 StockDescriptor — AI Метаданные для Стоковых Фото",
        "settings_title": "⚙️ Настройки нейросети — StockDescriptor",
        "settings_header": "Выберите провайдер AI и настройте подключение",
        "app_title": "📸 StockDescriptor",
        "app_subtitle": "Пакетный AI-генератор метаданных для стоковой фотографии",
        "settings_btn": "⚙️  Настройки AI",
        "folder_label": "📁  Папка с оригинальными фотографиями",
        "folder_placeholder": "Выберите папку с JPG файлами...",
        "browse_btn": "Обзор...",
        "browse_title": "Выберите папку с JPG фотографиями для стока",
        "run_btn": "🚀  ЗАПУСТИТЬ ПАЙПЛАЙН",
        "run_btn_running": "⏳  ВЫПОЛНЯЕТСЯ... (см. журнал)",
        "provider_label": "🤖 Провайдер: {}",
        "model_label": "Модель: {}",
        "log_label": "📋  Журнал выполнения",
        "status_ready": "✅ Готов к работе. Выберите папку и нажмите «ЗАПУСТИТЬ ПАЙПЛАЙН»",
        "status_running": "🚀 Пайплайн запущен...",
        "status_done": "✅ Пайплайн завершён. Готов к следующему запуску.",
        "status_error": "❌ Ошибка выполнения",
        "status_no_thumbs": "❌ Ошибка: нет THMBS",
        "hint": "API ключи хранятся локально в ~/.stockdescriptor/config.json",
        "step_resize": "=== ШАГ 1/4: Создание миниатюр (resize_for_vision) ===",
        "step_metadata": "\n=== ШАГ 2/4: Генерация метаданных через AI ===",
        "step_exif": "\n=== ШАГ 3/4: Инжекция метаданных в оригиналы (EXIF) ===",
        "step_nav": "\n=== ШАГ 4/4: Создание навигации для Obsidian ===",
        "pipeline_done": "\n═══════════════════════════════════════════\n🎉 ПАЙПЛАЙН ЗАВЕРШЁН УСПЕШНО!",
        "log_loaded_folder": "📂 Загружена последняя папка из конфига.",
        "log_welcome": "👋 Добро пожаловать! Выберите папку с фотографиями.",
        "log_folder_selected": "📁 Выбрана папка: {}",
        "log_settings_saved": "⚙️ Настройки сохранены. API ключи записаны в пользовательский файл.",
        "log_thumbs_ok": "Миниатюры успешно созданы в папке THMBS/",
        "log_thumbs_skip": "resize_for_vision.ps1 не найден — пропускаем (убедитесь что THMBS уже есть)",
        "log_metadata_ok": "METADATA.md создан: {}",
        "log_metadata_warn": "Генерация метаданных завершилась с проблемами.",
        "log_preview_ok": "METADATA_PREVIEW.md создан для быстрого просмотра.",
        "log_preview_err": "Не удалось создать превью: {}",
        "log_exif_ok": "EXIF метаданные успешно записаны в оригинальные файлы.",
        "log_exif_err": "Ошибка при выполнении write_exif.ps1",
        "log_exif_skip": "write_exif.ps1 не найден — пропускаем инжекцию EXIF.",
        "log_exif_skip_errors": "\n⚠️ Пропущена инжекция EXIF из-за ошибок в metadata_error.md",
        "log_exif_fix": "Исправьте ошибки и запустите с --check-errs или через GUI заново.",
        "log_nav_ok": "METADATA-NAV.md успешно создан для Obsidian.",
        "log_critical": "КРИТИЧЕСКАЯ ОШИБКА: {}",
        "settings_provider": "Провайдер:",
        "seg_lmstudio": "LM Studio (локально)",
        "seg_gemini": "Google Gemini (онлайн)",
        "lm_frame_title": "LM Studio (OpenAI-совместимый)",
        "lm_url_label": "URL эндпоинта:",
        "lm_model_label": "Название модели:",
        "gemini_frame_title": "Google Gemini Vision",
        "gemini_key_label": "API Key (сохраняется локально):",
        "gemini_model_label": "Модель (рекомендуется gemini-1.5-flash-latest или gemini-2.0-flash):",
        "exiftool_label": "Путь к ExifTool:",
        "exiftool_browse": "Обзор...",
        "common_params": "Общие параметры обработки",
        "batch_label": "Размер батча (рекомендуется 2-4):",
        "delay_label": "Задержка между батчами (сек):",
        "save_btn": "💾 Сохранить настройки",
        "cancel_btn": "Отмена",
        "warn_text": "🔒 API ключи сохраняются в текстовом файле ~/.stockdescriptor/config.json\nХраните компьютер в безопасности. Никому не передавайте этот файл.",
        "msg_running": "В процессе",
        "msg_running_text": "Пайплайн уже выполняется. Дождитесь завершения.",
        "msg_no_folder": "Ошибка",
        "msg_no_folder_text": "Сначала выберите папку с фотографиями!",
        "msg_folder_not_found": "Ошибка",
        "msg_folder_not_found_text": "Папка не найдена:\n{}",
        "msg_no_key_title": "Нет ключа Gemini",
        "msg_no_key_text": "Для Gemini не указан API ключ.\n\nХотите открыть настройки сейчас?",
        "msg_empty_key_title": "Пустой ключ",
        "msg_empty_key_text": "Вы выбрали Gemini, но не ввели API ключ.\nСохраняю без ключа — при запуске будет предупреждение.",
        "msg_save_ok_title": "Готово",
        "msg_save_ok_text": "Настройки успешно сохранены!\n\nПри первом использовании Gemini ключ будет сохранён в вашем профиле.",
        "msg_save_err_title": "Ошибка",
        "msg_save_err_text": "Не удалось сохранить конфиг.",
        "resize_warn": "Предупреждение при resize: {}",
        "resize_script_missing": "resize_for_vision.ps1 не найден — пропускаем (убедитесь что THMBS уже есть)",
        "resize_no_thumbs": "ОШИБКА: Папка THMBS не создана. Проверьте наличие JPG файлов.",
        "upload_btn": "📤 Загрузить на стоки",
        "upload_section": "📤  Загрузка на стоковые платформы",
        "upload_shutterstock": "Shutterstock",
        "upload_adobe": "Adobe Stock",
        "upload_pond5": "Pond5",
        "upload_start_btn": "📤 Загрузить выбранные",
        "upload_started": "📤 Запуск параллельной загрузки на стоки...",
        "upload_running": "📤 Параллельная загрузка на стоки...",
        "upload_done": "✅ Загрузка завершена. Готов к следующему запуску.",
        "upload_no_folder": "Выберите папку с JPG для загрузки на стоки",
        "upload_platform_start": "▶️ Начинаем загрузку на {}...",
        "upload_platform_done": "✅ {} завершён.",
        "upload_platform_error": "❌ Ошибка на {}: {}",
        "upload_settings_title": "📤 Настройки FTP загрузки — StockDescriptor",
        "upload_settings_header": "Настройте FTP/SFTP учётные данные для стоковых платформ",
        "upload_host_label": "Хост:",
        "upload_port_label": "Порт:",
        "upload_user_label": "Имя пользователя:",
        "upload_pass_label": "Пароль:",
        "upload_path_label": "Удалённый путь:",
        "upload_save_ok": "Настройки загрузки успешно сохранены!",
        "upload_save_err": "Не удалось сохранить конфиг загрузки.",
        "auto_upload": "Автозагрузка на стоки после EXIF",
        "show_password": "Показать пароль",
        "hide_password": "Скрыть пароль",
        "lang_toggle": "RU",
    }
}


# ================== GUI APPEARANCE ==================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

ACCENT_COLOR = "#2E8B57"
DARK_BG = "#1E1E2E"
CARD_BG = "#25253A"
SUCCESS_GREEN = "#4ADE80"
WARNING_ORANGE = "#FBBF24"
ERROR_RED = "#F87171"


class StockDescriptorGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config: Dict[str, Any] = load_config()
        self.current_folder: Optional[Path] = None
        if self.config.get("last_folder"):
            self.current_folder = Path(self.config["last_folder"])
        self.lang: str = self.config.get("language", "ru")
        if self.lang not in ("en", "ru"):
            self.lang = "ru"
        self.log_queue: queue.Queue = queue.Queue()
        self.worker_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.is_uploading = False

        self.title(self.tr("window_title"))
        self._setup_geometry()
        self.minsize(900, 700)

        # Grid layout for main window
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        self._build_ui()
        self._load_last_folder()
        self._poll_log_queue()

    def tr(self, key: str, *args) -> str:
        val = LANGUAGES.get(self.lang, LANGUAGES["ru"]).get(key, key)
        if args:
            return val.format(*args)
        return val

    def _setup_geometry(self):
        """Center window and size it to 85% of screen, but cap at reasonable max."""
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = min(1100, int(sw * 0.85))
        h = min(850, int(sh * 0.85))
        x = max(20, (sw - w) // 2)
        y = max(30, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _toggle_language(self):
        self.lang = "en" if self.lang == "ru" else "ru"
        self.config["language"] = self.lang
        save_config(self.config)
        self._refresh_ui_text()
        self.log(self.tr("log_settings_saved"), "success")

    def _refresh_ui_text(self):
        self.title(self.tr("window_title"))
        self.title_label.configure(text=self.tr("app_title"))
        self.subtitle_label.configure(text=self.tr("app_subtitle"))
        self.settings_btn.configure(text=self.tr("settings_btn"))
        self.folder_label.configure(text=self.tr("folder_label"))
        self.folder_entry.configure(placeholder_text=self.tr("folder_placeholder"))
        self.browse_btn.configure(text=self.tr("browse_btn"))
        self.run_btn.configure(text=self.tr("run_btn"))
        self.provider_label.configure(text=self.tr("provider_label", self.config.get("provider", "lmstudio").upper()))
        self.model_label.configure(text=self.tr("model_label", self._get_current_model()))
        self.log_label.configure(text=self.tr("log_label"))
        self.status_label.configure(text=self.tr("status_ready"))
        self.hint_label.configure(text=self.tr("hint"))
        self.lang_btn.configure(text=self.tr("lang_toggle"))
        self.auto_upload_cb.configure(text=self.tr("auto_upload"))
        if hasattr(self, 'upload_section_label'):
            self.upload_section_label.configure(text=self.tr("upload_section"))
        if hasattr(self, 'upload_start_btn'):
            self.upload_start_btn.configure(text=self.tr("upload_start_btn"))
        for platform_key in ["shutterstock", "adobe", "pond5"]:
            cb = getattr(self, f'{platform_key}_checkbox', None)
            if cb:
                cb.configure(text=self.tr(f'upload_{platform_key}'))
        if self.is_uploading:
            self.upload_status_label.configure(text=self.tr("upload_running"))
        else:
            self.upload_status_label.configure(text="")

    def _build_ui(self):
        # === Header (row 0) ===
        header_frame = ctk.CTkFrame(self, height=70, corner_radius=0, fg_color=DARK_BG)
        header_frame.grid(row=0, column=0, sticky="new")
        header_frame.grid_columnconfigure(1, weight=1)

        self.title_label = ctk.CTkLabel(
            header_frame, text=self.tr("app_title"),
            font=ctk.CTkFont(size=28, weight="bold"), text_color="#E0E7FF"
        )
        self.title_label.grid(row=0, column=0, padx=25, pady=15, sticky="w")

        self.subtitle_label = ctk.CTkLabel(
            header_frame, text=self.tr("app_subtitle"),
            font=ctk.CTkFont(size=13), text_color="#94A3B8"
        )
        self.subtitle_label.grid(row=0, column=1, padx=10, pady=20, sticky="w")

        self.lang_btn = ctk.CTkButton(
            header_frame, text=self.tr("lang_toggle"),
            width=50, height=36, corner_radius=8,
            fg_color="#334155", hover_color="#475569",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._toggle_language
        )
        self.lang_btn.grid(row=0, column=3, padx=(0, 10), pady=17, sticky="e")

        self.settings_btn = ctk.CTkButton(
            header_frame, text=self.tr("settings_btn"),
            width=160, height=36, corner_radius=8,
            fg_color="#334155", hover_color="#475569",
            command=self.open_settings_window
        )
        self.settings_btn.grid(row=0, column=2, padx=(0, 5), pady=17, sticky="e")

        # === Scrollable main content (row 1) ===
        scroll_frame = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        scroll_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        scroll_frame.grid_columnconfigure(0, weight=1)

        main_card = ctk.CTkFrame(scroll_frame, corner_radius=16, fg_color=CARD_BG)
        main_card.pack(fill="both", expand=True, padx=20, pady=(10, 15))

        # Folder selection
        self.folder_label = ctk.CTkLabel(
            main_card, text=self.tr("folder_label"),
            font=ctk.CTkFont(size=15, weight="bold"), anchor="w"
        )
        self.folder_label.pack(fill="x", padx=25, pady=(20, 8))

        folder_frame = ctk.CTkFrame(main_card, fg_color="transparent")
        folder_frame.pack(fill="x", padx=25, pady=(0, 15))
        folder_frame.grid_columnconfigure(0, weight=1)

        self.folder_entry = ctk.CTkEntry(
            folder_frame, placeholder_text=self.tr("folder_placeholder"),
            height=42, corner_radius=10, font=ctk.CTkFont(size=13)
        )
        self.folder_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.browse_btn = ctk.CTkButton(
            folder_frame, text=self.tr("browse_btn"),
            width=110, height=42, corner_radius=10,
            fg_color="#475569", hover_color="#64748B",
            command=self.browse_folder
        )
        self.browse_btn.grid(row=0, column=1, sticky="e")

        # Action row
        action_frame = ctk.CTkFrame(main_card, fg_color="transparent")
        action_frame.pack(fill="x", padx=25, pady=(5, 15))

        self.run_btn = ctk.CTkButton(
            action_frame, text=self.tr("run_btn"),
            height=52, corner_radius=12,
            font=ctk.CTkFont(size=17, weight="bold"),
            fg_color=ACCENT_COLOR, hover_color="#3CB371",
            command=self.start_pipeline
        )
        self.run_btn.pack(fill="x", pady=(5, 0))

        # Info row
        info_row = ctk.CTkFrame(main_card, fg_color="transparent")
        info_row.pack(fill="x", padx=25, pady=(8, 5))

        self.provider_label = ctk.CTkLabel(
            info_row, text=self.tr("provider_label", self.config.get("provider", "lmstudio").upper()),
            font=ctk.CTkFont(size=12), text_color="#CBD5E1"
        )
        self.provider_label.pack(side="left")

        self.model_label = ctk.CTkLabel(
            info_row, text=self.tr("model_label", self._get_current_model()),
            font=ctk.CTkFont(size=12), text_color="#94A3B8"
        )
        self.model_label.pack(side="left", padx=20)

        # === Log header with auto-upload checkbox (NEW) ===
        log_header_frame = ctk.CTkFrame(main_card, fg_color="transparent")
        log_header_frame.pack(fill="x", padx=25, pady=(15, 6))
        log_header_frame.grid_columnconfigure(0, weight=1)

        self.log_label = ctk.CTkLabel(
            log_header_frame, text=self.tr("log_label"),
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        )
        self.log_label.grid(row=0, column=0, sticky="w")

        self.auto_upload_var = ctk.BooleanVar(value=self.config.get("auto_upload", False))
        self.auto_upload_cb = ctk.CTkCheckBox(
            log_header_frame,
            text=self.tr("auto_upload"),
            variable=self.auto_upload_var,
            font=ctk.CTkFont(size=11),
            command=self._on_auto_upload_toggle
        )
        self.auto_upload_cb.grid(row=0, column=1, sticky="e", padx=(10, 0))

        self.log_text = ctk.CTkTextbox(
            main_card, height=220, corner_radius=10,
            fg_color="#1A1A2E", border_color="#334155", border_width=1,
            font=ctk.CTkFont(family="Consolas", size=11), wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=25, pady=(0, 10))

        # === Upload section (row with gear icon inline) ===
        upload_section_frame = ctk.CTkFrame(main_card, fg_color="transparent")
        upload_section_frame.pack(fill="x", padx=25, pady=(5, 6))
        upload_section_frame.grid_columnconfigure(0, weight=1)

        self.upload_section_label = ctk.CTkLabel(
            upload_section_frame, text=self.tr("upload_section"),
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        )
        self.upload_section_label.grid(row=0, column=0, sticky="w")

        # Gear icon button inline with the header
        self.upload_gear_btn = ctk.CTkButton(
            upload_section_frame, text="⚙️",
            width=32, height=28, corner_radius=6,
            fg_color="#334155", hover_color="#475569",
            font=ctk.CTkFont(size=13),
            command=self.open_upload_settings
        )
        self.upload_gear_btn.grid(row=0, column=1, sticky="e", padx=(8, 0))

        # Upload card
        upload_frame = ctk.CTkFrame(main_card, fg_color="#1E293B", corner_radius=10)
        upload_frame.pack(fill="x", padx=25, pady=(0, 10))

        checkbox_frame = ctk.CTkFrame(upload_frame, fg_color="transparent")
        checkbox_frame.pack(fill="x", padx=15, pady=(10, 5))

        self.upload_platforms = {
            "shutterstock": ctk.BooleanVar(value=True),
            "adobe": ctk.BooleanVar(value=True),
            "pond5": ctk.BooleanVar(value=True),
        }

        self.shutterstock_checkbox = ctk.CTkCheckBox(
            checkbox_frame, text=self.tr("upload_shutterstock"),
            variable=self.upload_platforms["shutterstock"], font=ctk.CTkFont(size=12)
        )
        self.shutterstock_checkbox.pack(side="left", padx=(0, 20))

        self.adobe_checkbox = ctk.CTkCheckBox(
            checkbox_frame, text=self.tr("upload_adobe"),
            variable=self.upload_platforms["adobe"], font=ctk.CTkFont(size=12)
        )
        self.adobe_checkbox.pack(side="left", padx=(0, 20))

        self.pond5_checkbox = ctk.CTkCheckBox(
            checkbox_frame, text=self.tr("upload_pond5"),
            variable=self.upload_platforms["pond5"], font=ctk.CTkFont(size=12)
        )
        self.pond5_checkbox.pack(side="left", padx=(0, 20))

        # Progress bars
        progress_frame = ctk.CTkFrame(upload_frame, fg_color="transparent")
        progress_frame.pack(fill="x", padx=15, pady=(5, 5))

        self.upload_progress = {}
        self.upload_progress_labels = {}
        platform_colors = {"shutterstock": "#FF6B6B", "adobe": "#FFD93D", "pond5": "#6BCB77"}
        platform_short = {"shutterstock": "SS", "adobe": "AS", "pond5": "P5"}

        for platform, color in platform_colors.items():
            row = ctk.CTkFrame(progress_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{platform_short[platform]}:", width=30, font=ctk.CTkFont(size=11)).pack(side="left")
            bar = ctk.CTkProgressBar(row, width=300, height=14, corner_radius=4, fg_color="#334155", progress_color=color)
            bar.set(0)
            bar.pack(side="left", padx=(5, 8), fill="x", expand=True)
            self.upload_progress[platform] = bar
            pct = ctk.CTkLabel(row, text="0%", width=40, font=ctk.CTkFont(size=11))
            pct.pack(side="left")
            self.upload_progress_labels[platform] = pct

        upload_action_frame = ctk.CTkFrame(upload_frame, fg_color="transparent")
        upload_action_frame.pack(fill="x", padx=15, pady=(5, 10))

        self.upload_start_btn = ctk.CTkButton(
            upload_action_frame, text=self.tr("upload_start_btn"),
            width=180, height=36, corner_radius=8,
            fg_color="#475569", hover_color="#64748B",
            command=self.start_parallel_upload
        )
        self.upload_start_btn.pack(side="left", padx=(0, 10))

        self.upload_status_label = ctk.CTkLabel(
            upload_action_frame, text="",
            font=ctk.CTkFont(size=11), text_color="#94A3B8"
        )
        self.upload_status_label.pack(side="left", padx=15)

        # === Status bar (row 2) ===
        status_frame = ctk.CTkFrame(self, height=32, corner_radius=0, fg_color="#0F172A")
        status_frame.grid(row=2, column=0, sticky="sew")
        status_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            status_frame, text=self.tr("status_ready"),
            font=ctk.CTkFont(size=12), text_color="#64748B"
        )
        self.status_label.grid(row=0, column=0, padx=20, pady=6, sticky="w")

        self.hint_label = ctk.CTkLabel(
            status_frame, text=self.tr("hint"),
            font=ctk.CTkFont(size=10), text_color="#475569"
        )
        self.hint_label.grid(row=0, column=1, padx=20, pady=6, sticky="e")

    def _on_auto_upload_toggle(self):
        """Save auto-upload preference to config."""
        self.config["auto_upload"] = self.auto_upload_var.get()
        save_config(self.config)

    def _get_current_model(self) -> str:
        if self.config.get("provider") == "gemini":
            return self.config.get("gemini_model", "gemini-1.5-flash-latest")
        return self.config.get("lmstudio_model", "qwen3.6-35b-a3b")

    def _load_last_folder(self):
        if self.current_folder and self.current_folder.exists():
            self.folder_entry.insert(0, str(self.current_folder))
            self.log(self.tr("log_loaded_folder"))
        else:
            self.log(self.tr("log_welcome"))

    def log(self, message: str, level: str = "info"):
        timestamp = time.strftime("%H:%M:%S")
        prefix = {"info": "•", "success": "✅", "warning": "⚠️", "error": "❌", "step": "➤"}.get(level, "•")
        formatted = f"[{timestamp}] {prefix} {message}\n"
        print(formatted, end="", flush=True)
        try:
            self.log_text.insert("end", formatted)
            self.log_text.see("end")
        except Exception:
            pass

    def update_status(self, text: str, color: str = "#64748B"):
        self.status_label.configure(text=text, text_color=color)

    def browse_folder(self):
        folder = filedialog.askdirectory(
            title=self.tr("browse_title"),
            initialdir=str(self.current_folder) if self.current_folder else str(Path.home())
        )
        if folder:
            self.current_folder = Path(folder)
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            self.config["last_folder"] = folder
            save_config(self.config)
            self.log(self.tr("log_folder_selected", folder), "success")

    def open_settings_window(self):
        SettingsWindow(self, self.config, self.on_settings_saved, self.lang)

    def on_settings_saved(self, new_config: Dict[str, Any]):
        self.config = new_config
        self.provider_label.configure(text=self.tr("provider_label", self.config.get("provider", "lmstudio").upper()))
        self.model_label.configure(text=self.tr("model_label", self._get_current_model()))
        self.log(self.tr("log_settings_saved"), "success")

    def start_pipeline(self):
        if self.is_running:
            messagebox.showwarning(self.tr("msg_running"), self.tr("msg_running_text"))
            return

        folder_str = self.folder_entry.get().strip()
        if not folder_str:
            messagebox.showerror(self.tr("msg_no_folder"), self.tr("msg_no_folder_text"))
            return

        folder = Path(folder_str)
        if not folder.exists():
            messagebox.showerror(self.tr("msg_folder_not_found"), self.tr("msg_folder_not_found_text", str(folder)))
            return

        if self.config.get("provider") == "gemini" and not self.config.get("gemini_api_key"):
            if not messagebox.askyesno(self.tr("msg_no_key_title"), self.tr("msg_no_key_text")):
                return
            self.open_settings_window()
            return

        self.is_running = True
        self.run_btn.configure(state="disabled", text=self.tr("run_btn_running"))
        self.log_text.delete("1.0", "end")
        self.update_status(self.tr("status_running"), SUCCESS_GREEN)

        self.log("═══════════════════════════════════════════", "step")
        self.log(f"Pipeline for: {folder}", "step")
        self.log(f"Provider: {self.config.get('provider', 'lmstudio').upper()}", "info")

        self.worker_thread = threading.Thread(target=self._pipeline_worker, args=(folder,), daemon=True)
        self.worker_thread.start()

    def _pipeline_worker(self, folder: Path):
        q = self.log_queue

        def put(msg, level="info"):
            q.put(("log", msg, level))

        def set_status(msg, color="#64748B"):
            q.put(("status", msg, color))

        pipeline_ok = False
        try:
            put(self.tr("step_resize"), "step")
            set_status("🔄 Creating thumbnails...", WARNING_ORANGE)

            resize_script = ROOT / "processing" / "resize_for_vision.ps1"
            if resize_script.exists():
                cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(resize_script), "-ImageFolder", str(folder)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if result.returncode != 0:
                    put(self.tr("resize_warn", result.stderr[-300:] if result.stderr else 'code ' + str(result.returncode)), "warning")
                else:
                    put(self.tr("log_thumbs_ok"), "success")
            else:
                put(self.tr("resize_script_missing"), "warning")

            thumbs_folder = folder / "THMBS"
            if not thumbs_folder.exists():
                put(self.tr("resize_no_thumbs"), "error")
                set_status(self.tr("status_no_thumbs"), ERROR_RED)
                return

            put(self.tr("step_metadata"), "step")
            set_status("🤖 Generating Title/Description/Keywords...", "#60A5FA")

            metadata_file, error_file = generate_metadata_for_folder(
                folder, thumbs_folder,
                batch_size=self.config.get("batch_size", 3),
                delay=self.config.get("delay", 3),
                mock=False, check_errs=False, llm_config=self.config
            )

            if metadata_file and metadata_file.exists():
                put(self.tr("log_metadata_ok", str(metadata_file)), "success")
            else:
                put(self.tr("log_metadata_warn"), "warning")

            try:
                generate_preview_file(folder, metadata_file, thumbs_folder)
                put(self.tr("log_preview_ok"), "info")
            except Exception as e:
                put(self.tr("log_preview_err", str(e)), "warning")

            has_errors = error_file is not None and error_file.exists()

            if not has_errors:
                put(self.tr("step_exif"), "step")
                set_status("🏷️ Writing EXIF to JPG...", "#FBBF24")

                exif_script = folder / "write_exif.ps1"
                if not exif_script.exists():
                    exif_script = ROOT / "processing" / "write_exif.ps1"

                if exif_script.exists():
                    exiftool_path = self.config.get("exiftool_path", "D:\\PROGRAMS\\EXIFTOOL\\exiftool.exe")
                    success = run_write_exif(folder, exif_script, exiftool_path)
                    if success:
                        put(self.tr("log_exif_ok"), "success")
                    else:
                        put(self.tr("log_exif_err"), "error")
                else:
                    put(self.tr("log_exif_skip"), "warning")
            else:
                put(self.tr("log_exif_skip_errors"), "warning")
                put(self.tr("log_exif_fix"), "info")

            put(self.tr("step_nav"), "step")
            set_status("🗂️ Generating METADATA-NAV.md...", "#A78BFA")

            nav_success = run_nav_script(folder, metadata_file, ROOT / "processing", ask=False)
            if nav_success:
                put(self.tr("log_nav_ok"), "success")

            put(self.tr("pipeline_done"), "success")
            set_status(self.tr("status_done"), SUCCESS_GREEN)
            pipeline_ok = True

            self.config["last_folder"] = str(folder)
            save_config(self.config)

        except Exception as e:
            put(self.tr("log_critical", str(e)), "error")
            set_status(self.tr("status_error"), ERROR_RED)
        finally:
            q.put(("done",))
            if pipeline_ok and self.auto_upload_var.get():
                q.put(("auto_upload_start",))

    def _poll_log_queue(self):
        try:
            while True:
                item = self.log_queue.get_nowait()
                if item[0] == "log":
                    _, msg, level = item
                    self.log(msg, level)
                elif item[0] == "status":
                    _, text, color = item
                    self.update_status(text, color)
                elif item[0] == "done":
                    self.is_running = False
                    self.run_btn.configure(state="normal", text=self.tr("run_btn"))
                    self.update_status(self.tr("status_done"), SUCCESS_GREEN)
                elif item[0] == "auto_upload_start":
                    self.after(500, self._trigger_auto_upload)
                elif item[0] == "upload_start":
                    _, platform, total = item
                    self.upload_progress[platform].set(0)
                    self.upload_progress_labels[platform].configure(text=f"0/{total}")
                elif item[0] == "progress":
                    _, platform, current, total, filename = item
                    pct = current / total if total > 0 else 0
                    self.upload_progress[platform].set(pct)
                    self.upload_progress_labels[platform].configure(text=f"{current}/{total}")
                elif item[0] == "upload_done":
                    _, platform, uploaded, total = item
                    self.upload_progress[platform].set(1.0)
                    self.upload_progress_labels[platform].configure(text=f"{uploaded}/{total} ✅")
                elif item[0] == "upload_error":
                    _, platform, err = item
                    self.upload_progress_labels[platform].configure(text="❌")
                elif item[0] == "upload_thread_done":
                    _, platform = item
                    self.is_running = False
                    self.is_uploading = False
                    self.upload_start_btn.configure(state="normal", text=self.tr("upload_start_btn"))
                    self.upload_status_label.configure(text="")
                    self.update_status(self.tr("status_ready"))
        except queue.Empty:
            pass
        self.after(120, self._poll_log_queue)

    def _trigger_auto_upload(self):
        self.log("📤 Auto-upload triggered (checkbox enabled)", "step")
        self.current_folder = Path(self.folder_entry.get().strip())
        selected = [p for p, var in self.upload_platforms.items() if var.get()]
        if not selected:
            self.log("⚠️ No platforms selected for auto-upload", "warning")
            return

        self.is_running = True
        self.is_uploading = True
        self.upload_start_btn.configure(state="disabled", text="⏳ Uploading...")
        self.upload_status_label.configure(text=self.tr("upload_running"))

        for platform in self.upload_progress:
            self.upload_progress[platform].set(0)
            self.upload_progress_labels[platform].configure(text="0/0")

        self.log(self.tr("upload_started"), "step")
        self.update_status(self.tr("upload_running"), WARNING_ORANGE)

        for platform in selected:
            t = threading.Thread(target=self._upload_worker, args=(platform, self.current_folder), daemon=True)
            t.start()

    # ================== UPLOAD METHODS ==================

    def open_upload_settings(self):
        UploadSettingsWindow(self, self.config, self.lang)

    def start_parallel_upload(self):
        if self.is_running:
            messagebox.showwarning(self.tr("msg_running"), self.tr("msg_running_text"))
            return

        folder_str = self.folder_entry.get().strip()
        if not folder_str or not Path(folder_str).exists():
            folder = filedialog.askdirectory(
                title=self.tr("upload_no_folder"),
                initialdir=str(self.current_folder) if self.current_folder else str(Path.home())
            )
            if not folder:
                return
            self.current_folder = Path(folder)
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            self.config["last_folder"] = folder
            save_config(self.config)
        else:
            self.current_folder = Path(folder_str)

        selected = [p for p, var in self.upload_platforms.items() if var.get()]
        if not selected:
            messagebox.showwarning("Upload", "Select at least one platform!")
            return

        self.is_running = True
        self.is_uploading = True
        self.upload_start_btn.configure(state="disabled", text="⏳ Uploading...")
        self.upload_status_label.configure(text=self.tr("upload_running"))

        for platform in self.upload_progress:
            self.upload_progress[platform].set(0)
            self.upload_progress_labels[platform].configure(text="0/0")

        self.log(self.tr("upload_started"), "step")
        self.update_status(self.tr("upload_running"), WARNING_ORANGE)

        for platform in selected:
            t = threading.Thread(target=self._upload_worker, args=(platform, self.current_folder), daemon=True)
            t.start()

    def _upload_worker(self, platform: str, folder: Path):
        q = self.log_queue
        try:
            q.put(("log", self.tr("upload_platform_start", platform.upper()), "step"))
            if platform == "shutterstock":
                upload_shutterstock(folder, self.config, progress_queue=q, move_uploaded=True)
            elif platform == "adobe":
                upload_adobe(folder, self.config, progress_queue=q, move_uploaded=True)
            elif platform == "pond5":
                upload_pond5(folder, self.config, progress_queue=q, move_uploaded=True)
            q.put(("log", self.tr("upload_platform_done", platform.upper()), "success"))
        except Exception as e:
            q.put(("log", self.tr("upload_platform_error", platform.upper(), str(e)), "error"))
        finally:
            q.put(("upload_thread_done", platform))


class UploadSettingsWindow(ctk.CTkToplevel):
    """Settings dialog for FTP/SFTP upload credentials — scalable, resizable, ESC to close, clamped to screen."""

    def __init__(self, parent: StockDescriptorGUI, current_config: Dict[str, Any], lang: str = "ru"):
        super().__init__(parent)
        self.parent = parent
        self.lang = lang
        # Load upload config from main config (already decrypted by config_manager)
        self.upload_config = current_config.get("upload_config", {})
        self._password_visible = {}

        self.title(parent.tr("upload_settings_title"))
        self.geometry("720x580")
        self.minsize(620, 480)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Configure>", self._clamp_to_screen)

        self._build_ui()
        self.center()

    def tr(self, key: str, *args) -> str:
        val = LANGUAGES.get(self.lang, LANGUAGES["ru"]).get(key, key)
        if args:
            return val.format(*args)
        return val

    def center(self):
        self.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _clamp_to_screen(self, event=None):
        """Prevent window from moving outside visible screen area (multi-monitor friendly)."""
        try:
            self.update_idletasks()
            x = self.winfo_x()
            y = self.winfo_y()
            w = self.winfo_width()
            h = self.winfo_height()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            new_x = max(0, min(x, sw - w - 20))
            new_y = max(0, min(y, sh - h - 20))
            if new_x != x or new_y != y:
                self.geometry(f"+{new_x}+{new_y}")
        except Exception:
            pass

    def _toggle_password_visible(self, platform: str, entry: ctk.CTkEntry, btn: ctk.CTkButton):
        """Toggle password visibility for a platform's password field."""
        is_visible = self._password_visible.get(platform, False)
        if is_visible:
            entry.configure(show="•")
            btn.configure(text="👁")
            self._password_visible[platform] = False
        else:
            entry.configure(show="")
            btn.configure(text="🙈")
            self._password_visible[platform] = True

    def _build_ui(self):
        # Use grid for full scalability
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        container = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        container.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(container, text=self.tr("upload_settings_header"),
                              font=ctk.CTkFont(size=15, weight="bold"))
        header.pack(pady=(15, 10))

        self.platform_entries = {}
        platforms = ["shutterstock", "adobe", "pond5"]
        platform_labels = {"shutterstock": "Shutterstock", "adobe": "Adobe Stock", "pond5": "Pond5"}

        for platform in platforms:
            frame = ctk.CTkFrame(container, fg_color="#1E293B", corner_radius=10)
            frame.pack(fill="x", padx=20, pady=5, expand=True)
            frame.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(frame, text=platform_labels[platform],
                         font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(8, 4))

            plat_cfg = self.upload_config.get(platform, {})
            entries = {}
            fields = [
                ("upload_host_label", "host", plat_cfg.get("host", "")),
                ("upload_port_label", "port", str(plat_cfg.get("port", 22))),
                ("upload_user_label", "username", plat_cfg.get("username", "")),
                ("upload_pass_label", "password", plat_cfg.get("password", "")),
                ("upload_path_label", "remote_path", plat_cfg.get("remote_path", "/")),
            ]

            for r, (label_key, field_key, default_val) in enumerate(fields, start=1):
                ctk.CTkLabel(frame, text=self.tr(label_key), width=120, anchor="w",
                             font=ctk.CTkFont(size=11)).grid(row=r, column=0, padx=15, pady=4, sticky="w")

                if field_key == "password":
                    pass_frame = ctk.CTkFrame(frame, fg_color="transparent")
                    pass_frame.grid(row=r, column=1, padx=(5, 15), pady=4, sticky="ew")
                    pass_frame.grid_columnconfigure(0, weight=1)

                    entry = ctk.CTkEntry(pass_frame, show="•")
                    entry.insert(0, default_val)
                    entry.grid(row=0, column=0, sticky="ew")
                    entries[field_key] = entry
                    self._password_visible[platform] = False

                    eye_btn = ctk.CTkButton(
                        pass_frame, text="👁", width=32, height=28, corner_radius=6,
                        fg_color="#334155", hover_color="#475569",
                        font=ctk.CTkFont(size=12),
                        command=lambda p=platform, e=entry, b=None: self._toggle_password_visible(p, e, eye_btn)
                    )
                    eye_btn.configure(command=lambda p=platform, e=entry, b=eye_btn: self._toggle_password_visible(p, e, b))
                    eye_btn.grid(row=0, column=1, padx=(4, 0))
                else:
                    entry = ctk.CTkEntry(frame)
                    entry.insert(0, default_val)
                    entry.grid(row=r, column=1, padx=(5, 15), pady=4, sticky="ew")
                    entries[field_key] = entry

            self.platform_entries[platform] = entries

        # Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=15, padx=20)
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        save_btn = ctk.CTkButton(
            btn_frame, text=self.tr("save_btn"),
            fg_color=ACCENT_COLOR, hover_color="#3CB371",
            width=200, height=40, command=self.save_and_close
        )
        save_btn.grid(row=0, column=0, padx=10, sticky="e")

        cancel_btn = ctk.CTkButton(
            btn_frame, text=self.tr("cancel_btn"),
            fg_color="#475569", hover_color="#64748B",
            width=120, height=40, command=self.destroy
        )
        cancel_btn.grid(row=0, column=1, padx=10, sticky="w")

    def save_and_close(self):
        new_upload_cfg = {}
        for platform, entries in self.platform_entries.items():
            new_upload_cfg[platform] = {
                "host": entries["host"].get().strip(),
                "port": int(entries["port"].get().strip() or 22),
                "username": entries["username"].get().strip(),
                "password": entries["password"].get().strip(),
                "remote_path": entries["remote_path"].get().strip() or "/",
            }

        # Save into main config (passwords will be encrypted by config_manager)
        self.parent.config["upload_config"] = new_upload_cfg
        if save_config(self.parent.config):
            messagebox.showinfo(self.tr("msg_save_ok_title"), self.tr("upload_save_ok"))
            self.destroy()
        else:
            messagebox.showerror(self.tr("msg_save_err_title"), self.tr("upload_save_err"))


class SettingsWindow(ctk.CTkToplevel):
    """Beautiful settings dialog — resizable, ESC to close."""

    def __init__(self, parent: StockDescriptorGUI, current_config: Dict[str, Any], on_save_callback, lang: str = "ru"):
        super().__init__(parent)
        self.parent = parent
        self.current_config = current_config.copy()
        self.on_save = on_save_callback
        self.lang = lang

        self.title(parent.tr("settings_title"))
        self.geometry("640x600")
        self.minsize(560, 480)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.bind("<Escape>", lambda e: self.destroy())

        self._build_settings_ui()
        self.center()

    def tr(self, key: str, *args) -> str:
        val = LANGUAGES.get(self.lang, LANGUAGES["ru"]).get(key, key)
        if args:
            return val.format(*args)
        return val

    def center(self):
        self.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _build_settings_ui(self):
        container = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=0, pady=0)
        container.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(container, text=self.tr("settings_header"),
                              font=ctk.CTkFont(size=15, weight="bold"))
        header.pack(pady=(15, 10))

        provider_frame = ctk.CTkFrame(container, fg_color=CARD_BG, corner_radius=12)
        provider_frame.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(provider_frame, text=self.tr("settings_provider"), font=ctk.CTkFont(weight="bold")).pack(side="left", padx=15, pady=12)

        self.provider_var = ctk.StringVar(value=self.current_config.get("provider", "lmstudio"))
        seg = ctk.CTkSegmentedButton(
            provider_frame,
            values=[self.tr("seg_lmstudio"), self.tr("seg_gemini")],
            variable=self.provider_var, command=self._on_provider_change, width=380
        )
        seg.pack(side="right", padx=15, pady=10)

        self.lm_frame = ctk.CTkFrame(container, fg_color="#1E293B", corner_radius=10)
        self.lm_frame.pack(fill="x", padx=20, pady=6)

        ctk.CTkLabel(self.lm_frame, text=self.tr("lm_frame_title"), font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(10, 4))
        ctk.CTkLabel(self.lm_frame, text=self.tr("lm_url_label")).pack(anchor="w", padx=15)
        self.lm_url_entry = ctk.CTkEntry(self.lm_frame)
        self.lm_url_entry.pack(padx=15, pady=4, fill="x")
        self.lm_url_entry.insert(0, self.current_config.get("lmstudio_url", "http://localhost:1234/v1/chat/completions"))

        ctk.CTkLabel(self.lm_frame, text=self.tr("lm_model_label")).pack(anchor="w", padx=15)
        self.lm_model_entry = ctk.CTkEntry(self.lm_frame)
        self.lm_model_entry.pack(padx=15, pady=(4, 12), fill="x")
        self.lm_model_entry.insert(0, self.current_config.get("lmstudio_model", "qwen3.6-35b-a3b"))

        self.gemini_frame = ctk.CTkFrame(container, fg_color="#1E293B", corner_radius=10)
        self.gemini_frame.pack(fill="x", padx=20, pady=6)

        ctk.CTkLabel(self.gemini_frame, text=self.tr("gemini_frame_title"), font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(10, 4))
        ctk.CTkLabel(self.gemini_frame, text=self.tr("gemini_key_label")).pack(anchor="w", padx=15)
        self.gemini_key_entry = ctk.CTkEntry(self.gemini_frame, show="•")
        self.gemini_key_entry.pack(padx=15, pady=4, fill="x")
        if self.current_config.get("gemini_api_key"):
            self.gemini_key_entry.insert(0, self.current_config["gemini_api_key"])

        ctk.CTkLabel(self.gemini_frame, text=self.tr("gemini_model_label")).pack(anchor="w", padx=15)
        self.gemini_model_entry = ctk.CTkEntry(self.gemini_frame)
        self.gemini_model_entry.pack(padx=15, pady=(4, 12), fill="x")
        self.gemini_model_entry.insert(0, self.current_config.get("gemini_model", "gemini-1.5-flash-latest"))

        # ExifTool path
        self.exiftool_frame = ctk.CTkFrame(container, fg_color="#1E293B", corner_radius=10)
        self.exiftool_frame.pack(fill="x", padx=20, pady=6)

        ctk.CTkLabel(self.exiftool_frame, text="ExifTool", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(10, 4))
        ctk.CTkLabel(self.exiftool_frame, text=self.tr("exiftool_label")).pack(anchor="w", padx=15)

        exiftool_row = ctk.CTkFrame(self.exiftool_frame, fg_color="transparent")
        exiftool_row.pack(fill="x", padx=15, pady=(4, 12))
        exiftool_row.grid_columnconfigure(0, weight=1)

        self.exiftool_entry = ctk.CTkEntry(exiftool_row)
        self.exiftool_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.exiftool_entry.insert(0, self.current_config.get("exiftool_path", "D:\\PROGRAMS\\EXIFTOOL\\exiftool.exe"))

        self.exiftool_browse_btn = ctk.CTkButton(
            exiftool_row, text=self.tr("exiftool_browse"),
            width=90, height=32, corner_radius=8,
            fg_color="#475569", hover_color="#64748B", command=self._browse_exiftool
        )
        self.exiftool_browse_btn.grid(row=0, column=1)

        # Common params
        common_frame = ctk.CTkFrame(container, fg_color="transparent")
        common_frame.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(common_frame, text=self.tr("common_params"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 6))

        batch_frame = ctk.CTkFrame(common_frame, fg_color="transparent")
        batch_frame.pack(fill="x")
        ctk.CTkLabel(batch_frame, text=self.tr("batch_label")).pack(side="left", padx=5)
        self.batch_slider = ctk.CTkSlider(batch_frame, from_=1, to=6, number_of_steps=5, width=200,
                                          command=lambda v: self.batch_label_val.configure(text=str(int(v))))
        self.batch_slider.set(self.current_config.get("batch_size", 3))
        self.batch_slider.pack(side="left", padx=10)
        self.batch_label_val = ctk.CTkLabel(batch_frame, text=str(int(self.batch_slider.get())), width=30)
        self.batch_label_val.pack(side="left")

        delay_frame = ctk.CTkFrame(common_frame, fg_color="transparent")
        delay_frame.pack(fill="x", pady=6)
        ctk.CTkLabel(delay_frame, text=self.tr("delay_label")).pack(side="left", padx=5)
        self.delay_slider = ctk.CTkSlider(delay_frame, from_=0, to=10, number_of_steps=10, width=200,
                                          command=lambda v: self.delay_label_val.configure(text=str(int(v))))
        self.delay_slider.set(self.current_config.get("delay", 3))
        self.delay_slider.pack(side="left", padx=10)
        self.delay_label_val = ctk.CTkLabel(delay_frame, text=str(int(self.delay_slider.get())), width=30)
        self.delay_label_val.pack(side="left")

        # Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=15, padx=20)
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        save_btn = ctk.CTkButton(
            btn_frame, text=self.tr("save_btn"),
            fg_color=ACCENT_COLOR, hover_color="#3CB371",
            width=200, height=40, command=self.save_and_close
        )
        save_btn.grid(row=0, column=0, padx=10, sticky="e")

        cancel_btn = ctk.CTkButton(
            btn_frame, text=self.tr("cancel_btn"),
            fg_color="#475569", hover_color="#64748B",
            width=120, height=40, command=self.destroy
        )
        cancel_btn.grid(row=0, column=1, padx=10, sticky="w")

        self._on_provider_change(self.provider_var.get())

        warn = ctk.CTkLabel(
            container, text=self.tr("warn_text"),
            font=ctk.CTkFont(size=10), text_color="#FCA5A5", justify="center"
        )
        warn.pack(pady=(5, 10))

    def _browse_exiftool(self):
        file_path = filedialog.askopenfilename(
            title=self.tr("exiftool_browse"),
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")],
            initialdir=str(Path(self.exiftool_entry.get()).parent) if self.exiftool_entry.get() else str(Path.home())
        )
        if file_path:
            self.exiftool_entry.delete(0, "end")
            self.exiftool_entry.insert(0, file_path)

    def _on_provider_change(self, value: str):
        if "Gemini" in value or "онлайн" in value:
            self.provider_var.set("gemini")
            self.gemini_frame.pack(fill="x", padx=20, pady=6)
            self.lm_frame.pack_forget()
        else:
            self.provider_var.set("lmstudio")
            self.lm_frame.pack(fill="x", padx=20, pady=6)
            self.gemini_frame.pack_forget()

    def save_and_close(self):
        provider = "gemini" if self.provider_var.get() == "gemini" else "lmstudio"
        new_cfg = self.current_config.copy()
        new_cfg["provider"] = provider
        new_cfg["batch_size"] = int(self.batch_slider.get())
        new_cfg["delay"] = int(self.delay_slider.get())
        new_cfg["exiftool_path"] = self.exiftool_entry.get().strip() or "D:\\PROGRAMS\\EXIFTOOL\\exiftool.exe"

        if provider == "lmstudio":
            new_cfg["lmstudio_url"] = self.lm_url_entry.get().strip()
            new_cfg["lmstudio_model"] = self.lm_model_entry.get().strip()
        else:
            key = self.gemini_key_entry.get().strip()
            new_cfg["gemini_api_key"] = key
            new_cfg["gemini_model"] = self.gemini_model_entry.get().strip() or "gemini-1.5-flash-latest"
            if not key:
                messagebox.showwarning(self.tr("msg_empty_key_title"), self.tr("msg_empty_key_text"))

        if save_config(new_cfg):
            self.on_save(new_cfg)
            messagebox.showinfo(self.tr("msg_save_ok_title"), self.tr("msg_save_ok_text"))
            self.destroy()
        else:
            messagebox.showerror(self.tr("msg_save_err_title"), self.tr("msg_save_err_text"))


def main():
    app = StockDescriptorGUI()
    app.mainloop()


if __name__ == "__main__":
    main()