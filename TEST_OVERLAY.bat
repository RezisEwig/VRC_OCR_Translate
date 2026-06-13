@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title VRC OCR Translate - Overlay Test

where uv >nul 2>nul
if errorlevel 1 (
    echo [ERROR] uv was not found.
    pause
    exit /b 1
)

echo Checking packages...
uv sync --quiet
if errorlevel 1 (
    echo [ERROR] Package setup failed.
    pause
    exit /b 1
)

echo SteamVR must be running.
echo The test subtitle will be visible for 15 seconds.
echo.
uv run vrc-ocr-translate --config config.json --demo-overlay
set "APP_EXIT_CODE=%ERRORLEVEL%"

echo.
if not "%APP_EXIT_CODE%"=="0" echo [ERROR] Overlay test failed.
pause
exit /b %APP_EXIT_CODE%
