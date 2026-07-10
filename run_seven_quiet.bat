@echo off
REM Quiet companion: type to talk, free will on, no mic/speakers (good at night)
setlocal
cd /d "%~dp0"
set SEVEN_QUIET=1

if defined PYTHON_EXE (
  "%PYTHON_EXE%" -m seven --quiet %*
) else (
  py -3.11 -m seven --quiet %* 2>nul || py -3 -m seven --quiet %* 2>nul || python -m seven --quiet %*
)

endlocal
