#!/usr/bin/env python3
"""
Production Deployment Script

This script prepares and deploys the Auto Scouter application for production.
"""

import os
import sys
import subprocess
import shutil
import time
from pathlib import Path
from datetime import datetime

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)

def print_step(step, description):
    """Print a formatted step"""
    print(f"\n📋 Step {step}: {description}")
    print("-" * 40)

def run_command(command, description, check=True):
    """Run a command with error handling"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"   {e.stderr.strip()}")
        return False

def check_prerequisites():
    """Check if all prerequisites are installed"""
    print("🔍 Checking prerequisites...")
    
    prerequisites = [
        ("python3", "Python 3.8+"),
        ("pip", "Python package manager"),
        ("redis-server", "Redis server"),
        ("postgresql", "PostgreSQL database"),
        ("nginx", "Nginx web server"),
        ("systemctl", "Systemd service manager")
    ]
    
    all_good = True
    for command, description in prerequisites:
        if shutil.which(command):
            print(f"✅ {description}: Found")
        else:
            print(f"❌ {description}: Not found")
            all_good = False
    
    return all_good

def setup_environment():
    """Set up production environment"""
    print("🌍 Setting up production environment...")
    
    # Copy production environment file
    if Path(".env.production").exists():
        shutil.copy(".env.production", ".env")
        print("✅ Production environment file copied")
    else:
        print("⚠️  .env.production not found, using defaults")
    
    # Create necessary directories
    directories = [
        "/var/log/auto_scouter",
        "/var/lib/auto_scouter",
        "/etc/auto_scouter"
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        except PermissionError:
            print(f"⚠️  Need sudo to create: {directory}")

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    commands = [
        ("pip install --upgrade pip", "Upgrading pip"),
        ("pip install -r requirements.txt", "Installing requirements"),
        ("pip install gunicorn", "Installing Gunicorn WSGI server"),
        ("pip install supervisor", "Installing Supervisor process manager")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def setup_database():
    """Set up production database"""
    print("🗄️  Setting up database...")
    
    # Create database tables
    if not run_command("python create_db.py", "Creating database tables"):
        return False
    
    # Run any migrations
    if Path("alembic").exists():
        if not run_command("alembic upgrade head", "Running database migrations"):
            return False
    
    return True

def create_systemd_services():
    """Create systemd service files"""
    print("⚙️ Creating systemd services...")
    
    # FastAPI service
    fastapi_service = """[Unit]
Description=Auto Scouter FastAPI Application
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/auto_scouter/backend
Environment=PATH=/opt/auto_scouter/venv/bin
ExecStart=/opt/auto_scouter/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    # Celery worker service
    celery_service = """[Unit]
Description=Auto Scouter Celery Worker
After=network.target redis.service postgresql.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/auto_scouter/backend
Environment=PATH=/opt/auto_scouter/venv/bin
ExecStart=/opt/auto_scouter/venv/bin/celery -A app.core.celery_app worker --loglevel=info
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    # Celery beat service
    celery_beat_service = """[Unit]
Description=Auto Scouter Celery Beat Scheduler
After=network.target redis.service postgresql.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/auto_scouter/backend
Environment=PATH=/opt/auto_scouter/venv/bin
ExecStart=/opt/auto_scouter/venv/bin/celery -A app.core.celery_app beat --loglevel=info
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    services = [
        ("auto-scouter-api.service", fastapi_service),
        ("auto-scouter-worker.service", celery_service),
        ("auto-scouter-beat.service", celery_beat_service)
    ]
    
    for service_name, service_content in services:
        try:
            with open(f"/etc/systemd/system/{service_name}", "w") as f:
                f.write(service_content)
            print(f"✅ Created service: {service_name}")
        except PermissionError:
            print(f"⚠️  Need sudo to create service: {service_name}")
    
    # Reload systemd
    run_command("systemctl daemon-reload", "Reloading systemd", check=False)

def create_nginx_config():
    """Create Nginx configuration"""
    print("🌐 Creating Nginx configuration...")
    
    nginx_config = """server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL configuration (update with your certificates)
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Frontend static files
    location / {
        root /opt/auto_scouter/frontend/dist;
        try_files $uri $uri/ /index.html;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000;
        access_log off;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    location /api/ {
        limit_req zone=api burst=20 nodelay;
    }
}
"""
    
    try:
        with open("/etc/nginx/sites-available/auto-scouter", "w") as f:
            f.write(nginx_config)
        print("✅ Created Nginx configuration")
        
        # Enable the site
        run_command("ln -sf /etc/nginx/sites-available/auto-scouter /etc/nginx/sites-enabled/", 
                   "Enabling Nginx site", check=False)
        
    except PermissionError:
        print("⚠️  Need sudo to create Nginx configuration")

def run_tests():
    """Run production readiness tests"""
    print("🧪 Running production readiness tests...")
    
    test_commands = [
        ("python -m pytest tests/ -v", "Running unit tests"),
        ("python test_realtime_alerts.py", "Testing alert system"),
        ("python quick_scraper_test.py", "Testing scraper")
    ]
    
    all_passed = True
    for command, description in test_commands:
        if not run_command(command, description, check=False):
            all_passed = False
    
    return all_passed

def create_backup_script():
    """Create backup script"""
    print("💾 Creating backup script...")
    
    backup_script = """#!/bin/bash
# Auto Scouter Backup Script

BACKUP_DIR="/var/backups/auto_scouter"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="auto_scouter_backup_$DATE.tar.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
pg_dump auto_scouter_prod > $BACKUP_DIR/database_$DATE.sql

# Backup application files
tar -czf $BACKUP_DIR/$BACKUP_FILE /opt/auto_scouter --exclude=node_modules --exclude=__pycache__

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/$BACKUP_FILE"
"""
    
    try:
        with open("/usr/local/bin/auto-scouter-backup", "w") as f:
            f.write(backup_script)
        os.chmod("/usr/local/bin/auto-scouter-backup", 0o755)
        print("✅ Created backup script")
    except PermissionError:
        print("⚠️  Need sudo to create backup script")

def main():
    """Main deployment function"""
    print_header("Auto Scouter Production Deployment")
    
    deployment_steps = [
        (1, "Prerequisites Check", check_prerequisites),
        (2, "Environment Setup", setup_environment),
        (3, "Dependencies Installation", install_dependencies),
        (4, "Database Setup", setup_database),
        (5, "Systemd Services", create_systemd_services),
        (6, "Nginx Configuration", create_nginx_config),
        (7, "Backup Script", create_backup_script),
        (8, "Production Tests", run_tests)
    ]
    
    success_count = 0
    
    for step_num, step_name, step_func in deployment_steps:
        print_step(step_num, step_name)
        
        try:
            if step_func():
                print(f"✅ {step_name} completed successfully")
                success_count += 1
            else:
                print(f"❌ {step_name} failed")
        except Exception as e:
            print(f"❌ {step_name} failed with error: {e}")
    
    # Summary
    print_header("Deployment Summary")
    
    total_steps = len(deployment_steps)
    success_rate = (success_count / total_steps) * 100
    
    print(f"📊 Completed: {success_count}/{total_steps} steps ({success_rate:.1f}%)")
    
    if success_count == total_steps:
        print("🎉 Production deployment completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Update SSL certificates in Nginx configuration")
        print("   2. Update domain names in configuration files")
        print("   3. Start services: systemctl start auto-scouter-*")
        print("   4. Enable services: systemctl enable auto-scouter-*")
        print("   5. Test the application: curl https://your-domain.com/health")
    else:
        print("⚠️  Deployment completed with issues. Please review the failed steps.")
    
    return success_count == total_steps

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
