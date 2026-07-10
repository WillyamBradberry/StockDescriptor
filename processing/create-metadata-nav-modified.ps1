param(
    [Parameter(Mandatory=$false)]
    [string]$MetadataFile = "METADATA.md",

    [Parameter(Mandatory=$false)]
    [int]$ThumbSize = 120,

    [Parameter(Mandatory=$false)]
    [int]$Columns = 4,

    [Parameter(Mandatory=$false)]
    [string]$ThumbsDir = "./THMBS"
)

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== Создание METADATA-NAV.md ===" -ForegroundColor Cyan

$mdPath = Resolve-Path $MetadataFile -ErrorAction Stop
$originalContent = Get-Content $mdPath -Raw -Encoding UTF8

# Удаляем старую навигацию
$content = $originalContent -replace '(?s)^## Навигация.+?^---\s*\n', ''

# Вставляем [[## Навигация]] после секции Keywords (закрывающие ``` на ту же строку)
$nl = "`n"
$content = $content -replace '(\*\*Keywords:\*\*\s*```\s*\n)([^`\n]+)\n```\s*\n---', ('$1$2'+ $nl + '```' + $nl + '[[## Навигация]]' + $nl + '---')

$blocks = [regex]::Split($content, '(?=^## )', [System.Text.RegularExpressions.RegexOptions]::Multiline) `
    | Where-Object { $_ -match '##\s+\S+\.jpg' }

$navItems = @()

foreach ($block in $blocks) {
    $fileMatch = [regex]::Match($block, '##\s+(\S+\.jpg)')
    if (-not $fileMatch.Success) { continue }

    $filename = $fileMatch.Groups[1].Value.Trim()

    $titleMatch = [regex]::Match($block,
        '\*\*Title:\*\*\s*\r?\n```+\r?\n(.+?)\r?\n```+',
        [System.Text.RegularExpressions.RegexOptions]::Singleline)
    $title = if ($titleMatch.Success) { $titleMatch.Groups[1].Value.Trim() } else { $filename }
    $shortTitle = if ($title.Length -gt 90) { $title.Substring(0,87) + "..." } else { $title }
    $safeTitle = $shortTitle -replace '"', '"'
    $thumbSrc  = "$ThumbsDir/$filename"

    # Картинка с тултипом + крохотная ссылка-стрелка под ней (единственный способ навигации в Obsidian)
    $navItems += "| <img src=`"$thumbSrc`" title=`"$safeTitle`" style=`"width:${ThumbSize}px;height:${ThumbSize}px;object-fit:cover;border-radius:6px;display:block;margin:0 auto;`"><div style=`"text-align:center;font-size:10px;opacity:0.4;margin-top:2px;`">[[#$filename\|## $filename ##]]</div> "
}

# Собираем таблицу
$header    = ("|   " * $Columns) + "|"
$separator = ("|---" * $Columns) + "|"

$rows = @($header, $separator)
$row = ""
$cellCount = 0

foreach ($item in $navItems) {
    $row += $item
    $cellCount++
    if ($cellCount -eq $Columns) {
        $rows += $row + "|"
        $row = ""
        $cellCount = 0
    }
}
if ($cellCount -gt 0) {
    while ($cellCount -lt $Columns) {
        $row += "|   "
        $cellCount++
    }
    $rows += $row + "|"
}

$galleryLines = @(
    "## Навигация",
    "",
    ($rows -join "`n"),
    "",
    "---",
    ""
)

$newContent = ($galleryLines -join "`n") + $content.TrimStart()

$navFileName = "METADATA-NAV.md"
$navPath = Join-Path (Split-Path $mdPath -Parent) $navFileName
$newContent | Set-Content -Path $navPath -Encoding UTF8 -Force

Write-Host "OK  METADATA-NAV.md создан" -ForegroundColor Green
Write-Host "    Файл:            $navFileName"
Write-Host "    Колонок:         $Columns"
Write-Host "    Размер превью:   ${ThumbSize}px"
Write-Host "    Превьюшки из:    $ThumbsDir"
Write-Host "    Изображений:     $($navItems.Count)"