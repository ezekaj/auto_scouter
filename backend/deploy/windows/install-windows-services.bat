@echo off
REM Auto Scouter Windows Service Installation Script
REM Run as Administrator

echo ========================================
echo    Auto Scouter Windows Setup
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Set variables
set "PROJECT_DIR=%~dp0..\.."
set "PYTHON_PATH=%PROJECT_DIR%\venv\Scripts\python.exe"
set "NSSM_URL=https://nssm.cc/release/nssm-2.24.zip"
set "NSSM_DIR=%PROJECT_DIR%\tools\nssm"

echo Project Directory: %PROJECT_DIR%
echo Python Path: %PYTHON_PATH%
echo.

REM Check if Python virtual environment exists
if not exist "%PYTHON_PATH%" (
    echo ERROR: Python virtual environment not found
    echo Please run setup-windows.bat first
    pause
    exit /b 1
)

REM Create tools directory
if not exist "%PROJECT_DIR%\tools" mkdir "%PROJECT_DIR%\tools"

REM Download and extract NSSM if not exists
if not exist "%NSSM_DIR%\win64\nssm.exe" (
    echo Downloading NSSM...
    powershell -Command "& {Invoke-WebRequest -Uri '%NSSM_URL%' -OutFile '%PROJECT_DIR%\tools\nssm.zip'}"
    
    echo Extracting NSSM...
    powershell -Command "& {Expand-Archive -Path '%PROJECT_DIR%\tools\nssm.zip' -DestinationPath '%PROJECT_DIR%\tools' -Force}"
    
    REM Move NSSM to correct location
    move "%PROJECT_DIR%\tools\nssm-2.24" "%NSSM_DIR%"
    del "%PROJECT_DIR%\tools\nssm.zip"
)

set "NSSM_EXE=%NSSM_DIR%\win64\nssm.exe"

echo Installing Auto Scouter Windows Services...
echo.

REM Stop existing services if they exist
echo Stopping existing services...
"%NSSM_EXE%" stop "AutoScouterAPI" >nul 2>&1
"%NSSM_EXE%" stop "AutoScouterWorker" >nul 2>&1
"%NSSM_EXE%" stop "AutoScouterBeat" >nul 2>&1

REM Remove existing services
echo Removing existing services...
"%NSSM_EXE%" remove "AutoScouterAPI" confirm >nul 2>&1
"%NSSM_EXE%" remove "AutoScouterWorker" confirm >nul 2>&1
"%NSSM_EXE%" remove "AutoScouterBeat" confirm >nul 2>&1

REM Install Auto Scouter API Service
echo Installing Auto Scouter API Service...
"%NSSM_EXE%" install "AutoScouterAPI" "%PYTHON_PATH%" "-m" "uvicorn" "app.main:app" "--host" "0.0.0.0" "--port" "8000" "--reload"
"%NSSM_EXE%" set "AutoScouterAPI" AppDirectory "%PROJECT_DIR%"
"%NSSM_EXE%" set "AutoScouterAPI" DisplayName "Auto Scouter API Server"
"%NSSM_EXE%" set "AutoScouterAPI" Description "Auto Scouter FastAPI Backend Server"
"%NSSM_EXE%" set "AutoScouterAPI" Start SERVICE_AUTO_START
"%NSSM_EXE%" set "AutoScouterAPI" AppStdout "%PROJECT_DIR%\logs\api-stdout.log"
"%NSSM_EXE%" set "AutoScouterAPI" AppStderr "%PROJECT_DIR%\logs\api-stderr.log"
"%NSSM_EXE%" set "AutoScouterAPI" AppRotateFiles 1
"%NSSM_EXE%" set "AutoScouterAPI" AppRotateOnline 1
"%NSSM_EXE%" set "AutoScouterAPI" AppRotateBytes 10485760

REM Install Auto Scouter Worker Service
echo Installing Auto Scouter Worker Service...
"%NSSM_EXE%" install "AutoScouterWorker" "%PYTHON_PATH%" "-m" "celery" "-A" "app.core.celery_app" "worker" "--loglevel=info" "--concurrency=4"
"%NSSM_EXE%" set "AutoScouterWorker" AppDirectory "%PROJECT_DIR%"
"%NSSM_EXE%" set "AutoScouterWorker" DisplayName "Auto Scouter Background Worker"
"%NSSM_EXE%" set "AutoScouterWorker" Description "Auto Scouter Celery Background Worker"
"%NSSM_EXE%" set "AutoScouterWorker" Start SERVICE_AUTO_START
"%NSSM_EXE%" set "AutoScouterWorker" AppStdout "%PROJECT_DIR%\logs\worker-stdout.log"
"%NSSM_EXE%" set "AutoScouterWorker" AppStderr "%PROJECT_DIR%\logs\worker-stderr.log"
"%NSSM_EXE%" set "AutoScouterWorker" AppRotateFiles 1
"%NSSM_EXE%" set "AutoScouterWorker" AppRotateOnline 1
"%NSSM_EXE%" set "AutoScouterWorker" AppRotateBytes 10485760

REM Install Auto Scouter Beat Service
echo Installing Auto Scouter Beat Service...
"%NSSM_EXE%" install "AutoScouterBeat" "%PYTHON_PATH%" "-m" "celery" "-A" "app.core.celery_app" "beat" "--loglevel=info"
"%NSSM_EXE%" set "AutoScouterBeat" AppDirectory "%PROJECT_DIR%"
"%NSSM_EXE%" set "AutoScouterBeat" DisplayName "Auto Scouter Task Scheduler"
"%NSSM_EXE%" set "AutoScouterBeat" Description "Auto Scouter Celery Beat Task Scheduler"
"%NSSM_EXE%" set "AutoScouterBeat" Start SERVICE_AUTO_START
"%NSSM_EXE%" set "AutoScouterBeat" AppStdout "%PROJECT_DIR%\logs\beat-stdout.log"
"%NSSM_EXE%" set "AutoScouterBeat" AppStderr "%PROJECT_DIR%\logs\beat-stderr.log"
"%NSSM_EXE%" set "AutoScouterBeat" AppRotateFiles 1
"%NSSM_EXE%" set "AutoScouterBeat" AppRotateOnline 1
"%NSSM_EXE%" set "AutoScouterBeat" AppRotateBytes 10485760

REM Create logs directory
if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"

REM Start services
echo Starting Auto Scouter services...
"%NSSM_EXE%" start "AutoScouterAPI"
timeout /t 5 /nobreak >nul
"%NSSM_EXE%" start "AutoScouterWorker"
timeout /t 3 /nobreak >nul
"%NSSM_EXE%" start "AutoScouterBeat"

echo.
echo ========================================
echo    Installation Complete!
echo ========================================
echo.
echo Services installed:
echo   - AutoScouterAPI (FastAPI Server)
echo   - AutoScouterWorker (Background Jobs)
echo   - AutoScouterBeat (Task Scheduler)
echo.
echo Access Auto Scouter at:
echo   http://localhost:8000
echo   http://YOUR_IP_ADDRESS:8000
echo.
echo Service Management:
echo   - Use manage-windows-services.bat
echo   - Or Windows Services Manager (services.msc)
echo.
echo Logs location: %PROJECT_DIR%\logs\
echo.
pause
