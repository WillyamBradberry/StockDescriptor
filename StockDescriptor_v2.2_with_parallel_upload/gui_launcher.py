#!/usr/bin/env python3
"""
StockDescriptor GUI Launcher
Beautiful modern GUI for batch stock photo metadata generation.
Supports LM Studio (local) and Google Gemini (online) with persistent user config.
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
sys.path.insert(0, str(ROOT / "scripts"))

try:
    from _config_manager import load_config, save_config
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
        load_config as load_upload_config
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you run from project root and venv has dependencies (including paramiko).")
    sys.exit(1)


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

        self.title("📸 StockDescriptor — AI Metadata for Stock Photos")
        self.geometry("820x680")
        self.minsize(780, 620)
        self.resizable(True, True)

        # Load user config
        self.config: Dict[str, Any] = load_config()
        self.current_folder: Optional[Path] = None
        if self.config.get("last_folder"):
            self.current_folder = Path(self.config["last_folder"])

        # Queue for thread <-> GUI communication
        self.log_queue: queue.Queue = queue.Queue()
        self.worker_thread: Optional[threading.Thread] = None
        self.is_running = False

        self._build_ui()
        self._load_last_folder()
        self._poll_log_queue()  # start polling

        # Center window
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        # Top header
        header_frame = ctk.CTkFrame(self, height=70, corner_radius=0, fg_color=DARK_BG)
        header_frame.pack(fill="x", padx=0, pady=0)

        title_label = ctk.CTkLabel(
            header_frame,
            text="📸 StockDescriptor",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#E0E7FF"
        )
        title_label.pack(side="left", padx=25, pady=15)

        subtitle = ctk.CTkLabel(
            header_frame,
            text="Batch AI Metadata Generator for Stock Photography",
            font=ctk.CTkFont(size=13),
            text_color="#94A3B8"
        )
        subtitle.pack(side="left", padx=10, pady=20)

        # Settings button top right
        settings_btn = ctk.CTkButton(
            header_frame,
            text="⚙️  Настройки AI",
            width=160,
            height=36,
            corner_radius=8,
            fg_color="#334155",
            hover_color="#475569",
            command=self.open_settings_window
        )
        settings_btn.pack(side="right", padx=25, pady=17)

        # Upload button
        upload_btn = ctk.CTkButton(
            header_frame,
            text="📤 Upload to Stocks",
            width=170,
            height=36,
            corner_radius=8,
            fg_color="#475569",
            hover_color="#64748B",
            command=self.start_parallel_upload
        )
        upload_btn.pack(side="right", padx=10, pady=17)

        # Main content card
        main_card = ctk.CTkFrame(self, corner_radius=16, fg_color=CARD_BG)
        main_card.pack(fill="both", expand=True, padx=20, pady=(10, 15))

        # === Folder selection section ===
        folder_label = ctk.CTkLabel(
            main_card,
            text="📁  Папка с оригинальными фотографиями",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        folder_label.pack(fill="x", padx=25, pady=(20, 8))

        folder_frame = ctk.CTkFrame(main_card, fg_color="transparent")
        folder_frame.pack(fill="x", padx=25, pady=(0, 15))

        self.folder_entry = ctk.CTkEntry(
            folder_frame,
            placeholder_text="Выберите папку с JPG файлами...",
            width=520,
            height=42,
            corner_radius=10,
            font=ctk.CTkFont(size=13)
        )
        self.folder_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)

        browse_btn = ctk.CTkButton(
            folder_frame,
            text="Обзор...",
            width=110,
            height=42,
            corner_radius=10,
            fg_color="#475569",
            hover_color="#64748B",
            command=self.browse_folder
        )
        browse_btn.pack(side="right")

        # === Action buttons ===
        action_frame = ctk.CTkFrame(main_card, fg_color="transparent")
        action_frame.pack(fill="x", padx=25, pady=(5, 15))

        self.run_btn = ctk.CTkButton(
            action_frame,
            text="🚀  ЗАПУСТИТЬ ПАЙПЛАЙН",
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
            text=f"🤖 Провайдер: {self.config.get('provider', 'lmstudio').upper()}",
            font=ctk.CTkFont(size=12),
            text_color="#CBD5E1"
        )
        self.provider_label.pack(side="left")

        self.model_label = ctk.CTkLabel(
            info_row,
            text=f"Модель: {self._get_current_model()}",
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8"
        )
        self.model_label.pack(side="left", padx=20)

        # === Log / Status console ===
        log_label = ctk.CTkLabel(
            main_card,
            text="📋  Журнал выполнения",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        log_label.pack(fill="x", padx=25, pady=(15, 6))

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
            text="✅ Готов к работе. Выберите папку и нажмите «ЗАПУСТИТЬ ПАЙПЛАЙН»",
            font=ctk.CTkFont(size=12),
            text_color="#64748B"
        )
        self.status_label.pack(side="left", padx=20, pady=6)

        # Footer hint
        hint = ctk.CTkLabel(
            status_frame,
            text="API ключи хранятся локально в ~/.stockdescriptor/config.json",
            font=ctk.CTkFont(size=10),
            text_color="#475569"
        )
        hint.pack(side="right", padx=20)

    def _get_current_model(self) -> str:
        if self.config.get("provider") == "gemini":
            return self.config.get("gemini_model", "gemini-1.5-flash-latest")
        return self.config.get("lmstudio_model", "qwen3.6-35b-a3b")

    def _load_last_folder(self):
        if self.current_folder and self.current_folder.exists():
            self.folder_entry.insert(0, str(self.current_folder))
            self.log("📂 Загружена последняя папка из конфига.")
        else:
            self.log("👋 Добро пожаловать! Выберите папку с фотографиями.")

    def log(self, message: str, level: str = "info"):
        """Append message to log textbox (thread-safe via queue or direct if main thread)."""
        timestamp = time.strftime("%H:%M:%S")
        prefix = {
            "info": "•",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "step": "➤"
        }.get(level, "•")

        formatted = f"[{timestamp}] {prefix} {message}\n"
        try:
            self.log_text.insert("end", formatted)
            self.log_text.see("end")
        except Exception:
            pass  # during init or shutdown

    def update_status(self, text: str, color: str = "#64748B"):
        self.status_label.configure(text=text, text_color=color)

    def browse_folder(self):
        folder = filedialog.askdirectory(
            title="Выберите папку с JPG фотографиями для стока",
            initialdir=str(self.current_folder) if self.current_folder else str(Path.home())
        )
        if folder:
            self.current_folder = Path(folder)
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            self.config["last_folder"] = folder
            save_config(self.config)
            self.log(f"📁 Выбрана папка: {folder}", "success")

    def open_settings_window(self):
        SettingsWindow(self, self.config, self.on_settings_saved)

    def on_settings_saved(self, new_config: Dict[str, Any]):
        """Called from settings window after successful save."""
        self.config = new_config
        # Update labels
        self.provider_label.configure(text=f"🤖 Провайдер: {self.config.get('provider', 'lmstudio').upper()}")
        self.model_label.configure(text=f"Модель: {self._get_current_model()}")
        self.log("⚙️ Настройки сохранены. API ключи записаны в пользовательский файл.", "success")

    def start_pipeline(self):
        if self.is_running:
            messagebox.showwarning("В процессе", "Пайплайн уже выполняется. Дождитесь завершения.")
            return

        folder_str = self.folder_entry.get().strip()
        if not folder_str:
            messagebox.showerror("Ошибка", "Сначала выберите папку с фотографиями!")
            return

        folder = Path(folder_str)
        if not folder.exists():
            messagebox.showerror("Ошибка", f"Папка не найдена:\n{folder}")
            return

        # Confirm if Gemini and no key
        if self.config.get("provider") == "gemini" and not self.config.get("gemini_api_key"):
            if not messagebox.askyesno(
                "Нет ключа Gemini",
                "Для Gemini не указан API ключ.\n\n"
                "Хотите открыть настройки сейчас?"
            ):
                return
            self.open_settings_window()
            return

        # Start
        self.is_running = True
        self.run_btn.configure(state="disabled", text="⏳  ВЫПОЛНЯЕТСЯ... (см. журнал)")
        self.log_text.delete("1.0", "end")
        self.update_status("🚀 Пайплайн запущен...", SUCCESS_GREEN)

        self.log("═══════════════════════════════════════════", "step")
        self.log(f"Запуск полного пайплайна для: {folder}", "step")
        self.log(f"Провайдер: {self.config.get('provider', 'lmstudio').upper()}", "info")

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
            put("=== ШАГ 1/4: Создание миниатюр (resize_for_vision) ===", "step")
            set_status("🔄 Создание миниатюр...", WARNING_ORANGE)

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
                    put(f"Предупреждение при resize: {result.stderr[-300:] if result.stderr else 'код ' + str(result.returncode)}", "warning")
                else:
                    put("Миниатюры успешно созданы в папке THMBS/", "success")
            else:
                put("resize_for_vision.ps1 не найден — пропускаем (убедитесь что THMBS уже есть)", "warning")

            thumbs_folder = folder / "THMBS"
            if not thumbs_folder.exists():
                put("ОШИБКА: Папка THMBS не создана. Проверьте наличие JPG файлов.", "error")
                set_status("❌ Ошибка: нет THMBS", ERROR_RED)
                return

            # Metadata generation
            put("\n=== ШАГ 2/4: Генерация метаданных через AI ===", "step")
            set_status("🤖 Генерация Title/Description/Keywords...", "#60A5FA")

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
                put(f"METADATA.md создан: {metadata_file}", "success")
            else:
                put("Генерация метаданных завершилась с проблемами.", "warning")

            # Preview
            try:
                generate_preview_file(folder, metadata_file, thumbs_folder)
                put("METADATA_PREVIEW.md создан для быстрого просмотра.", "info")
            except Exception as e:
                put(f"Не удалось создать превью: {e}", "warning")

            has_errors = error_file is not None and error_file.exists()

            # EXIF
            if not has_errors:
                put("\n=== ШАГ 3/4: Инжекция метаданных в оригиналы (EXIF) ===", "step")
                set_status("🏷️ Запись EXIF в JPG...", "#FBBF24")

                exif_script = folder / "write_exif.ps1"
                if not exif_script.exists():
                    exif_script = ROOT / "processing" / "write_exif.ps1"

                if exif_script.exists():
                    success = run_write_exif(folder, exif_script)
                    if success:
                        put("EXIF метаданные успешно записаны в оригинальные файлы.", "success")
                    else:
                        put("Ошибка при выполнении write_exif.ps1", "error")
                else:
                    put("write_exif.ps1 не найден — пропускаем инжекцию EXIF.", "warning")
            else:
                put("\n⚠️ Пропущена инжекция EXIF из-за ошибок в metadata_error.md", "warning")
                put("Исправьте ошибки и запустите с --check-errs или через GUI заново.", "info")

            # Navigation
            put("\n=== ШАГ 4/4: Создание навигации для Obsidian ===", "step")
            set_status("🗂️ Генерация METADATA-NAV.md...", "#A78BFA")

            nav_success = run_nav_script(folder, metadata_file, ROOT / "processing", ask=False)
            if nav_success:
                put("METADATA-NAV.md успешно создан для Obsidian.", "success")

            # Final
            put("\n═══════════════════════════════════════════", "success")
            put("🎉 ПАЙПЛАЙН ЗАВЕРШЁН УСПЕШНО!", "success")
            set_status("✅ Готово! Проверьте METADATA.md и METADATA-NAV.md", SUCCESS_GREEN)

            # Update last folder
            self.config["last_folder"] = str(folder)
            save_config(self.config)

        except Exception as e:
            put(f"КРИТИЧЕСКАЯ ОШИБКА: {str(e)}", "error")
            set_status("❌ Ошибка выполнения", ERROR_RED)
        finally:
            q.put(("done",))

    def _poll_log_queue(self):
        """Poll queue every 120ms and update GUI from worker thread."""
        try:
            while True:
                item = self.log_queue.get_nowait()
                if item[0] == "log":
                    if len(item) == 3:
                        _, msg, level = item
                        self.log(msg, level)
                    elif len(item) >= 3 and item[1] in ["shutterstock", "adobe", "pond5"]:
                        # Upload progress/log from stock uploader
                        msg_type, platform, *rest = item
                        if msg_type == "log":
                            self.log(f"[{platform.upper()}] {rest[0]}", "info")
                        elif msg_type == "progress":
                            current, total, filename = rest
                            self.log(f"[{platform.upper()}] {current}/{total} — {filename}", "info")
                elif item[0] == "status":
                    _, text, color = item
                    self.update_status(text, color)
                elif item[0] == "done":
                    self.is_running = False
                    self.run_btn.configure(state="normal", text="🚀  ЗАПУСТИТЬ ПАЙПЛАЙН")
                    self.update_status("✅ Пайплайн завершён. Готов к следующему запуску.", SUCCESS_GREEN)
        except queue.Empty:
            pass

        # Schedule next poll
        self.after(120, self._poll_log_queue)

    def start_parallel_upload(self):
        """Start parallel uploads to all stock platforms using threads."""
        if self.is_running:
            messagebox.showwarning("В процессе", "Другая операция уже выполняется.")
            return

        if not self.current_folder or not self.current_folder.exists():
            folder = filedialog.askdirectory(title="Выберите папку с JPG для загрузки на стоки")
            if not folder:
                return
            self.current_folder = Path(folder)

        self.is_running = True
        self.log("📤 Запуск параллельной загрузки на стоки...", "step")
        self.update_status("📤 Параллельная загрузка на стоки...", WARNING_ORANGE)

        # Start one thread per platform
        platforms = ["shutterstock", "adobe", "pond5"]
        threads = []

        for platform in platforms:
            t = threading.Thread(
                target=self._upload_worker,
                args=(platform, self.current_folder),
                daemon=True
            )
            threads.append(t)
            t.start()

        # Note: We don't wait for all here; polling will handle updates
        self.log("Запущены потоки для всех платформ. Следите за логом.", "info")

    def _upload_worker(self, platform: str, folder: Path):
        """Worker thread for one platform. Reports via log_queue."""
        try:
            self.log_queue.put(("log", f"▶️ Начинаем загрузку на {platform.upper()}...", "step"))

            # Call the appropriate upload function with queue for progress
            if platform == "shutterstock":
                upload_shutterstock(folder, self.config, progress_queue=self.log_queue, move_uploaded=True)
            elif platform == "adobe":
                upload_adobe(folder, self.config, progress_queue=self.log_queue, move_uploaded=True)
            elif platform == "pond5":
                upload_pond5(folder, self.config, progress_queue=self.log_queue, move_uploaded=True)

            self.log_queue.put(("log", f"✅ {platform.upper()} завершён.", "success"))
        except Exception as e:
            self.log_queue.put(("log", f"❌ Ошибка на {platform}: {e}", "error"))
        finally:
            # Signal completion (GUI can check if all done)
            pass


class SettingsWindow(ctk.CTkToplevel):
    """Beautiful settings dialog for choosing provider and entering API keys."""

    def __init__(self, parent: StockDescriptorGUI, current_config: Dict[str, Any], on_save_callback):
        super().__init__(parent)
        self.parent = parent
        self.current_config = current_config.copy()
        self.on_save = on_save_callback

        self.title("⚙️ Настройки нейросети — StockDescriptor")
        self.geometry("620x520")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_settings_ui()
        self.center()

    def center(self):
        self.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _build_settings_ui(self):
        # Header
        header = ctk.CTkLabel(self, text="Выберите провайдер AI и настройте подключение", 
                              font=ctk.CTkFont(size=15, weight="bold"))
        header.pack(pady=(15, 10))

        # Provider selector
        provider_frame = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12)
        provider_frame.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(provider_frame, text="Провайдер:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=15, pady=12)

        self.provider_var = ctk.StringVar(value=self.current_config.get("provider", "lmstudio"))
        seg = ctk.CTkSegmentedButton(
            provider_frame,
            values=["LM Studio (локально)", "Google Gemini (онлайн)"],
            variable=self.provider_var,
            command=self._on_provider_change,
            width=380
        )
        seg.pack(side="right", padx=15, pady=10)

        # === LM Studio frame ===
        self.lm_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        self.lm_frame.pack(fill="x", padx=20, pady=6)

        ctk.CTkLabel(self.lm_frame, text="LM Studio (OpenAI-compatible)", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(10, 4))

        ctk.CTkLabel(self.lm_frame, text="URL эндпоинта:").pack(anchor="w", padx=15)
        self.lm_url_entry = ctk.CTkEntry(self.lm_frame, width=560)
        self.lm_url_entry.pack(padx=15, pady=4)
        self.lm_url_entry.insert(0, self.current_config.get("lmstudio_url", "http://localhost:1234/v1/chat/completions"))

        ctk.CTkLabel(self.lm_frame, text="Название модели:").pack(anchor="w", padx=15)
        self.lm_model_entry = ctk.CTkEntry(self.lm_frame, width=560)
        self.lm_model_entry.pack(padx=15, pady=(4, 12))
        self.lm_model_entry.insert(0, self.current_config.get("lmstudio_model", "qwen3.6-35b-a3b"))

        # === Gemini frame ===
        self.gemini_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10)
        self.gemini_frame.pack(fill="x", padx=20, pady=6)

        ctk.CTkLabel(self.gemini_frame, text="Google Gemini Vision", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(10, 4))

        ctk.CTkLabel(self.gemini_frame, text="API Key (сохраняется локально):").pack(anchor="w", padx=15)
        self.gemini_key_entry = ctk.CTkEntry(self.gemini_frame, width=560, show="•")
        self.gemini_key_entry.pack(padx=15, pady=4)
        if self.current_config.get("gemini_api_key"):
            self.gemini_key_entry.insert(0, self.current_config["gemini_api_key"])

        ctk.CTkLabel(self.gemini_frame, text="Модель (рекомендуется gemini-1.5-flash-latest или gemini-2.0-flash):").pack(anchor="w", padx=15)
        self.gemini_model_entry = ctk.CTkEntry(self.gemini_frame, width=560)
        self.gemini_model_entry.pack(padx=15, pady=(4, 12))
        self.gemini_model_entry.insert(0, self.current_config.get("gemini_model", "gemini-1.5-flash-latest"))

        # Common params
        common_frame = ctk.CTkFrame(self, fg_color="transparent")
        common_frame.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(common_frame, text="Общие параметры обработки", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 6))

        # Batch size
        batch_frame = ctk.CTkFrame(common_frame, fg_color="transparent")
        batch_frame.pack(fill="x")
        ctk.CTkLabel(batch_frame, text="Размер батча (рекомендуется 2-4):").pack(side="left", padx=5)
        self.batch_slider = ctk.CTkSlider(batch_frame, from_=1, to=6, number_of_steps=5, width=200,
                                          command=lambda v: self.batch_label.configure(text=str(int(v))))
        self.batch_slider.set(self.current_config.get("batch_size", 3))
        self.batch_slider.pack(side="left", padx=10)
        self.batch_label = ctk.CTkLabel(batch_frame, text=str(int(self.batch_slider.get())), width=30)
        self.batch_label.pack(side="left")

        # Delay
        delay_frame = ctk.CTkFrame(common_frame, fg_color="transparent")
        delay_frame.pack(fill="x", pady=6)
        ctk.CTkLabel(delay_frame, text="Задержка между батчами (сек):").pack(side="left", padx=5)
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
            btn_frame, text="💾 Сохранить настройки",
            fg_color=ACCENT_COLOR, hover_color="#3CB371",
            width=200, height=40, command=self.save_and_close
        )
        save_btn.pack(side="left", padx=10)

        cancel_btn = ctk.CTkButton(
            btn_frame, text="Отмена",
            fg_color="#475569", hover_color="#64748B",
            width=120, height=40, command=self.destroy
        )
        cancel_btn.pack(side="right", padx=10)

        # Initial state
        self._on_provider_change(self.provider_var.get())

        # Warning label
        warn = ctk.CTkLabel(
            self,
            text="🔒 API ключи сохраняются в текстовом файле ~/.stockdescriptor/config.json\n"
                 "Храните компьютер в безопасности. Никому не передавайте этот файл.",
            font=ctk.CTkFont(size=10),
            text_color="#FCA5A5",
            justify="center"
        )
        warn.pack(pady=(5, 10))

    def _on_provider_change(self, value: str):
        if "Gemini" in value:
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

        if provider == "lmstudio":
            new_cfg["lmstudio_url"] = self.lm_url_entry.get().strip()
            new_cfg["lmstudio_model"] = self.lm_model_entry.get().strip()
        else:
            key = self.gemini_key_entry.get().strip()
            new_cfg["gemini_api_key"] = key
            new_cfg["gemini_model"] = self.gemini_model_entry.get().strip() or "gemini-1.5-flash-latest"

            if not key:
                messagebox.showwarning(
                    "Пустой ключ",
                    "Вы выбрали Gemini, но не ввели API ключ.\n"
                    "Сохраняю без ключа — при запуске будет предупреждение."
                )

        if save_config(new_cfg):
            self.on_save(new_cfg)
            messagebox.showinfo("Готово", "Настройки успешно сохранены!\n\n"
                                "При первом использовании Gemini ключ будет сохранён в вашем профиле.")
            self.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить конфиг.")


def main():
    app = StockDescriptorGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
