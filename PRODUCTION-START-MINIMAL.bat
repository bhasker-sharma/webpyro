@echo off
REM ===================================================================
REM PRODUCTION STARTUP (MINIMAL) - Web Pyrometer Monitoring System
REM ===================================================================
REM This version uses Python's built-in HTTP server to serve frontend
REM ADVANTAGE: No Node.js needed on production server!
REM REQUIREMENT: Only Python and PostgreSQL needed
REM ===================================================================

title Web Pyrometer Production Server (Minimal)

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

REM Start backend in a new window
echo [1/2] Starting Backend Server...
start "Backend Server - DO NOT CLOSE" /min cmd /c "cd /d "%~dp0backend" && call venv\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8000 --log-level warning"

REM Wait for backend to start
timeout /t 5 /nobreak >nul

REM Start frontend with Python's HTTP server (no Node.js needed!)
echo [2/2] Starting Frontend Server (Python HTTP Server)...
start "Frontend Server - DO NOT CLOSE" /min cmd /c "cd /d "%~dp0frontend\dist" && python -m http.server 5173 --bind 0.0.0.0"

REM Wait for frontend to start
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo SYSTEM IS NOW RUNNING
echo ========================================
echo.
echo Access the application from any computer on your network:
echo.
echo   http://%SERVER_IP%:5173
echo   or
echo   http://localhost:5173 (from this computer)
echo.
echo Two windows opened in background:
echo   - Backend Server (port 8000)
echo   - Frontend Server (port 5173) [Python HTTP Server]
echo.
echo BENEFITS OF THIS VERSION:
echo   - No Node.js required on server
echo   - Smaller deployment package
echo   - Simpler dependencies
echo.
echo To stop the system:
echo   - Close both "Backend Server" and "Frontend Server" windows
echo   OR
echo   - Run PRODUCTION-STOP.bat
echo.
echo ========================================
echo.
pause
