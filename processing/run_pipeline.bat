@echo off
rem Run pipeline: resize -> metadata -> exif injection -> obsidian nav
rem Usage: run_pipeline.bat "C:\path\to\images"
rem Test:   run_pipeline.bat "D:\projects\photo\2017_03_16_waves\test"

setlocal enabledelayedexpansion

if "%~1"=="" (
  echo Usage: %~n0 "C:\path\to\images"
  echo Example: %~n0 "D:\projects\photo\2017_03_16_waves\test"
  exit /b 1
)

set "IMAGE_FOLDER=%~1"
set "SCRIPT_DIR=%~dp0"

echo === Pipeline start ===
echo Image folder: "%IMAGE_FOLDER%"

set "PS_HIDDEN="
if defined STOCK_GUI_HIDDEN (
  set "PS_HIDDEN=-WindowStyle Hidden"
)

echo.
echo 1) Generating thumbnails (THMBS)...
powershell -NoProfile -ExecutionPolicy Bypass %PS_HIDDEN% -File "%SCRIPT_DIR%resize_for_vision.ps1" -ImageFolder "%IMAGE_FOLDER%"
if errorlevel 1 (
  echo Error: resize_for_vision failed.
  if not defined STOCK_GUI_HIDDEN pause
  exit /b 1
)

echo.
echo 2) Running metadata analysis (batch_metadata.py)...
rem try to use venv python next to repo root
set "PYTHON_EXE=%SCRIPT_DIR%..\venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
  set "PYTHON_EXE=python"
)
rem when launched from GUI, use pythonw (no console window)
if defined STOCK_GUI_HIDDEN (
  set "PYTHON_EXE=%SCRIPT_DIR%..\venv\Scripts\pythonw.exe"
  if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=pythonw"
  )
)

rem Run batch_metadata in metadata-only mode (no EXIF injection, no nav)
rem Python handles: LLM analysis, METADATA.md, METADATA_PREVIEW.md
"%PYTHON_EXE%" "%SCRIPT_DIR%batch_metadata.py" "%IMAGE_FOLDER%" --no-inject --no-nav
if errorlevel 1 (
  echo Error: batch_metadata.py failed.
  if not defined STOCK_GUI_HIDDEN pause
  exit /b 1
)

echo.
echo 3) Injecting metadata into original images...
powershell -NoProfile -ExecutionPolicy Bypass %PS_HIDDEN% -File "%SCRIPT_DIR%write_exif.ps1" -OriginalFolder "%IMAGE_FOLDER%"
if errorlevel 1 (
  echo Error: write_exif.ps1 failed.
  if not defined STOCK_GUI_HIDDEN pause
  exit /b 1
)

echo.
echo 4) Generating Obsidian navigation file...
powershell -NoProfile -ExecutionPolicy Bypass %PS_HIDDEN% -File "%SCRIPT_DIR%create-metadata-nav-modified.ps1" -MetadataFile "%IMAGE_FOLDER%\METADATA.md"
if errorlevel 1 (
  echo Warning: create-metadata-nav-modified.ps1 had issues.
)

echo.
echo === Pipeline completed. ===
endlocal
exit /b 0