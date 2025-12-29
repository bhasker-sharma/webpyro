@echo off
echo ====================================================
echo Pyrometer Desktop Monitor - Build Script
echo ====================================================
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Set error handling
setlocal enabledelayedexpansion

echo Step 1: Installing Python dependencies...
cd ..\backend
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)
echo Python dependencies installed successfully!
echo.

echo Step 2: Building React frontend...
cd ..\frontend
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install npm dependencies
    pause
    exit /b 1
)
call npm run build
if errorlevel 1 (
    echo ERROR: Failed to build frontend
    pause
    exit /b 1
)
echo Frontend built successfully!
echo.

echo Step 3: Copying frontend to backend folder...
xcopy /E /I /Y ..\frontend\dist ..\backend\frontend
if errorlevel 1 (
    echo ERROR: Failed to copy frontend files
    pause
    exit /b 1
)
echo Frontend copied successfully!
echo.

echo Step 4: Building executable with PyInstaller...
cd ..\backend
pyinstaller pyrometer_desktop.spec --clean --noconfirm
if errorlevel 1 (
    echo ERROR: Failed to build executable
    pause
    exit /b 1
)
echo Executable built successfully!
echo.

echo ====================================================
echo Build completed successfully!
echo ====================================================
echo.
echo The executable is located at:
echo %~dp0..\backend\dist\PyrometerMonitor\
echo.
echo To create an installer, run: build-installer.bat
echo.
pause
