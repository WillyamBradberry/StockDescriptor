param(
    [Parameter(Mandatory=$true)]
    [string]$ImageFolder
)

Write-Host "=== Vision Image Resizer ===" -ForegroundColor Cyan
Write-Host "Processing folder: $ImageFolder" -ForegroundColor Yellow

# Проверка папки
if (-not (Test-Path $ImageFolder)) {
    Write-Host "❌ Folder not found: $ImageFolder" -ForegroundColor Red
    exit 1
}

# Создаем папку THMBS
$thumbsFolder = Join-Path -Path $ImageFolder -ChildPath "THMBS"
if (-not (Test-Path $thumbsFolder)) {
    New-Item -ItemType Directory -Path $thumbsFolder -Force | Out-Null
    Write-Host "✅ Created folder: $thumbsFolder" -ForegroundColor Green
}

# Python скрипт для обработки изображений
$pythonScript = @"
import os
import sys
from PIL import Image
import math

image_folder = r'$ImageFolder'
thumbs_folder = r'$thumbsFolder'

# Целевые размеры и их соотношения
target_sizes = {
    (1200, 800): 1.5,      # 3:2
    (1024, 1024): 1.0,     # 1:1
    (1280, 720): 1.777778  # 16:9
}

jpg_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.jpg', '.jpeg'))]

if not jpg_files:
    print('No JPG files found in folder')
    sys.exit(0)

print(f'Found {len(jpg_files)} JPG files')
print('-' * 50)

for filename in jpg_files:
    filepath = os.path.join(image_folder, filename)
    
    try:
        # Открываем оригинальное изображение
        img = Image.open(filepath)
        original_size = img.size  # (width, height)
        
        # Вычисляем соотношение сторон
        aspect_ratio = original_size[0] / original_size[1]
        
        # Находим ближайший целевой размер
        best_size = min(target_sizes.keys(), 
                       key=lambda x: abs(target_sizes[x] - aspect_ratio))
        
        target_width, target_height = best_size
        target_ar = target_sizes[best_size]
        
        # Пропорциональное масштабирование с letterboxing
        scale_factor = min(target_width / original_size[0], 
                          target_height / original_size[1])
        
        new_width = int(original_size[0] * scale_factor)
        new_height = int(original_size[1] * scale_factor)
        
        # Создаем новое изображение с фоном
        new_img = Image.new('RGB', (target_width, target_height), (0, 0, 0))
        
        # Масштабируем оригинал
        resized = img.convert('RGB').resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Вставляем отмасштабированное изображение в центр
        offset_x = (target_width - new_width) // 2
        offset_y = (target_height - new_height) // 2
        new_img.paste(resized, (offset_x, offset_y))
        
        # Сохраняем в THMBS
        output_path = os.path.join(thumbs_folder, filename)
        new_img.save(output_path, 'JPEG', quality=85, optimize=True)
        
        print(f'✅ {filename}')
        print(f'   Original: {original_size[0]}×{original_size[1]} (AR: {aspect_ratio:.2f})')
        print(f'   Resized to: {target_width}×{target_height}')
        print(f'   Saved to: THMBS/{filename}')
        
    except Exception as e:
        print(f'❌ ERROR: {filename}')
        print(f'   {str(e)}')
    
    print()

print('=' * 50)
print('Processing completed!')
"@

# Запускаем Python скрипт
Write-Host "Starting image processing..." -ForegroundColor Cyan

# Получаем путь к Python из venv
$pythonExe = Join-Path -Path (Split-Path -Path $ImageFolder) -ChildPath "venv\Scripts\python.exe"

# Если venv не найден, пробуем использовать глобальный python
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$pythonScript | & $pythonExe

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python script failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Resize Complete ===" -ForegroundColor Green
Write-Host "Thumbnails saved to: $thumbsFolder" -ForegroundColor Green
Write-Host ""

# Предлагаем запустить write_exif.ps1
$writeExifPath = Join-Path -Path (Split-Path -Path $ImageFolder) -ChildPath "write_exif.ps1"

if (Test-Path $writeExifPath) {
    Write-Host "Do you want to inject metadata into original images?" -ForegroundColor Yellow
    Write-Host "This will run: write_exif.ps1" -ForegroundColor Gray
    
    $response = Read-Host "Continue? (y/n)"
    
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host ""
        Write-Host "Running write_exif.ps1..." -ForegroundColor Cyan
        & $writeExifPath -OriginalFolder $ImageFolder
    }
} else {
    Write-Host "ℹ️  write_exif.ps1 not found in parent directory" -ForegroundColor Gray
}
