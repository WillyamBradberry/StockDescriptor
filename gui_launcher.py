#!/usr/bin/env python3
"""
StockDescriptor GUI Launcher
Beautiful modern GUI for batch stock photo metadata generation.
Supports LM Studio (local) and Google Gemini (online) with persistent user config.
Multilingual: English / Русский
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

# Add processing to path
ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT / "processing"))

try:
    from config_manager import load_config, save_config
    from batch_metadata import (
        generate_metadata_for_folder,
        generate_preview_file,
        run_write_exif,
        run_nav_script
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you run from project root and venv has dependencies.")
    sys.exit(1)


# ================== MULTILINGUAL STRINGS ==================
LANGUAGES = {
    "en": {
        # Window
        "window_title": "📸 StockDescriptor — AI Metadata for Stock Photos",
        "settings_title": "⚙️ AI Settings — StockDescriptor",
        "settings_header": "Select AI provider and configure connection",
        # Header
        "app_title": "📸 StockDescriptor",
        "app_subtitle": "Batch AI Metadata Generator for Stock Photography",
        "settings_btn": "⚙️  AI Settings",
        # Folder
        "folder_label": "📁  Folder with original photos",
        "folder_placeholder": "Select folder with JPG files...",
        "browse_btn": "Browse...",
        "browse_title": "Select folder with JPG photos for stock",
        # Run button
        "run_btn": "🚀  RUN PIPELINE",
        "run_btn_running": "⏳  RUNNING... (see log)",
        # Provider / Model labels
        "provider_label": "🤖 Provider: {}",
        "model_label": "Model: {}",
        # Log
        "log_label": "📋  Execution Log",
        # Status bar
        "status_ready": "✅ Ready. Select a folder and click «RUN PIPELINE»",
        "status_running": "🚀 Pipeline started...",
        "status_done": "✅ Pipeline complete. Ready for next run.",
        "status_error": "❌ Execution error",
        "status_no_thumbs": "❌ Error: no THMBS folder",
        "hint": "API keys stored locally in ~/.stockdescriptor/config.json",
        # Pipeline steps
        "step_resize": "=== STEP 1/4: Creating thumbnails (resize_for_vision) ===",
        "step_metadata": "\n=== STEP 2/4: AI Metadata Generation ===",
        "step_exif": "\n=== STEP 3/4: Injecting metadata into originals (EXIF) ===",
        "step_nav": "\n=== STEP 4/4: Creating Obsidian navigation ===",
        "pipeline_done": "\n═══════════════════════════════════════════\n🎉 PIPELINE COMPLETED SUCCESSFULLY!",
        # Log messages
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
        # Settings window
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
        # Messages
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
        # Resize
        "resize_warn": "Warning during resize: {}",
        "resize_script_missing": "resize_for_vision.ps1 not found — skipping (ensure THMBS already exists)",
        "resize_no_thumbs": "ERROR: THMBS folder not created. Check JPG files exist.",
        # Language toggle
        "lang_toggle": "EN",
    },
    "ru": {
        # Window
        "window_title": "📸 StockDescriptor — AI Метаданные для Стоковых Фото",
        "settings_title": "⚙️ Настройки нейросети — StockDescriptor",
        "settings_header": "Выберите провайдер AI и настройте подключение",
        # Header
        "app_title": "📸 StockDescriptor",
        "app_subtitle": "Пакетный AI-генератор метаданных для стоковой фотографии",
        "settings_btn": "⚙️  Настройки AI",
        # Folder
        "folder_label": "📁  Папка с оригинальными фотографиями",
        "folder_placeholder": "Выберите папку с JPG файлами...",
        "browse_btn": "Обзор...",
        "browse_title": "Выберите папку с JPG фотографиями для стока",
        # Run button
        "run_btn": "🚀  ЗАПУСТИТЬ ПАЙПЛАЙН",
        "run_btn_running": "⏳  ВЫПОЛНЯЕТСЯ... (см. журнал)",
        # Provider / Model labels
        "provider_label": "🤖 Провайдер: {}",
        "model_label": "Модель: {}",
        # Log
        "log_label": "📋  Журнал выполнения",
        # Status bar
        "status_ready": "✅ Готов к работе. Выберите папку и нажмите «ЗАПУСТИТЬ ПАЙПЛАЙН»",
        "status_running": "🚀 Пайплайн запущен...",
        "status_done": "✅ Пайплайн завершён. Готов к следующему запуску.",
        "status_error": "❌ Ошибка выполнения",
        "status_no_thumbs": "❌ Ошибка: нет THMBS",
        "hint": "API ключи хранятся локально в ~/.stockdescriptor/config.json",
        # Pipeline steps
        "step_resize": "=== ШАГ 1/4: Создание миниатюр (resize_for_vision) ===",
        "step_metadata": "\n=== ШАГ 2/4: Генерация метаданных через AI ===",
        "step_exif": "\n=== ШАГ 3/4: Инжекция метаданных в оригиналы (EXIF) ===",
        "step_nav": "\n=== ШАГ 4/4: Создание навигации для Obsidian ===",
        "pipeline_done": "\n═══════════════════════════════════════════\n🎉 ПАЙПЛАЙН ЗАВЕРШЁН УСПЕШНО!",
        # Log messages
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
        # Settings window
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
        # Messages
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
        # Resize
        "resize_warn": "Предупреждение при resize: {}",
        "resize_script_missing": "resize_for_vision.ps1 не найден — пропускаем (убедитесь что THMBS уже есть)",
        "resize_no_thumbs": "ОШИБКА: Папка THMBS не создана. Проверьте наличие JPG файлов.",
        # Language toggle
        "lang_toggle": "RU",
    }
}


# ================== GUI APPEARANCE ==================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")  # nice blue theme for professional look

# Colors
ACCENT_COLOR = "#2E8B57"      # sea green for stock/marine vibe
DARK_BG = "#1E1E2E"
CARD_BG = "#25253A"
SUCCESS_GREEN = "#4ADE80"
WARNING_ORANGE = "#FBBF24"
ERROR_RED = "#F87171"


class StockDescriptorGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Load user config
        self.config: Dict[str, Any] = load_config()
        self.current_folder: Optional[Path] = None
        if self.config.get("last_folder"):
            self.current_folder = Path(self.config["last_folder"])

        # Language
        self.lang: str = self.config.get("language", "ru")
        if self.lang not in ("en", "ru"):
            self.lang = "ru"

        # Queue for thread <-> GUI communication
        self.log_queue: queue.Queue = queue.Queue()
        self.worker_thread: Optional[threading.Thread] = None
        self.is_running = False

        self._build_ui()
        self._load_last_folder()
        self._poll_log_queue()  # start polling

        # Center window
        self.center_window()

    # ================== TRANSLATION ==================
    def tr(self, key: str, *args) -> str:
        """Get translated string for current language."""
        val = LANGUAGES.get(self.lang, LANGUAGES["ru"]).get(key, key)
        if args:
            return val.format(*args)
        return val

    def _toggle_language(self):
        """Switch between EN and RU and update all UI text."""
        self.lang = "en" if self.lang == "ru" else "ru"
        self.config["language"] = self.lang
        save_config(self.config)
        self._refresh_ui_text()
        self.log(self.tr("log_settings_saved"), "success")

    def _refresh_ui_text(self):
        """Update all visible UI text after language switch."""
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

    def center_window(self):
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        # Responsive size: 75% of screen width, 80% of screen height, capped
        w = min(900, int(screen_w * 0.75))
        h = min(750, int(screen_h * 0.8))
        # Center with margins (top margin at least 30px)
        x = max(20, (screen_w - w) // 2)
        y = max(30, (screen_h - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        # Top header
        header_frame = ctk.CTkFrame(self, height=70, corner_radius=0, fg_color=DARK_BG)
        header_frame.pack(fill="x", padx=0, pady=0)

        self.title_label = ctk.CTkLabel(
            header_frame,
            text=self.tr("app_title"),
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#E0E7FF"
        )
        self.title_label.pack(side="left", padx=25, pady=15)

        self.subtitle_label = ctk.CTkLabel(
            header_frame,
            text=self.tr("app_subtitle"),
            font=ctk.CTkFont(size=13),
            text_color="#94A3B8"
        )
        self.subtitle_label.pack(side="left", padx=10, pady=20)

        # Language toggle button
        self.lang_btn = ctk.CTkButton(
            header_frame,
            text=self.tr("lang_toggle"),
            width=50,
            height=36,
            corner_radius=8,
            fg_color="#334155",
            hover_color="#475569",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._toggle_language
        )
        self.lang_btn.pack(side="right", padx=(0, 10), pady=17)

        # Settings button top right
        self.settings_btn = ctk.CTkButton(
            header_frame,
            text=self.tr("settings_btn"),
            width=160,
            height=36,
            corner_radius=8,
            fg_color="#334155",
            hover_color="#475569",
            command=self.open_settings_window
        )
        self.settings_btn.pack(side="right", padx=(0, 5), pady=17)

        # Main content card
        main_card = ctk.CTkFrame(self, corner_radius=16, fg_color=CARD_BG)
        main_card.pack(fill="both", expand=True, padx=20, pady=(10, 15))

        # === Folder selection section ===
        self.folder_label = ctk.CTkLabel(
            main_card,
            text=self.tr("folder_label"),
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        self.folder_label.pack(fill="x", padx=25, pady=(20, 8))

        folder_frame = ctk.CTkFrame(main_card, fg_color="transparent")
        folder_frame.pack(fill="x", padx=25, pady=(0, 15))

        self.folder_entry = ctk.CTkEntry(
            folder_frame,
            placeholder_text=self.tr("folder_placeholder"),
            width=520,
            height=42,
            corner_radius=10,
            font=ctk.CTkFont(size=13)
        )
        self.folder_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)

        self.browse_btn = ctk.CTkButton(
            folder_frame,
            text=self.tr("browse_btn"),
            width=110,
            height=42,
            corner_radius=10,
            fg_color="#475569",
            hover_color="#64748B",
            command=self.browse_folder
        )
        self.browse_btn.pack(side="right")

        # === Action buttons ===
        action_frame = ctk.CTkFrame(main_card, fg_color="transparent")
        action_frame.pack(fill="x", padx=25, pady=(5, 15))

        self.run_btn = ctk.CTkButton(
            action_frame,
            text=self.tr("run_btn"),
            height=52,
            corner_radius=12,
            font=ctk.CTkFont(size=17, weight="bold"),
            fg_color=ACCENT_COLOR,
            hover_color="#3CB371",
            command=self.start_pipeline
        )
        self.run_btn.pack(fill="x", pady=(5, 0))

        # Quick info row
        info_row = ctk.CTkFrame(main_card, fg_color="transparent")
        info_row.pack(fill="x", padx=25, pady=(8, 5))

        self.provider_label = ctk.CTkLabel(
            info_row,
            text=self.tr("provider_label", self.config.get("provider", "lmstudio").upper()),
            font=ctk.CTkFont(size=12),
            text_color="#CBD5E1"
        )
        self.provider_label.pack(side="left")

        self.model_label = ctk.CTkLabel(
            info_row,
            text=self.tr("model_label", self._get_current_model()),
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8"
        )
        self.model_label.pack(side="left", padx=20)

        # === Log / Status console ===
        self.log_label = ctk.CTkLabel(
            main_card,
            text=self.tr("log_label"),
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        self.log_label.pack(fill="x", padx=25, pady=(15, 6))

        self.log_text = ctk.CTkTextbox(
            main_card,
            height=220,
            corner_radius=10,
            fg_color="#1A1A2E",
            border_color="#334155",
            border_width=1,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        # Status bar at bottom
        status_frame = ctk.CTkFrame(self, height=32, corner_radius=0, fg_color="#0F172A")
        status_frame.pack(fill="x", side="bottom")

        self.status_label = ctk.CTkLabel(
            status_frame,
            text=self.tr("status_ready"),
            font=ctk.CTkFont(size=12),
            text_color="#64748B"
        )
        self.status_label.pack(side="left", padx=20, pady=6)

        # Footer hint
        self.hint_label = ctk.CTkLabel(
            status_frame,
            text=self.tr("hint"),
            font=ctk.CTkFont(size=10),
            text_color="#475569"
        )
        self.hint_label.pack(side="right", padx=20)

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
        """Append message to log textbox (thread-safe via queue or direct if main thread).
        Also prints to console for CLI visibility."""
        timestamp = time.strftime("%H:%M:%S")
        prefix = {
            "info": "•",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "step": "➤"
        }.get(level, "•")

        formatted = f"[{timestamp}] {prefix} {message}\n"

        # Console output
        print(formatted, end="", flush=True)

        # GUI output
        try:
            self.log_text.insert("end", formatted)
            self.log_text.see("end")
        except Exception:
            pass  # during init or shutdown

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
        """Called from settings window after successful save."""
        self.config = new_config
        # Update labels
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

        # Confirm if Gemini and no key
        if self.config.get("provider") == "gemini" and not self.config.get("gemini_api_key"):
            if not messagebox.askyesno(
                self.tr("msg_no_key_title"),
                self.tr("msg_no_key_text")
            ):
                return
            self.open_settings_window()
            return

        # Start
        self.is_running = True
        self.run_btn.configure(state="disabled", text=self.tr("run_btn_running"))
        self.log_text.delete("1.0", "end")
        self.update_status(self.tr("status_running"), SUCCESS_GREEN)

        self.log("═══════════════════════════════════════════", "step")
        self.log(f"Pipeline for: {folder}", "step")
        self.log(f"Provider: {self.config.get('provider', 'lmstudio').upper()}", "info")

        # Run in background thread
        self.worker_thread = threading.Thread(
            target=self._pipeline_worker,
            args=(folder,),
            daemon=True
        )
        self.worker_thread.start()

    def _pipeline_worker(self, folder: Path):
        """Heavy work in background thread. Puts messages into self.log_queue."""
        q = self.log_queue

        def put(msg, level="info"):
            q.put(("log", msg, level))

        def set_status(msg, color="#64748B"):
            q.put(("status", msg, color))

        try:
            put(self.tr("step_resize"), "step")
            set_status("🔄 Creating thumbnails...", WARNING_ORANGE)

            # Run resize PowerShell
            resize_script = ROOT / "processing" / "resize_for_vision.ps1"
            if resize_script.exists():
                cmd = [
                    "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", str(resize_script),
                    "-ImageFolder", str(folder)
                ]
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

            # Metadata generation
            put(self.tr("step_metadata"), "step")
            set_status("🤖 Generating Title/Description/Keywords...", "#60A5FA")

            metadata_file, error_file = generate_metadata_for_folder(
                folder,
                thumbs_folder,
                batch_size=self.config.get("batch_size", 3),
                delay=self.config.get("delay", 3),
                mock=False,
                check_errs=False,
                llm_config=self.config
            )

            if metadata_file and metadata_file.exists():
                put(self.tr("log_metadata_ok", str(metadata_file)), "success")
            else:
                put(self.tr("log_metadata_warn"), "warning")

            # Preview
            try:
                generate_preview_file(folder, metadata_file, thumbs_folder)
                put(self.tr("log_preview_ok"), "info")
            except Exception as e:
                put(self.tr("log_preview_err", str(e)), "warning")

            has_errors = error_file is not None and error_file.exists()

            # EXIF
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

            # Navigation
            put(self.tr("step_nav"), "step")
            set_status("🗂️ Generating METADATA-NAV.md...", "#A78BFA")

            nav_success = run_nav_script(folder, metadata_file, ROOT / "processing", ask=False)
            if nav_success:
                put(self.tr("log_nav_ok"), "success")

            # Final
            put(self.tr("pipeline_done"), "success")
            set_status(self.tr("status_done"), SUCCESS_GREEN)

            # Update last folder
            self.config["last_folder"] = str(folder)
            save_config(self.config)

        except Exception as e:
            put(self.tr("log_critical", str(e)), "error")
            set_status(self.tr("status_error"), ERROR_RED)
        finally:
            q.put(("done",))

    def _poll_log_queue(self):
        """Poll queue every 120ms and update GUI from worker thread."""
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
        except queue.Empty:
            pass

        # Schedule next poll
        self.after(120, self._poll_log_queue)


class SettingsWindow(ctk.CTkToplevel):
    """Beautiful settings dialog for choosing provider and entering API keys."""

    def __init__(self, parent: StockDescriptorGUI, current_config: Dict[str, Any], on_save_callback, lang: str = "ru"):
        super().__init__(parent)
        self.parent = parent
        self.current_config = current_config.copy()
        self.on_save = on_save_callback
        self.lang = lang

        self.title(parent.tr("settings_title"))
        self.geometry("620x580")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

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
        # Header
        header = ctk.CTkLabel(self, text=self.tr("settings_header"),
                              font=ctk.CTkFont(size=15, weight="bold"))
        header.pack(pady=(15, 10))

        # Provider selector
        provider_frame = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12)
        provider_frame.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(provider_frame, text=self.tr("settings_provider"), font=ctk.CTkFont(weight="bold")).pack(side="left", padx=15, pady=12)

        self.provider_var = ctk.StringVar(value=self.current_config.get("provider", "lmstudio"))
        seg = ctk.CTkSegmentedButton(
            provider_frame,
            values=[self.tr("seg_lmstudio"), self.tr("seg_gemini")],
            variable=self.provider_var,
            command=self._on_provider_change,
            width=380
        )
        seg.pack(side="right", padx=15, pady=10)

        # === LM Studio frame ===
        self.lm_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        self.lm_frame.pack(fill="x", padx=20, pady=6)

        ctk.CTkLabel(self.lm_frame, text=self.tr("lm_frame_title"), font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(10, 4))

        ctk.CTkLabel(self.lm_frame, text=self.tr("lm_url_label")).pack(anchor="w", padx=15)
        self.lm_url_entry = ctk.CTkEntry(self.lm_frame, width=560)
        self.lm_url_entry.pack(padx=15, pady=4)
        self.lm_url_entry.insert(0, self.current_config.get("lmstudio_url", "http://localhost:1234/v1/chat/completions"))

        ctk.CTkLabel(self.lm_frame, text=self.tr("lm_model_label")).pack(anchor="w", padx=15)
        self.lm_model_entry = ctk.CTkEntry(self.lm_frame, width=560)
        self.lm_model_entry.pack(padx=15, pady=(4, 12))
        self.lm_model_entry.insert(0, self.current_config.get("lmstudio_model", "qwen3.6-35b-a3b"))

        # === Gemini frame ===
        self.gemini_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        self.gemini_frame.pack(fill="x", padx=20, pady=6)

        ctk.CTkLabel(self.gemini_frame, text=self.tr("gemini_frame_title"), font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(10, 4))

        ctk.CTkLabel(self.gemini_frame, text=self.tr("gemini_key_label")).pack(anchor="w", padx=15)
        self.gemini_key_entry = ctk.CTkEntry(self.gemini_frame, width=560, show="•")
        self.gemini_key_entry.pack(padx=15, pady=4)
        if self.current_config.get("gemini_api_key"):
            self.gemini_key_entry.insert(0, self.current_config["gemini_api_key"])

        ctk.CTkLabel(self.gemini_frame, text=self.tr("gemini_model_label")).pack(anchor="w", padx=15)
        self.gemini_model_entry = ctk.CTkEntry(self.gemini_frame, width=560)
        self.gemini_model_entry.pack(padx=15, pady=(4, 12))
        self.gemini_model_entry.insert(0, self.current_config.get("gemini_model", "gemini-1.5-flash-latest"))

        # === ExifTool path frame ===
        self.exiftool_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        self.exiftool_frame.pack(fill="x", padx=20, pady=6)

        ctk.CTkLabel(self.exiftool_frame, text="ExifTool", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(10, 4))

        ctk.CTkLabel(self.exiftool_frame, text=self.tr("exiftool_label")).pack(anchor="w", padx=15)

        exiftool_row = ctk.CTkFrame(self.exiftool_frame, fg_color="transparent")
        exiftool_row.pack(fill="x", padx=15, pady=(4, 12))

        self.exiftool_entry = ctk.CTkEntry(exiftool_row, width=460)
        self.exiftool_entry.pack(side="left", padx=(0, 8), fill="x", expand=True)
        self.exiftool_entry.insert(0, self.current_config.get("exiftool_path", "D:\\PROGRAMS\\EXIFTOOL\\exiftool.exe"))

        self.exiftool_browse_btn = ctk.CTkButton(
            exiftool_row,
            text=self.tr("exiftool_browse"),
            width=90,
            height=32,
            corner_radius=8,
            fg_color="#475569",
            hover_color="#64748B",
            command=self._browse_exiftool
        )
        self.exiftool_browse_btn.pack(side="right")

        # Common params
        common_frame = ctk.CTkFrame(self, fg_color="transparent")
        common_frame.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(common_frame, text=self.tr("common_params"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 6))

        # Batch size
        batch_frame = ctk.CTkFrame(common_frame, fg_color="transparent")
        batch_frame.pack(fill="x")
        ctk.CTkLabel(batch_frame, text=self.tr("batch_label")).pack(side="left", padx=5)
        self.batch_slider = ctk.CTkSlider(batch_frame, from_=1, to=6, number_of_steps=5, width=200,
                                          command=lambda v: self.batch_label.configure(text=str(int(v))))
        self.batch_slider.set(self.current_config.get("batch_size", 3))
        self.batch_slider.pack(side="left", padx=10)
        self.batch_label = ctk.CTkLabel(batch_frame, text=str(int(self.batch_slider.get())), width=30)
        self.batch_label.pack(side="left")

        # Delay
        delay_frame = ctk.CTkFrame(common_frame, fg_color="transparent")
        delay_frame.pack(fill="x", pady=6)
        ctk.CTkLabel(delay_frame, text=self.tr("delay_label")).pack(side="left", padx=5)
        self.delay_slider = ctk.CTkSlider(delay_frame, from_=0, to=10, number_of_steps=10, width=200,
                                          command=lambda v: self.delay_label.configure(text=str(int(v))))
        self.delay_slider.set(self.current_config.get("delay", 3))
        self.delay_slider.pack(side="left", padx=10)
        self.delay_label = ctk.CTkLabel(delay_frame, text=str(int(self.delay_slider.get())), width=30)
        self.delay_label.pack(side="left")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", pady=15, padx=20)

        save_btn = ctk.CTkButton(
            btn_frame, text=self.tr("save_btn"),
            fg_color=ACCENT_COLOR, hover_color="#3CB371",
            width=200, height=40, command=self.save_and_close
        )
        save_btn.pack(side="left", padx=10)

        cancel_btn = ctk.CTkButton(
            btn_frame, text=self.tr("cancel_btn"),
            fg_color="#475569", hover_color="#64748B",
            width=120, height=40, command=self.destroy
        )
        cancel_btn.pack(side="right", padx=10)

        # Initial state
        self._on_provider_change(self.provider_var.get())

        # Warning label
        warn = ctk.CTkLabel(
            self,
            text=self.tr("warn_text"),
            font=ctk.CTkFont(size=10),
            text_color="#FCA5A5",
            justify="center"
        )
        warn.pack(pady=(5, 10))

    def _browse_exiftool(self):
        """Open file dialog to select exiftool.exe."""
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
                messagebox.showwarning(
                    self.tr("msg_empty_key_title"),
                    self.tr("msg_empty_key_text")
                )

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