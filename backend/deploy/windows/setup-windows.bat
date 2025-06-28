@echo off
REM Auto Scouter Windows Setup Script
REM This script sets up the complete Auto Scouter environment on Windows

echo ========================================
echo    Auto Scouter Windows Setup
echo ========================================
echo.

set "PROJECT_DIR=%~dp0..\.."
set "BACKEND_DIR=%PROJECT_DIR%"

echo Project Directory: %PROJECT_DIR%
echo Backend Directory: %BACKEND_DIR%
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo ✓ Python is installed
python --version

REM Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: pip is not available
    echo Please reinstall Python with pip included
    pause
    exit /b 1
)

echo ✓ pip is available

REM Create virtual environment if it doesn't exist
if not exist "%BACKEND_DIR%\venv" (
    echo Creating Python virtual environment...
    cd /d "%BACKEND_DIR%"
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

REM Activate virtual environment and install dependencies
echo Installing Python dependencies...
cd /d "%BACKEND_DIR%"
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install requirements
if exist "requirements.txt" (
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install requirements
        pause
        exit /b 1
    )
    echo ✓ Requirements installed
) else (
    echo ERROR: requirements.txt not found
    pause
    exit /b 1
)

REM Install additional Windows-specific packages
pip install uvicorn[standard]
pip install psutil

REM Check if Redis is needed (for background jobs)
echo.
echo Checking Redis availability...
redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Redis is not running
    echo.
    echo For full functionality, you need Redis for background jobs.
    echo Options:
    echo   1. Install Redis for Windows
    echo   2. Use Docker: docker run -d -p 6379:6379 redis:alpine
    echo   3. Use WSL with Redis
    echo   4. Continue without background jobs (limited functionality)
    echo.
    set /p redis_choice="Continue anyway? (y/N): "
    if /i not "!redis_choice!"=="y" (
        echo Setup cancelled. Please install Redis and run again.
        pause
        exit /b 1
    )
) else (
    echo ✓ Redis is available
)

REM Create database
echo.
echo Setting up database...
python create_db.py
if %errorlevel% neq 0 (
    echo WARNING: Database setup failed, but continuing...
) else (
    echo ✓ Database setup completed
)

REM Create logs directory
if not exist "%PROJECT_DIR%\logs" (
    mkdir "%PROJECT_DIR%\logs"
    echo ✓ Logs directory created
)

REM Test the application
echo.
echo Testing Auto Scouter application...
timeout /t 2 /nobreak >nul

REM Quick test import
python -c "from app.main import app; print('✓ Auto Scouter imports successfully')" 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Application import test failed
) else (
    echo ✓ Application import test passed
)

echo.
echo ========================================
echo    Setup Complete!
echo ========================================
echo.
echo Next steps:
echo.
echo 1. Install as Windows Services (recommended):
echo    Run: backend\deploy\windows\install-windows-services.bat
echo.
echo 2. Or run manually for testing:
echo    cd backend
echo    venv\Scripts\activate
echo    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
echo.
echo 3. Access Auto Scouter:
echo    http://localhost:8000
echo    http://localhost:8000/docs (API documentation)
echo.
echo 4. For client access from other machines:
echo    http://YOUR_IP_ADDRESS:8000
echo.
echo Service Management:
echo   Use: backend\deploy\windows\manage-windows-services.bat
echo.
pause
