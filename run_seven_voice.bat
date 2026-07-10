@echo off
setlocal
cd /d "%~dp0"

if defined PYTHON_EXE (
  "%PYTHON_EXE%" -m seven --voice %*
) else (
  py -3.11 -m seven --voice %* 2>nul || py -3 -m seven --voice %* 2>nul || python -m seven --voice %*
)

endlocal
