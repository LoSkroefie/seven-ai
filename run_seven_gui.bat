@echo off
setlocal
cd /d "%~dp0"

if defined PYTHON_EXE (
  "%PYTHON_EXE%" -m seven --gui %*
) else (
  py -3.11 -m seven --gui %* 2>nul || py -3 -m seven --gui %* 2>nul || python -m seven --gui %*
)

endlocal
