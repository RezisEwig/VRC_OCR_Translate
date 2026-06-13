@echo off
setlocal EnableExtensions
cd /d "%~dp0"
chcp 65001 >nul
title VRC OCR Translate - Easy Install

echo ========================================
echo  VRC OCR Translate - Easy Install
echo ========================================
echo.
echo This installer prepares everything automatically.
echo About 3 GB will be downloaded on the first run.
echo.

set "UV_DIR=%~dp0tools\uv"
set "UV_EXE=%UV_DIR%\uv.exe"

if not exist "%UV_EXE%" (
    echo [1/4] Installing the project launcher...
    if not exist "%UV_DIR%" mkdir "%UV_DIR%"
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$env:UV_INSTALL_DIR='%UV_DIR%'; $env:UV_NO_MODIFY_PATH='1'; irm https://astral.sh/uv/install.ps1 | iex"
    if errorlevel 1 goto install_failed
)

if not exist "%UV_EXE%" (
    echo [ERROR] uv was not installed correctly.
    goto install_failed
)

echo [2/4] Creating your personal settings...
if not exist "config.json" copy /y "config.example.json" "config.json" >nul

echo [3/4] Installing Python and required packages...
"%UV_EXE%" sync --quiet
if errorlevel 1 goto install_failed

echo [4/4] Downloading and checking the local AI model...
call SETUP_LOCAL_AI.bat --no-pause
if errorlevel 1 goto install_failed

echo.
echo ========================================
echo  Installation complete!
echo ========================================
echo Start Virtual Desktop, SteamVR, and VRChat,
echo then double-click RUN_TRANSLATOR.bat.
echo.
if /i not "%~1"=="--no-pause" pause
exit /b 0

:install_failed
echo.
echo [ERROR] Installation did not finish.
echo Check your internet connection and try INSTALL.bat again.
echo.
if /i not "%~1"=="--no-pause" pause
exit /b 1
