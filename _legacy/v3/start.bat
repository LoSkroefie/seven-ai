@echo off
title Seven AI
echo.
echo   Starting Seven AI...
echo.
cd /d "%LOCALAPPDATA%\SevenAI"
start "" pythonw main_with_gui_and_tray.py
echo   Seven is running. You can close this window.
echo.
timeout /t 3 >nul
