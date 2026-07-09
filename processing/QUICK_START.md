# 🚀 БЫСТРЫЙ СТАРТ

## Использование resize_for_vision.ps1

### Вариант 1: Запустить отсюда (processing папка)
```powershell
# Из PowerShell в папке processing:
.\resize_for_vision.ps1 -ImageFolder "C:\path\to\your\images"
```

### Вариант 2: Скопировать в папку с картинками

```powershell
# Скопируйте оба файла:
Copy-Item resize_for_vision.ps1, write_exif.ps1 -Destination "C:\path\to\your\images\"

# Затем:
cd "C:\path\to\your\images"
.\resize_for_vision.ps1 -ImageFolder "."
```

## ✨ Что произойдет

1. ✅ Определятся соотношения сторон картинок
2. ✅ Выберутся оптимальные размеры (1200×800, 1024×1024 или 1280×720)
3. ✅ Создастся папка `THMBS/` 
4. ✅ Картинки масштабируются (пропорционально, черные полосы добавляются)
5. ✅ Сохраняются в `THMBS/` с оригинальными именами
6. ✅ Предложится запустить `write_exif.ps1` если есть `METADATA.md`

## 📖 Полная документация

Смотри [README_VISION.md](README_VISION.md)
