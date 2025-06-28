#!/bin/bash

# Auto Scouter Frontend Deployment Script
# This script builds and prepares the frontend for production deployment

set -e  # Exit on any error

echo "🚀 Starting Auto Scouter Frontend Deployment..."

# Check if required environment variables are set
if [ -z "$VITE_API_BASE_URL" ]; then
    echo "❌ Error: VITE_API_BASE_URL environment variable is required"
    echo "Please set it to your production API URL (e.g., https://api.yourdomain.com/api/v1)"
    exit 1
fi

# Set build timestamp and git commit
export VITE_BUILD_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
export VITE_GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo "📋 Build Information:"
echo "  API URL: $VITE_API_BASE_URL"
echo "  Build Time: $VITE_BUILD_TIMESTAMP"
echo "  Git Commit: $VITE_GIT_COMMIT"
echo ""

# Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf dist/

# Install dependencies
echo "📦 Installing dependencies..."
npm ci --only=production

# Build the application
echo "🔨 Building application for production..."
npm run build

# Verify build was successful
if [ ! -d "dist" ]; then
    echo "❌ Build failed: dist directory not found"
    exit 1
fi

echo "✅ Build completed successfully!"
echo ""

# Display build statistics
echo "📊 Build Statistics:"
echo "  Build size: $(du -sh dist/ | cut -f1)"
echo "  Files created: $(find dist/ -type f | wc -l)"
echo ""

# Create deployment package
echo "📦 Creating deployment package..."
tar -czf auto-scouter-frontend-$(date +%Y%m%d-%H%M%S).tar.gz dist/

echo "🎉 Deployment package ready!"
echo ""
echo "Next steps:"
echo "1. Upload the dist/ folder to your web server"
echo "2. Configure your web server (see nginx.conf for example)"
echo "3. Set up SSL certificate"
echo "4. Configure domain DNS"
echo ""
echo "For detailed instructions, see DEPLOYMENT.md"
