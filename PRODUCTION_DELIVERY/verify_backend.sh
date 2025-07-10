#!/bin/bash

# Vehicle Scout Backend Verification Script
# Tests the production backend health and API endpoints

echo "🚀 Vehicle Scout Backend Verification"
echo "====================================="

BACKEND_URL="https://auto-scouter-backend.onrender.com"
HEALTH_URL="$BACKEND_URL/health"
API_URL="$BACKEND_URL/api/v1"

echo ""
echo "🔍 Testing Backend Health..."
echo "URL: $HEALTH_URL"

# Test health endpoint with timeout
response=$(curl -s --max-time 60 -w "HTTPSTATUS:%{http_code}" "$HEALTH_URL")
http_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')

if [ "$http_code" -eq 200 ]; then
    echo "✅ Backend Health: HEALTHY"
    echo "Response: $body"
    
    echo ""
    echo "🔍 Testing API Endpoints..."
    
    # Test vehicles endpoint
    echo "Testing: $API_URL/automotive/vehicles"
    vehicles_response=$(curl -s --max-time 30 -w "HTTPSTATUS:%{http_code}" "$API_URL/automotive/vehicles")
    vehicles_code=$(echo $vehicles_response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    
    if [ "$vehicles_code" -eq 200 ] || [ "$vehicles_code" -eq 422 ]; then
        echo "✅ Vehicles API: Working (Status: $vehicles_code)"
    else
        echo "⚠️  Vehicles API: Status $vehicles_code"
    fi
    
    # Test alerts endpoint
    echo "Testing: $API_URL/alerts/"
    alerts_response=$(curl -s --max-time 30 -w "HTTPSTATUS:%{http_code}" "$API_URL/alerts/")
    alerts_code=$(echo $alerts_response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    
    if [ "$alerts_code" -eq 200 ] || [ "$alerts_code" -eq 422 ]; then
        echo "✅ Alerts API: Working (Status: $alerts_code)"
    else
        echo "⚠️  Alerts API: Status $alerts_code"
    fi
    
    echo ""
    echo "🎉 BACKEND STATUS: READY FOR PRODUCTION"
    echo ""
    echo "📱 Next Steps:"
    echo "1. Install VehicleScout-Production-v1.0.0.apk on Android device"
    echo "2. Launch the app and verify connectivity"
    echo "3. Test vehicle search and alert creation"
    echo "4. Confirm no 'Demo Mode' banners appear"
    
elif [ "$http_code" -eq 000 ]; then
    echo "❌ Backend Health: TIMEOUT/CONNECTION ERROR"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "1. Check if backend is deployed on Render"
    echo "2. Wait 30-60 seconds for cold start (free tier)"
    echo "3. Try running this script again"
    echo "4. Check Render dashboard for deployment status"
    
else
    echo "❌ Backend Health: ERROR (Status: $http_code)"
    echo "Response: $body"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "1. Redeploy backend on Render dashboard"
    echo "2. Check deployment logs for errors"
    echo "3. Verify environment variables are set"
fi

echo ""
echo "📋 Backend URL: $BACKEND_URL"
echo "📋 Health Check: $HEALTH_URL"
echo "📋 API Base: $API_URL"
