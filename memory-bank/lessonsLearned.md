# Lessons Learned — AI Film Factory

## Refactoring Discoveries

### Architecture Patterns
- **Pipeline Pattern** работает хорошо для последовательной обработки кадров, но stage_prompt_review.py (stage 3.5) добавляет сложности — нужен явный documentation механизма ревью
- **Observer Pattern** через WebSocket требует careful concurrency handling — pipeline.lock был введён как workaround
- **Strategy Pattern** для prompt building позволяет легко добавлять новые стили, но controlled vocabulary усложняет кастомизацию

### Framework Quirks
- **FastAPI** + WebSocket: требуется reverse proxy для production (nginx/apache) с WebSocket support
- **ComfyUI WebSocket API**: 600s timeout может быть недостаточен, retry logic должен быть robust
- **Tailwind CSS inline в SPA**: нет hot reload без build step, но это design choice для простоты

### Common Mistakes
- Не удалять `pipeline.lock` при crash — приводит к blocked UI/CLI access
- Schema v1 файлы не auto-converted без write operation — нужно явно запускать migration
- Translit table manual maintenance не масштабируется с ростом числа персонажей

### Framework Limitations
- Vanilla JS SPA: нет component reusability, но pros — zero build step
- ComfyUI VRAM management: model_unloader.py работает, но нет memory monitoring для LLM providers
- Shot schema v2 dual state (generated + edited): усложняет логику, но enables easy revert

## Implementation Notes

### Prompt Architecture
- 7-block structure предсказуемее для ComfyUI чем free-form prompts
- `prompt_adapter.py` conflict resolution требует careful testing при добавлении новых персонажей
- Controlled vocabulary (5 типов кадров) лучше для consistency, но хуже для flexibility

### Web UI Development
- Async task queue необходим для long-running операций (rebuild/regenerate)
- WebSocket reconnect с exponential backoff — критичен для unstable networks
- Lazy load shot grid важен для performance при большом количестве shots

## Migration Lessons

### Schema v1 → v2
- Automatic upcast on read работает, но permanent conversion только на first write
- Healthcheck должен обнаруживать legacy schema файлы явно
- Все downstream code должно поддерживать v2 с самого начала

---

*Last updated: 2026-06-20 (Memory Bank consolidation)*