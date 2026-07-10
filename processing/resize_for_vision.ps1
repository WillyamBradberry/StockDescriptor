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

# Python скрипт для обработки изображений: записываем во временный .py файл
$pyContent = @'
import os
import sys
from PIL import Image

# placeholders will be replaced by PowerShell
image_folder = r"__IMAGEFOLDER__"
thumbs_folder = r"__THUMBSFOLDER__"

max_width = 1024

jpg_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.jpg', '.jpeg'))]

if not jpg_files:
    print('No JPG files found in folder')
    sys.exit(0)

print(f'Found {len(jpg_files)} JPG files')
print('-' * 50)

for filename in jpg_files:
    filepath = os.path.join(image_folder, filename)
    output_path = os.path.join(thumbs_folder, filename)

    # Skip if thumbnail already exists
    if os.path.exists(output_path):
        print(f'⏭️  {filename} (already exists, skipped)')
        print()
        continue

    try:
        img = Image.open(filepath)
        w, h = img.size

        # Resize proportionally only if width > max_width
        if w > max_width:
            new_w = max_width
            new_h = int(h * (new_w / w))
            resized = img.convert('RGB').resize((new_w, new_h), Image.Resampling.LANCZOS)
        else:
            resized = img.convert('RGB')

        resized.save(output_path, 'JPEG', quality=85, optimize=True)

        print(f'✅ {filename}')
        print(f'   Original: {w}×{h}')
        print(f'   Saved to: THMBS/{filename}')

    except Exception as e:
        print(f'❌ ERROR: {filename}')
        print(f'   {str(e)}')

    print()

print('=' * 50)
print('Processing completed!')
'@

Write-Host "Starting image processing..." -ForegroundColor Cyan

# Создаем временный python файл в %TEMP%
$tempPy = Join-Path -Path $env:TEMP -ChildPath ("resize_for_vision_{0}.py" -f ([System.Guid]::NewGuid().ToString()))

# Заменяем плейсхолдеры безопасно (экранируем обратные слэши)
$safeImageFolder = $ImageFolder -replace "\\", "\\\\"
$safeThumbsFolder = $thumbsFolder -replace "\\", "\\\\"

$pyContent = $pyContent -replace "__IMAGEFOLDER__", $safeImageFolder
$pyContent = $pyContent -replace "__THUMBSFOLDER__", $safeThumbsFolder

$pyContent | Out-File -FilePath $tempPy -Encoding UTF8

# Получаем путь к Python из venv (ищем venv рядом с репозиторием root)
$repoRoot = Split-Path -Path $PSScriptRoot -Parent
$pythonExe = Join-Path -Path $repoRoot -ChildPath "venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) { $pythonExe = "python" }

# Запускаем временный python скрипт
& $pythonExe $tempPy

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python script failed!" -ForegroundColor Red
    Remove-Item -Force $tempPy -ErrorAction SilentlyContinue
    exit 1
}

Remove-Item -Force $tempPy -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=== Resize Complete ===" -ForegroundColor Green
Write-Host "Thumbnails saved to: $thumbsFolder" -ForegroundColor Green
Write-Host ""

# Предлагаем запустить write_exif.ps1
$writeExifPath = Join-Path -Path (Split-Path -Path $ImageFolder) -ChildPath 'write_exif.ps1'

if (Test-Path $writeExifPath) {
    Write-Host 'Do you want to inject metadata into original images?' -ForegroundColor Yellow
    Write-Host 'This will run: write_exif.ps1' -ForegroundColor Gray

    $response = Read-Host 'Continue? (y/n)'

    if ($response -match '^[yY]$') {
        Write-Host ''
        Write-Host 'Running write_exif.ps1...' -ForegroundColor Cyan
        & $writeExifPath -OriginalFolder $ImageFolder
    }
} else {
    Write-Host 'Info: write_exif.ps1 not found' -ForegroundColor Gray
}
