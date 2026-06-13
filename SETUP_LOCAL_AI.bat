@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title VRC OCR Translate - Local AI Setup

echo ========================================
echo  Local AI one-time setup
echo ========================================
echo TranslateGemma model: about 2.49 GB
echo llama.cpp Vulkan runtime: about 39 MB
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup_local_ai.ps1"
set "SETUP_EXIT_CODE=%ERRORLEVEL%"

echo.
if not "%SETUP_EXIT_CODE%"=="0" (
    echo [ERROR] Setup failed with exit code %SETUP_EXIT_CODE%.
) else (
    echo Local AI setup completed.
)
if /i not "%~1"=="--no-pause" pause
exit /b %SETUP_EXIT_CODE%
