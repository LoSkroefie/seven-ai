@echo off
REM ============================================
REM Seven AI Assistant - Windows Installer
REM ============================================
title Seven AI Assistant - Installation

color 0B
echo.
echo ================================================
echo   SEVEN AI ASSISTANT - Installation Wizard
echo ================================================
echo.
echo   Version: 2.6.0 (Advanced Sentience Architecture)
echo   Author: JVR Software
echo   Date: February 2026
echo.
echo ================================================
echo.

REM Check for Python
echo [Step 1/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python is not installed!
    echo.
    echo Please install Python 3.11 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

python --version
echo [OK] Python found!
echo.

REM Check Python version
echo [Step 2/6] Verifying Python version...
python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 (
    echo.
    echo [ERROR] Python 3.11 or higher is required!
    echo.
    pause
    exit /b 1
)
echo [OK] Python version is compatible!
echo.

REM Create installation directory
echo [Step 3/6] Setting up installation directory...
set INSTALL_DIR=%LOCALAPPDATA%\SevenAI
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
echo [OK] Installation directory: %INSTALL_DIR%
echo.

REM Copy files
echo [Step 4/6] Copying application files...
xcopy /E /I /Y "%~dp0*" "%INSTALL_DIR%\" >nul
echo [OK] Files copied successfully!
echo.

REM Install dependencies
echo [Step 5/6] Installing Python dependencies...
echo This may take a few minutes...
echo.
cd /d "%INSTALL_DIR%"
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [WARNING] Some dependencies failed to install.
    echo Seven will still work, but some features may be limited.
    echo.
    echo You can install missing dependencies later with:
    echo   pip install -r requirements.txt
    echo.
) else (
    echo [OK] Dependencies installed successfully!
)
echo.

REM Check and install Ollama
echo [Step 6/7] Checking Ollama installation...
echo.
ollama --version >nul 2>&1
if errorlevel 1 (
    echo Ollama is not installed. Installing automatically...
    echo.
    echo Downloading Ollama installer...
    powershell -Command "Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile '%TEMP%\OllamaSetup.exe'"
    if errorlevel 1 (
        echo.
        echo [WARNING] Could not download Ollama automatically.
        echo Please install Ollama manually from: https://ollama.com/download
        echo.
    ) else (
        echo Installing Ollama...
        "%TEMP%\OllamaSetup.exe" /VERYSILENT /NORESTART
        echo Waiting for Ollama service to start...
        timeout /t 10 /nobreak >nul
        del "%TEMP%\OllamaSetup.exe" >nul 2>&1
        echo [OK] Ollama installed!
        echo.
    )
) else (
    echo [OK] Ollama is already installed!
)
echo.

REM Check for llama3.2 model
echo Checking for llama3.2 model...
ollama list 2>nul | findstr /i "llama3.2" >nul 2>&1
if errorlevel 1 (
    echo llama3.2 model not found. Downloading now...
    echo This will take several minutes ^(~2GB download^)...
    echo.
    ollama pull llama3.2
    if errorlevel 1 (
        echo.
        echo [WARNING] Model download failed. You can retry later with:
        echo   ollama pull llama3.2
        echo.
    ) else (
        echo [OK] llama3.2 model downloaded!
    )
) else (
    echo [OK] llama3.2 model found!
)
echo.

REM Check for llama3.2-vision model
echo Checking for llama3.2-vision model (needed for screen/webcam vision)...
ollama list 2>nul | findstr /i "llama3.2-vision" >nul 2>&1
if errorlevel 1 (
    echo llama3.2-vision model not found. Downloading now...
    echo This will take several minutes ^(~8GB download^)...
    echo.
    ollama pull llama3.2-vision
    if errorlevel 1 (
        echo.
        echo [WARNING] Vision model download failed. You can retry later with:
        echo   ollama pull llama3.2-vision
        echo.
    ) else (
        echo [OK] llama3.2-vision model downloaded!
    )
) else (
    echo [OK] llama3.2-vision model found!
)
echo.

REM Run setup wizard
echo [Step 7/7] Launching setup wizard...
echo.
python setup_wizard.py

if errorlevel 1 (
    echo.
    echo [ERROR] Setup wizard failed!
    echo You can run it manually later with:
    echo   python setup_wizard.py
    echo.
    pause
    exit /b 1
)

REM Create shortcuts
echo.
echo Creating desktop shortcuts...
powershell -ExecutionPolicy Bypass -File "%INSTALL_DIR%\create_shortcuts.ps1"

REM Success message
cls
echo.
echo ================================================
echo   INSTALLATION COMPLETE!
echo ================================================
echo.
echo Seven AI Assistant has been installed to:
echo   %INSTALL_DIR%
echo.
echo Desktop shortcuts created:
echo   - Seven Voice Assistant
echo   - Seven (Wake Word Mode)
echo   - Seven Test Mode
echo.
echo To launch Seven:
echo   1. Double-click desktop shortcut, OR
echo   2. Search for "Seven" in Start Menu
echo.
echo Documentation:
echo   - Quick Start: README.md
echo   - User Guide: SEVEN-SHORTCUTS-GUIDE.md
echo   - Features: IMPLEMENTATION_COMPLETE.md
echo.
echo ================================================
echo.
echo Would you like to launch Seven now?
echo.
set /p LAUNCH="Launch Seven? (Y/N): "
if /i "%LAUNCH%"=="Y" (
    echo.
    echo Launching Seven...
    start "" "%INSTALL_DIR%\main.py"
)

echo.
echo Thank you for installing Seven!
echo.
pause
