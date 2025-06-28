# Auto Scouter Docker Setup for Windows
# Run with: PowerShell -ExecutionPolicy Bypass -File docker-setup.ps1

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("setup", "start", "stop", "restart", "status", "logs", "cleanup")]
    [string]$Action = "setup"
)

# Colors for output
$Red = [System.ConsoleColor]::Red
$Green = [System.ConsoleColor]::Green
$Yellow = [System.ConsoleColor]::Yellow
$Blue = [System.ConsoleColor]::Blue

function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    } else {
        $input | Write-Output
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Header($Message) {
    Write-Host ""
    Write-ColorOutput $Blue "========================================"
    Write-ColorOutput $Blue "🚀 $Message"
    Write-ColorOutput $Blue "========================================"
    Write-Host ""
}

function Write-Step($Step, $Message) {
    Write-ColorOutput $Blue "📋 Step $Step`: $Message"
}

function Write-Success($Message) {
    Write-ColorOutput $Green "✅ $Message"
}

function Write-Error($Message) {
    Write-ColorOutput $Red "❌ $Message"
}

function Write-Warning($Message) {
    Write-ColorOutput $Yellow "⚠️  $Message"
}

function Test-DockerInstalled {
    try {
        $dockerVersion = docker --version 2>$null
        if ($dockerVersion) {
            Write-Success "Docker is installed: $dockerVersion"
            return $true
        }
    } catch {
        Write-Error "Docker is not installed or not accessible"
        return $false
    }
    return $false
}

function Test-DockerComposeInstalled {
    try {
        $composeVersion = docker-compose --version 2>$null
        if ($composeVersion) {
            Write-Success "Docker Compose is installed: $composeVersion"
            return $true
        }
    } catch {
        Write-Error "Docker Compose is not installed or not accessible"
        return $false
    }
    return $false
}

function Setup-AutoScouter {
    Write-Header "Auto Scouter Docker Setup"
    
    # Check prerequisites
    Write-Step 1 "Checking prerequisites"
    
    if (-not (Test-DockerInstalled)) {
        Write-Error "Please install Docker Desktop for Windows from https://docker.com"
        return $false
    }
    
    if (-not (Test-DockerComposeInstalled)) {
        Write-Error "Please install Docker Compose"
        return $false
    }
    
    # Check if Docker is running
    try {
        docker ps >$null 2>&1
        Write-Success "Docker daemon is running"
    } catch {
        Write-Error "Docker daemon is not running. Please start Docker Desktop."
        return $false
    }
    
    # Navigate to backend directory
    $backendDir = Split-Path -Parent $PSScriptRoot
    $backendDir = Split-Path -Parent $backendDir
    Set-Location $backendDir
    
    Write-Step 2 "Setting up environment"
    
    # Create .env file if it doesn't exist
    if (-not (Test-Path ".env")) {
        Write-Host "Creating .env file..."
        @"
# Auto Scouter Docker Environment
PROJECT_NAME=Auto Scouter
VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql://autoscouter:auto_scouter_secure_password@postgres:5432/auto_scouter_prod
SQLITE_FALLBACK=false

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Security
SECRET_KEY=$((New-Guid).Guid.Replace('-',''))
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=*
ALLOWED_METHODS=GET,POST,PUT,DELETE,OPTIONS
ALLOWED_HEADERS=*

# Scraping
SCRAPING_ENABLED=true
SCRAPING_INTERVAL_HOURS=0.083
SCRAPING_MAX_VEHICLES_PER_RUN=100
"@ | Out-File -FilePath ".env" -Encoding UTF8
        Write-Success "Environment file created"
    } else {
        Write-Success "Environment file already exists"
    }
    
    # Create logs directory
    if (-not (Test-Path "logs")) {
        New-Item -ItemType Directory -Path "logs" | Out-Null
        Write-Success "Logs directory created"
    }
    
    Write-Step 3 "Building and starting containers"
    
    # Build and start containers
    try {
        docker-compose -f docker-compose.windows.yml up -d --build
        Write-Success "Containers started successfully"
    } catch {
        Write-Error "Failed to start containers"
        return $false
    }
    
    Write-Step 4 "Waiting for services to start"
    Start-Sleep -Seconds 10
    
    # Test API health
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 30
        Write-Success "API health check passed"
    } catch {
        Write-Warning "API health check failed, but containers are running"
    }
    
    Write-Header "Setup Complete!"
    Write-Host ""
    Write-Success "Auto Scouter is now running in Docker containers!"
    Write-Host ""
    Write-Host "Access points:"
    Write-Host "  Web Interface: http://localhost:8000"
    Write-Host "  API Documentation: http://localhost:8000/docs"
    Write-Host "  Health Check: http://localhost:8000/health"
    Write-Host ""
    Write-Host "Management commands:"
    Write-Host "  Start:   PowerShell -File docker-setup.ps1 -Action start"
    Write-Host "  Stop:    PowerShell -File docker-setup.ps1 -Action stop"
    Write-Host "  Status:  PowerShell -File docker-setup.ps1 -Action status"
    Write-Host "  Logs:    PowerShell -File docker-setup.ps1 -Action logs"
    Write-Host ""
    
    return $true
}

