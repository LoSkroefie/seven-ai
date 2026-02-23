@echo off
REM Launch Seven with Wake Word Enabled
title Seven AI - Wake Word Mode

cd /d "%~dp0"

echo.
echo ================================================
echo   SEVEN AI - Wake Word Mode
echo ================================================
echo.
echo Wake word: "Seven"
echo.
echo Say "Seven" to activate listening!
echo Seven will respond when the wake word is detected.
echo.
echo Press Ctrl+C to exit
echo.
echo ================================================
echo.

REM Temporarily set wake word environment variable
set USE_WAKE_WORD=true

python main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Seven failed to start!
    echo.
    pause
)
