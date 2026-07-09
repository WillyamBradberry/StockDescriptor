# Vision Image Processing Scripts

## Скрипты для подготовки изображений к анализу через Vision API

### 📋 Содержание
1. `resize_for_vision.ps1` - масштабирование и создание миниатюр
2. `write_exif.ps1` - инжекция метаданных в оригинальные фото

---

## 🚀 Использование

### 1️⃣ Подготовка окружения (один раз)

```powershell
cd d:\projects\AI\stock-descriptor
.\venv\Scripts\Activate.ps1
pip install pillow
```

✅ **Pillow 12.3.0** установлен в venv и готов к использованию.

> **Примечание:** pillow-simd требует специальной компиляции. Для большинства случаев обычный pillow работает достаточно быстро с использованием встроенной оптимизации.

---

### 2️⃣ Использование скрипта resize_for_vision.ps1

#### Способ 1: Из папки processing

```powershell
cd d:\projects\AI\stock-descriptor\processing
.\resize_for_vision.ps1 -ImageFolder "C:\path\to\images"
```

#### Способ 2: Скопировать скрипт в папку с картинками

```powershell
# Скопируйте оба скрипта в папку с картинками
Copy-Item "d:\projects\AI\stock-descriptor\processing\resize_for_vision.ps1" -Destination "C:\path\to\images\"
Copy-Item "d:\projects\AI\stock-descriptor\processing\write_exif.ps1" -Destination "C:\path\to\images\"
Copy-Item "d:\projects\AI\stock-descriptor\processing\write_exif.ps1" -Destination "C:\path\to\images\write_exif.ps1"

# Затем запустите из папки с картинками
cd "C:\path\to\images"
.\resize_for_vision.ps1 -ImageFolder "."
```

---

### 📊 Что делает resize_for_vision.ps1

1. **Определяет соотношение сторон** каждого изображения
2. **Выбирает оптимальный размер**:
   - 3:2 (1200×800) - для фото с классическим соотношением
   - 1:1 (1024×1024) - для квадратных изображений
   - 16:9 (1280×720) - для широкоформатных фото
3. **Масштабирует пропорционально** (сохраняет соотношение сторон, добавляет черные полосы)
4. **Сохраняет** в папке `THMBS/` с оригинальным именем файла
5. **Оптимизирует** для быстрой загрузки (качество JPEG 85%)

#### Результат
```
images/
├── photo1.jpg
├── photo2.jpg
└── THMBS/
    ├── photo1.jpg (1200×800)
    └── photo2.jpg (1024×1024)
```

---

### 🏷️ Инжекция метаданных (опционально)

Если у вас есть файл `METADATA.md`, скрипт предложит запустить `write_exif.ps1`:

```
Do you want to inject metadata into original images?
Continue? (y/n) y
```

Это добавит в оригинальные фото:
- **Title** (ObjectName)
- **Description** (Caption)
- **Keywords**
- **Author** (Vitaly Sokol)
- **Copyright** (© Vitaliy-sokol.com)

---

## 📝 Формат METADATA.md

```markdown
## photo1.jpg
**Title:**
```
My Photo Title
```

**Description:**
```
Detailed description of the photo
```

**Keywords:**
```
keyword1, keyword2, keyword3
```

## photo2.jpg
**Title:**
```
Another Photo
```
...
```

---

## ⚙️ Требования

- **Python 3.8+** (в venv)
- **Pillow 12.3.0** (установлен в venv)
- **ExifTool** (для write_exif.ps1) - путь: `D:\PROGRAMS\EXIFTOOL\exiftool.exe`
- **PowerShell 5.1+**

---

## 🐛 Отладка

### Если Python не найден
```powershell
# Активируйте venv вручную
.\venv\Scripts\Activate.ps1

# Затем запустите скрипт
.\resize_for_vision.ps1 -ImageFolder "C:\path\to\images"
```

### Если ExifTool не найден
```powershell
# Проверьте путь в write_exif.ps1
# Строка: $exiftool = "D:\PROGRAMS\EXIFTOOL\exiftool.exe"

# Или установите ExifTool в системный PATH
```

### Просмотр команд ExifTool (отладка)
Раскомментируйте строку в `write_exif.ps1`:
```powershell
# Uncomment for debugging: Write-Host $cmd -ForegroundColor DarkGray
```

---

## 📌 Примеры использования

### Пример 1: Обработать папку с фото
```powershell
.\resize_for_vision.ps1 -ImageFolder "D:\photos\vacation"
```

### Пример 2: Обработать + инжектить метаданные
```powershell
.\resize_for_vision.ps1 -ImageFolder "D:\photos\vacation"
# Ответьте 'y' когда будет предложено
```

### Пример 3: Только инжектить метаданные (без resize)
```powershell
.\write_exif.ps1 -OriginalFolder "D:\photos\vacation"

# Или если скрипт в той же папке:
.\write_exif.ps1
```

---

## 📦 Структура проекта

```
stock-descriptor/
├── processing/
│   ├── resize_for_vision.ps1  ← Главный скрипт
│   ├── write_exif.ps1         ← Инжекция метаданных
│   ├── README_VISION.md       ← Эта инструкция
│   └── venv/                  ← Python окружение
└── ...
```

---

## ✅ Готовые шаги

- [x] pillow удален
- [x] Pillow 12.3.0 установлен
- [x] resize_for_vision.ps1 создан
- [x] write_exif.ps1 адаптирован
- [x] Инструкция готова

**Можно использовать! 🎉**
