@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title VRC OCR Translate - Local AI Check

if not exist "models\translategemma-4b-it.Q4_K_M.gguf" call SETUP_LOCAL_AI.bat --no-pause
if errorlevel 1 goto failed
if not exist "tools\llama.cpp\b9610\llama-server.exe" call SETUP_LOCAL_AI.bat --no-pause
if errorlevel 1 goto failed

uv sync --quiet
if errorlevel 1 goto failed
uv run vrc-ocr-translate --config config.json --check-local
if errorlevel 1 goto failed

echo.
echo Local OCR and GPU translation are ready.
pause
exit /b 0

:failed
echo.
echo [ERROR] Local AI check failed. Open logs\vrc-ocr-translate.log.
pause
exit /b 1