function Start-AutoScouter {
    Write-Header "Starting Auto Scouter"
    
    $backendDir = Split-Path -Parent $PSScriptRoot
    $backendDir = Split-Path -Parent $backendDir
    Set-Location $backendDir
    
    try {
        docker-compose -f docker-compose.windows.yml up -d
        Write-Success "Auto Scouter started"
        Show-Status
    } catch {
        Write-Error "Failed to start Auto Scouter"
    }
}

function Stop-AutoScouter {
    Write-Header "Stopping Auto Scouter"
    
    $backendDir = Split-Path -Parent $PSScriptRoot
    $backendDir = Split-Path -Parent $backendDir
    Set-Location $backendDir
    
    try {
        docker-compose -f docker-compose.windows.yml down
        Write-Success "Auto Scouter stopped"
    } catch {
        Write-Error "Failed to stop Auto Scouter"
    }
}

function Restart-AutoScouter {
    Write-Header "Restarting Auto Scouter"
    Stop-AutoScouter
    Start-Sleep -Seconds 3
    Start-AutoScouter
}

function Show-Status {
    Write-Header "Auto Scouter Status"
    
    $backendDir = Split-Path -Parent $PSScriptRoot
    $backendDir = Split-Path -Parent $backendDir
    Set-Location $backendDir
    
    try {
        docker-compose -f docker-compose.windows.yml ps
        
        Write-Host ""
        Write-Host "Container Health:"
        $containers = @("auto-scouter-api", "auto-scouter-worker", "auto-scouter-beat", "auto-scouter-redis", "auto-scouter-postgres")
        
        foreach ($container in $containers) {
            $status = docker inspect --format='{{.State.Status}}' $container 2>$null
            if ($status -eq "running") {
                Write-Success "$container`: Running"
            } else {
                Write-Error "$container`: $status"
            }
        }
        
        Write-Host ""
        Write-Host "Network Access:"
        $ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*" -and $_.InterfaceAlias -notlike "*Docker*"} | Select-Object -First 1).IPAddress
        Write-Host "  Local: http://localhost:8000"
        Write-Host "  Network: http://$ip`:8000"
        
    } catch {
        Write-Error "Failed to get status"
    }
}

function Show-Logs {
    Write-Header "Auto Scouter Logs"
    
    $backendDir = Split-Path -Parent $PSScriptRoot
    $backendDir = Split-Path -Parent $backendDir
    Set-Location $backendDir
    
    Write-Host "Select service to view logs:"
    Write-Host "1. API Server"
    Write-Host "2. Worker"
    Write-Host "3. Beat Scheduler"
    Write-Host "4. All services"
    
    $choice = Read-Host "Enter choice (1-4)"
    
    switch ($choice) {
        "1" { docker-compose -f docker-compose.windows.yml logs -f auto-scouter-api }
        "2" { docker-compose -f docker-compose.windows.yml logs -f auto-scouter-worker }
        "3" { docker-compose -f docker-compose.windows.yml logs -f auto-scouter-beat }
        "4" { docker-compose -f docker-compose.windows.yml logs -f }
        default { docker-compose -f docker-compose.windows.yml logs --tail=50 }
    }
}

function Cleanup-AutoScouter {
    Write-Header "Cleaning up Auto Scouter"
    
    $backendDir = Split-Path -Parent $PSScriptRoot
    $backendDir = Split-Path -Parent $backendDir
    Set-Location $backendDir
    
    Write-Warning "This will remove all containers and volumes. Data will be lost!"
    $confirm = Read-Host "Are you sure? (y/N)"
    
    if ($confirm -eq "y" -or $confirm -eq "Y") {
        try {
            docker-compose -f docker-compose.windows.yml down -v --remove-orphans
            docker system prune -f
            Write-Success "Cleanup completed"
        } catch {
            Write-Error "Cleanup failed"
        }
    } else {
        Write-Host "Cleanup cancelled"
    }
}

# Main execution
switch ($Action) {
    "setup" { Setup-AutoScouter }
    "start" { Start-AutoScouter }
    "stop" { Stop-AutoScouter }
    "restart" { Restart-AutoScouter }
    "status" { Show-Status }
    "logs" { Show-Logs }
    "cleanup" { Cleanup-AutoScouter }
    default { 
        Write-Host "Usage: PowerShell -File docker-setup.ps1 -Action [setup|start|stop|restart|status|logs|cleanup]"
        Write-Host ""
        Write-Host "Actions:"
        Write-Host "  setup   - Initial setup and start"
        Write-Host "  start   - Start all services"
        Write-Host "  stop    - Stop all services"
        Write-Host "  restart - Restart all services"
        Write-Host "  status  - Show service status"
        Write-Host "  logs    - View service logs"
        Write-Host "  cleanup - Remove all containers and data"
    }
}
