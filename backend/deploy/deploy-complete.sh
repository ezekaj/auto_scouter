#!/bin/bash
# Complete Auto Scouter Production Deployment Script
# This is the master deployment script that orchestrates the entire setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DOMAIN_NAME="${1:-auto-scouter.local}"
ENVIRONMENT="${2:-production}"

print_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║                🚀 AUTO SCOUTER DEPLOYMENT 🚀                ║"
    echo "║                                                              ║"
    echo "║              Production-Ready Server Setup                  ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}\n"
}

print_header() {
    echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║ $1${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}\n"
}

print_step() {
    echo -e "${BLUE}📋 Phase $1: $2${NC}"
    echo -e "${BLUE}$(printf '─%.0s' {1..60})${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

check_prerequisites() {
    print_step "1" "Checking Prerequisites"
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
    
    # Check if in correct directory
    if [[ ! -f "$PROJECT_ROOT/backend/app/main.py" ]]; then
        print_error "Please run this script from the auto-scouter project root directory"
        print_info "Current directory: $(pwd)"
        print_info "Expected backend/app/main.py to exist"
        exit 1
    fi
    
    # Check internet connectivity
    if ! ping -c 1 google.com &> /dev/null; then
        print_warning "No internet connectivity detected. Some steps may fail."
    fi
    
    print_success "Prerequisites check completed"
    echo ""
}

show_deployment_plan() {
    print_header "DEPLOYMENT PLAN"
    
    echo -e "${YELLOW}📋 Deployment Configuration:${NC}"
    echo "   Domain Name: $DOMAIN_NAME"
    echo "   Environment: $ENVIRONMENT"
    echo "   Project Root: $PROJECT_ROOT"
    echo "   Server IP: $(hostname -I | awk '{print $1}')"
    echo ""
    
    echo -e "${YELLOW}🔧 Components to Deploy:${NC}"
    echo "   ✓ PostgreSQL Database"
    echo "   ✓ Redis Cache & Message Broker"
    echo "   ✓ FastAPI Backend Application"
    echo "   ✓ Celery Background Workers"
    echo "   ✓ Celery Beat Scheduler"
    echo "   ✓ Nginx Reverse Proxy"
    echo "   ✓ SSL/TLS Certificates"
    echo "   ✓ Systemd Services"
    echo "   ✓ Firewall Configuration"
    echo "   ✓ Monitoring & Health Checks"
    echo ""
    
    echo -e "${YELLOW}📊 Deployment Phases:${NC}"
    echo "   Phase 1: Prerequisites Check"
    echo "   Phase 2: System Dependencies Installation"
    echo "   Phase 3: Application Installation"
    echo "   Phase 4: Network Configuration"
    echo "   Phase 5: Service Setup & Start"
    echo "   Phase 6: Verification & Testing"
    echo ""
    
    read -p "Continue with deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 0
    fi
}

run_system_installation() {
    print_step "2" "System Dependencies Installation"
    
    print_info "Running system installation script..."
    
    # Make scripts executable
    chmod +x "$SCRIPT_DIR/install-production.sh"
    
    # Run the installation script
    if bash "$SCRIPT_DIR/install-production.sh"; then
        print_success "System installation completed successfully"
    else
        print_error "System installation failed"
        exit 1
    fi
    
    echo ""
}

run_network_configuration() {
    print_step "3" "Network Configuration"
    
    print_info "Configuring network access and SSL..."
    
    # Make script executable
    chmod +x "$SCRIPT_DIR/configure-network.sh"
    
    # Run network configuration
    if bash "$SCRIPT_DIR/configure-network.sh" "$DOMAIN_NAME"; then
        print_success "Network configuration completed successfully"
    else
        print_error "Network configuration failed"
        exit 1
    fi
    
    echo ""
}

setup_monitoring() {
    print_step "4" "Monitoring & Health Checks Setup"
    
    print_info "Setting up monitoring and health checks..."
    
    # Create monitoring script
    cat > /usr/local/bin/auto-scouter-monitor << 'EOF'
#!/bin/bash
# Auto Scouter Monitoring Script

LOG_FILE="/var/log/auto-scouter/monitor.log"
ALERT_EMAIL="admin@example.com"  # Configure this

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

check_service() {
    local service=$1
    if systemctl is-active "$service" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

check_api_health() {
    if curl -f -s http://localhost:8000/health >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

main() {
    # Check all services
    services=("auto-scouter-api" "auto-scouter-worker" "auto-scouter-beat" "nginx" "postgresql" "redis-server")
    
    for service in "${services[@]}"; do
        if check_service "$service"; then
            log_message "✅ $service is running"
        else
            log_message "❌ $service is not running - attempting restart"
            systemctl restart "$service" || log_message "Failed to restart $service"
        fi
    done
    
    # Check API health
    if check_api_health; then
        log_message "✅ API health check passed"
    else
        log_message "❌ API health check failed"
    fi
    
    # Check disk space
    disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 90 ]]; then
        log_message "⚠️ Disk usage is high: ${disk_usage}%"
    fi
    
    # Check memory usage
    memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [[ $memory_usage -gt 90 ]]; then
        log_message "⚠️ Memory usage is high: ${memory_usage}%"
    fi
}

main "$@"
EOF
    
    chmod +x /usr/local/bin/auto-scouter-monitor
    
    # Create monitoring cron job
    cat > /etc/cron.d/auto-scouter-monitor << EOF
# Auto Scouter Monitoring - runs every 5 minutes
*/5 * * * * root /usr/local/bin/auto-scouter-monitor
EOF
    
    print_success "Monitoring setup completed"
    echo ""
}

run_verification() {
    print_step "5" "Deployment Verification"
    
    print_info "Running comprehensive verification tests..."
    
    # Wait for services to fully start
    sleep 10
    
    # Test results
    tests_passed=0
    total_tests=0
    
    # Test 1: Service Status
    echo "🔍 Testing service status..."
    services=("auto-scouter-api" "auto-scouter-worker" "auto-scouter-beat" "nginx")
    for service in "${services[@]}"; do
        ((total_tests++))
        if systemctl is-active "$service" >/dev/null 2>&1; then
            echo "  ✅ $service: Running"
            ((tests_passed++))
        else
            echo "  ❌ $service: Not running"
        fi
    done
    
    # Test 2: API Health
    echo -e "\n🌐 Testing API endpoints..."
    endpoints=("http://localhost:8000/health" "http://localhost/health" "https://localhost/health")
    for endpoint in "${endpoints[@]}"; do
        ((total_tests++))
        if curl -f -s -k "$endpoint" >/dev/null 2>&1; then
            echo "  ✅ $endpoint: Accessible"
            ((tests_passed++))
        else
            echo "  ❌ $endpoint: Not accessible"
        fi
    done
    
    # Test 3: Database Connection
    echo -e "\n🗄️ Testing database connection..."
    ((total_tests++))
    if sudo -u autoscouter /opt/auto-scouter/venv/bin/python -c "
import sys
sys.path.append('/opt/auto-scouter')
from app.models.base import engine
try:
    engine.connect()
    print('Database connection successful')
    exit(0)
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" 2>/dev/null; then
        echo "  ✅ Database: Connected"
        ((tests_passed++))
    else
        echo "  ❌ Database: Connection failed"
    fi
    
    # Test 4: Redis Connection
    echo -e "\n📦 Testing Redis connection..."
    ((total_tests++))
    if redis-cli ping >/dev/null 2>&1; then
        echo "  ✅ Redis: Connected"
        ((tests_passed++))
    else
        echo "  ❌ Redis: Connection failed"
    fi
    
    # Test 5: Celery Workers
    echo -e "\n⚙️ Testing Celery workers..."
    ((total_tests++))
    if sudo -u autoscouter /opt/auto-scouter/venv/bin/celery --app=app.core.celery_app inspect ping >/dev/null 2>&1; then
        echo "  ✅ Celery workers: Responding"
        ((tests_passed++))
    else
        echo "  ❌ Celery workers: Not responding"
    fi
    
    # Calculate success rate
    success_rate=$((tests_passed * 100 / total_tests))
    
    echo -e "\n📊 Verification Results:"
    echo "========================"
    echo "Tests Passed: $tests_passed/$total_tests"
    echo "Success Rate: $success_rate%"
    
    if [[ $success_rate -ge 80 ]]; then
        print_success "Deployment verification passed!"
        return 0
    else
        print_error "Deployment verification failed. Please check the issues above."
        return 1
    fi
}

show_deployment_summary() {
    local server_ip=$(hostname -I | awk '{print $1}')
    
    print_header "DEPLOYMENT COMPLETE!"
    
    echo -e "${GREEN}🎉 Auto Scouter has been successfully deployed!${NC}\n"
    
    echo -e "${CYAN}📊 Deployment Summary:${NC}"
    echo "   Server IP: $server_ip"
    echo "   Domain: $DOMAIN_NAME"
    echo "   Environment: $ENVIRONMENT"
    echo "   SSL: Self-signed certificate (replace for production)"
    echo ""
    
    echo -e "${CYAN}🌐 Access Points:${NC}"
    echo "   Web Interface: https://$server_ip/ or https://$DOMAIN_NAME/"
    echo "   API Endpoint:  https://$server_ip/api/v1/ or https://$DOMAIN_NAME/api/v1/"
    echo "   API Docs:      https://$server_ip/docs or https://$DOMAIN_NAME/docs"
    echo "   Health Check:  https://$server_ip/health or https://$DOMAIN_NAME/health"
    echo ""
    
    echo -e "${CYAN}🔧 Service Management:${NC}"
    echo "   Start all:     sudo systemctl start auto-scouter.target"
    echo "   Stop all:      sudo systemctl stop auto-scouter.target"
    echo "   Restart all:   sudo systemctl restart auto-scouter.target"
    echo "   Check status:  sudo systemctl status auto-scouter.target"
    echo "   View logs:     sudo journalctl -u auto-scouter-api -f"
    echo ""
    
    echo -e "${CYAN}📁 Important Paths:${NC}"
    echo "   Application:   /opt/auto-scouter/"
    echo "   Logs:          /var/log/auto-scouter/"
    echo "   Configuration: /opt/auto-scouter/.env"
    echo "   SSL Certs:     /etc/ssl/auto-scouter/"
    echo ""
    
    echo -e "${CYAN}🛠️ Management Scripts:${NC}"
    echo "   Service control: /opt/auto-scouter/deploy/manage-services.sh"
    echo "   Monitoring:      /usr/local/bin/auto-scouter-monitor"
    echo ""
    
    echo -e "${YELLOW}⚠️ Next Steps:${NC}"
    echo "   1. Replace self-signed SSL certificate with proper certificate"
    echo "   2. Update database password in /opt/auto-scouter/.env"
    echo "   3. Configure email settings for notifications"
    echo "   4. Set up external monitoring (optional)"
    echo "   5. Configure backup strategy"
    echo ""
    
    echo -e "${GREEN}✅ Auto Scouter is now running and accessible to clients!${NC}"
}

main() {
    print_banner
    
    check_prerequisites
    show_deployment_plan
    run_system_installation
    run_network_configuration
    setup_monitoring
    
    if run_verification; then
        show_deployment_summary
        exit 0
    else
        print_error "Deployment completed with issues. Please review the verification results."
        exit 1
    fi
}

# Show usage if help requested
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Auto Scouter Complete Production Deployment"
    echo "==========================================="
    echo ""
    echo "Usage: $0 [domain-name] [environment]"
    echo ""
    echo "Parameters:"
    echo "  domain-name   Domain name for the server (default: auto-scouter.local)"
    echo "  environment   Deployment environment (default: production)"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Default settings"
    echo "  $0 auto-scouter.company.com         # Custom domain"
    echo "  $0 192.168.1.100 production         # IP address with environment"
    echo ""
    echo "This script will:"
    echo "  - Install all system dependencies"
    echo "  - Set up PostgreSQL and Redis"
    echo "  - Deploy Auto Scouter application"
    echo "  - Configure Nginx reverse proxy"
    echo "  - Set up SSL certificates"
    echo "  - Configure firewall"
    echo "  - Create systemd services"
    echo "  - Set up monitoring"
    echo "  - Verify the deployment"
    echo ""
    echo "Requirements:"
    echo "  - Ubuntu 18.04+ or CentOS 7+"
    echo "  - Root privileges (run with sudo)"
    echo "  - Internet connectivity"
    echo "  - At least 4GB RAM and 20GB disk space"
    echo ""
    exit 0
fi

# Run main function
main "$@"
