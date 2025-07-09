#!/usr/bin/env python3
"""
Render Deployment Testing Script
Tests all API endpoints after deployment to Render
"""

import requests
import json
import sys
from datetime import datetime

# Update this with your actual Render app URL
BASE_URL = "https://auto-scouter-backend.onrender.com"
API_URL = f"{BASE_URL}/api/v1"

def test_health_endpoint():
    """Test the health endpoint"""
    print("🏥 Testing Health Endpoint")
    print("-" * 40)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Health endpoint working")
            print(f"   Status: {data.get('status')}")
            print(f"   Environment: {data.get('environment')}")
            print(f"   Database: {data.get('database', 'Not specified')}")
            print(f"   Version: {data.get('version', 'Not specified')}")
            
            # Check for updated response format
            if data.get('version') == '2.0.0-alerts-enabled':
                print("✅ Updated backend code deployed successfully!")
                return True
            else:
                print("❌ Old backend code still deployed")
                return False
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_vehicle_listings():
    """Test vehicle listings endpoint"""
    print("\n🚗 Testing Vehicle Listings Endpoint")
    print("-" * 40)
    
    try:
        response = requests.get(f"{API_URL}/automotive/vehicles/simple?limit=3", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            vehicles = data.get('vehicles', [])
            print(f"✅ Vehicle listings working - {len(vehicles)} vehicles returned")
            
            if vehicles:
                vehicle = vehicles[0]
                print(f"   Sample: {vehicle.get('make')} {vehicle.get('model')} - €{vehicle.get('price'):,}")
                print(f"   Location: {vehicle.get('city')}, {vehicle.get('country')}")
            
            return True
        else:
            print(f"❌ Vehicle listings failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Vehicle listings error: {e}")
        return False

def test_alert_creation():
    """Test alert creation endpoint"""
    print("\n🔔 Testing Alert Creation Endpoint")
    print("-" * 40)
    
    alert_data = {
        "name": "Test Alert - BMW 3 Series",
        "description": "Testing alert creation on Render deployment",
        "make": "BMW",
        "model": "3 Series",
        "max_price": 25000,
        "min_year": 2015,
        "fuel_type": "Diesel",
        "is_active": True,
        "notification_frequency": "immediate"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/alerts/",
            json=alert_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Alert creation working")
            print(f"   Alert ID: {data.get('alert', {}).get('id')}")
            print(f"   Alert Name: {data.get('alert', {}).get('name')}")
            print(f"   Status: {data.get('status')}")
            return data.get('alert', {}).get('id')
        else:
            print(f"❌ Alert creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Alert creation error: {e}")
        return None

def test_alert_retrieval():
    """Test alert retrieval endpoint"""
    print("\n📋 Testing Alert Retrieval Endpoint")
    print("-" * 40)
    
    try:
        response = requests.get(f"{API_URL}/alerts/", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            alerts = data.get('alerts', [])
            print(f"✅ Alert retrieval working - {len(alerts)} alerts found")
            
            if alerts:
                alert = alerts[0]
                print(f"   Sample: {alert.get('name')}")
                print(f"   Active: {alert.get('is_active')}")
                print(f"   Created: {alert.get('created_at', 'Unknown')}")
            
            return True
        else:
            print(f"❌ Alert retrieval failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Alert retrieval error: {e}")
        return False

def test_alert_testing(alert_id):
    """Test alert testing endpoint"""
    if not alert_id:
        print("\n⚠️  Skipping alert testing - no alert ID available")
        return False
        
    print(f"\n🎯 Testing Alert Testing Endpoint (Alert ID: {alert_id})")
    print("-" * 40)
    
    test_data = {
        "test_days": 7,
        "max_listings": 10,
        "create_notifications": False
    }
    
    try:
        response = requests.post(
            f"{API_URL}/alerts/{alert_id}/test",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Alert testing working")
            print(f"   Vehicles tested: {data.get('vehicles_tested', 0)}")
            print(f"   Matches found: {data.get('matches_found', 0)}")
            print(f"   Status: {data.get('status')}")
            return True
        else:
            print(f"❌ Alert testing failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Alert testing error: {e}")
        return False

def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("🚀 Auto Scouter Render Deployment Test")
    print("=" * 60)
    print(f"Testing backend at: {BASE_URL}")
    print(f"API endpoints at: {API_URL}")
    print("=" * 60)
    
    results = []
    
    # Test 1: Health endpoint
    health_ok = test_health_endpoint()
    results.append(("Health Endpoint", health_ok))
    
    # Test 2: Vehicle listings
    vehicles_ok = test_vehicle_listings()
    results.append(("Vehicle Listings", vehicles_ok))
    
    # Test 3: Alert creation
    alert_id = test_alert_creation()
    alert_creation_ok = alert_id is not None
    results.append(("Alert Creation", alert_creation_ok))
    
    # Test 4: Alert retrieval
    alert_retrieval_ok = test_alert_retrieval()
    results.append(("Alert Retrieval", alert_retrieval_ok))
    
    # Test 5: Alert testing
    alert_testing_ok = test_alert_testing(alert_id)
    results.append(("Alert Testing", alert_testing_ok))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if success:
            passed += 1
    
    print("-" * 60)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Render deployment is working correctly")
        print("✅ All API endpoints are functional")
        print("✅ Mobile app should work with this backend")
        return True
    else:
        print(f"\n❌ {total - passed} TESTS FAILED")
        print("❌ Deployment needs attention")
        return False

if __name__ == "__main__":
    print("Update BASE_URL with your actual Render app URL before running!")
    print(f"Current URL: {BASE_URL}")
    print()
    
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]
        API_URL = f"{BASE_URL}/api/v1"
        print(f"Using provided URL: {BASE_URL}")
    
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
