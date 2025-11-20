@echo off
REM ===================================================================
REM CREATE DEPLOYMENT PACKAGE - Web Pyrometer
REM ===================================================================
REM This script creates a clean deployment package ready for production
REM ===================================================================

title Creating Deployment Package

echo ========================================
echo Web Pyrometer Deployment Packager
echo ========================================
echo.

REM Navigate to project directory
cd /d "%~dp0"

REM Set deployment folder name
set DEPLOY_FOLDER=WebPyrometer_Production
set TIMESTAMP=%date:~-4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%
set TIMESTAMP=%TIMESTAMP: =0%
set DEPLOY_PATH=%~dp0..\%DEPLOY_FOLDER%_%TIMESTAMP%

echo Creating deployment package at:
echo %DEPLOY_PATH%
echo.

REM Check prerequisites
echo [1/6] Checking prerequisites...
if not exist "backend\dist\webpyro_backend\webpyro_backend.exe" (
    echo [ERROR] Backend executable not found!
    echo Please build it first: cd backend ^&^& build.bat
    pause
    exit /b 1
)

if not exist "frontend\dist\index.html" (
    echo [ERROR] Frontend build not found!
    echo Please build it first: cd frontend ^&^& npm run build
    pause
    exit /b 1
)

echo [2/6] Creating deployment folder structure...
mkdir "%DEPLOY_PATH%" 2>nul
mkdir "%DEPLOY_PATH%\backend\dist" 2>nul
mkdir "%DEPLOY_PATH%\frontend" 2>nul

echo [3/6] Copying backend files...
xcopy "backend\dist\webpyro_backend" "%DEPLOY_PATH%\backend\dist\webpyro_backend\" /E /I /Y /Q

echo [4/6] Copying frontend files...
xcopy "frontend\dist" "%DEPLOY_PATH%\frontend\dist\" /E /I /Y /Q

echo [5/6] Copying startup scripts...
copy "PRODUCTION-START-MINIMAL.bat" "%DEPLOY_PATH%\" /Y >nul
copy "PRODUCTION-STOP.bat" "%DEPLOY_PATH%\" /Y >nul

echo [6/6] Copying documentation...
copy "PRODUCTION_README.txt" "%DEPLOY_PATH%\" /Y >nul
copy "USER_GUIDE.txt" "%DEPLOY_PATH%\" /Y >nul 2>nul

echo.
echo ========================================
echo DEPLOYMENT PACKAGE CREATED!
echo ========================================
echo.
echo Location: %DEPLOY_PATH%
echo.
echo Next steps:
echo 1. Review the .env files in backend\dist\webpyro_backend\
echo 2. Update database connection for production
echo 3. Copy the entire folder to production machine
echo 4. Run PRODUCTION-START-MINIMAL.bat as administrator
echo.
echo For full instructions, see README.md in the package
echo.
echo ========================================
echo.

REM Open the deployment folder
explorer "%DEPLOY_PATH%"

pause
