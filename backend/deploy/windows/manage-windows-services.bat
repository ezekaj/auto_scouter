@echo off
REM Auto Scouter Windows Service Management Script

setlocal enabledelayedexpansion

echo ========================================
echo    Auto Scouter Service Manager
echo ========================================
echo.

set "PROJECT_DIR=%~dp0..\.."
set "NSSM_EXE=%PROJECT_DIR%\tools\nssm\win64\nssm.exe"

REM Check if NSSM exists
if not exist "%NSSM_EXE%" (
    echo ERROR: NSSM not found. Please run install-windows-services.bat first.
    pause
    exit /b 1
)

if "%1"=="" goto :show_menu

REM Handle command line arguments
if /i "%1"=="start" goto :start_services
if /i "%1"=="stop" goto :stop_services
if /i "%1"=="restart" goto :restart_services
if /i "%1"=="status" goto :show_status
if /i "%1"=="logs" goto :show_logs
if /i "%1"=="health" goto :health_check
goto :show_usage

:show_menu
echo Select an option:
echo.
echo 1. Start all services
echo 2. Stop all services
echo 3. Restart all services
echo 4. Show service status
echo 5. View logs
echo 6. Health check
echo 7. Open Windows Services Manager
echo 8. Exit
echo.
set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto :start_services
if "%choice%"=="2" goto :stop_services
if "%choice%"=="3" goto :restart_services
if "%choice%"=="4" goto :show_status
if "%choice%"=="5" goto :show_logs
if "%choice%"=="6" goto :health_check
if "%choice%"=="7" goto :open_services_manager
if "%choice%"=="8" goto :exit
goto :show_menu

:start_services
echo Starting Auto Scouter services...
echo.
"%NSSM_EXE%" start "AutoScouterAPI"
if %errorlevel% equ 0 (echo ✓ AutoScouterAPI started) else (echo ✗ AutoScouterAPI failed to start)

timeout /t 3 /nobreak >nul

"%NSSM_EXE%" start "AutoScouterWorker"
if %errorlevel% equ 0 (echo ✓ AutoScouterWorker started) else (echo ✗ AutoScouterWorker failed to start)

timeout /t 2 /nobreak >nul

"%NSSM_EXE%" start "AutoScouterBeat"
if %errorlevel% equ 0 (echo ✓ AutoScouterBeat started) else (echo ✗ AutoScouterBeat failed to start)

echo.
echo All services start commands sent.
timeout /t 5 /nobreak >nul
goto :show_status

:stop_services
echo Stopping Auto Scouter services...
echo.
"%NSSM_EXE%" stop "AutoScouterBeat"
if %errorlevel% equ 0 (echo ✓ AutoScouterBeat stopped) else (echo ✗ AutoScouterBeat failed to stop)

"%NSSM_EXE%" stop "AutoScouterWorker"
if %errorlevel% equ 0 (echo ✓ AutoScouterWorker stopped) else (echo ✗ AutoScouterWorker failed to stop)

"%NSSM_EXE%" stop "AutoScouterAPI"
if %errorlevel% equ 0 (echo ✓ AutoScouterAPI stopped) else (echo ✗ AutoScouterAPI failed to stop)

echo.
echo All services stop commands sent.
if "%1"=="" pause
goto :eof

:restart_services
echo Restarting Auto Scouter services...
call :stop_services silent
timeout /t 3 /nobreak >nul
call :start_services
goto :eof

:show_status
echo Auto Scouter Service Status:
echo ============================
echo.

REM Check API service
sc query "AutoScouterAPI" | find "STATE" | find "RUNNING" >nul
if %errorlevel% equ 0 (
    echo ✓ AutoScouterAPI: Running
) else (
    echo ✗ AutoScouterAPI: Stopped
)

REM Check Worker service
sc query "AutoScouterWorker" | find "STATE" | find "RUNNING" >nul
if %errorlevel% equ 0 (
    echo ✓ AutoScouterWorker: Running
) else (
    echo ✗ AutoScouterWorker: Stopped
)

REM Check Beat service
sc query "AutoScouterBeat" | find "STATE" | find "RUNNING" >nul
if %errorlevel% equ 0 (
    echo ✓ AutoScouterBeat: Running
) else (
    echo ✗ AutoScouterBeat: Stopped
)

