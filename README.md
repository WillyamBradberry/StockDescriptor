# 📸 Stock Descriptor

Инструменты для подготовки и обработки фотографий для анализа через Vision API и управления метаданными EXIF.

## 🎯 Основные возможности

### 1. 🖼️ Масштабирование для Vision API (`resize_for_vision.ps1`)
- **Автоматическое определение** соотношения сторон изображения
- **Оптимальное масштабирование** под 3 основных формата:
  - 3:2 → 1200×800 пикселей
  - 1:1 → 1024×1024 пикселей  
  - 16:9 → 1280×720 пикселей
- **Пропорциональное масштабирование** (без искажений)
- **Автоматическое сохранение** в папку `THMBS/` с оригинальными именами
- **Оптимизация для web** (качество JPEG 85%)

### 2. 🏷️ Инжекция метаданных EXIF (`write_exif.ps1`)
- Добавление Title, Description, Keywords в фотографии
- Инжекция информации об авторе и копирайте
- XMP и IPTC метаданные
- Поддержка формата METADATA.md

### 3. 📥 Загрузка YouTubes миниатюр (`YT-crawler-bot/`)
- Скачивание превью видео с YouTube
- Сохранение в высоком качестве

## 📁 Структура проекта

```
stock-descriptor/
├── README.md                          # Этот файл
├── processing/                        # 🎯 Основные скрипты
│   ├── resize_for_vision.ps1         # Масштабирование изображений
│   ├── write_exif.ps1                # Инжекция метаданных
│   ├── README_VISION.md              # Полная документация
│   ├── QUICK_START.md                # Быстрый старт
│   ├── THMBS/                        # Выходная папка для миниатюр
│   ├── batch_metadata.py             # Пакетная обработка метаданных
│   └── venv/                         # Python окружение
├── YT-crawler-bot/                   # 📥 Загрузка YouTube превью
│   ├── download_thumbnails.py
│   ├── requirements.txt
│   └── README.md
└── templates/                        # 📋 Шаблоны

```

## 🚀 Быстрый старт

### Вариант 1: Запуск из папки processing

```powershell
cd d:\projects\AI\stock-descriptor\processing
.\venv\Scripts\Activate.ps1
.\resize_for_vision.ps1 -ImageFolder "C:\path\to\your\images"
```

### Вариант 2: Скопировать скрипты в папку с картинками

```powershell
# Скопируйте файлы
Copy-Item processing\resize_for_vision.ps1, processing\write_exif.ps1 `
  -Destination "C:\path\to\your\images\"

# Запустите
cd "C:\path\to\your\images"
.\resize_for_vision.ps1 -ImageFolder "."
```

## 📊 Примеры использования

### Пример 1: Обработать папку с фото
```powershell
.\resize_for_vision.ps1 -ImageFolder "D:\photos\vacation"
```

Результат:
```
D:\photos\vacation/
├── photo1.jpg           (оригинал)
├── photo2.jpg           (оригинал)
└── THMBS/
    ├── photo1.jpg       (1200×800)
    └── photo2.jpg       (1024×1024)
```

### Пример 2: С инжекцией метаданных
```powershell
# Подготовьте METADATA.md в папке с картинками
.\resize_for_vision.ps1 -ImageFolder "."

# При завершении ответьте "y" чтобы инжектить метаданные
```

### Пример 3: Только инжекция метаданных
```powershell
.\write_exif.ps1 -OriginalFolder "D:\photos"
```

## 📝 Формат METADATA.md

```markdown
## photo1.jpg
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
**Title:**
```
Another Shot
```
...
```

## ⚙️ Требования

### Системные требования
- **PowerShell 5.1+** (Windows)
- **ExifTool** для инжекции метаданных
  - По умолчанию: `D:\PROGRAMS\EXIFTOOL\exiftool.exe`
  - Скачать: https://exiftool.org/

### Python зависимости (в venv)
- **Python 3.8+**
- **Pillow 12.3.0** (для обработки изображений)

### Установка зависимостей

```powershell
cd d:\projects\AI\stock-descriptor
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 📖 Полная документация

- [processing/README_VISION.md](processing/README_VISION.md) - Подробное описание всех возможностей
- [processing/QUICK_START.md](processing/QUICK_START.md) - Быстрый старт за 2 минуты
- [YT-crawler-bot/README.md](YT-crawler-bot/README.md) - Загрузка YouTube превью

## 🔧 Конфигурация

### Путь к ExifTool

Если ExifTool установлен в другом месте, отредактируйте [write_exif.ps1](processing/write_exif.ps1):

```powershell
# Строка 11
$exiftool = "D:\PROGRAMS\EXIFTOOL\exiftool.exe"  # ← Измените этот путь
```

### Python окружение

Все скрипты используют встроенный venv:
```
d:\projects\AI\stock-descriptor\venv\
```

Чтобы использовать другое окружение, отредактируйте пути в скриптах.

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

Раскомментируйте строку в [write_exif.ps1](processing/write_exif.ps1):
```powershell
# Uncomment for debugging: Write-Host $cmd -ForegroundColor DarkGray
```

## 📦 Python скрипты

### batch_metadata.py
Пакетная обработка метаданных для папки с изображениями.

```powershell
.\venv\Scripts\Activate.ps1
python processing\batch_metadata.py
```

## 📜 Лицензия

MIT License - используйте свободно!

## 👤 Автор

**Vitaly Sokol** - Professional Photographer  
Website: https://vitaliy-sokol.com

---

## 💡 Советы и трюки

### Массовая обработка нескольких папок

```powershell
$folders = "D:\photos\folder1", "D:\photos\folder2", "D:\photos\folder3"
foreach ($folder in $folders) {
    .\resize_for_vision.ps1 -ImageFolder $folder
}
```

### Резервная копия перед обработкой

```powershell
Copy-Item "D:\photos" -Destination "D:\photos_backup" -Recurse
```

### Проверка размеров файлов

```powershell
Get-ChildItem ".\THMBS\*.jpg" | Select-Object Name, @{N="Size (KB)"; E={[math]::Round($_.Length/1KB, 2)}}
```

## 🤝 Вклад

Предложения и улучшения приветствуются!

## 📞 Поддержка

Если у вас возникли проблемы:
1. Проверьте [README_VISION.md](processing/README_VISION.md)
2. Откройте issue на GitHub
3. Проверьте пути и конфигурацию

---

**Версия:** 1.0.0  
**Последнее обновление:** July 2026
