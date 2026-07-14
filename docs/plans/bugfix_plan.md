Good day, Главнокомандующий.

Я изучил все файлы и ваши ответы. Представляю детальный план работ.

---

## ПЛАН РАБОТ: Исправление ошибок и новые функции

### Часть 1. Исправление ошибок (баги)

#### 1.1. Остановка процесса при недоступности LLM
**Где:** `gui_launcher.py` → `start_pipeline()`

**Что сделать:**
- Перед запуском пайплайна проверить выбранного провайдера:
  - **LM Studio:** вызвать `LMStudioClient.is_available()`. Если недоступен — попробовать `ensure_available()` (автозапуск). Если не удалось — показать `messagebox.showerror()` и прервать запуск.
  - **Gemini:** проверить наличие `gemini_api_key` в конфиге. Если пуст — показать `messagebox.showerror()` и прервать запуск.

#### 1.2. Пропуск файлов с ошибками при загрузке на FTP
**Где:** `gui_launcher.py` → `start_parallel_upload()` и `_trigger_auto_upload()`

**Что сделать:**
- Перед началом загрузки проверить наличие `metadata_error.md` в папке с фото.
- Если файл существует и содержит имена файлов:
  - Показать `messagebox.showwarning()` со списком файлов, которые НЕ обработаны и не будут загружены.
  - Загружать только файлы, которых нет в `metadata_error.md`.
- Если `METADATA.md` пуст или отсутствует — не загружать ничего, показать предупреждение.

#### 1.3. Корректная обработка ошибок в пайплайне
**Где:** `gui_launcher.py` → `_pipeline_worker()`

**Что сделать:**
- При наличии `metadata_error.md`:
  - ШАГ EXIF: пропускать только файлы из error-списка (сейчас пропускается весь EXIF).
  - ШАГ NAV: создавать навигацию только для файлов без ошибок.
  - Авто-загрузка (`auto_upload`): не запускать, если есть хотя бы одна ошибка.

---

### Часть 2. Интеграция LM Studio (скрипты из `./scripts/`)

#### 2.1. Поле BROWSE для пути к LM Studio в настройках
**Где:** `gui_launcher.py` → `SettingsWindow._build_settings_ui()`

**Что сделать:**
- Добавить в LM Studio секцию (`self.lm_frame`) новое поле:
  - **Label:** "LM Studio path (если не найден автоматически):"
  - **Entry:** отображает текущий путь из конфига (`lm_studio_path`)
  - **Кнопка "Browse...":** открывает `filedialog.askopenfilename()` для выбора `LM Studio.exe`
- При открытии окна настроек:
  - Попытаться найти LM Studio автоматически:
    1. Проверить `%LOCALAPPDATA%\Programs\LM Studio\LM Studio.exe`
    2. Проверить `%PROGRAMFILES%\LM Studio\LM Studio.exe`
    3. Проверить через `where lms` в PATH
  - Если найден — автоматически заполнить поле и сохранить в config.
  - Если не найден — показать предупреждение: "LM Studio не найдена. Укажите путь вручную."

#### 2.2. Проверка запуска и автозапуск LM Studio
**Где:** `gui_launcher.py` → `start_pipeline()` (интеграция с `LMStudioClient`)

**Что сделать:**
- Использовать готовый `LMStudioClient` из `scripts/lm_studio_client.py`:
  ```python
  client = LMStudioClient(
      base_url=config.get("lmstudio_url", "http://127.0.0.1:1234"),
      launch_path=config.get("lm_studio_path")
  )
  if not client.ensure_available(timeout=60):
      # показать ошибку и остановить процесс
  ```
- `ensure_available()` уже реализует: проверку → автозапуск → ожидание.

#### 2.3. Выпадающий список моделей LM Studio
**Где:** `gui_launcher.py` → `SettingsWindow._build_settings_ui()`

**Что сделать:**
- Заменить `CTkEntry` для `lm_model_entry` на `CTkOptionMenu` (выпадающий список).
- Добавить кнопку "🔄 Обновить список моделей":
  - При нажатии: `LMStudioClient.get_available_models()` → заполнить `CTkOptionMenu`.
  - Если сервер недоступен — показать предупреждение.
- Выбранная модель сохраняется в `config.json` как `lmstudio_model`.
- При открытии настроек: если сервер доступен — автоматически загрузить список.

