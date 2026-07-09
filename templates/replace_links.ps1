# # Сам найдёт .html файл в текущей папке
#.\replace_links.ps1 -ThumbBasePath "tonga\04\jpgs\thmbs"

# Или явно указать файл
#.\replace_links.ps1 -HtmlFilePath "tonga-humpback-whales.html.html" -ThumbBasePath "tonga\04\jpgs\thmbs"

param(
    [string]$HtmlFilePath,
    [Parameter(Mandatory=$true)]
    [string]$ThumbBasePath
)

# Автопоиск файла
if (-not $HtmlFilePath) {
    $htmlFiles = Get-ChildItem -Path "." -Filter "*.html" -File
    if ($htmlFiles.Count -eq 0) { Write-Host "HTML не найден!" -ForegroundColor Red; exit 1 }
    $HtmlFilePath = $htmlFiles[0].FullName
    Write-Host "Обрабатываем: $HtmlFilePath" -ForegroundColor Green
}

$content = Get-Content -Path $HtmlFilePath -Raw -Encoding UTF8

# Исправляем target
$content = $content -replace 'target="_self"', 'target="_blank"'

# === УЛУЧШЕННЫЙ РЕГУЛЯРНЫЙ ВЫРАЖЕНИЕ ===
$pattern = '(?is)(<span\b[^>]*?)(?:[\s]*(?:alt|src)="[^"]*?")*?([^>]*)(>)(.*?)(</span>)'

$content = [regex]::Replace($content, $pattern, {
    param($m)

    $spanOpenStart = $m.Groups[1].Value   # <span ...
    $attributes    = $m.Groups[2].Value   # class, style и т.д.
    $closeGt       = $m.Groups[3].Value   # >
    $innerContent  = $m.Groups[4].Value   # содержимое внутри span
    $spanClose     = $m.Groups[5].Value   # </span>

    # Извлекаем имя файла
    if ($m.Value -match '(?i)(?:alt|src)="([^"/\\]+?\.jpe?g)"') {
        $filename = $Matches[1]
    } else {
        return $m.Value
    }

    $newSrc = (Join-Path $ThumbBasePath $filename).Replace('\', '/')

    # Чистим открывающий <span>
    $newOpen = $spanOpenStart -replace '(?i)\s+(?:alt|src)="[^"]*"', ''
    $newOpen = $newOpen.TrimEnd() + $attributes.Trim()

    # Добавляем src и target
    if ($newOpen -notmatch '(?i)src=') {
        $newOpen += " src=`"$newSrc`""
    }
    if ($newOpen -notmatch '(?i)target=') {
        $newOpen += ' target="_blank"'
    }
    $newOpen += '>'

    # Обновляем <img> внутри
    $newInner = $innerContent
    $newInner = $newInner -replace '(?i)(<img\b[^>]*?)(?:src="[^"]*")?', "`$1 src=`"$newSrc`""
    $newInner = $newInner -replace '(?i)(<img\b[^>]*?)(?:alt="[^"]*")?', "`$1 alt=`"$filename`""
    $newInner = $newInner -replace '(?i)(<img\b[^>]*?)(?=>)', "`$1 target=`"_blank`""   # добавляем target в img

    # Убираем возможный &gt;
    $newInner = $newInner -replace '&gt;', '>'

    return $newOpen + $newInner + $spanClose
}, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)

# Дополнительная глобальная чистка
$content = $content -replace '&gt;\s*<img', '><img'
$content = $content -replace '>\s*class=', ' class='
$content = $content -replace '(src="[^"]+?")\s+target="_blank"\s+target="_blank"', '$1 target="_blank"'

# Сохранение
$backupPath = $HtmlFilePath + ".bak"
Copy-Item $HtmlFilePath $backupPath -Force
$content | Set-Content -Path $HtmlFilePath -Encoding UTF8

Write-Host "Готово! &gt; должен исчезнуть." -ForegroundColor Green
Write-Host "Файл: $HtmlFilePath" -ForegroundColor Cyan
Write-Host "Бэкап: $backupPath" -ForegroundColor Yellow