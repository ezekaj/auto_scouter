# 🪟 Auto Scouter Windows 10 Production Setup

## 🚀 Quick Start Options

### Option 1: Windows Services (Recommended)
Best for: Permanent server setup, automatic startup, Windows integration

### Option 2: Docker (Alternative)
Best for: Easy deployment, isolated environment, cross-platform consistency

---

## 🔧 Option 1: Windows Services Setup

### Prerequisites
1. **Python 3.8+** installed from [python.org](https://python.org)
   - ✅ Check "Add Python to PATH" during installation
2. **Git** (optional, for updates)

### Step 1: Initial Setup
```cmd
# Open Command Prompt as Administrator
# Navigate to your Auto Scouter directory
cd C:\path\to\auto-scouter\backend

# Run the setup script
deploy\windows\setup-windows.bat
```

### Step 2: Install Windows Services
```cmd
# Run as Administrator
deploy\windows\install-windows-services.bat
```

This will:
- ✅ Download and install NSSM (service manager)
- ✅ Create 3 Windows services:
  - `AutoScouterAPI` - FastAPI backend server
  - `AutoScouterWorker` - Background job processor
  - `AutoScouterBeat` - Task scheduler
- ✅ Configure automatic startup
- ✅ Set up logging

### Step 3: Manage Services
```cmd
# Use the management script
deploy\windows\manage-windows-services.bat

# Or use Windows Services Manager
services.msc
```

### Service Management Commands
```cmd
# Start all services
deploy\windows\manage-windows-services.bat start

# Stop all services
deploy\windows\manage-windows-services.bat stop

# Check status
deploy\windows\manage-windows-services.bat status

# View logs
deploy\windows\manage-windows-services.bat logs

# Health check
deploy\windows\manage-windows-services.bat health
```

---

## 🐳 Option 2: Docker Setup

### Prerequisites
1. **Docker Desktop for Windows** from [docker.com](https://docker.com)
2. **PowerShell** (included with Windows 10)

### Step 1: Setup with Docker
```powershell
# Open PowerShell as Administrator
# Navigate to backend directory
cd C:\path\to\auto-scouter\backend

# Run Docker setup
PowerShell -ExecutionPolicy Bypass -File deploy\windows\docker-setup.ps1 -Action setup
```

### Step 2: Manage Docker Services
```powershell
# Start services
PowerShell -File deploy\windows\docker-setup.ps1 -Action start

# Stop services
PowerShell -File deploy\windows\docker-setup.ps1 -Action stop

# Check status
PowerShell -File deploy\windows\docker-setup.ps1 -Action status

# View logs
PowerShell -File deploy\windows\docker-setup.ps1 -Action logs
```

---

## 🌐 Client Access Configuration

### Local Network Access
After setup, clients can access Auto Scouter at:

**Windows Services:**
- `http://YOUR_PC_IP:8000/` - Web interface
- `http://YOUR_PC_IP:8000/docs` - API documentation

**Docker:**
- `http://YOUR_PC_IP:8000/` - Web interface (via Nginx)
- `http://YOUR_PC_IP:8000/docs` - API documentation

### Find Your PC's IP Address
```cmd
ipconfig | findstr "IPv4"
```

### Windows Firewall Configuration
```cmd
# Open Command Prompt as Administrator

# Allow Auto Scouter through firewall
netsh advfirewall firewall add rule name="Auto Scouter API" dir=in action=allow protocol=TCP localport=8000

# For Docker (if using Nginx)
netsh advfirewall firewall add rule name="Auto Scouter HTTP" dir=in action=allow protocol=TCP localport=80
netsh advfirewall firewall add rule name="Auto Scouter HTTPS" dir=in action=allow protocol=TCP localport=443
```

### Router Configuration (For Internet Access)
1. **Port Forwarding:**
   - Forward external port 8000 → internal port 8000 (your PC's IP)
   - Or ports 80/443 if using Docker with Nginx

2. **Dynamic DNS** (optional):
   - Use services like DuckDNS, No-IP for domain name

---

## 🔧 Service Management

### Windows Services (Option 1)

**Using Management Script:**
```cmd
# Interactive menu
deploy\windows\manage-windows-services.bat

# Command line
deploy\windows\manage-windows-services.bat start
deploy\windows\manage-windows-services.bat stop
deploy\windows\manage-windows-services.bat status
```

**Using Windows Services Manager:**
1. Press `Win + R`, type `services.msc`
2. Look for services starting with "AutoScouter"
3. Right-click to Start/Stop/Restart

**Using Command Line:**
```cmd
# Start services
net start AutoScouterAPI
net start AutoScouterWorker
net start AutoScouterBeat

# Stop services
net stop AutoScouterBeat
net stop AutoScouterWorker
net stop AutoScouterAPI
```

### Docker Services (Option 2)

**Using PowerShell Script:**
```powershell
# All operations
PowerShell -File deploy\windows\docker-setup.ps1 -Action [start|stop|restart|status|logs]
```

**Using Docker Compose:**
```cmd
# Start all services
docker-compose -f docker-compose.windows.yml up -d

# Stop all services
docker-compose -f docker-compose.windows.yml down

# View status
docker-compose -f docker-compose.windows.yml ps

# View logs
docker-compose -f docker-compose.windows.yml logs -f
```

---

## 📊 Monitoring & Logs

### Log Locations

**Windows Services:**
- API: `backend\logs\api-stdout.log`
- Worker: `backend\logs\worker-stdout.log`
- Beat: `backend\logs\beat-stdout.log`

**Docker:**
- Use: `docker-compose -f docker-compose.windows.yml logs`
- Or: PowerShell script logs command

### Health Checks
```cmd
# Test API health
curl http://localhost:8000/health

# Or open in browser
start http://localhost:8000/health
```

### Performance Monitoring
- **Task Manager**: Monitor CPU/Memory usage
- **Resource Monitor**: Detailed system monitoring
- **Windows Performance Monitor**: Advanced metrics

---

## 🔒 Security & Network

### Windows Defender Firewall
Auto Scouter should be automatically allowed, but if blocked:
1. Open Windows Defender Firewall
2. Click "Allow an app or feature through Windows Defender Firewall"
3. Add Python.exe or Docker Desktop

### Network Security
- **Local Network**: Generally safe, Windows firewall provides protection
- **Internet Access**: Consider VPN or proper authentication for production

### User Account Control (UAC)
- Services run under system account (secure)
- Management scripts may require Administrator privileges

---

## 🚨 Troubleshooting

### Common Issues

**"Python not found":**
- Reinstall Python with "Add to PATH" checked
- Or add Python to PATH manually

**"Permission denied":**
- Run Command Prompt as Administrator
- Check Windows Defender isn't blocking files

**"Port 8000 already in use":**
```cmd
# Find what's using the port
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F
```

**Services won't start:**
- Check logs in `backend\logs\` directory
- Verify Python virtual environment exists
- Run `deploy\windows\setup-windows.bat` again

**Docker issues:**
- Ensure Docker Desktop is running
- Check Docker has enough resources allocated
- Restart Docker Desktop

### Getting Help
1. Check logs first
2. Run health check: `manage-windows-services.bat health`
3. Verify all prerequisites are installed
4. Try restarting services

---

## 🎉 Success!

Once set up, Auto Scouter will:
- ✅ Start automatically when Windows boots
- ✅ Run in the background (no terminal windows needed)
- ✅ Be accessible to clients on your network
- ✅ Scrape vehicle data every 5 minutes
- ✅ Send real-time alerts
- ✅ Restart automatically if it crashes

**Your clients can now access Auto Scouter from any device on your network using a web browser!**

### Access URLs:
- **Local**: `http://localhost:8000`
- **Network**: `http://YOUR_PC_IP:8000`
- **API Docs**: `http://YOUR_PC_IP:8000/docs`
- **Health**: `http://YOUR_PC_IP:8000/health`
