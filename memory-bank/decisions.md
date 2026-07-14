# Decisions — AI Film Factory (Architectural Decision Records)

## ADR-001: JSON Shot Schema v2 (State + Status Dual Model)

**Status**: Accepted  
**Date**: 2026-06-XX (from PROJECT_MATRIX.md)  
**Context**: Нужна была чёткая модель жизненного цикла кадров. Один флаг не работал для разделения business lifecycle и operational state.
**Decision**: Использовать dual model — `state` (draft→ready→generated→approved→archived) + `status` (complete|rebuild|regenerate|recreate).
**Consequences**: 
- ✅ Auto-checkup может автоматически определять действие по статусу
- ✅ Разделение concerns упрощает логику
- ⚠️ Extra field adds slight complexity

## ADR-002: 7-Block Prompt Architecture

**Status**: Accepted  
**Date**: 2026-06-XX (from PROJECT_MATRIX.md)  
**Context**: Свободная форма промптов приводила к непредсказуемым результатам генерации.
**Decision**: Строгая структура из 7 блоков: Scene Action, Character Definitions, Composition, Camera, Location, Style, Lighting.
**Consequences**:
- ✅ Предсказуемая генерация через ComfyUI
- ✅ Валидация по блокам (prompt_validator.py)
- ⚠️ Жёсткая структура ограничивает креативность

## ADR-003: Controlled Vocabulary for Shot Types

**Status**: Accepted  
**Date**: 2026-06-XX (from PROJECT_MATRIX.md)  
**Context**: Свободный ввод типов кадров приводил к inconsistent prompts.
**Decision**: 5 канонических типов с алиасами: Above the waist shot, Close-up, Medium close-up, Full body shot, Wide shot.
**Consequences**:
- ✅ Consistent camera descriptions across all shots
- ⚠️ Ограниченное количество типов (может потребовать расширения)

## ADR-004: Character Description Filtering by Shot Type

**Status**: Accepted  
**Date**: 2026-06-XX (from PROJECT_MATRIX.md)  
**Context**: В Close-up промптах описывалась полная фигура, что создавало noise.
**Decision**: Фильтрация character descriptions по видимым частям тела для каждого типа кадра:
| Shot Type | Visible Parts |
|-----------|---------------|
| Close-up | head, face, neck, shoulders, hair |
| Medium close-up | head, face, neck, shoulders, chest, upper torso |
| Above the waist shot | head, face, torso, arms, visible equipment |
| Full body shot | Full description (no filter) |
| Wide shot | Minimal silhouette (build, clothing, equipment only) |

## ADR-005: Async Task Queue for Web UI

**Status**: Accepted  
**Date**: 2026-06-XX (from PROJECT_MATRIX.md)  
**Context**: Long-running операции (rebuild/regenerate/recreate) блокировали бы HTTP сервер.
**Decision**: Async task queue (core/queue.py) с WebSocket broadcast прогресса.
**Consequences**:
- ✅ Non-blocking UI operations
- ✅ Real-time progress via WebSocket
- ⚠️ Added complexity with lock management (pipeline.lock)

## ADR-006: FastAPI + Vanilla JS SPA Architecture

**Status**: Accepted  
**Date**: 2026-06-XX (from PROJECT_MATRIX.md)  
**Context**: Нужен был веб-интерфейс для редактирования shots без heavy frontend framework.
**Decision**: FastAPI backend с Tailwind CSS + vanilla JavaScript SPA.
**Consequences**:
- ✅ No build step, no npm dependencies
- ✅ Direct API access from Python pipeline modules
- ⚠️ Limited component reusability vs React/Vue

## ADR-007: Markdown→JSON Parser (md2json.py) для Stage 1 & 2

**Status**: Accepted  
**Date**: 2026-06-XX (from PROJECT_MATRIX.md)  
**Context**: Сценарии хранятся в .md, но pipeline работает с JSON.
**Decision**: Универсальный парсер YAML frontmatter + markdown body → JSON для Stage 1 (story analysis) и Stage 2 (shot detail).
**Consequences**:
- ✅ Flexible input format for writers
- ✅ Structured output for pipeline

## ADR-008: Transliteration Table for Cyrillic Support

**Status**: Accepted  
**Date**: 2026-06-XX (from PROJECT_MATRIX.md)  
**Context**: Персонажи с кириллическими именами требуют латинских версий для AI генерации.
**Decision**: Unified transliteration table (translit.py) с NAME_ALIASES и get_translit_variants.
**Consequences**:
- ✅ Consistent name handling across pipeline
- ⚠️ Manual maintenance of transliteration rules

## ADR-009: Multi-Image Navigation Pattern (Thumbnail Strip)

**Status**: Accepted  
**Date**: 2026-06-21  
**Context**: Shots can have multiple generated images (Stage A, Stage B, variants), but UI only showed one image. Users needed a way to browse all variants.
**Decision**: 
- Backend: `/api/shots/{episode}/{shot_id}/images` endpoint scans `render_pipeline/` + fallback to `storyboard/shots/`
- Backend: `file_prefix` filtering ensures only images for the current shot are returned
- Frontend: Dot strip overlay on grid cards + mouse move navigation
- Frontend: Centered thumbnail strip under main image in detail view
- Grid view: "?" info button instead of full-card hover overlay (cleaner UX)
**Consequences**:
- ✅ Users can browse all generated variants without leaving grid/detail views
- ✅ Mouse navigation provides intuitive frame switching
- ✅ Backend scanning is flexible (render_pipeline or fallback directories)
- ⚠️ Additional API calls per shot (mitigated by caching in browser)

---

*Last updated: 2026-06-20 (Memory Bank consolidation)*