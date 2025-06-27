# Auto Scouter Development Startup Script
# This script starts both frontend and backend services

Write-Host "🚀 Starting Auto Scouter Development Environment" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path "frontend") -or -not (Test-Path "backend")) {
    Write-Host "❌ Please run this script from the auto_scouter root directory" -ForegroundColor Red
    exit 1
}

# Function to start backend
function Start-Backend {
    Write-Host "🔧 Starting Backend (FastAPI)..." -ForegroundColor Yellow
    Set-Location backend
    
    # Create database if it doesn't exist
    if (-not (Test-Path "auto_scouter.db")) {
        Write-Host "📊 Creating database..." -ForegroundColor Cyan
        python create_db.py
    }
    
    # Start backend server
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# Function to start frontend
function Start-Frontend {
    Write-Host "⚛️ Starting Frontend (React + Vite)..." -ForegroundColor Yellow
    Set-Location frontend
    npm run dev
}

# Start both services
Write-Host "🔄 Starting services..." -ForegroundColor Cyan

# Start backend in background
Start-Job -ScriptBlock { 
    Set-Location $using:PWD
    Start-Backend 
} -Name "AutoScouterBackend"

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start frontend in foreground
Start-Frontend

# Cleanup
Write-Host "🧹 Cleaning up background jobs..." -ForegroundColor Yellow
Get-Job -Name "AutoScouterBackend" | Stop-Job
Get-Job -Name "AutoScouterBackend" | Remove-Job

Write-Host "👋 Auto Scouter development environment stopped" -ForegroundColor Green
