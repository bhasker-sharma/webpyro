@echo off
REM ===================================================================
REM Backend Build Script - Creates standalone executable
REM ===================================================================

title Building Backend Executable

echo ========================================
echo Web Pyrometer Backend Builder
echo ========================================
echo.

REM Navigate to backend directory
cd /d "%~dp0"

REM Activate virtual environment
echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat

REM Clean previous builds
echo [2/3] Cleaning previous builds...
if exist "dist\webpyro_backend" rmdir /s /q "dist\webpyro_backend"
if exist "build" rmdir /s /q "build"

REM Build executable using PyInstaller
echo [3/3] Building executable (this may take a few minutes)...
pyinstaller build_backend.spec --clean

echo.
if exist "dist\webpyro_backend\webpyro_backend.exe" (
    echo ========================================
    echo BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Executable created at:
    echo   %~dp0dist\webpyro_backend\
    echo.
    echo Main executable:
    echo   webpyro_backend.exe
    echo.
) else (
    echo ========================================
    echo BUILD FAILED!
    echo ========================================
    echo.
    echo Please check the error messages above.
    echo.
)

pause
