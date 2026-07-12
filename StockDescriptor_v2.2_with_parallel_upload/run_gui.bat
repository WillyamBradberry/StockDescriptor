@echo off
rem StockDescriptor GUI Launcher
rem Beautiful window for folder selection + AI settings (LM Studio / Gemini)

cd /d "%~dp0"

echo Starting StockDescriptor GUI...
python gui_launcher.py

if errorlevel 1 (
    echo.
    echo Error running GUI. Make sure Python and dependencies are installed.
    echo Try: python -m pip install -r requirements.txt
    pause
)
