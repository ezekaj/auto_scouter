#!/bin/bash
# Auto Scouter Production Installation Script
# Run with: sudo bash install-production.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_USER="autoscouter"
APP_GROUP="autoscouter"
APP_DIR="/opt/auto-scouter"
LOG_DIR="/var/log/auto-scouter"
RUN_DIR="/var/run/auto-scouter"
LIB_DIR="/var/lib/auto-scouter"
BACKUP_DIR="/var/backups/auto-scouter"

print_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}🚀 $1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

print_step() {
    echo -e "${GREEN}📋 Step $1: $2${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_os() {
    if [[ ! -f /etc/os-release ]]; then
        print_error "Cannot determine OS version"
        exit 1
    fi
    
    . /etc/os-release
    if [[ "$ID" != "ubuntu" ]] && [[ "$ID" != "debian" ]] && [[ "$ID" != "centos" ]] && [[ "$ID" != "rhel" ]]; then
        print_warning "This script is designed for Ubuntu/Debian/CentOS/RHEL"
        print_warning "Continuing anyway, but you may need to adjust package names"
    fi
}

install_dependencies() {
    print_step "1" "Installing system dependencies"
    
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        apt-get update
        apt-get install -y \
            python3 python3-pip python3-venv python3-dev \
            postgresql postgresql-contrib \
            redis-server \
            nginx \
            curl wget git \
            build-essential \
            supervisor \
            logrotate \
            ufw
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        yum update -y
        yum install -y \
            python3 python3-pip python3-devel \
            postgresql postgresql-server postgresql-contrib \
            redis \
            nginx \
            curl wget git \
            gcc gcc-c++ make \
            supervisor \
            logrotate \
            firewalld
    else
        print_error "Unsupported package manager"
        exit 1
    fi
    
    print_success "System dependencies installed"
}

create_user() {
    print_step "2" "Creating application user"
    
    if ! id "$APP_USER" &>/dev/null; then
        useradd -r -s /bin/bash -d "$APP_DIR" -m "$APP_USER"
        print_success "Created user: $APP_USER"
    else
        print_success "User $APP_USER already exists"
    fi
}

create_directories() {
    print_step "3" "Creating application directories"
    
    # Create directories
    mkdir -p "$APP_DIR" "$LOG_DIR" "$RUN_DIR" "$LIB_DIR" "$BACKUP_DIR"
    
    # Set ownership
    chown -R "$APP_USER:$APP_GROUP" "$APP_DIR" "$LOG_DIR" "$RUN_DIR" "$LIB_DIR" "$BACKUP_DIR"
    
    # Set permissions
    chmod 755 "$APP_DIR" "$LOG_DIR" "$LIB_DIR" "$BACKUP_DIR"
    chmod 750 "$RUN_DIR"
    
    print_success "Directories created and configured"
}

setup_database() {
    print_step "4" "Setting up PostgreSQL database"
    
    # Start PostgreSQL
    systemctl enable postgresql
    systemctl start postgresql
    
    # Create database and user
    sudo -u postgres psql -c "CREATE DATABASE auto_scouter_prod;" 2>/dev/null || true
    sudo -u postgres psql -c "CREATE USER $APP_USER WITH PASSWORD 'auto_scouter_secure_password';" 2>/dev/null || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE auto_scouter_prod TO $APP_USER;" 2>/dev/null || true
    sudo -u postgres psql -c "ALTER USER $APP_USER CREATEDB;" 2>/dev/null || true
    
    print_success "PostgreSQL database configured"
}

setup_redis() {
    print_step "5" "Setting up Redis"
    
    # Configure Redis
    sed -i 's/^# maxmemory <bytes>/maxmemory 256mb/' /etc/redis/redis.conf 2>/dev/null || true
    sed -i 's/^# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf 2>/dev/null || true
    
    # Start Redis
    systemctl enable redis-server 2>/dev/null || systemctl enable redis
    systemctl start redis-server 2>/dev/null || systemctl start redis
    
    print_success "Redis configured and started"
}

