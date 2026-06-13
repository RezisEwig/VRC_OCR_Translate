@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title VRC OCR Translate - Overlay Test

set "UV_EXE=%~dp0tools\uv\uv.exe"
if not exist "%UV_EXE%" (
    for /f "delims=" %%I in ('where uv 2^>nul') do if not defined UV_FOUND set "UV_FOUND=%%I"
    if defined UV_FOUND set "UV_EXE=%UV_FOUND%"
)
if not exist "%UV_EXE%" (
    echo [ERROR] Run INSTALL.bat first.
    pause
    exit /b 1
)

echo Checking packages...
"%UV_EXE%" sync --quiet
if errorlevel 1 (
    echo [ERROR] Package setup failed.
    pause
    exit /b 1
)

echo SteamVR must be running.
echo The test subtitle will be visible for 15 seconds.
echo.
"%UV_EXE%" run vrc-ocr-translate --config config.json --demo-overlay
set "APP_EXIT_CODE=%ERRORLEVEL%"

echo.
if not "%APP_EXIT_CODE%"=="0" echo [ERROR] Overlay test failed.
pause
exit /b %APP_EXIT_CODE%
