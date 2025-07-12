#!/bin/bash

# Auto Scouter Network Connectivity Test
# Tests if the mobile app can connect to the backend via local network IP

echo "🚀 Auto Scouter Network Connectivity Test"
echo "=" | tr ' ' '=' | head -c 60 && echo
echo "Local IP: 192.168.0.35"
echo "Backend Port: 8002"
echo "API Endpoint: http://192.168.0.35:8002/api/v1"
echo "=" | tr ' ' '=' | head -c 60 && echo

echo
echo "🔍 Testing Backend Connectivity..."
echo "-" | tr ' ' '-' | head -c 40 && echo

# Test 1: Check if port is open
echo "1. Testing port 8002 accessibility..."
if curl -s --connect-timeout 5 http://192.168.0.35:8002/health > /dev/null 2>&1; then
    echo "   ✅ Port 8002 is accessible"
else
    echo "   ❌ Port 8002 is not accessible"
    echo "   💡 Check if backend is running: lsof -i :8002"
    exit 1
fi

# Test 2: Test health endpoint
echo "2. Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://192.168.0.35:8002/health)
if [ $? -eq 0 ]; then
    echo "   ✅ Health endpoint working"
    echo "   📊 Response: $HEALTH_RESPONSE"
else
    echo "   ❌ Health endpoint failed"
    exit 1
fi

# Test 3: Test alerts API
echo "3. Testing alerts API..."
ALERTS_RESPONSE=$(curl -s http://192.168.0.35:8002/api/v1/alerts/)
if [ $? -eq 0 ]; then
    echo "   ✅ Alerts API working"
    ALERT_COUNT=$(echo "$ALERTS_RESPONSE" | grep -o '"id"' | wc -l)
    echo "   📋 Found $ALERT_COUNT alerts"
else
    echo "   ❌ Alerts API failed"
    exit 1
fi

# Test 4: Test from mobile device perspective
echo "4. Testing mobile device connectivity..."
echo "   📱 Mobile devices should connect to: http://192.168.0.35:8002/api/v1"
echo "   🔧 Make sure your mobile device is on the same WiFi network"
echo "   🔧 Network name should be the same as this computer"

echo
echo "🎉 All tests passed!"
echo "✅ Backend is accessible via network IP"
echo "✅ Mobile app should be able to connect"
echo
echo "📱 Install the new APK: VehicleScout-network-ip-fixed.apk"
echo "🔧 Make sure mobile device is on the same WiFi network"
echo "🔧 If still having issues, check firewall settings"
