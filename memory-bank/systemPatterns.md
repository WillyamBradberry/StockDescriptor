# System Patterns — AI Film Factory

## Architecture Overview

### Layered Architecture
```
┌───────────────────────────────────────┐
│         Web UI (FastAPI + SPA)        │  ← Presentation layer
│   /api/shots, /ws/progress           │
├───────────────────────────────────────┤
│       Pipeline Core (Python)          │  ← Business logic
│   server.py → stages/*              │
│   shot_manager.py, prompt_builder.py │
├───────────────────────────────────────┤
│        AI Providers                   │  ← External services
│   ai_provider.py (Gemini/LM Studio)  │
│   comfy_client.py (ComfyUI WS)       │
└───────────────────────────────────────┘
```

### Design Patterns Used

#### Pipeline Pattern
5 последовательных stage-модулей с возможностью промежуточного ревью:
- `stage_analysis.py` — анализ сценария
- `stage_detail.py` — валидация кадров
- `stage_prompt_review.py` — ревью промпта (3.5)
- `stage_prompt.py` — сборка промпта
- `stage_render.py` — рендер ComfyUI

#### Observer Pattern (WebSocket Events)
- `core/events.py` — event bus subscribe/broadcast по episode
- `core/queue.py` — async queue с broadcast прогресса
- WebSocket `/ws/progress` подписывается на эпизод

#### Strategy Pattern (Prompt Building)
- `prompt_builder.py` — 7-block assembler
- `prompt_adapter.py` — controlled vocabulary + conflict resolution
- `prompt_validator.py` — validation layer
- `style_loader.py` — style templates

#### Repository Pattern (Data Access)
- `shot_serializer.py` — JSON read/write, v1→v2 upcast
- `character_registry.py` — character/monster registry
- `reference_manager.py` — character card references
- `translit.py` — transliteration table

## Folder Structure

```
AI_Film_Factory_Sandbox/
├── pipeline/                    # CORE CODE (business logic)
│   ├── server.py                # CLI orchestrator
│   ├── stages/                  # Pipeline stages
│   │   ├── stage_analysis.py    # Stage 1: scenario analysis
│   │   ├── stage_detail.py      # Stage 2: shot validation
│   │   ├── stage_prompt.py      # Stage 3: prompt assembly
│   │   ├── stage_render.py      # Stage 4: ComfyUI rendering
│   │   └── stage_prompt_review.py # Stage 3.5: editor review
│   ├── shot_serializer.py       # JSON read/write, v1→v2 upcast
│   ├── shot_manager.py          # rebuild/regenerate/recreate/checkup
│   ├── prompt_builder.py        # 7-block prompt assembler
│   ├── prompt_validator.py      # Validation layer
│   ├── prompt_adapter.py        # Controlled vocabulary + conflict resolution
│   ├── character_registry.py    # Character/monster registry
│   ├── reference_manager.py     # Character card references
│   ├── comfy_client.py          # ComfyUI client + workflow + retry logic
│   ├── lm_studio_client.py      # LM Studio client
│   ├── ai_provider.py           # LLM abstraction (Gemini/LM Studio)
│   ├── director_agent.py        # Director agent (scenario analysis)
│   ├── style_loader.py          # Style template loader
│   ├── prompt_rules.py          # Prompt rule system
│   ├── load_prompt.py           # Load system prompts from Markdown
│   ├── md2json.py               # Markdown→JSON parser
│   └── translit.py              # Transliteration table
├── web_app/                     # Web UI (FastAPI + SPA)
│   ├── app.py                   # FastAPI factory, lifespan
│   ├── api/                     # Route modules
│   │   ├── episodes.py          # GET /api/episodes
│   │   ├── shots.py             # Shot CRUD (16 endpoints)
│   │   └── characters.py        # GET /api/characters
│   ├── core/                    # Shared logic
│   │   ├── config.py            # WebConfig typed loader
│   │   ├── lock.py              # pipeline.lock management
│   │   ├── queue.py             # Async task queue + worker
│   │   └── events.py            # WebSocket event bus
│   └── static/                  # Frontend assets
│       ├── index.html           # Tailwind SPA
│       ├── css/app.css          # Custom styles + themes
│       └── js/
│           ├── api.js           # HTTP API client
│           ├── grid.js          # Shot grid (lazy load, filters)
│           ├── detail.js        # Split-pane editor
│           └── ws.js            # WebSocket client
├── storyboard/shots/            # Canonical shot state (.json)
├── database/characters/         # Character descriptions
├── prompts/                     # Prompt rules & templates
│   ├── model_guides/
│   ├── styles/
│   └── templates/
├── skills/                      # Agent/model skill prompts
├── drafts/                      # Scenario drafts (.md)
├── tests/                       # All tests
├── scripts/                     # Utility scripts
├── config/                      # Configuration (config.json + web section)
└── docs/                        # Documentation
```

## Dependency Relationships

### Core Dependencies
- **FastAPI** — веб-сервер
- **Uvicorn** — ASGI server
- **ComfyUI** — генерация изображений (WebSocket API)
- **LM Studio / Gemini API** — LLM для анализа и промптов
- **Tailwind CSS** — стилизация SPA

### Module Dependencies
```
server.py → stages/* → comfy_client.py → ComfyUI
          → shot_manager.py → shot_serializer.py
          → prompt_builder.py → prompt_adapter.py → character_registry.py
          → ai_provider.py → lm_studio_client.py / Gemini API

web_app/ → api/shots.py → pipeline/shot_manager.py (via import)
         → core/queue.py → pipeline/* (async execution)
         → static/js/*.js → FastAPI endpoints
```

## Key Technical Decisions

1. **JSON Shot Schema v2** — единый источник правды для каждого кадра, с auto-upgrade из v1
2. **State + Status Dual Model** — разделение lifecycle и operational status
3. **Controlled Vocabulary** — 5 канонических типов кадров вместо свободного текста
4. **Async Task Queue** — UI не блокируется при long-running операциях (rebuild/regenerate)
5. **7-Block Prompt Architecture** — строгая структура промпта для предсказуемости генерации

---

*Last updated: 2026-06-19 (Memory Bank initialization)*