install_application() {
    print_step "6" "Installing Auto Scouter application"
    
    # Copy application files (assuming they're in current directory)
    if [[ -d "$(pwd)/backend" ]]; then
        cp -r "$(pwd)/backend"/* "$APP_DIR/"
        cp -r "$(pwd)/frontend" "$APP_DIR/" 2>/dev/null || true
    else
        print_error "Backend directory not found. Please run this script from the auto-scouter root directory"
        exit 1
    fi
    
    # Set ownership
    chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"
    
    # Create virtual environment
    sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
    
    # Install Python dependencies
    sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --upgrade pip
    sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"
    sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install gunicorn
    
    print_success "Application installed"
}

configure_environment() {
    print_step "7" "Configuring environment"
    
    # Create production environment file
    cat > "$APP_DIR/.env" << EOF
# Auto Scouter Production Configuration
PROJECT_NAME="Auto Scouter"
VERSION="1.0.0"
ENVIRONMENT="production"
DEBUG=false

# Database
DATABASE_URL="postgresql://$APP_USER:auto_scouter_secure_password@localhost:5432/auto_scouter_prod"
SQLITE_FALLBACK=false

# Redis
REDIS_URL="redis://localhost:6379/0"
CELERY_BROKER_URL="redis://localhost:6379/0"
CELERY_RESULT_BACKEND="redis://localhost:6379/0"

# Security
SECRET_KEY="$(openssl rand -hex 32)"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS="*"
ALLOWED_METHODS="GET,POST,PUT,DELETE,OPTIONS"
ALLOWED_HEADERS="*"

# Scraping
SCRAPING_ENABLED=true
SCRAPING_INTERVAL_HOURS=0.083
SCRAPING_MAX_VEHICLES_PER_RUN=100

# Logging
LOG_LEVEL="INFO"
LOG_FILE_PATH="$LOG_DIR/app.log"
EOF
    
    chown "$APP_USER:$APP_GROUP" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    
    print_success "Environment configured"
}

install_systemd_services() {
    print_step "8" "Installing systemd services"
    
    # Copy service files
    cp "$APP_DIR/deploy/systemd/"*.service /etc/systemd/system/
    cp "$APP_DIR/deploy/systemd/"*.target /etc/systemd/system/
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable services
    systemctl enable auto-scouter-api.service
    systemctl enable auto-scouter-worker.service
    systemctl enable auto-scouter-beat.service
    systemctl enable auto-scouter.target
    
    print_success "Systemd services installed and enabled"
}

setup_database_schema() {
    print_step "9" "Setting up database schema"
    
    # Run database creation script
    sudo -u "$APP_USER" bash -c "cd $APP_DIR && ./venv/bin/python create_db.py"
    
    print_success "Database schema created"
}

configure_firewall() {
    print_step "10" "Configuring firewall"
    
    if command -v ufw &> /dev/null; then
        # Ubuntu/Debian
        ufw --force enable
        ufw allow ssh
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow 8000/tcp  # API port
    elif command -v firewall-cmd &> /dev/null; then
        # CentOS/RHEL
        systemctl enable firewalld
        systemctl start firewalld
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --permanent --add-port=8000/tcp
        firewall-cmd --reload
    fi
    
    print_success "Firewall configured"
}

setup_logging() {
    print_step "11" "Setting up log rotation"
    
    cat > /etc/logrotate.d/auto-scouter << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $APP_USER $APP_GROUP
    postrotate
        systemctl reload auto-scouter-api.service
    endscript
}
EOF
    
    print_success "Log rotation configured"
}

start_services() {
    print_step "12" "Starting Auto Scouter services"
    
    # Start individual services
    systemctl start auto-scouter-api.service
    sleep 5
    systemctl start auto-scouter-worker.service
    sleep 3
    systemctl start auto-scouter-beat.service
    
    # Start the target (manages all services)
    systemctl start auto-scouter.target
    
    print_success "All services started"
}

verify_installation() {
    print_step "13" "Verifying installation"
    
    # Check service status
    echo "Service Status:"
    systemctl is-active auto-scouter-api.service && echo "✅ API Service: Running" || echo "❌ API Service: Failed"
    systemctl is-active auto-scouter-worker.service && echo "✅ Worker Service: Running" || echo "❌ Worker Service: Failed"
    systemctl is-active auto-scouter-beat.service && echo "✅ Beat Service: Running" || echo "❌ Beat Service: Failed"
    
    # Test API endpoint
    sleep 5
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ API Health Check: Passed"
    else
        echo "❌ API Health Check: Failed"
    fi
    
    print_success "Installation verification completed"
}

main() {
    print_header "Auto Scouter Production Installation"
    
    check_root
    check_os
    
    install_dependencies
    create_user
    create_directories
    setup_database
    setup_redis
    install_application
    configure_environment
    install_systemd_services
    setup_database_schema
    configure_firewall
    setup_logging
    start_services
    verify_installation
    
    print_header "Installation Complete!"
    echo -e "${GREEN}🎉 Auto Scouter has been successfully installed!${NC}\n"
    
    echo "📋 Service Management Commands:"
    echo "  Start all services:    sudo systemctl start auto-scouter.target"
    echo "  Stop all services:     sudo systemctl stop auto-scouter.target"
    echo "  Restart all services:  sudo systemctl restart auto-scouter.target"
    echo "  Check status:          sudo systemctl status auto-scouter.target"
    echo ""
    echo "📊 Individual Service Commands:"
    echo "  API:     sudo systemctl [start|stop|restart|status] auto-scouter-api"
    echo "  Worker:  sudo systemctl [start|stop|restart|status] auto-scouter-worker"
    echo "  Beat:    sudo systemctl [start|stop|restart|status] auto-scouter-beat"
    echo ""
    echo "🌐 Access Points:"
    echo "  API:           http://$(hostname -I | awk '{print $1}'):8000"
    echo "  Health Check:  http://$(hostname -I | awk '{print $1}'):8000/health"
    echo "  API Docs:      http://$(hostname -I | awk '{print $1}'):8000/docs"
    echo ""
    echo "📁 Important Paths:"
    echo "  Application:   $APP_DIR"
    echo "  Logs:          $LOG_DIR"
    echo "  Configuration: $APP_DIR/.env"
    echo ""
    echo "⚠️  Next Steps:"
    echo "  1. Update the database password in $APP_DIR/.env"
    echo "  2. Configure SSL certificates for production"
    echo "  3. Set up Nginx reverse proxy (see nginx configuration)"
    echo "  4. Configure monitoring and alerting"
}

# Run main function
main "$@"
