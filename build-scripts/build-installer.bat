@echo off
echo ====================================================
echo Pyrometer Desktop Monitor - Installer Build Script
echo ====================================================
echo.

REM Change to the script directory
cd /d "%~dp0"

echo Checking if Inno Setup is installed...
set INNO_SETUP="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if not exist %INNO_SETUP% (
    echo ERROR: Inno Setup not found!
    echo Please install Inno Setup from: https://jrsoftware.org/isdl.php
    echo.
    pause
    exit /b 1
)

echo Inno Setup found!
echo.

echo Building installer...
%INNO_SETUP% "..\installer\installer_script.iss"
if errorlevel 1 (
    echo ERROR: Failed to build installer
    pause
    exit /b 1
)

echo ====================================================
echo Installer built successfully!
echo ====================================================
echo.
echo The installer is located at:
echo %~dp0..\output\
echo.
pause
