param(
    [Parameter(Mandatory=$false)]
    [string]$OriginalFolder = (Get-Location).Path,
    [Parameter(Mandatory=$false)]
    [string]$ExifToolPath = "D:\PROGRAMS\EXIFTOOL\exiftool.exe"
)

Write-Host "=== ExifTool Writer ===" -ForegroundColor Cyan
Write-Host "Processing folder: $OriginalFolder" -ForegroundColor Yellow
Write-Host "ExifTool path: $ExifToolPath" -ForegroundColor Yellow

# Путь к ExifTool
$exiftool = $ExifToolPath

# Проверяем наличие ExifTool
if (-not (Test-Path $exiftool)) {
    Write-Host "❌ ExifTool not found at: $exiftool" -ForegroundColor Red
    exit 1
}

# Полный путь к METADATA.md
$metadataPath = Join-Path -Path $OriginalFolder -ChildPath "METADATA.md"

if (-not (Test-Path $metadataPath)) {
    Write-Host "❌ File METADATA.md not found in folder:" -ForegroundColor Red
    Write-Host $OriginalFolder -ForegroundColor Yellow
    exit 1
}

# Читаем файл
$metadataContent = Get-Content $metadataPath -Raw -Encoding UTF8

# Разбиваем на блоки по файлам
$blocks = $metadataContent -split "(?=##\s)" | Where-Object { $_ -match '\.jpg' }

if ($blocks.Count -eq 0) {
    Write-Host "⚠️  No JPG entries found in METADATA.md" -ForegroundColor Yellow
    exit 0
}

Write-Host "Found $($blocks.Count) image(s) to process" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor DarkGray

foreach ($block in $blocks) {
    # Extract filename
    if ($block -match '##\s*(.+?\.jpg)') {
        $filename = $matches[1].Trim()
        
        $fullPath = Join-Path $OriginalFolder $filename
        
        if (-not (Test-Path $fullPath)) {
            Write-Host "⚠️  File not found: $filename" -ForegroundColor Yellow
            continue
        }

        # Extract Title, Description, Keywords from markdown
        $titleMatch = [regex]::Match($block, '\*\*Title:\*\*\s*\n```+\s*(.+?)\s*```+', 'Singleline')
        $descMatch  = [regex]::Match($block, '\*\*Description:\*\*\s*\n```+\s*(.+?)\s*```+', 'Singleline')
        $kwMatch    = [regex]::Match($block, '\*\*Keywords:\*\*\s*\n```+\s*(.+?)\s*```+', 'Singleline')

        $title = $titleMatch.Groups[1].Value.Trim()
        $desc  = $descMatch.Groups[1].Value.Trim()
        $kw    = $kwMatch.Groups[1].Value.Trim()

        Write-Host "Processing: $filename" -ForegroundColor Cyan

        # Split keywords into individual items so each becomes a SEPARATE IPTC keyword
        # (a single comma-joined string would be stored as one giant keyword, which
        #  stock platforms reject). Support comma, semicolon or newline separators.
        $keywords = @()
        if ($kw -ne '') {
            $keywords = $kw -split '[,;]\s*|\n' | Where-Object { $_.Trim() -ne '' } | ForEach-Object { $_.Trim() }
        }

        # Build ExifTool command. Keywords are added one-by-one via the
        # list syntax (-IPTC:Keywords+=value) so ExifTool stores them as
        # distinct keywords regardless of any separator handling.
        $cmd = "& `"$exiftool`" -overwrite_original " +
               "-IPTC:ObjectName=`"$title`" " +
               "-IPTC:Caption-Abstract=`"$desc`" "
        foreach ($k in $keywords) {
            $cmd += "-IPTC:Keywords+=`"$k`" "
        }
        $cmd += "-IPTC:By-line=`"Vitaly Sokol`" " +
               "-IPTC:By-lineTitle=`"Professional Photographer`" " +
               "-IPTC:CopyrightNotice=`"© Vitaliy-sokol.com`" " +
               "-XMP-dc:Creator=`"Vitaly Sokol`" " +
               "-XMP-dc:Rights=`"© Vitaliy-sokol.com`" " +
               "`"$fullPath`""

        # Uncomment for debugging: Write-Host $cmd -ForegroundColor DarkGray

        try {
            $result = Invoke-Expression $cmd
            Write-Host "✅ SUCCESS" -ForegroundColor Green
            if ($result) { $result | Write-Host -ForegroundColor Gray }
        }
        catch {
            Write-Host "❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
        }

        Write-Host "----------------------------------------" -ForegroundColor DarkGray
    }
}

Write-Host "=== Processing Complete ===" -ForegroundColor Cyan