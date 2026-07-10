@echo off
REM Seven Real launcher — pins this repo and preferred Python if set
setlocal
cd /d "%~dp0"

if defined PYTHON_EXE (
  "%PYTHON_EXE%" -m seven %*
) else (
  py -3.11 -m seven %* 2>nul || py -3 -m seven %* 2>nul || python -m seven %*
)

endlocal
