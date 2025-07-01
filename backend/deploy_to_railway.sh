#!/bin/bash

# Vehicle Scout Backend Deployment to Railway
# This script helps deploy the backend to Railway.app

set -e

echo "🚀 Vehicle Scout Backend - Railway Deployment"
echo "=============================================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    curl -fsSL https://railway.app/install.sh | sh
    export PATH="$HOME/.railway/bin:$PATH"
fi

# Login to Railway (if not already logged in)
echo "🔐 Checking Railway authentication..."
if ! railway whoami &> /dev/null; then
    echo "Please login to Railway:"
    railway login
fi

# Create new Railway project
echo "📦 Creating Railway project..."
railway login
railway init

# Add PostgreSQL database
echo "🗄️ Adding PostgreSQL database..."
railway add --database postgres

# Add Redis for Celery
echo "🔴 Adding Redis for background tasks..."
railway add --database redis

# Set environment variables
echo "⚙️ Setting environment variables..."

# Database will be automatically set by Railway
# We need to set other environment variables

railway variables set SECRET_KEY="$(openssl rand -base64 32)"
railway variables set ALGORITHM="HS256"
railway variables set ACCESS_TOKEN_EXPIRE_MINUTES="30"
railway variables set SCRAPER_SCRAPING_ENABLED="true"
railway variables set SCRAPER_SCRAPING_INTERVAL_HOURS="6"
railway variables set SCRAPER_MAX_PAGES_TO_SCRAPE="100"
railway variables set SCRAPER_REQUEST_DELAY="1.5"
railway variables set SCRAPER_ENABLE_DEDUPLICATION="true"
railway variables set SCRAPER_KEEP_HISTORICAL_DATA="true"
railway variables set SCRAPER_DATA_RETENTION_DAYS="365"
railway variables set SCRAPER_ENABLE_METRICS="true"
railway variables set SCRAPER_LOG_LEVEL="INFO"
railway variables set RATE_LIMIT_ENABLED="true"
railway variables set RATE_LIMIT_REQUESTS_PER_MINUTE="120"
railway variables set MAX_NOTIFICATIONS_PER_USER_PER_DAY="100"
railway variables set NOTIFICATION_BATCH_SIZE="100"
railway variables set ALERT_MATCHING_INTERVAL_SECONDS="300"
railway variables set ENVIRONMENT="production"
railway variables set DEBUG="false"

# Deploy the application
echo "🚀 Deploying to Railway..."
railway up

# Get the deployment URL
echo "✅ Deployment complete!"
echo "🌐 Your API will be available at:"
railway status

echo ""
echo "📋 Next Steps:"
echo "1. Update your frontend configuration to use the new API URL"
echo "2. Set up your email configuration for notifications"
echo "3. Configure your domain (optional)"
echo "4. Set up monitoring and alerts"
echo ""
echo "🔧 To manage your deployment:"
echo "- View logs: railway logs"
echo "- Check status: railway status"
echo "- Update variables: railway variables"
echo "- Redeploy: railway up"
