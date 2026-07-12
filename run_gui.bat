@echo off
rem StockDescriptor GUI Launcher
rem Beautiful window for folder selection + AI settings (LM Studio / Gemini)

cd /d "%~dp0"

rem Check Python availability
where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python not found in PATH.
    echo Install Python from python.org and make sure it is added to PATH.
    pause
    exit /b 1
)

rem Create virtual environment if missing
if not exist venv\ (
    echo.
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created.
)

rem Activate virtual environment
call venv\Scripts\activate.bat

rem Check and install dependencies
echo Checking dependencies...
python -c "import customtkinter" 2>nul
if errorlevel 1 (
    echo Installing dependencies from requirements.txt...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
    echo Dependencies installed.
)

echo.
echo Starting StockDescriptor GUI...
python gui_launcher.py

if errorlevel 1 (
    echo.
    echo [ERROR] Program exited with an error.
    echo Check the log window in the GUI for details.
    pause
)