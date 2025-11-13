@echo off
REM ===================================================================
REM PRODUCTION STARTUP - Web Pyrometer Monitoring System
REM ===================================================================
REM This is the ONLY file you need to run for production
REM Starts both backend and frontend servers
REM ===================================================================

title Web Pyrometer Production Server

echo ========================================
echo Web Pyrometer Production Server
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

REM Start backend in a new window
echo [1/2] Starting Backend Server...
start "Backend Server - DO NOT CLOSE" /min cmd /c "cd /d "%~dp0backend" && call venv\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8000 --log-level warning"

REM Wait for backend to start
timeout /t 5 /nobreak >nul

REM Start frontend preview server in a new window
echo [2/2] Starting Frontend Server...
start "Frontend Server - DO NOT CLOSE" /min cmd /c "cd /d "%~dp0frontend" && npm run preview -- --host 0.0.0.0 --port 5173"

REM Wait for frontend to start
timeout /t 5 /nobreak >nul

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
echo   - Frontend Server (port 5173)
echo.
echo To stop the system:
echo   - Close both "Backend Server" and "Frontend Server" windows
echo   OR
echo   - Run PRODUCTION-STOP.bat
echo.
echo ========================================
echo.
pause
