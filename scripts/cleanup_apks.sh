#!/bin/bash

# Auto Scouter APK Cleanup Script
# This script manages APK files in the CLIENT_DELIVERY_PACKAGE directory
# It keeps only the latest working APK and removes older versions

set -e

# Configuration
CLIENT_DIR="CLIENT_DELIVERY_PACKAGE"
BACKUP_DIR="CLIENT_DELIVERY_PACKAGE/backup"
MAX_BACKUPS=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to get APK version from filename
get_apk_version() {
    local filename="$1"
    # Extract version/timestamp from filename
    if [[ "$filename" =~ ([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{10,}) ]]; then
        echo "${BASH_REMATCH[1]}"
    elif [[ "$filename" =~ (v[0-9]+\.[0-9]+\.[0-9]+) ]]; then
        echo "${BASH_REMATCH[1]}"
    else
        # Use file modification time as fallback
        stat -c %Y "$filename" 2>/dev/null || echo "0"
    fi
}

# Function to backup old APKs
backup_apk() {
    local apk_file="$1"
    local backup_name="$2"
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    
    # Move APK to backup
    mv "$apk_file" "$BACKUP_DIR/$backup_name"
    print_status "Backed up: $apk_file -> $BACKUP_DIR/$backup_name"
}

# Function to clean old backups
clean_old_backups() {
    if [ ! -d "$BACKUP_DIR" ]; then
        return
    fi
    
    # Count backup files
    local backup_count=$(find "$BACKUP_DIR" -name "*.apk" | wc -l)
    
    if [ "$backup_count" -gt "$MAX_BACKUPS" ]; then
        print_status "Cleaning old backups (keeping $MAX_BACKUPS most recent)..."
        
        # Remove oldest backups, keeping only MAX_BACKUPS
        find "$BACKUP_DIR" -name "*.apk" -type f -printf '%T@ %p\n' | \
        sort -n | \
        head -n -"$MAX_BACKUPS" | \
        cut -d' ' -f2- | \
        while read -r file; do
            rm -f "$file"
            print_status "Removed old backup: $(basename "$file")"
        done
    fi
}

# Function to generate new APK name
generate_apk_name() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    echo "AutoScouter-Production-${timestamp}.apk"
}

# Main cleanup function
cleanup_apks() {
    print_status "Starting APK cleanup in $CLIENT_DIR..."
    
    # Check if CLIENT_DIR exists
    if [ ! -d "$CLIENT_DIR" ]; then
        print_error "CLIENT_DELIVERY_PACKAGE directory not found!"
        exit 1
    fi
    
    cd "$CLIENT_DIR"
    
    # Find all APK files
    local apk_files=($(find . -maxdepth 1 -name "*.apk" -type f))
    
    if [ ${#apk_files[@]} -eq 0 ]; then
        print_warning "No APK files found in $CLIENT_DIR"
        return
    fi
    
    print_status "Found ${#apk_files[@]} APK file(s)"
    
    # If only one APK, nothing to clean
    if [ ${#apk_files[@]} -eq 1 ]; then
        print_success "Only one APK found: ${apk_files[0]}"
        print_success "No cleanup needed"
        return
    fi
    
    # Sort APKs by modification time (newest first)
    local sorted_apks=($(ls -t *.apk 2>/dev/null))
    
    if [ ${#sorted_apks[@]} -eq 0 ]; then
        print_warning "No APK files to process"
        return
    fi
    
    # Keep the newest APK, backup the rest
    local newest_apk="${sorted_apks[0]}"
    print_success "Keeping newest APK: $newest_apk"
    
    # Process older APKs
    for ((i=1; i<${#sorted_apks[@]}; i++)); do
        local old_apk="${sorted_apks[i]}"
        local backup_name="$(basename "$old_apk" .apk)_backup_$(date +%Y%m%d_%H%M%S).apk"
        
        backup_apk "$old_apk" "$backup_name"
    done
    
    # Clean old backups
    clean_old_backups
    
    print_success "APK cleanup completed!"
    print_status "Active APK: $newest_apk"
    
    # Show summary
    echo ""
    echo "=== APK CLEANUP SUMMARY ==="
    echo "Active APK: $newest_apk"
    echo "Backup directory: $BACKUP_DIR"
    if [ -d "$BACKUP_DIR" ]; then
        local backup_count=$(find "$BACKUP_DIR" -name "*.apk" | wc -l)
        echo "Backup APKs: $backup_count"
    fi
    echo "=========================="
}

# Function to list APKs
list_apks() {
    print_status "APK files in $CLIENT_DIR:"
    
    if [ ! -d "$CLIENT_DIR" ]; then
        print_error "CLIENT_DELIVERY_PACKAGE directory not found!"
        return 1
    fi
    
    cd "$CLIENT_DIR"
    
    # List active APKs
    local apk_files=($(find . -maxdepth 1 -name "*.apk" -type f))
    
    if [ ${#apk_files[@]} -eq 0 ]; then
        print_warning "No active APK files found"
    else
        echo ""
        echo "=== ACTIVE APKs ==="
        for apk in "${apk_files[@]}"; do
            local size=$(du -h "$apk" | cut -f1)
            local date=$(stat -c %y "$apk" | cut -d' ' -f1,2 | cut -d'.' -f1)
            printf "%-40s %8s %s\n" "$(basename "$apk")" "$size" "$date"
        done
    fi
    
    # List backup APKs
    if [ -d "$BACKUP_DIR" ]; then
        local backup_files=($(find "$BACKUP_DIR" -name "*.apk" -type f))
        
        if [ ${#backup_files[@]} -gt 0 ]; then
            echo ""
            echo "=== BACKUP APKs ==="
            for apk in "${backup_files[@]}"; do
                local size=$(du -h "$apk" | cut -f1)
                local date=$(stat -c %y "$apk" | cut -d' ' -f1,2 | cut -d'.' -f1)
                printf "%-40s %8s %s\n" "$(basename "$apk")" "$size" "$date"
            done
        fi
    fi
    
    echo ""
}

# Function to show help
show_help() {
    echo "Auto Scouter APK Cleanup Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  cleanup    Clean up old APK files (default)"
    echo "  list       List all APK files"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                 # Run cleanup"
    echo "  $0 cleanup         # Run cleanup"
    echo "  $0 list           # List APK files"
    echo ""
}

# Main script logic
main() {
    local command="${1:-cleanup}"
    
    case "$command" in
        "cleanup")
            cleanup_apks
            ;;
        "list")
            list_apks
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
