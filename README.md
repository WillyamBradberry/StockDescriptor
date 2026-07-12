# 📸 Stock Descriptor

Инструменты для подготовки, AI-анализа и обработки фотографий для стоковых платформ с управлением метаданными EXIF.

Showcase: https://stock.adobe.com/contributor/202223264/willyam

## 🎯 Основные возможности

### 1. 🖼️ Масштабирование для Vision API (`processing/resize_for_vision.ps1`)
- **Автоматическое определение** соотношения сторон изображения
- **Пропорциональное масштабирование** до 1024px по большей стороне (без искажений)
- **Автоматическое сохранение** в папку `THMBS/` с оригинальными именами
- **Оптимизация для web** (качество JPEG 85%)
- **Пропуск уже обработанных** файлов (idempotent)

### 2. 🤖 AI-генерация метаданных (`processing/batch_metadata.py`)
- **Пакетная обработка** изображений через Vision API (LM Studio)
- **Автоматическое создание** Title, Description, Keywords для каждого фото
- **Парсинг контекста** из `README.md` в папке с изображениями (вид, локация и т.д.)
- **Resume mode** — продолжение с прерванного места (не пересоздаёт готовые блоки)
- **--check-errs** — переобработка только ошибочных файлов
- **Mock mode** (`--mock`) — тестовая генерация без API
- **Инкрементальное сохранение** в `METADATA.md`
- **Генерация PREVIEW** (`METADATA_PREVIEW.md`) для быстрого просмотра
- **Генерация навигации** (`METADATA-NAV.md`) для Obsidian

### 3. 🏷️ Инжекция метаданных EXIF (`processing/write_exif.ps1`)
- Добавление Title, Description, Keywords в оригиналы фотографий
- Инжекция информации об авторе и копирайте
- XMP и IPTC метаданные
- Поддержка формата `METADATA.md`

### 4. 🔄 Полный пайплайн (`processing/run_pipeline.bat`)
Одной командой: **resize → AI metadata → EXIF injection → Obsidian nav**

### 5. 📋 Obsidian-навигация (`processing/create-metadata-nav-modified.ps1`)
- Создание `METADATA-NAV.md` с галереей превью для быстрой навигации в Obsidian
- Настраиваемое количество колонок и размер превью

## 📁 Структура проекта

```
stock-descriptor/
├── README.md                          # Этот файл
├── processing/                        # 🎯 Основные скрипты
│   ├── resize_for_vision.ps1         # Масштабирование → THMBS/
│   ├── batch_metadata.py             # AI-генерация метаданных (LLM Vision)
│   ├── write_exif.ps1                # Инжекция метаданных в оригиналы
│   ├── create-metadata-nav-modified.ps1  # Навигация для Obsidian
│   ├── run_pipeline.bat              # Полный пайплайн одной командой
│   ├── base_prompt.md                # Системный промпт для AI
│   ├── prompt_w_exif.md              # Промпт для EXIF-агента
│   ├── QUICK_START.md                # Быстрый старт
│   ├── README_VISION.md              # Документация по resize
│   ├── METADATA_gallery.md           # Пример галереи
│   └── METADATA-NAV.md               # Пример навигации
├── templates/                        # 📋 Шаблоны метаданных
│   ├── README.md                     # Шаблон контекста (вид, локация)
│   ├── replace_links.ps1             # Замена ссылок в HTML
│   └── CHINCHORRO/                   # Пример: крокодилы Чинчорро
│       ├── CHINCHORRO.md
│       └── CROCODILLES-OF-CHINCHORRO-MEXICO.md
└── requirements.txt                  # Python зависимости
```

## 🚀 Быстрый старт

### Вариант 1: Полный пайплайн (рекомендуется)

```batch
cd d:\projects\AI\stock-descriptor
processing\run_pipeline.bat "C:\path\to\your\images"
```

Это выполнит:
1. **resize_for_vision.ps1** — создаст `THMBS/` с уменьшенными копиями
2. **batch_metadata.py** — сгенерирует Title/Description/Keywords через AI
3. **write_exif.ps1** — запишет метаданные в оригиналы
4. **create-metadata-nav-modified.ps1** — создаст навигацию для Obsidian

### Вариант 2: Пошагово

```powershell
cd d:\projects\AI\stock-descriptor
.\venv\Scripts\Activate.ps1

# Шаг 1: Создать миниатюры
.\processing\resize_for_vision.ps1 -ImageFolder "C:\path\to\your\images"

# Шаг 2: Сгенерировать метаданные через AI (LM Studio должен быть запущен)
python .\processing\batch_metadata.py "C:\path\to\your\images"

# Шаг 3: Инжектировать метаданные в оригиналы
.\processing\write_exif.ps1 -OriginalFolder "C:\path\to\your\images"
```

## 📊 Примеры использования

### Пример 1: Только масштабирование
```powershell
.\processing\resize_for_vision.ps1 -ImageFolder "D:\photos\vacation"
```

Результат:
```
D:\photos\vacation/
├── photo1.jpg           (оригинал)
├── photo2.jpg           (оригинал)
└── THMBS/
    ├── photo1.jpg       (1024px)
    └── photo2.jpg       (1024px)
```

