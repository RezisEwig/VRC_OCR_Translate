@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title VRC OCR Translate - Local AI Check

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

if not exist "models\translategemma-4b-it.Q4_K_M.gguf" call SETUP_LOCAL_AI.bat --no-pause
if errorlevel 1 goto failed
if not exist "tools\llama.cpp\b9610\llama-server.exe" call SETUP_LOCAL_AI.bat --no-pause
if errorlevel 1 goto failed

"%UV_EXE%" sync --quiet
if errorlevel 1 goto failed
"%UV_EXE%" run vrc-ocr-translate --config config.json --check-local
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