echo.
echo Detailed Status:
echo ================
sc query "AutoScouterAPI" | findstr "STATE DISPLAY_NAME"
sc query "AutoScouterWorker" | findstr "STATE DISPLAY_NAME"
sc query "AutoScouterBeat" | findstr "STATE DISPLAY_NAME"

if "%1"=="" (
    echo.
    pause
)
goto :eof

:show_logs
echo Auto Scouter Logs:
echo ==================
echo.
echo Log files location: %PROJECT_DIR%\logs\
echo.
echo Available log files:
if exist "%PROJECT_DIR%\logs\api-stdout.log" echo   - api-stdout.log
if exist "%PROJECT_DIR%\logs\api-stderr.log" echo   - api-stderr.log
if exist "%PROJECT_DIR%\logs\worker-stdout.log" echo   - worker-stdout.log
if exist "%PROJECT_DIR%\logs\worker-stderr.log" echo   - worker-stderr.log
if exist "%PROJECT_DIR%\logs\beat-stdout.log" echo   - beat-stdout.log
if exist "%PROJECT_DIR%\logs\beat-stderr.log" echo   - beat-stderr.log
echo.

set /p log_choice="Which log to view? (api/worker/beat/all): "

if /i "%log_choice%"=="api" (
    echo.
    echo === API Service Logs ===
    if exist "%PROJECT_DIR%\logs\api-stdout.log" (
        echo --- STDOUT ---
        type "%PROJECT_DIR%\logs\api-stdout.log" | more
    )
    if exist "%PROJECT_DIR%\logs\api-stderr.log" (
        echo --- STDERR ---
        type "%PROJECT_DIR%\logs\api-stderr.log" | more
    )
) else if /i "%log_choice%"=="worker" (
    echo.
    echo === Worker Service Logs ===
    if exist "%PROJECT_DIR%\logs\worker-stdout.log" (
        echo --- STDOUT ---
        type "%PROJECT_DIR%\logs\worker-stdout.log" | more
    )
    if exist "%PROJECT_DIR%\logs\worker-stderr.log" (
        echo --- STDERR ---
        type "%PROJECT_DIR%\logs\worker-stderr.log" | more
    )
) else if /i "%log_choice%"=="beat" (
    echo.
    echo === Beat Service Logs ===
    if exist "%PROJECT_DIR%\logs\beat-stdout.log" (
        echo --- STDOUT ---
        type "%PROJECT_DIR%\logs\beat-stdout.log" | more
    )
    if exist "%PROJECT_DIR%\logs\beat-stderr.log" (
        echo --- STDERR ---
        type "%PROJECT_DIR%\logs\beat-stderr.log" | more
    )
) else if /i "%log_choice%"=="all" (
    echo.
    echo Opening logs folder...
    explorer "%PROJECT_DIR%\logs"
)

if "%1"=="" pause
goto :eof

:health_check
echo Auto Scouter Health Check:
echo ==========================
echo.

REM Check if API is responding
echo Testing API health endpoint...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ API Health Check: PASSED
    curl -s http://localhost:8000/health
) else (
    echo ✗ API Health Check: FAILED
    echo   API is not responding on http://localhost:8000
)

echo.
echo Network Information:
echo ====================
echo Server IP addresses:
ipconfig | findstr "IPv4"

echo.
echo Access URLs:
echo   Local:    http://localhost:8000
echo   Network:  http://YOUR_IP:8000
echo   Docs:     http://localhost:8000/docs
echo   Health:   http://localhost:8000/health

if "%1"=="" pause
goto :eof

:open_services_manager
echo Opening Windows Services Manager...
services.msc
goto :eof

:show_usage
echo Usage: %0 [command]
echo.
echo Commands:
echo   start    - Start all Auto Scouter services
echo   stop     - Stop all Auto Scouter services
echo   restart  - Restart all Auto Scouter services
echo   status   - Show service status
echo   logs     - View service logs
echo   health   - Perform health check
echo.
echo Examples:
echo   %0 start
echo   %0 status
echo   %0 health
echo.
goto :eof

:exit
echo Goodbye!
goto :eof
