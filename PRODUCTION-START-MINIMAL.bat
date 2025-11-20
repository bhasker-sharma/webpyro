@echo off
REM ===================================================================
REM PRODUCTION STARTUP - Web Pyrometer Monitoring System
REM ===================================================================
REM This version uses Python's built-in HTTP server to serve frontend
REM ADVANTAGE: No Node.js needed on production server!
REM REQUIREMENT: Only Python and PostgreSQL needed
REM NOTE: Must run as Administrator to use port 80
REM ===================================================================

REM Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ========================================
    echo ERROR: Administrator Rights Required
    echo ========================================
    echo.
    echo This script must be run as Administrator to use port 80.
    echo Right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

title Web Pyrometer Production Server

echo ========================================
echo Web Pyrometer Production Server
echo MINIMAL VERSION - No Node.js Required
echo ========================================
echo.
echo Starting production services...
echo.

REM Get the server's IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set SERVER_IP=%%a
)
set SERVER_IP=%SERVER_IP:~1%

REM Get computer name
set COMPUTER_NAME=%COMPUTERNAME%

REM Navigate to project directory
cd /d "%~dp0"

REM Check if dist folder exists
if not exist "frontend\dist" (
    echo [ERROR] Frontend build not found!
    echo Please run: cd frontend && npm run build
    echo.
    pause
    exit /b 1
)

REM Start backend - using compiled executable
echo [1/2] Starting Backend Server...
if not exist "%~dp0backend\dist\webpyro_backend\webpyro_backend.exe" (
    echo    [ERROR] Backend executable not found!
    echo    Expected: backend\dist\webpyro_backend\webpyro_backend.exe
    echo.
    echo    Please build the executable first by running:
    echo      backend\build.bat
    echo.
    pause
    exit /b 1
)

echo    Using compiled executable...
echo    Opening backend terminal window...
start "Backend Server - DO NOT CLOSE" cmd /k "cd /d "%~dp0backend\dist\webpyro_backend" && webpyro_backend.exe"

:backend_started

REM Wait for backend to start
timeout /t 5 /nobreak >nul

REM Start frontend with Python's HTTP server on port 80 (no Node.js needed!)
echo [2/2] Starting Frontend Server (Port 80)...
echo    Checking Python availability...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo    [ERROR] Python not found in PATH!
    echo    Please ensure Python is installed and added to PATH.
    pause
    exit /b 1
)
echo    Opening frontend terminal window...
start "Frontend Server - DO NOT CLOSE" cmd /k "cd /d "%~dp0frontend\dist" && echo Starting frontend server on port 80... && python -m http.server 80 --bind 0.0.0.0"

REM Wait for frontend to start
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo SYSTEM IS NOW RUNNING ON PORT 80
echo ========================================
echo.
echo Access from any computer on your network (NO SETUP NEEDED):
echo.
echo   Using Computer Name:  http://%COMPUTER_NAME%
echo   Using IP Address:     http://%SERVER_IP%
echo   From this computer:   http://localhost
echo.
echo ========================================
echo.
echo Two server windows have been opened:
echo   - Backend Server (port 8000)
echo   - Frontend Server (port 80)
echo.
echo IMPORTANT: Keep both server windows open!
echo To stop: Run PRODUCTION-STOP.bat or close both windows
echo.
echo This launcher window can now be closed (press any key).
echo.
echo ========================================
echo.
pause
