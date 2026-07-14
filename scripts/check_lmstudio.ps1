function Find-LMStudio {
    # 1. Проверяем, есть ли lms в PATH
    $lmsCli = Get-Command lms -ErrorAction SilentlyContinue
    if ($lmsCli) {
        # Извлекаем путь к директории исполняемого файла lms
        $cliDir = Split-Path $lmsCli.Source
        # Часто LM Studio лежит на один-два уровня выше CLI-папки
        $possibleExe = Join-Path (Split-Path $cliDir) "LM Studio.exe"
        if (Test-Path $possibleExe) { return $possibleExe }
    }

    # 2. Ищем в реестре Windows (в ветке текущего пользователя и системы)
    $regPaths = @(
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )
    foreach ($path in $regPaths) {
        $app = Get-ItemProperty $path -ErrorAction SilentlyContinue | 
               Where-Object { $_.DisplayName -like "*LM Studio*" }
        if ($app -and $app.InstallLocation) {
            $exe = Join-Path $app.InstallLocation "LM Studio.exe"
            if (Test-Path $exe) { return $exe }
        }
    }

    # 3. Сканируем стандартные папки в AppData
    $localAppData = $env:LOCALAPPDATA
    $fallbackPaths = @(
        "$localAppData\Programs\LM-Studio\LM Studio.exe",
        "$localAppData\LM-Studio\LM Studio.exe",
        "$localAppData\Programs\lmstudio\LM Studio.exe"
    )
    foreach ($path in $fallbackPaths) {
        if (Test-Path $path) { return $path }
    }

    return $null
}

$path = Find-LMStudio
if ($path) {
    Write-Host "[+] Путь к LM Studio найден: $path" -ForegroundColor Green
} else {
    Write-Host "[-] Не удалось найти установленный LM Studio." -ForegroundColor Red
}