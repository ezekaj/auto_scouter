#!/bin/bash
# Auto Scouter Service Management Script
# Usage: ./manage-services.sh [start|stop|restart|status|logs|health]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service names
SERVICES=("auto-scouter-api" "auto-scouter-worker" "auto-scouter-beat")
TARGET="auto-scouter.target"

print_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}🚀 $1${NC}"
    echo -e "${BLUE}================================${NC}\n"
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

check_sudo() {
    if [[ $EUID -ne 0 ]] && [[ "$1" != "status" ]] && [[ "$1" != "logs" ]] && [[ "$1" != "health" ]]; then
        print_error "This operation requires sudo privileges"
        exit 1
    fi
}

service_start() {
    print_header "Starting Auto Scouter Services"
    
    # Start services in order
    for service in "${SERVICES[@]}"; do
        echo "Starting $service..."
        if systemctl start "$service.service"; then
            print_success "$service started"
        else
            print_error "Failed to start $service"
            return 1
        fi
        sleep 2
    done
    
    # Start the target
    echo "Starting service target..."
    if systemctl start "$TARGET"; then
        print_success "Auto Scouter target started"
    else
        print_error "Failed to start Auto Scouter target"
        return 1
    fi
    
    print_success "All services started successfully"
    
    # Wait a moment and check health
    sleep 5
    service_health
}

service_stop() {
    print_header "Stopping Auto Scouter Services"
    
    # Stop the target first
    echo "Stopping service target..."
    systemctl stop "$TARGET" 2>/dev/null || true
    
    # Stop services in reverse order
    for ((i=${#SERVICES[@]}-1; i>=0; i--)); do
        service="${SERVICES[$i]}"
        echo "Stopping $service..."
        if systemctl stop "$service.service"; then
            print_success "$service stopped"
        else
            print_warning "$service may not have been running"
        fi
        sleep 1
    done
    
    print_success "All services stopped"
}

service_restart() {
    print_header "Restarting Auto Scouter Services"
    
    service_stop
    sleep 3
    service_start
}

service_status() {
    print_header "Auto Scouter Service Status"
    
    echo "📊 Service Status:"
    echo "=================="
    
    for service in "${SERVICES[@]}"; do
        echo -n "$service: "
        if systemctl is-active "$service.service" >/dev/null 2>&1; then
            echo -e "${GREEN}Running${NC}"
        else
            echo -e "${RED}Stopped${NC}"
        fi
    done
    
    echo -n "$TARGET: "
    if systemctl is-active "$TARGET" >/dev/null 2>&1; then
        echo -e "${GREEN}Active${NC}"
    else
        echo -e "${RED}Inactive${NC}"
    fi
    
    echo -e "\n📈 Detailed Status:"
    echo "==================="
    
    for service in "${SERVICES[@]}"; do
        echo -e "\n${BLUE}--- $service ---${NC}"
        systemctl status "$service.service" --no-pager -l || true
    done
    
    echo -e "\n${BLUE}--- $TARGET ---${NC}"
    systemctl status "$TARGET" --no-pager -l || true
}

service_logs() {
    print_header "Auto Scouter Service Logs"
    
    if [[ -n "$2" ]]; then
        # Show logs for specific service
        service="auto-scouter-$2"
        echo "📋 Logs for $service:"
        journalctl -u "$service.service" -f --no-pager
    else
        # Show recent logs for all services
        echo "📋 Recent logs for all services:"
        echo "================================="
        
        for service in "${SERVICES[@]}"; do
            echo -e "\n${BLUE}--- $service (last 10 lines) ---${NC}"
            journalctl -u "$service.service" -n 10 --no-pager || true
        done
        
        echo -e "\n${YELLOW}💡 To follow logs for a specific service:${NC}"
        echo "   ./manage-services.sh logs api"
        echo "   ./manage-services.sh logs worker"
        echo "   ./manage-services.sh logs beat"
    fi
}

service_health() {
    print_header "Auto Scouter Health Check"
    
    echo "🏥 Health Status:"
    echo "================="
    
    # Check if services are running
    all_running=true
    for service in "${SERVICES[@]}"; do
        if systemctl is-active "$service.service" >/dev/null 2>&1; then
            print_success "$service is running"
        else
            print_error "$service is not running"
            all_running=false
        fi
    done
    
    if [[ "$all_running" == "true" ]]; then
        echo -e "\n🌐 API Health Check:"
        echo "===================="
        
        # Test API health endpoint
        if curl -f -s http://localhost:8000/health >/dev/null 2>&1; then
            print_success "API health check passed"
            
            # Get detailed health info
            echo -e "\n📊 Detailed Health Information:"
            curl -s http://localhost:8000/health/detailed | python3 -m json.tool 2>/dev/null || echo "Could not parse health details"
        else
            print_error "API health check failed"
        fi
        
        echo -e "\n🔄 Background Jobs Status:"
        echo "=========================="
        
        # Check Celery worker status
        if sudo -u autoscouter /opt/auto-scouter/venv/bin/celery --app=app.core.celery_app inspect ping >/dev/null 2>&1; then
            print_success "Celery workers are responding"
        else
            print_error "Celery workers are not responding"
        fi
        
        # Check active tasks
        echo -e "\n📋 Active Tasks:"
        sudo -u autoscouter /opt/auto-scouter/venv/bin/celery --app=app.core.celery_app inspect active 2>/dev/null || echo "Could not retrieve active tasks"
        
    else
        print_error "Some services are not running. Please check service status."
    fi
}

show_usage() {
    echo "Auto Scouter Service Management"
    echo "==============================="
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start     Start all Auto Scouter services"
    echo "  stop      Stop all Auto Scouter services"
    echo "  restart   Restart all Auto Scouter services"
    echo "  status    Show service status"
    echo "  logs      Show service logs"
    echo "  health    Perform comprehensive health check"
    echo ""
    echo "Log Options:"
    echo "  logs api     Show API service logs (follow mode)"
    echo "  logs worker  Show worker service logs (follow mode)"
    echo "  logs beat    Show beat service logs (follow mode)"
    echo ""
    echo "Examples:"
    echo "  $0 start                 # Start all services"
    echo "  $0 status                # Check service status"
    echo "  $0 logs api              # Follow API logs"
    echo "  $0 health                # Comprehensive health check"
    echo ""
    echo "Service Management:"
    echo "  Individual services can also be managed with systemctl:"
    echo "  sudo systemctl [start|stop|restart] auto-scouter-api"
    echo "  sudo systemctl [start|stop|restart] auto-scouter-worker"
    echo "  sudo systemctl [start|stop|restart] auto-scouter-beat"
    echo ""
    echo "  Or manage all services with the target:"
    echo "  sudo systemctl [start|stop|restart] auto-scouter.target"
}

main() {
    case "${1:-}" in
        start)
            check_sudo "$1"
            service_start
            ;;
        stop)
            check_sudo "$1"
            service_stop
            ;;
        restart)
            check_sudo "$1"
            service_restart
            ;;
        status)
            service_status
            ;;
        logs)
            service_logs "$@"
            ;;
        health)
            service_health
            ;;
        "")
            show_usage
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
