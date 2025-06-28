#!/bin/bash
# Auto Scouter Network Configuration Script
# Configures networking, firewall, and SSL for client access

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN_NAME="${1:-auto-scouter.local}"
SERVER_IP=$(hostname -I | awk '{print $1}')
SSL_DIR="/etc/ssl/auto-scouter"
NGINX_AVAILABLE="/etc/nginx/sites-available"
NGINX_ENABLED="/etc/nginx/sites-enabled"

print_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}🌐 $1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

print_step() {
    echo -e "${GREEN}📋 Step $1: $2${NC}"
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
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

install_nginx() {
    print_step "1" "Installing and configuring Nginx"
    
    # Install Nginx if not present
    if ! command -v nginx &> /dev/null; then
        if command -v apt-get &> /dev/null; then
            apt-get update
            apt-get install -y nginx
        elif command -v yum &> /dev/null; then
            yum install -y nginx
        else
            print_error "Could not install Nginx. Please install manually."
            exit 1
        fi
    fi
    
    # Enable and start Nginx
    systemctl enable nginx
    systemctl start nginx
    
    print_success "Nginx installed and started"
}

generate_ssl_certificate() {
    print_step "2" "Generating SSL certificate"
    
    # Create SSL directory
    mkdir -p "$SSL_DIR"
    
    # Generate self-signed certificate for development/testing
    if [[ ! -f "$SSL_DIR/auto-scouter.crt" ]]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$SSL_DIR/auto-scouter.key" \
            -out "$SSL_DIR/auto-scouter.crt" \
            -subj "/C=US/ST=State/L=City/O=Organization/OU=OrgUnit/CN=$DOMAIN_NAME"
        
        # Set proper permissions
        chmod 600 "$SSL_DIR/auto-scouter.key"
        chmod 644 "$SSL_DIR/auto-scouter.crt"
        
        print_success "Self-signed SSL certificate generated"
        print_warning "For production, replace with a proper SSL certificate from a CA"
    else
        print_success "SSL certificate already exists"
    fi
}

configure_nginx() {
    print_step "3" "Configuring Nginx for Auto Scouter"
    
    # Copy Nginx configuration
    if [[ -f "/opt/auto-scouter/deploy/nginx/auto-scouter.conf" ]]; then
        cp "/opt/auto-scouter/deploy/nginx/auto-scouter.conf" "$NGINX_AVAILABLE/auto-scouter"
        
        # Update SSL certificate paths in configuration
        sed -i "s|/etc/ssl/certs/auto-scouter.crt|$SSL_DIR/auto-scouter.crt|g" "$NGINX_AVAILABLE/auto-scouter"
        sed -i "s|/etc/ssl/private/auto-scouter.key|$SSL_DIR/auto-scouter.key|g" "$NGINX_AVAILABLE/auto-scouter"
        
        # Update server name if provided
        if [[ "$DOMAIN_NAME" != "auto-scouter.local" ]]; then
            sed -i "s/server_name _;/server_name $DOMAIN_NAME;/g" "$NGINX_AVAILABLE/auto-scouter"
        fi
        
        # Enable the site
        ln -sf "$NGINX_AVAILABLE/auto-scouter" "$NGINX_ENABLED/auto-scouter"
        
        # Remove default site if it exists
        rm -f "$NGINX_ENABLED/default"
        
        # Test Nginx configuration
        if nginx -t; then
            print_success "Nginx configuration is valid"
            systemctl reload nginx
            print_success "Nginx reloaded with new configuration"
        else
            print_error "Nginx configuration test failed"
            exit 1
        fi
    else
        print_error "Nginx configuration file not found"
        exit 1
    fi
}

configure_firewall() {
    print_step "4" "Configuring firewall"
    
    if command -v ufw &> /dev/null; then
        # Ubuntu/Debian - UFW
        print_info "Configuring UFW firewall..."
        
        # Enable UFW
        ufw --force enable
        
        # Allow SSH (important!)
        ufw allow ssh
        ufw allow 22/tcp
        
        # Allow HTTP and HTTPS
        ufw allow 80/tcp
        ufw allow 443/tcp
        
        # Allow API port for direct access
        ufw allow 8000/tcp
        
        # Allow development port
        ufw allow 8080/tcp
        
        # Show status
        ufw status verbose
        
        print_success "UFW firewall configured"
        
    elif command -v firewall-cmd &> /dev/null; then
        # CentOS/RHEL - firewalld
        print_info "Configuring firewalld..."
        
        # Enable firewalld
        systemctl enable firewalld
        systemctl start firewalld
        
        # Allow services
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        
        # Allow custom ports
        firewall-cmd --permanent --add-port=8000/tcp
        firewall-cmd --permanent --add-port=8080/tcp
        
        # Reload firewall
        firewall-cmd --reload
        
        # Show status
        firewall-cmd --list-all
        
        print_success "Firewalld configured"
        
    else
        print_warning "No supported firewall found. Please configure manually:"
        print_info "Allow ports: 22 (SSH), 80 (HTTP), 443 (HTTPS), 8000 (API), 8080 (Dev)"
    fi
}

configure_hosts() {
    print_step "5" "Configuring local DNS resolution"
    
    # Add entry to /etc/hosts for local testing
    if ! grep -q "$DOMAIN_NAME" /etc/hosts; then
        echo "127.0.0.1 $DOMAIN_NAME" >> /etc/hosts
        print_success "Added $DOMAIN_NAME to /etc/hosts"
    else
        print_success "$DOMAIN_NAME already in /etc/hosts"
    fi
}

test_configuration() {
    print_step "6" "Testing network configuration"
    
    # Test if services are running
    echo "🔍 Service Status:"
    systemctl is-active nginx && echo "✅ Nginx: Running" || echo "❌ Nginx: Not running"
    systemctl is-active auto-scouter-api && echo "✅ API: Running" || echo "❌ API: Not running"
    
    # Test HTTP endpoints
    echo -e "\n🌐 HTTP Endpoint Tests:"
    
    # Test direct API access
    if curl -f -s http://localhost:8000/health >/dev/null; then
        echo "✅ Direct API (port 8000): Accessible"
    else
        echo "❌ Direct API (port 8000): Not accessible"
    fi
    
    # Test Nginx proxy
    if curl -f -s http://localhost/health >/dev/null; then
        echo "✅ Nginx HTTP proxy (port 80): Working"
    else
        echo "❌ Nginx HTTP proxy (port 80): Not working"
    fi
    
    # Test HTTPS (ignore certificate errors for self-signed)
    if curl -f -s -k https://localhost/health >/dev/null; then
        echo "✅ Nginx HTTPS proxy (port 443): Working"
    else
        echo "❌ Nginx HTTPS proxy (port 443): Not working"
    fi
    
    # Test external access
    echo -e "\n🌍 External Access Information:"
    echo "Server IP: $SERVER_IP"
    echo "Domain: $DOMAIN_NAME"
    echo ""
    echo "Access URLs:"
    echo "  HTTP:  http://$SERVER_IP/ or http://$DOMAIN_NAME/"
    echo "  HTTPS: https://$SERVER_IP/ or https://$DOMAIN_NAME/"
    echo "  API:   http://$SERVER_IP:8000/ (direct)"
    echo "  Docs:  http://$SERVER_IP/docs or https://$DOMAIN_NAME/docs"
}

show_client_instructions() {
    print_header "Client Access Instructions"
    
    echo "🖥️  For clients to access Auto Scouter from other machines:"
    echo ""
    echo "1. 📡 Network Access:"
    echo "   - Server IP: $SERVER_IP"
    echo "   - Make sure clients can reach this IP"
    echo "   - Check network connectivity: ping $SERVER_IP"
    echo ""
    echo "2. 🌐 Web Access:"
    echo "   - HTTP:  http://$SERVER_IP/"
    echo "   - HTTPS: https://$SERVER_IP/ (accept self-signed certificate)"
    echo "   - API:   http://$SERVER_IP:8000/ (direct API access)"
    echo ""
    echo "3. 📱 Mobile/Remote Access:"
    echo "   - Ensure firewall allows connections from client networks"
    echo "   - For internet access, configure port forwarding on router"
    echo "   - Consider using a VPN for secure remote access"
    echo ""
    echo "4. 🔒 Security Considerations:"
    echo "   - Replace self-signed certificate with proper SSL for production"
    echo "   - Configure authentication if needed"
    echo "   - Restrict access to monitoring endpoints"
    echo ""
    echo "5. 🛠️  Troubleshooting:"
    echo "   - Check firewall: sudo ufw status"
    echo "   - Check services: sudo systemctl status auto-scouter.target"
    echo "   - Check logs: sudo journalctl -u nginx -f"
    echo "   - Test connectivity: curl http://$SERVER_IP/health"
    echo ""
    echo "6. 📋 DNS Configuration (Optional):"
    echo "   - Add DNS record: $DOMAIN_NAME -> $SERVER_IP"
    echo "   - Or add to client hosts file: $SERVER_IP $DOMAIN_NAME"
}

main() {
    print_header "Auto Scouter Network Configuration"
    
    check_root
    
    echo "Configuring network access for Auto Scouter"
    echo "Domain: $DOMAIN_NAME"
    echo "Server IP: $SERVER_IP"
    echo ""
    
    install_nginx
    generate_ssl_certificate
    configure_nginx
    configure_firewall
    configure_hosts
    test_configuration
    
    print_header "Configuration Complete!"
    print_success "Auto Scouter network configuration completed successfully"
    
    show_client_instructions
}

# Show usage if no arguments
if [[ $# -eq 0 ]]; then
    echo "Auto Scouter Network Configuration"
    echo "=================================="
    echo ""
    echo "Usage: $0 [domain-name]"
    echo ""
    echo "Examples:"
    echo "  $0                           # Use default domain (auto-scouter.local)"
    echo "  $0 auto-scouter.company.com # Use custom domain"
    echo "  $0 192.168.1.100            # Use IP address"
    echo ""
    echo "This script will:"
    echo "  - Install and configure Nginx reverse proxy"
    echo "  - Generate SSL certificate for HTTPS"
    echo "  - Configure firewall for client access"
    echo "  - Set up local DNS resolution"
    echo "  - Test the configuration"
    echo ""
    echo "Run with sudo privileges."
    exit 0
fi

# Run main function
main "$@"
