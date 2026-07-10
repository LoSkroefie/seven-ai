@echo off
REM ============================================
REM Seven AI Assistant - Uninstaller
REM ============================================
title Seven AI Assistant - Uninstall

color 0C
echo.
echo ================================================
echo   SEVEN AI ASSISTANT - Uninstaller
echo ================================================
echo.

set INSTALL_DIR=%LOCALAPPDATA%\SevenAI

echo This will remove Seven AI Assistant from your computer.
echo.
echo Installation directory: %INSTALL_DIR%
echo.
echo The following will be removed:
echo   - Application files
echo   - Desktop shortcuts
echo   - Start menu shortcuts
echo.
echo NOTE: Your personal data in %USERPROFILE%\.chatbot will be preserved.
echo You can manually delete it later if desired.
echo.

set /p CONFIRM="Are you sure you want to uninstall? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo.
    echo Uninstall cancelled.
    pause
    exit /b 0
)

echo.
echo Uninstalling...
echo.

REM Remove desktop shortcuts
echo Removing desktop shortcuts...
del "%USERPROFILE%\Desktop\Seven Voice Assistant.lnk" 2>nul
del "%USERPROFILE%\Desktop\Seven (Wake Word).lnk" 2>nul
del "%USERPROFILE%\Desktop\Seven Test Mode.lnk" 2>nul
echo   Done

REM Remove start menu shortcuts
echo Removing Start Menu shortcuts...
rmdir /S /Q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Seven AI" 2>nul
echo   Done

REM Remove installation directory
echo Removing application files...
cd /d "%TEMP%"
rmdir /S /Q "%INSTALL_DIR%" 2>nul
echo   Done

echo.
echo ================================================
echo   UNINSTALL COMPLETE
echo ================================================
echo.
echo Seven AI Assistant has been removed.
echo.
echo Your personal data has been preserved in:
echo   %USERPROFILE%\.chatbot
echo.
echo To completely remove all data, delete that folder manually.
echo.
echo Thank you for using Seven!
echo.
pause
