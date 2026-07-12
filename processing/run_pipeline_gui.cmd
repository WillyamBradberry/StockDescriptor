@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_pipeline_gui.ps1"
exit /b %ERRORLEVEL%
