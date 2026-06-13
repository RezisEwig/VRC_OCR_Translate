@echo off
cd /d "%~dp0"
if not exist "logs\vrc-ocr-translate.log" (
    echo No log file exists yet. Run RUN_TRANSLATOR.bat first.
    pause
    exit /b 1
)
start "" notepad.exe "logs\vrc-ocr-translate.log"
