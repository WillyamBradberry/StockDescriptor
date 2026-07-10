# 🚀 БЫСТРЫЙ СТАРТ

## Вариант 1: Полный пайплайн (рекомендуется)

```batch
cd d:\projects\AI\stock-descriptor
processing\run_pipeline.bat "C:\path\to\your\images"
```

Одна команда выполнит всё:
1. ✅ **resize_for_vision.ps1** — создаст `THMBS/` с уменьшенными копиями
2. ✅ **batch_metadata.py** — сгенерирует Title/Description/Keywords через AI (LM Studio)
3. ✅ **write_exif.ps1** — запишет метаданные в оригиналы
4. ✅ **create-metadata-nav-modified.ps1** — создаст навигацию для Obsidian

---

## Вариант 2: Пошагово

### Шаг 1: Создать миниатюры

```powershell
cd d:\projects\AI\stock-descriptor
.\venv\Scripts\Activate.ps1
.\processing\resize_for_vision.ps1 -ImageFolder "C:\path\to\your\images"
```

Что произойдёт:
- Определятся размеры картинок
- Создастся папка `THMBS/`
- Картинки масштабируются до 1024px по большей стороне (пропорционально)
- Сохранятся в `THMBS/` с оригинальными именами
- Уже обработанные файлы будут пропущены

### Шаг 2: Сгенерировать метаданные через AI

```powershell
# Убедитесь, что LM Studio запущен (http://localhost:1234)
.\venv\Scripts\Activate.ps1
python .\processing\batch_metadata.py "C:\path\to\your\images"
```

Что произойдёт:
- AI проанализирует каждое фото через Vision API
- Создастся `METADATA.md` с Title, Description, Keywords
- Создастся `METADATA_PREVIEW.md` для быстрого просмотра
- Ошибочные файлы попадут в `metadata_error.md`

**Полезные флаги:**
| Флаг | Описание |
|------|----------|
| `--mock` | Тестовая генерация без API |
| `--batch-size 3` | Количество фото за один запрос |
| `--delay 3` | Пауза между батчами (сек) |
| `--check-errs` | Переобработать только ошибки |
| `--no-inject` | Не запускать EXIF после генерации |
| `--no-nav` | Не создавать навигацию Obsidian |

### Шаг 3: Инжектировать метаданные в оригиналы

```powershell
.\processing\write_exif.ps1 -OriginalFolder "C:\path\to\your\images"
```

Что произойдёт:
- Прочитает `METADATA.md`
- Запишет Title, Description, Keywords в оригинальные JPG
- Добавит автора (Vitaly Sokol) и копирайт

---

## 📝 Формат METADATA.md

```markdown
## photo1.jpg

![[photo1.jpg|600]]

**Title:**
```
My Amazing Photo
```

**Description:**
```
A detailed description of the photo
```

**Keywords:**
```
keyword1, keyword2, keyword3
```

## photo2.jpg
...
```

---

## 🧪 Mock-тестирование (без LM Studio)

```powershell
.\venv\Scripts\Activate.ps1
python .\processing\batch_metadata.py "C:\path\to\your\images" --mock
```

Сгенерирует тестовые метаданные без вызова API.

---

## 🔄 Resume-режим (добавление новых фото)

Просто запустите `batch_metadata.py` повторно:

```powershell
python .\processing\batch_metadata.py "C:\path\to\your\images"
```

Уже обработанные файлы будут пропущены, обработаются только новые.

---

## ❓ Если что-то пошло не так

```powershell
# Проверьте политику PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Активируйте venv
.\venv\Scripts\Activate.ps1

# Проверьте зависимости
python -c "import PIL; print(PIL.__version__)"
python -c "import requests; print(requests.__version__)"
```

---

## 📖 Полная документация

- [`README.md`](../README.md) — Главный README проекта
- [`README_VISION.md`](README_VISION.md) — Подробно о resize и EXIF
- [`base_prompt.md`](base_prompt.md) — Системный промпт для AI