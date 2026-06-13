@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title VRC OCR Translate

echo ========================================
echo  VRC OCR Translate
echo ========================================
echo.

where uv >nul 2>nul
if errorlevel 1 (
    echo [ERROR] uv was not found.
    echo Install uv, then run this file again:
    echo   winget install --id=astral-sh.uv -e
    echo.
    pause
    exit /b 1
)

if not exist "config.json" (
    echo [ERROR] config.json was not found.
    echo Copy config.example.json to config.json.
    echo.
    pause
    exit /b 1
)

if not exist "models\translategemma-4b-it.Q4_K_M.gguf" goto setup_local_ai
if not exist "tools\llama.cpp\b9610\llama-server.exe" goto setup_local_ai
goto packages

:setup_local_ai
echo Local AI files are missing. Starting one-time setup...
call SETUP_LOCAL_AI.bat --no-pause
if errorlevel 1 (
    echo.
    echo [ERROR] Local AI setup failed.
    pause
    exit /b 1
)

:packages
echo [1/2] Checking required packages...
uv sync --quiet
if errorlevel 1 (
    echo.
    echo [ERROR] Package setup failed.
    pause
    exit /b 1
)

echo [2/2] Starting OCR translation overlay...
echo Quest Pro, Virtual Desktop, SteamVR, and VRChat must be running.
echo Only the VRChat game window is captured; desktop apps and overlays are excluded.
echo A minimized VRChat window is restored without taking keyboard focus.
echo Translation runs locally on the CPU and RTX GPU.
echo Left trigger: translate once / Left grip: clear translations
echo Ctrl+Alt+T: toggle automatic and manual translation modes
echo Position: Ctrl+Alt+Arrow keys / Scale: Ctrl+Alt+Numpad +/-
echo Reset position: Ctrl+Alt+Home (changes are saved automatically)
echo Press Ctrl+C to stop.
echo.

uv run vrc-ocr-translate --config config.json
set "APP_EXIT_CODE=%ERRORLEVEL%"

echo.
if not "%APP_EXIT_CODE%"=="0" (
    echo [ERROR] The program stopped with exit code %APP_EXIT_CODE%.
) else (
    echo The program has stopped.
)
pause
exit /b %APP_EXIT_CODE%
