#!/bin/bash

# Vehicle Scout - Cloud APK Build Script
# Builds production APK that connects to Render cloud backend

set -e  # Exit on any error

echo "🚀 Building Vehicle Scout Cloud APK"
echo "=================================="

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

# Check if Render URL is configured
check_render_url() {
    print_status "Checking Render backend URL..."

    if grep -q "your-app.onrender.com" .env.production; then
        print_warning "Render URL not configured!"
        print_warning "Please update .env.production with your actual Render deployment URL"
        print_warning "Example: VITE_API_BASE_URL=https://auto-scouter-backend-abc123.onrender.com/api/v1"

        read -p "Do you want to continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "Deployment cancelled. Please configure Render URL first."
            exit 1
        fi
    else
        print_success "Render URL configured"
    fi
}

# Check if Firebase is configured
check_firebase_config() {
    print_status "Checking Firebase configuration..."
    
    if grep -q "your-firebase-api-key" .env.production; then
        print_warning "Firebase not configured - push notifications will be disabled"
        print_warning "To enable push notifications, configure Firebase in .env.production"
    else
        print_success "Firebase configuration found"
    fi
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    if [ ! -d "node_modules" ]; then
        npm install
    else
        print_status "Dependencies already installed"
    fi
    
    print_success "Dependencies ready"
}

# Build the web app
build_web_app() {
    print_status "Building web application for production..."
    
    # Use production environment
    export NODE_ENV=production
    
    # Build the app
    npm run build
    
    if [ $? -eq 0 ]; then
        print_success "Web application built successfully"
    else
        print_error "Web application build failed"
        exit 1
    fi
}

# Sync with Capacitor
sync_capacitor() {
    print_status "Syncing with Capacitor..."
    
    # Sync the built web app with Capacitor
    npx cap sync android
    
    if [ $? -eq 0 ]; then
        print_success "Capacitor sync completed"
    else
        print_error "Capacitor sync failed"
        exit 1
    fi
}

# Build Android APK
build_android_apk() {
    print_status "Building Android APK..."
    
    # Check if Android directory exists
    if [ ! -d "android" ]; then
        print_error "Android directory not found. Run 'npx cap add android' first."
        exit 1
    fi
    
    # Navigate to Android directory and build
    cd android
    
    # Clean previous builds
    ./gradlew clean
    
    # Build release APK
    print_status "Building release APK (this may take a few minutes)..."
    ./gradlew assembleRelease
    
    if [ $? -eq 0 ]; then
        print_success "Android APK built successfully"
    else
        print_error "Android APK build failed"
        cd ..
        exit 1
    fi
    
    cd ..
}

# Copy APK to output directory
copy_apk_files() {
    print_status "Copying APK files..."
    
    # Create output directory
    mkdir -p dist/apk
    
    # Copy APK files
    if [ -f "android/app/build/outputs/apk/release/app-release.apk" ]; then
        cp android/app/build/outputs/apk/release/app-release.apk dist/apk/VehicleScout-cloud-release.apk
        print_success "Release APK copied to dist/apk/VehicleScout-cloud-release.apk"
    fi
    
    if [ -f "android/app/build/outputs/apk/debug/app-debug.apk" ]; then
        cp android/app/build/outputs/apk/debug/app-debug.apk dist/apk/VehicleScout-cloud-debug.apk
        print_success "Debug APK copied to dist/apk/VehicleScout-cloud-debug.apk"
    fi
    
    # Get file sizes
    if [ -f "dist/apk/VehicleScout-cloud-release.apk" ]; then
        size=$(du -h dist/apk/VehicleScout-cloud-release.apk | cut -f1)
        print_success "Release APK size: $size"
    fi
}

# Generate deployment info
generate_deployment_info() {
    print_status "Generating deployment information..."
    
    cat > dist/apk/DEPLOYMENT_INFO.md << EOF
# Vehicle Scout Cloud APK - Deployment Information

**Build Date:** $(date)
**Version:** $(grep VITE_APP_VERSION .env.production | cut -d'=' -f2)
**Environment:** Production (Cloud)

## APK Files

### VehicleScout-cloud-release.apk
- **Purpose:** Production deployment
- **Backend:** Cloud (Render)
- **Push Notifications:** $(grep -q "your-firebase-api-key" .env.production && echo "Disabled (Firebase not configured)" || echo "Enabled (Firebase configured)")
- **Installation:** Enable "Unknown Sources" in Android settings

### VehicleScout-cloud-debug.apk
- **Purpose:** Development and testing
- **Backend:** Cloud (Render)
- **Installation:** Enable "Unknown Sources" in Android settings

## Backend Configuration

**API URL:** $(grep VITE_API_BASE_URL .env.production | cut -d'=' -f2)
**WebSocket URL:** $(grep VITE_WS_BASE_URL .env.production | cut -d'=' -f2)

## Installation Instructions

1. Download the APK file to your Android device
2. Enable "Unknown Sources" in Settings > Security
3. Tap the APK file to install
4. Launch "Vehicle Scout" app
5. Register/login to start using the app

## Features

- ✅ Real-time vehicle listings from cloud backend
- ✅ User registration and authentication
- ✅ Vehicle search and filtering
- ✅ Alert creation and management
- ✅ Offline mode with cached data
$(grep -q "your-firebase-api-key" .env.production || echo "- ✅ Push notifications for new matches")

## Support

- **Backend Health:** \$(API_URL)/health
- **API Documentation:** \$(API_URL)/docs
- **Issues:** Check Render deployment logs

---

**Built with:** Ionic + Capacitor + React + TypeScript
**Backend:** FastAPI + PostgreSQL (Render)
**Notifications:** Firebase Cloud Messaging
EOF

    print_success "Deployment information generated"
}

# Main build process
main() {
    print_status "Starting cloud APK build process..."
    
    # Check prerequisites
    check_render_url
    check_firebase_config
    
    # Build process
    install_dependencies
    build_web_app
    sync_capacitor
    build_android_apk
    copy_apk_files
    generate_deployment_info
    
    echo
    print_success "🎉 Cloud APK build completed successfully!"
    echo
    print_status "📱 APK Files:"
    if [ -f "dist/apk/VehicleScout-cloud-release.apk" ]; then
        echo "   - dist/apk/VehicleScout-cloud-release.apk (Production)"
    fi
    if [ -f "dist/apk/VehicleScout-cloud-debug.apk" ]; then
        echo "   - dist/apk/VehicleScout-cloud-debug.apk (Debug)"
    fi
    echo
    print_status "📋 Next Steps:"
    echo "   1. Test the APK on an Android device"
    echo "   2. Verify connection to cloud backend"
    echo "   3. Test user registration and vehicle search"
    echo "   4. Distribute APK to users"
    echo
    print_status "🌐 Backend URL: $(grep VITE_API_BASE_URL .env.production | cut -d'=' -f2)"
    echo
}

# Run main function
main "$@"
