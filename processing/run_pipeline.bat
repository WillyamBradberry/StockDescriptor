@echo off
rem Run pipeline: resize -> metadata -> optional exif injection
rem Usage: run_pipeline.bat "C:\path\to\images"

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

echo.
echo 1) Generating thumbnails (THMBS)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%resize_for_vision.ps1" -ImageFolder "%IMAGE_FOLDER%"
if errorlevel 1 (
  echo Error: resize_for_vision failed.
  pause
  exit /b 1
)

echo.
echo 2) Running metadata analysis (batch_metadata.py)...
rem try to use venv python next to repo root
set "PYTHON_EXE=%SCRIPT_DIR%..\venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
  set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" "%SCRIPT_DIR%batch_metadata.py" "%IMAGE_FOLDER%"
if errorlevel 1 (
  echo Error: batch_metadata.py failed.
  pause
  exit /b 1
)

echo.
echo 3) Metadata generation finished. Now injecting metadata into originals...

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%write_exif.ps1" -OriginalFolder "%IMAGE_FOLDER%"
if errorlevel 1 (
  echo Error: write_exif.ps1 failed.
  pause
  exit /b 1
)

echo.
echo Pipeline completed.
endlocal
exit /b 0