### Пример 2: AI-генерация метаданных
```powershell
# Активируйте venv и убедитесь, что LM Studio запущен
.\venv\Scripts\Activate.ps1
python .\processing\batch_metadata.py "D:\photos\whales" --batch-size 3 --delay 3
```

**Флаги `batch_metadata.py`:**
| Флаг | Описание |
|------|----------|
| (путь) | Папка с изображениями (по умолчанию `.`) |
| `--batch-size N` | Размер батча (рекомендуется 2-3) |
| `--delay N` | Задержка между батчами в секундах |
| `--mock` | Режим тестирования без API |
| `--no-inject` | Без EXIF-инжекции после генерации |
| `--no-nav` | Без генерации навигации Obsidian |
| `--check-errs` | Переобработка только ошибочных файлов |
| `--ask-nav` | Спросить перед генерацией навигации |

### Пример 3: Только инжекция метаданных
```powershell
.\processing\write_exif.ps1 -OriginalFolder "D:\photos"
```

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
A detailed description of the photo taken in the field
```

**Keywords:**
```
nature, landscape, photography, sunset
```

## photo2.jpg
...
```

## 🤖 AI-генерация метаданных

### Требования
- **LM Studio** (локально, порт 1234) или любой OpenAI-совместимый endpoint
- **Модель:** по умолчанию `qwen3.6-35b-a3b` (настраивается в `batch_metadata.py`)
- **Контекст:** поместите `README.md` в папку с изображениями — AI прочтёт его и учтёт при генерации

### Пример контекстного README.md
```markdown
endemic Chinchorro crocodile from Mexico's Banco Chinchorro reef
unique species, recently identified
```

### Черновик промпта
См. [`processing/base_prompt.md`](processing/base_prompt.md) — системный промпт для AI.

## ⚙️ Требования

### Системные требования
- **PowerShell 5.1+** (Windows)
- **Python 3.8+** (в `venv/`)
- **ExifTool** для инжекции метаданных
  - По умолчанию: `D:\PROGRAMS\EXIFTOOL\exiftool.exe`
  - Скачать: https://exiftool.org/

### Python зависимости
- **Pillow 12.3.0** (в `venv/`)
- **requests** (для API-запросов к LM Studio)

### Установка зависимостей

```powershell
cd d:\projects\AI\stock-descriptor
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install pillow requests
```

## 📖 Документация

- [`processing/README_VISION.md`](processing/README_VISION.md) — Подробно о resize и EXIF
- [`processing/QUICK_START.md`](processing/QUICK_START.md) — Быстрый старт
- [`processing/base_prompt.md`](processing/base_prompt.md) — Системный промпт для AI
- [`templates/CHINCHORRO/CROCODILLES-OF-CHINCHORRO-MEXICO.md`](templates/CHINCHORRO/CROCODILLES-OF-CHINCHORRO-MEXICO.md) — Пример готовых метаданных

## 🔧 Конфигурация

### Путь к ExifTool

Измените в [`processing/write_exif.ps1`](processing/write_exif.ps1):

```powershell
# Строка 10
$exiftool = "D:\PROGRAMS\EXIFTOOL\exiftool.exe"  # ← Ваш путь
```

### Endpoint LM Studio

Измените в [`processing/batch_metadata.py`](processing/batch_metadata.py):

```python
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL = "qwen3.6-35b-a3b"
```

## 🐛 Отладка

### Если скрипт не запускается

```powershell
# 1. Проверьте политику PowerShell
Get-ExecutionPolicy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 2. Активируйте venv
.\venv\Scripts\Activate.ps1

# 3. Проверьте Pillow
python -c "import PIL; print(PIL.__version__)"
```

### Просмотр команд ExifTool (отладка)

Раскомментируйте строку в [`processing/write_exif.ps1`](processing/write_exif.ps1):
```powershell
# Uncomment for debugging: Write-Host $cmd -ForegroundColor DarkGray
```

### Обработка ошибок AI

Если файлы не удалось обработать, они попадают в `metadata_error.md`:
```powershell
# Исправить проблему, затем переобработать только ошибки:
python .\processing\batch_metadata.py "D:\photos" --check-errs
```

## 📜 Лицензия

MIT License — используйте свободно!

## 👤 Автор

**Vitaly Sokol** — Professional Photographer  
Website: https://vitaliy-sokol.com

## 💡 Советы и трюки

### Массовая обработка нескольких папок

```powershell
$folders = "D:\photos\folder1", "D:\photos\folder2", "D:\photos\folder3"
foreach ($folder in $folders) {
    processing\run_pipeline.bat "$folder"
}
```

### Резервная копия перед обработкой

```powershell
Copy-Item "D:\photos" -Destination "D:\photos_backup" -Recurse
```

### Mock-тестирование без API

```powershell
python .\processing\batch_metadata.py "D:\photos" --mock
```

### Resume-режим (добавление новых фото)

Просто запустите `batch_metadata.py` повторно — уже обработанные файлы будут пропущены.

## 🤝 Вклад

Предложения и улучшения приветствуются!

## 📞 Поддержка

Если у вас возникли проблемы:
1. Проверьте [README_VISION.md](processing/README_VISION.md)
2. Откройте issue на GitHub
3. Проверьте пути и конфигурацию

---

**Версия:** 2.0.0  
**Последнее обновление:** July 2026