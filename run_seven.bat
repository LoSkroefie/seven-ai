@echo off
REM Primary launcher: one Seven avatar + voice + free will
setlocal
cd /d "%~dp0"

if defined PYTHON_EXE (
  "%PYTHON_EXE%" -m seven --companion %*
) else (
  py -3.11 -m seven --companion %* 2>nul || py -3 -m seven --companion %* 2>nul || python -m seven --companion %*
)

endlocal