#### 2.4. Автовыгрузка/загрузка модели
**Где:** `gui_launcher.py` → `_pipeline_worker()` (перед генерацией метаданных)

**Что сделать:**
- Использовать готовые скрипты:
  - `ModelUnloader` из `scripts/model_unloader.py`
  - `LMStudioClient.ensure_model_loaded()` из `scripts/lm_studio_client.py`
- Алгоритм:
  1. Проверить через `client.get_loaded_models_cli()` (`lms ps`) какая модель загружена.
  2. Если загружена другая модель (не совпадает с `lmstudio_model` из конфига):
     - Выгрузить: `ModelUnloader(client).free_vram()`
     - Загрузить нужную: `client.load_model(config["lmstudio_model"])`
  3. Если модель не загружена — просто загрузить.
  4. Если модель уже загружена — ничего не делать.

---

### Часть 3. Obsidian кнопка

#### 3.1. Кнопка "Просмотреть в Obsidian"
**Где:** `gui_launcher.py` → `_build_ui()` (добавить после пайплайна)

**Что сделать:**
- Добавить кнопку в main_card (после log_text или в отдельной строке):
  - **Текст по умолчанию:** "📖 Просмотреть в Obsidian" (disabled, серый)
  - **После успешного завершения пайплайна:** кнопка становится активной (зелёной)
- При нажатии:
  - Открыть `METADATA_nav.md` из папки с обработанными фото.

#### 3.2. Проверка установки Obsidian
**Где:** отдельная функция `is_obsidian_installed()` в `gui_launcher.py`

**Что сделать (лучший способ для Windows):**
- Проверить реестр Windows:
  ```python
  import winreg
  try:
      with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"obsidian\shell\open\command") as key:
          value, _ = winreg.QueryValueEx(key, "")
          return bool(value)
  except FileNotFoundError:
      return False
  ```
- Альтернатива: проверить `%LOCALAPPDATA%\Obsidian\Obsidian.exe`
- Если Obsidian не установлен:
  - Кнопка меняет текст на "⬇️ Загрузить Obsidian"
  - При нажатии открывается `https://obsidian.md` в браузере (`webbrowser.open()`)

#### 3.3. Открытие METADATA_nav.md
- Если Obsidian установлен: открыть через `os.startfile(path_to_md)` или `subprocess.run(["obsidian://open?vault=...&file=..."])` — но проще всего через `os.startfile()`, так как `.md` файлы ассоциированы с Obsidian.
- Если не установлен: кнопка ведёт на сайт.

---

### Файлы, которые будут изменены

| Файл | Изменения |
|------|-----------|
| `gui_launcher.py` | Все основные изменения: новые поля в SettingsWindow, проверки в pipeline, Obsidian кнопка, проверки перед загрузкой |
| `config_manager.py` | Возможно, добавить поле `lm_studio_path` в DEFAULT_CONFIG (если его там нет) |

### Файлы, которые НЕ будут изменены (уже готовы)

| Файл | Использование |
|------|---------------|
| `scripts/lm_studio_client.py` | `LMStudioClient` — проверка, автозапуск, список моделей, загрузка модели |
| `scripts/model_unloader.py` | `ModelUnloader` — выгрузка моделей из VRAM |
| `scripts/vram_manager.py` | `preflight()` / `postflight()` — управление VRAM |
| `scripts/ai_provider.py` | `LLMProvider` — генерация метаданных (уже использует LMStudioClient) |

---

### Порядок выполнения

1. **Исправление ошибок:**
   - 1.1 Остановка при недоступности LLM
   - 1.2 Проверка metadata_error.md перед загрузкой
   - 1.3 Пропуск файлов с ошибками в EXIF/NAV

2. **LM Studio интеграция:**
   - 2.1 Поле BROWSE + авто-поиск пути
   - 2.2 Проверка запуска и автозапуск
   - 2.3 Выпадающий список моделей
   - 2.4 Автовыгрузка/загрузка модели

3. **Obsidian кнопка:**
   - 3.1 Добавление кнопки
   - 3.2 Проверка установки Obsidian
   - 3.3 Открытие METADATA_nav.md

---

Утверждаете ли вы этот план? Если да — переключите меня в ACT MODE для реализации.