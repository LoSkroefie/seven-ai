@echo off
REM Seven AI v2.0 - Quick Distribution Package Creator
REM Wrapper for create_distribution_v2.ps1

title Seven AI v2.0 - Package Creator

color 0B
echo.
echo ================================================
echo   Seven AI v2.0 - Package Creator
echo ================================================
echo.
echo This will create: Seven-AI-v2.0-Complete.zip
echo.
echo The package will be ready for public distribution.
echo.
pause

echo.
echo Creating distribution package...
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0create_distribution_v2.ps1"

if errorlevel 1 (
    echo.
    echo [ERROR] Package creation failed!
    echo Check the error messages above.
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================
echo   SUCCESS! Package Created
echo ================================================
echo.
echo Package: Seven-AI-v2.0-Complete.zip
echo.
echo Next steps:
echo   1. Test installation on clean system
echo   2. Verify Seven launches successfully
echo   3. Test basic conversation
echo   4. Upload to distribution platform
echo.
pause
