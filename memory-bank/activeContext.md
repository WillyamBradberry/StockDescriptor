# Active Development Context

## Current Objective
Реализация исправлений и новых функций из `docs/plans/to_fix.md`:
1. Исправление ошибок при загрузке на FTP (проверка метаданных)
2. Остановка процесса при отсутствии LLM
3. Интеграция LM Studio (автопоиск, автостарт, список моделей, автовыгрузка)
4. Obsidian кнопка для просмотра METADATA-NAV.md

## Session Progress
- [x] Прочитаны и проанализированы все скрипты в `./scripts/`
- [x] Прочитан `gui_launcher.py` (1339 строк)
- [x] Прочитан `config_manager.py`
- [x] Прочитан `batch_metadata.py`
- [x] Прочитан `upload_to_stocks.py`
- [x] Согласован план с Главнокомандующим
- [x] Реализованы все изменения в `gui_launcher.py`:
  - Импорты LMStudioClient, ModelUnloader
  - Функция `_find_lm_studio_path()` — автопоиск LM Studio
  - Функция `_is_obsidian_installed()` — проверка через реестр Windows
  - Функция `_open_in_obsidian()` — открытие через obsidian:// URI
  - _check_llm_available() — проверка доступности LLM перед пайплайном
  - _ensure_correct_model_loaded() — проверка/переключение модели LM Studio
  - _filter_error_files() — фильтрация файлов с ошибками при загрузке
  - Поле BROWSE для LM Studio path в настройках
  - Выпадающий список моделей (CTkOptionMenu) + кнопка Refresh
  - Obsidian кнопка с проверкой установки
  - Проверка metadata_error.md перед загрузкой на FTP
  - Проверка METADATA.md перед загрузкой

## Open Questions
- Нет, все вопросы решены.

## Temporary Decisions
- `gui_launcher.py` — единственный файл, который был изменён (все изменения внутри него)
- Готовые скрипты `lm_studio_client.py`, `model_unloader.py` используются напрямую