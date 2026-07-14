# Product Context — AI Film Factory

## Business Logic

Проект автоматизирует создание комиксов/анимации через AI:
1. Пользователь пишет сценарий в `.md` (drafts/)
2. Director Agent анализирует сценарий → список кадров
3. Каждый кадр описывается JSON-схемой v2
4. Prompt Builder собирает 7-блочный промпт из шаблонов
5. ComfyUI генерирует изображение (Stage A: blocking → Stage B: final)
6. Веб-UI позволяет редактору ревьюить и корректировать

## Feature Behavior

### Pipeline Stages
- **Stage 1** — Анализ сценария через Director Agent + LM Studio/Gemini
- **Stage 2** — Валидация кадров, создание .json файлов
- **Stage 3** — Сборка промпта (7 блоков) через prompt_builder.py
- **Stage 3.5** — Ревью редактором (prompt_adapter.py — controlled vocabulary)
- **Stage 4** — Рендер через ComfyUI WebSocket клиент

### Shot Lifecycle (State + Status Dual Model)
- **state**: `draft → ready → generated → approved → archived`
- **status**: `complete | rebuild | regenerate | recreate`
- Auto-checkup: статус определяет действие (`rebuild`/`regenerate`/`recreate`)

### Prompt Architecture (7 Blocks)
```
[Scene Action]:        Что происходит в сцене
[Character Definitions]: Описание персонажей (без "character:" префикса)
[Composition]:         Кадровая композиция и размещение
[Camera]:              Тип камеры из controlled vocabulary (5 типов)
[Location]:            Локация одной строкой
[Style]:               Из Style Profile
[Lighting]:            Освещение одна схема
```

### Controlled Vocabulary
- 5 канонических типов кадров с алиасами
- Monster suffix rules для монстров-животных
- Character description filtering по типу кадра (Close-up → только лицо/шея, Wide shot → минимальное описание)

## Functional Requirements

### CLI
- Полный пайплайн: `--stage all`
- Поэтапный запуск: `--stage 1`, `--stage 4`
- Health check: `--checkhealth`, `--checkup`
- Bootstrap эпизода: `scripts/init_episode_shots.py`

### Web API (20 endpoints)
- CRUD shots (grid + detail views)
- PATCH: prompt, characters, metadata, style
- POST: rebuild, regenerate, recreate, approve, archive
- WebSocket `/ws/progress` для прогресса
- Static images with auto-generated thumbnails

### Validation Rules
- Каждый персонаж должен быть в CharacterRegistry
- Нет "character:" префикса в выводе
- Нет смешанного кириллического/латинского в одном понятии
- Нет конфликтов типов камеры/освещения/композиции
- Нет artistic garbage outside allowed blocks

---

*Last updated: 2026-06-19 (Memory Bank initialization)*