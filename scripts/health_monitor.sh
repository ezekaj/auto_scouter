#!/bin/bash
# Auto Scouter Health Monitoring Script
# Monitors API health, database connectivity, and system resources

LOG_FILE="/var/log/auto_scouter/health_monitor.log"
API_URL="http://127.0.0.1:8000/health"
DB_URL="postgresql://auto_scouter_user:OzXZ3bYnqxPx8LQk6SUNb7fTt5r70ZTRsc0lPfGMvx8=@localhost:5432/auto_scouter_prod"

# Create log directory if it doesn't exist
sudo mkdir -p /var/log/auto_scouter
sudo chown elo:elo /var/log/auto_scouter

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Check API Health
check_api() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL" --max-time 10)
    if [ "$response" = "200" ]; then
        log_message "✅ API Health: OK"
        return 0
    else
        log_message "❌ API Health: FAILED (HTTP $response)"
        return 1
    fi
}

# Check Database Connectivity
check_database() {
    if psql "$DB_URL" -c "SELECT 1;" >/dev/null 2>&1; then
        log_message "✅ Database: OK"
        return 0
    else
        log_message "❌ Database: FAILED"
        return 1
    fi
}

# Check Redis
check_redis() {
    if redis-cli ping >/dev/null 2>&1; then
        log_message "✅ Redis: OK"
        return 0
    else
        log_message "❌ Redis: FAILED"
        return 1
    fi
}

# Check System Resources
check_resources() {
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    local memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    log_message "📊 Disk Usage: ${disk_usage}%"
    log_message "📊 Memory Usage: ${memory_usage}%"
    
    if [ "$disk_usage" -gt 90 ]; then
        log_message "⚠️  WARNING: High disk usage (${disk_usage}%)"
    fi
    
    if [ "$memory_usage" -gt 90 ]; then
        log_message "⚠️  WARNING: High memory usage (${memory_usage}%)"
    fi
}

# Check Supervisor Services
check_supervisor() {
    if sudo supervisorctl status auto_scouter:auto_scouter_api | grep -q "RUNNING"; then
        log_message "✅ Supervisor API: RUNNING"
        return 0
    else
        log_message "❌ Supervisor API: NOT RUNNING"
        return 1
    fi
}

# Main monitoring function
main() {
    log_message "🔍 Starting health check..."
    
    local failures=0
    
    check_api || ((failures++))
    check_database || ((failures++))
    check_redis || ((failures++))
    check_supervisor || ((failures++))
    check_resources
    
    if [ $failures -eq 0 ]; then
        log_message "✅ All systems healthy"
    else
        log_message "❌ $failures system(s) failed health check"
    fi
    
    log_message "🔍 Health check completed"
    echo "---" >> "$LOG_FILE"
}

main "$@"
