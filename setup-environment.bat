@echo off
REM ===================================================================
REM Environment Setup Script for Web Pyrometer Monitoring System
REM ===================================================================
REM This script sets up the development/production environment
REM Run this script ONCE before first use
REM ===================================================================

echo ========================================
echo Web Pyrometer - Environment Setup
echo ========================================
echo.
echo This script will:
echo   1. Set up Python virtual environment
echo   2. Install backend dependencies
echo   3. Install frontend dependencies
echo   4. Configure environment files
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul

REM ===================================================================
REM BACKEND SETUP
REM ===================================================================

echo.
echo ========================================
echo BACKEND SETUP
echo ========================================
echo.

REM Navigate to backend directory
cd /d "%~dp0backend"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if exist "venv\" (
    echo [INFO] Virtual environment already exists, skipping creation...
) else (
    echo [1/4] Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo [3/4] Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo [4/4] Installing backend dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Failed to install backend dependencies!
    deactivate
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Backend setup completed!

REM Deactivate virtual environment
deactivate

REM ===================================================================
REM FRONTEND SETUP
REM ===================================================================

echo.
echo ========================================
echo FRONTEND SETUP
echo ========================================
echo.

REM Navigate to frontend directory
cd /d "%~dp0frontend"

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH!
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

REM Install npm dependencies
echo [1/1] Installing frontend dependencies...
echo This may take a few minutes...
call npm install

if errorlevel 1 (
    echo [ERROR] Failed to install frontend dependencies!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Frontend setup completed!

REM ===================================================================
REM ENVIRONMENT CONFIGURATION
REM ===================================================================

echo.
echo ========================================
echo ENVIRONMENT CONFIGURATION
echo ========================================
echo.

cd /d "%~dp0backend"

REM Check if .env exists
if exist ".env" (
    echo [INFO] .env file already exists
    echo If you need to update configuration, edit backend\.env manually
) else (
    echo [WARNING] .env file not found!
    if exist ".env.production" (
        echo Creating .env from .env.production template...
        copy .env.production .env
        echo [INFO] Please edit backend\.env to configure your settings
    )
)

REM ===================================================================
REM COMPLETION
REM ===================================================================

echo.
echo ========================================
echo SETUP COMPLETE!
echo ========================================
echo.
echo Next steps:
echo   1. Ensure PostgreSQL is installed and running
echo   2. Edit backend\.env to configure database and settings
echo   3. Run start-backend.bat to start the backend server
echo   4. Run start-frontend-prod.bat to build and serve frontend
echo.
echo For more information, see DEPLOYMENT-GUIDE.md
echo.
pause
