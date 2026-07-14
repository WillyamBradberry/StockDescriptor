# Known Issues — AI Film Factory

## Bugs

### BUG-001: Shot Schema v1 to v2 Migration
**Severity**: Medium  
**Module**: shot_serializer.py  
**Description**: Автоматический upcast срабатывает при чтении, но permanent conversion происходит только при первой записи. Если файл был прочитан через старый код и не записан заново — может остаться legacy schema.  
**Workaround**: Запустить `--checkhealth` для обнаружения v1 файлов, затем `--checkup`.

### BUG-002: pipeline.lock Concurrency Control
**Severity**: Medium  
**Module**: core/lock.py  
**Description**: Lock файл предотвращает concurrent CLI + UI access, но при crash одного из процессов lock может остаться.  
**Workaround**: Ручное удаление `pipeline.lock` файла.

### BUG-003: ComfyUI Timeout Handling
**Severity**: Low  
**Module**: comfy_client.py  
**Description**: 600s timeout может быть недостаточен для сложных workflow с ControlNet + IP-Adapter.  
**Workaround**: Настроить ComfyUI на оптимизацию или увеличить timeout в конфигурации.

## Technical Debt

### DEBT-001: No Type Hints in Pipeline Modules
**Severity**: Low  
**Module**: pipeline/*  
**Description**: Многие модули pipeline не имеют type hints, что затрудняет рефакторинг и понимание API.  
**Recommendation**: Добавить type hints постепенно при следующих изменениях кода.

### DEBT-002: Test Coverage for Pipeline Stages
**Severity**: Medium  
**Module**: tests/  
**Description**: Только `test_prompt_builder.py` (9 тестов) — отсутствует покрытие stages, shot_manager, web_app API endpoints.  
**Recommendation**: Добавить тесты для critical paths: shot_manager, prompt_validator, comfy_client.

### DEBT-003: Hardcoded ComfyUI Configuration
**Severity**: Low  
**Module**: comfy_client.py  
**Description**: URL и параметры ComfyUI могут быть в конфигурации вместо хардкода.  
**Recommendation**: Перенести в config.json.

### DEBT-004: No CI/CD Pipeline
**Severity**: Medium  
**Module**: Project-wide  
**Description**: Нет автоматического тестирования, линтинга или форматирования при коммитах.  
**Recommendation**: Добавить pre-commit hooks + GitHub Actions (если репозиторий в Git).

### DEBT-005: Translit Table Manual Maintenance
**Severity**: Low  
**Module**: translit.py  
**Description**: NAME_ALIASES и transliteration table требуют ручного обновления при добавлении новых персонажей.  
**Recommendation**: Автоматизировать через character registry или external config.

## Legacy Code Constraints

### LEGACY-001: Shot Schema v1 Files
**Status**: Supported via upcast  
**Description**: Старые .json файлы в schema v1 всё ещё могут существовать в `storyboard/shots/`.  
**Action**: shot_serializer.py handles automatic upcast on read.

### LEGACY-002: Dual Prompt Architecture (generated + edited)
**Status**: Active design choice  
**Description**: prompt объект хранит и generated, и edited версии с active flag. Это усложняет логику но позволяет easy revert.

## Areas Requiring Future Attention

### TODO-FUTURE-001: Style Profile Management
**Status**: Not documented in detail  
**Note**: `style_loader.py` загружает templates из `prompts/styles/`, но формат и механизм кастомных стилей требует документирования.

### TODO-FUTURE-002: Multi-Episode Support
**Status**: Partially implemented  
**Note**: Структура поддерживает multiple episodes (`epizod_1/shot_*.json`), но healthcheck/checkup должен корректно обрабатывать cross-episode references.

### TODO-FUTURE-003: Memory Management for Large Projects
**Status**: Not addressed  
**Note**: model_unloader.py решает VRAM issues для ComfyUI, но нет управления памятью для AI Provider (LM Studio / Gemini).

---

*Last updated: 2026-06-19 (Memory Bank initialization - issues inferred from PROJECT_MATRIX.md)*