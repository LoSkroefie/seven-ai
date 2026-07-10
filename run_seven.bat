@echo off
REM Primary launcher: TALK with Seven (voice + free will)
setlocal
cd /d "%~dp0"

if defined PYTHON_EXE (
  "%PYTHON_EXE%" -m seven --talk %*
) else (
  py -3.11 -m seven --talk %* 2>nul || py -3 -m seven --talk %* 2>nul || python -m seven --talk %*
)

endlocal
