# Project Brief — AI Film Factory

## Project Goals

Создать систему автоматизации производства анимационного контента (кино/комикс) с помощью AI. Система управляет полным пайплайном: от анализа сценария до генерации финальных изображений через ComfyUI.

## Product Vision

AI Film Factory — это платформа для создания комиксов и анимационных роликов, где:
- Сценарий анализируется AI (Director Agent) на основе стиля
- Каждый кадр (shot) проходит валидацию и сборку промпта
- Изображения генерируются через ComfyUI с ControlNet + IP-Adapter
- Веб-интерфейс позволяет редактировать все этапы

## High-Level System Overview

```
Сценарий (.md) → Stage 1: Analysis → Shot list
                                    → Stage 2: Validation → .json shots
                                    → Stage 3: Prompt Assembly
                              ↕ Editor Review (Stage 3.5)
                                    → Stage 4: ComfyUI Render
```

## Core User Workflows

### CLI Workflow
1. `python pipeline/server.py --stage all` — полный пайплайн
2. `python pipeline/server.py --stage 1-3` — до ревью
3. `python pipeline/server.py --stage 4` — рендер после ревью
4. `python scripts/init_episode_shots.py` — создать shots из анализа

### Web UI Workflow
1. Запуск: `python pipeline/server.py --app` → http://localhost:8080
2. Grid view — обзор всех кадров эпизода
3. Detail view — редактирование промпта, персонажей, метаданных, стиля
4. Actions — rebuild / regenerate / recreate с прогрессом через WebSocket

---

*Last updated: 2026-06-20 (Memory Bank consolidation)*