@echo off
REM ===================================================================
REM Windows Firewall Configuration Script
REM ===================================================================
REM This script configures Windows Firewall to allow network access
REM to the Web Pyrometer Monitoring System
REM
REM IMPORTANT: This script requires ADMINISTRATOR privileges
REM Right-click and select "Run as Administrator"
REM ===================================================================

echo ========================================
echo Firewall Configuration
echo ========================================
echo.

REM Check for administrator privileges
net session >nul 2>&1
if errorlevel 1 (
    echo [ERROR] This script requires administrator privileges!
    echo Please right-click and select "Run as Administrator"
    echo.
    pause
    exit /b 1
)

echo This script will configure Windows Firewall to allow:
echo   - Port 8000 (Backend API Server)
echo   - Port 80 (Frontend Web Server - Production)
echo   - Port 5173 (Frontend Web Server - Development)
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul

echo.
echo [1/3] Configuring firewall rule for Backend (Port 8000)...
netsh advfirewall firewall add rule name="Web Pyrometer Backend" dir=in action=allow protocol=TCP localport=8000 profile=private,domain

echo [2/3] Configuring firewall rule for Frontend Port 80...
netsh advfirewall firewall add rule name="Web Pyrometer Frontend (Port 80)" dir=in action=allow protocol=TCP localport=80 profile=private,domain

echo [3/3] Configuring firewall rule for Frontend Port 5173...
netsh advfirewall firewall add rule name="Web Pyrometer Frontend (Port 5173)" dir=in action=allow protocol=TCP localport=5173 profile=private,domain

echo.
echo ========================================
echo Firewall configuration complete!
echo ========================================
echo.
echo The following rules have been added:
echo   - Web Pyrometer Backend (TCP Port 8000)
echo   - Web Pyrometer Frontend Port 80 (Production)
echo   - Web Pyrometer Frontend Port 5173 (Development)
echo.
echo You can now access the application from other computers
echo on your local network using your server's IP address.
echo.
echo To find your IP address, run: ipconfig
echo Look for "IPv4 Address" under your active network adapter
echo.
pause
