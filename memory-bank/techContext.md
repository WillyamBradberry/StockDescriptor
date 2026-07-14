# Tech Context — AI Film Factory

## Technology Stack

### Backend (Python)
- **FastAPI** — веб-фреймворк для API и SPA сервера
- **Uvicorn** — ASGI server для FastAPI
- **Python 3.x** — основной язык
- **asyncio** — асинхронные операции (task queue, WebSocket)

### Frontend (JavaScript + Tailwind)
- **Tailwind CSS** — utility-first CSS framework
- **Vanilla JavaScript** — SPA без фреймворков
- **WebSocket API** — real-time progress updates
- **Fetch API** — HTTP client для FastAPI endpoints

### AI Services
- **ComfyUI** — генерация изображений (Node-based workflow)
  - ControlNet для композиции/структуры
  - IP-Adapter для стилизации
  - WebSocket клиент с retry logic и 600s timeout
- **LM Studio** — локальная LLM для анализа/промптов
- **Gemini API** — облачная LLM альтернатива

### Data Formats
- **JSON (v2 schema)** — canonical shot state
- **Markdown (.md)** — scenario drafts, prompt templates
- **YAML frontmatter** — metadata в prompt markdown файлах

## External Dependencies

### Python Packages (inferred from codebase)
```
fastapi
uvicorn
pydantic
aiohttp / websockets  # ComfyUI WS client
requests               # LM Studio API calls
```

### External Services Required
- **ComfyUI instance** — запущен локально или удалённо (по умолчанию localhost:8188)
- **LM Studio** — опционально, для local LLM inference
- **Gemini API key** — опционально, для cloud LLM

## Environment Setup

### Prerequisites
1. Python 3.8+ с pip
2. ComfyUI установлен и запущен
3. LM Studio (опционально) или Gemini API key
4. Node.js (опционально, для Tailwind dev)

### Configuration
- **config.json** — основной конфиг проекта
- **config.json["web"]** — веб-секция (port, host, etc.)
- **pipeline.lock** — prevents concurrent CLI + UI access

### Startup Commands
```bash
# Full pipeline (CLI)
python pipeline/server.py --stage all

# Web UI only
python pipeline/server.py --app  # http://localhost:8080

# Specific stage
python pipeline/server.py --stage 4 --no-pause

# Health check
python pipeline/server.py --checkhealth --episode epizod_1

# Bootstrap shots from analysis
python scripts/init_episode_shots.py

# Render only (shortcut)
python pipeline/server.py --comfy
```

## Deployment Requirements

### Local Development
- FastAPI + Uvicorn на localhost:8080
- ComfyUI на отдельном порту (обычно 8188)
- Static files serve'd через FastAPI

### Production Considerations
- Reverse proxy для WebSocket поддержки
- Static file serving optimization
- pipeline.lock для concurrency control
- Auto-generated thumbnails для производительности

## Known Framework Limitations

### ComfyUI Client
- 600s timeout на генерацию изображения
- Retry logic встроен в comfy_client.py
- VRAM management через model_unloader.py

### Shot Schema v2
- Automatic upcast on read (v1→v2)
- First write converts file to v2 permanently
- State + Status dual model adds complexity but enables auto-checkup

### Web UI
- Vanilla JS SPA — нет build step, но и нет component reusability
- Tailwind inline styles — нет hot reload без настройки
- WebSocket reconnect с exponential backoff

---

*Last updated: 2026-06-19 (Memory Bank initialization)*