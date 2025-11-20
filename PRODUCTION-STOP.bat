@echo off
REM ===================================================================
REM STOP SERVERS - Web Pyrometer Monitoring System
REM ===================================================================
REM Stops all services (backend and frontend)
REM Works for both Development and Production mode
REM ===================================================================

title Stop Web Pyrometer Servers

echo ========================================
echo Stopping Web Pyrometer Services
echo ========================================
echo.

REM Kill backend processes (executable or Python)
echo [1/2] Stopping Backend Server...
taskkill /FI "WINDOWTITLE eq Backend Server*" /T /F >nul 2>&1
taskkill /F /IM webpyro_backend.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Backend*" >nul 2>&1

REM Kill frontend server processes (Python HTTP or Node.js)
echo [2/2] Stopping Frontend Server...
taskkill /FI "WINDOWTITLE eq Frontend Server*" /T /F >nul 2>&1
taskkill /F /IM node.exe /FI "WINDOWTITLE eq *Frontend*" >nul 2>&1

echo.
echo ========================================
echo All services stopped
echo ========================================
echo.
echo You can now start the system again:
echo   DEV-START.bat (for development mode)
echo   PRODUCTION-START-MINIMAL.bat (for production)
echo.
pause
