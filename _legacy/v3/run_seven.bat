@echo off
REM ============================================================
REM Seven AI launcher — forces the correct Python interpreter.
REM
REM The default `python` on this machine is Windows Store Python,
REM which LACKS whisper / mcp / working torch. Seven's heavy
REM subsystems live in the unsloth studio env which has all of them.
REM
REM v3.2.20: pinned to the unsloth studio env so Whisper STT,
REM MCP server, CUDA, and the LoRA trainer all work.
REM ============================================================

title Seven AI

set "PYTHON_EXE=C:\Users\USER-PC\.unsloth\studio\unsloth_studio\Scripts\python.exe"
set "SEVEN_DIR=%~dp0"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Configured Python not found:
    echo   %PYTHON_EXE%
    echo.
    echo Edit run_seven.bat to point PYTHON_EXE at a Python with
    echo whisper, mcp, torch+cuda, and speech_recognition installed.
    pause
    exit /b 1
)

cd /d "%SEVEN_DIR%"
echo Starting Seven AI with: %PYTHON_EXE%
echo.
"%PYTHON_EXE%" launch_seven.py
echo.
echo Seven has stopped.
pause
