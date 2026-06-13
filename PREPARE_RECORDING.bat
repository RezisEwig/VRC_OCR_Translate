@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title VRC OCR Translate - Recording Setup

where uv >nul 2>nul
if errorlevel 1 (
    echo [ERROR] uv was not found.
    pause
    exit /b 1
)

echo Opening the SteamVR final VR View and OBS Studio...
uv run python scripts\prepare_vr_recording.py
if errorlevel 1 (
    echo.
    echo [ERROR] SteamVR and the headset must be active.
    pause
    exit /b 1
)

echo.
echo First-time OBS setup:
echo   1. Add Source ^> Window Capture.
echo   2. Select the window named VR View.
echo   3. Disable cursor capture and fit the source to the screen.
echo   4. Start Recording.
echo.
echo The VR View is SteamVR's final composed image, so translation overlays are included.
pause
