@echo off
setlocal
cd /d "%~dp0"

if defined PYTHON_EXE (
  "%PYTHON_EXE%" -m seven --daemon --api %*
) else (
  py -3.11 -m seven --daemon --api %* 2>nul || py -3 -m seven --daemon --api %* 2>nul || python -m seven --daemon --api %*
)

endlocal
