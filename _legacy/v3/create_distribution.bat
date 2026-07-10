@echo off
REM Create Distribution Package for Seven AI
title Seven AI - Create Distribution Package

echo.
echo ================================================
echo   SEVEN AI - Distribution Package Creator
echo ================================================
echo.
echo This will create a distributable ZIP file
echo containing Seven AI Assistant.
echo.
pause

echo.
echo Creating package...
echo.

powershell -ExecutionPolicy Bypass -File create_distribution.ps1

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to create package!
    pause
    exit /b 1
)

echo.
echo Press any key to exit...
pause >nul
