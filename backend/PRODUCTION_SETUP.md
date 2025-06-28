# 🚀 Auto Scouter Production Server Setup

## Quick Start (One-Command Deployment)

For a complete production deployment on a fresh server:

```bash
# Clone the repository
git clone https://github.com/your-org/auto-scouter.git
cd auto-scouter

# Run the complete deployment script
sudo bash backend/deploy/deploy-complete.sh your-domain.com

# That's it! 🎉
```

## Manual Step-by-Step Setup

If you prefer to run each step manually:

### 1. System Installation
```bash
sudo bash backend/deploy/install-production.sh
```

### 2. Network Configuration
```bash
sudo bash backend/deploy/configure-network.sh your-domain.com
```

### 3. Service Management
```bash
# Start all services
sudo bash backend/deploy/manage-services.sh start

# Check status
sudo bash backend/deploy/manage-services.sh status

# View logs
sudo bash backend/deploy/manage-services.sh logs
```

## 🖥️ Client Access Configuration

### For Local Network Access

After deployment, clients can access Auto Scouter at:

- **Web Interface**: `https://YOUR_SERVER_IP/`
- **API**: `https://YOUR_SERVER_IP/api/v1/`
- **Documentation**: `https://YOUR_SERVER_IP/docs`

### For Internet Access

1. **Port Forwarding** (Router Configuration):
   ```
   External Port 80  → Internal Port 80  (HTTP)
   External Port 443 → Internal Port 443 (HTTPS)
   ```

2. **Dynamic DNS** (Optional):
   - Set up DDNS service (DuckDNS, No-IP, etc.)
   - Point domain to your public IP

3. **Firewall Configuration**:
   ```bash
   # Allow external access
   sudo ufw allow from any to any port 80
   sudo ufw allow from any to any port 443
   ```

## 🔧 Service Management Commands

### Systemd Commands
```bash
# Start all Auto Scouter services
sudo systemctl start auto-scouter.target

# Stop all services
sudo systemctl stop auto-scouter.target

# Restart all services
sudo systemctl restart auto-scouter.target

# Check status
sudo systemctl status auto-scouter.target

# Enable auto-start on boot
sudo systemctl enable auto-scouter.target
```

### Individual Service Management
```bash
# API Server
sudo systemctl [start|stop|restart|status] auto-scouter-api

# Background Workers
sudo systemctl [start|stop|restart|status] auto-scouter-worker

# Task Scheduler
sudo systemctl [start|stop|restart|status] auto-scouter-beat

# Nginx Proxy
sudo systemctl [start|stop|restart|status] nginx
```

### Management Script
```bash
# Use the provided management script
cd /opt/auto-scouter/deploy

# Start all services
sudo ./manage-services.sh start

# Check status
./manage-services.sh status

# View logs
./manage-services.sh logs

# Health check
./manage-services.sh health

# Follow specific service logs
./manage-services.sh logs api
./manage-services.sh logs worker
./manage-services.sh logs beat
```

## 📊 Monitoring & Health Checks

### Built-in Health Endpoints
```bash
# Basic health check
curl https://your-server/health

# Detailed health information
curl https://your-server/health/detailed

# System metrics
curl https://your-server/api/v1/monitoring/system/metrics
```

### Log Locations
```
Application Logs:    /var/log/auto-scouter/
Nginx Logs:         /var/log/nginx/
System Logs:        journalctl -u auto-scouter-*
```

### Monitoring Script
```bash
# Manual monitoring check
sudo /usr/local/bin/auto-scouter-monitor

# View monitoring logs
tail -f /var/log/auto-scouter/monitor.log
```

## 🌐 Network Configuration

### Firewall Ports
```
22   - SSH (administration)
80   - HTTP (redirects to HTTPS)
443  - HTTPS (main web interface)
8000 - Direct API access (optional)
```

### Client Network Requirements
- Clients must be able to reach the server IP
- No special client-side configuration needed
- Modern web browser with JavaScript enabled
- WebSocket support for real-time features

## 🔒 Security Configuration

### SSL/TLS Certificates

**Development/Testing** (Self-signed - already configured):
```bash
# Certificate location
/etc/ssl/auto-scouter/auto-scouter.crt
/etc/ssl/auto-scouter/auto-scouter.key
```

**Production** (Replace with proper certificate):
```bash
# 1. Obtain certificate from CA (Let's Encrypt, etc.)
# 2. Replace files in /etc/ssl/auto-scouter/
# 3. Restart nginx
sudo systemctl restart nginx
```

### Database Security
```bash
# Change default password
sudo -u postgres psql
ALTER USER autoscouter PASSWORD 'your_secure_password';

# Update in configuration
sudo nano /opt/auto-scouter/.env
# Update DATABASE_URL with new password
```

## 🔄 Backup & Maintenance

### Database Backup
```bash
# Manual backup
sudo -u postgres pg_dump auto_scouter_prod > backup.sql

# Automated backup (already configured)
sudo /usr/local/bin/auto-scouter-backup
```

### Application Updates
```bash
# Stop services
sudo systemctl stop auto-scouter.target

# Update code
cd /opt/auto-scouter
git pull origin main

# Install new dependencies
sudo -u autoscouter ./venv/bin/pip install -r requirements.txt

# Run migrations (if any)
sudo -u autoscouter ./venv/bin/python create_db.py

# Start services
sudo systemctl start auto-scouter.target
```

### Log Rotation
Log rotation is automatically configured for:
- Application logs (30 days retention)
- Nginx logs (30 days retention)
- System logs (managed by systemd)

## 🚨 Troubleshooting

### Common Issues

**Services not starting:**
```bash
# Check service status
sudo systemctl status auto-scouter-api
sudo systemctl status auto-scouter-worker
sudo systemctl status auto-scouter-beat

# Check logs
sudo journalctl -u auto-scouter-api -f
```

**API not accessible:**
```bash
# Check if API is running
curl http://localhost:8000/health

# Check nginx configuration
sudo nginx -t
sudo systemctl status nginx
```

**Database connection issues:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
sudo -u postgres psql -c "SELECT 1;"
```

**Redis connection issues:**
```bash
# Check Redis status
sudo systemctl status redis-server

# Test connection
redis-cli ping
```

### Performance Tuning

**For high-traffic environments:**
```bash
# Increase worker processes
sudo nano /etc/systemd/system/auto-scouter-worker.service
# Modify --concurrency parameter

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart auto-scouter-worker
```

**Database optimization:**
```bash
# Monitor database performance
sudo -u postgres psql auto_scouter_prod
SELECT * FROM pg_stat_activity;
```

## 📞 Support

### Log Analysis
```bash
# View all Auto Scouter logs
sudo journalctl -u auto-scouter-* --since "1 hour ago"

# Follow logs in real-time
sudo journalctl -u auto-scouter-api -f

# Check system resources
htop
df -h
free -h
```

### Health Check Commands
```bash
# Quick health check
curl -s https://your-server/health | jq

# Detailed system status
curl -s https://your-server/health/detailed | jq

# Service status
sudo systemctl is-active auto-scouter.target
```

---

## 🎉 Success!

Once deployed, Auto Scouter will be:
- ✅ Running as background services
- ✅ Automatically starting on server boot
- ✅ Accessible to clients on your network
- ✅ Scraping vehicle data every 5 minutes
- ✅ Sending real-time alerts
- ✅ Monitoring system health
- ✅ Logging all activities

Your clients can now access the Auto Scouter application from any device on your network using a web browser!
