#!/usr/bin/env python3
"""
Railway Live Deployment Testing Script
Tests the deployed Auto Scouter API on Railway
"""

import requests
import sys
import json
import time
from datetime import datetime

def test_railway_deployment(base_url):
    """Test all critical endpoints on Railway deployment"""
    
    print(f"🚂 TESTING RAILWAY DEPLOYMENT")
    print(f"URL: {base_url}")
    print("=" * 60)
    
    results = []
    
    # Test 1: Health Check
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check: {data.get('status', 'unknown')}")
            print(f"   Database: {data.get('database', 'unknown')}")
            results.append(("Health Check", True))
        else:
            print(f"❌ Health check failed: {response.status_code}")
            results.append(("Health Check", False))
    except Exception as e:
        print(f"❌ Health check error: {e}")
        results.append(("Health Check", False))
    
    # Test 2: Root Endpoint
    print("\n🔍 Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint: {data.get('message', 'unknown')}")
            print(f"   Version: {data.get('version', 'unknown')}")
            results.append(("Root Endpoint", True))
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            results.append(("Root Endpoint", False))
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        results.append(("Root Endpoint", False))
    
    # Test 3: API Documentation
    print("\n🔍 Testing API documentation...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=30)
        if response.status_code == 200:
            print("✅ API documentation accessible")
            results.append(("API Documentation", True))
        else:
            print(f"❌ API documentation failed: {response.status_code}")
            results.append(("API Documentation", False))
    except Exception as e:
        print(f"❌ API documentation error: {e}")
        results.append(("API Documentation", False))
    
    # Test 4: Authentication Registration
    print("\n🔍 Testing user registration...")
    try:
        test_user = {
            "username": f"testuser_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "TestPassword123!"
        }
        
        response = requests.post(
            f"{base_url}/api/v1/auth/register",
            json=test_user,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            print("✅ User registration successful")
            results.append(("User Registration", True))
            
            # Test 5: Login with created user
            print("\n🔍 Testing user login...")
            login_data = {
                "username": test_user["username"],
                "password": test_user["password"]
            }
            
            login_response = requests.post(
                f"{base_url}/api/v1/auth/login",
                json=login_data,
                timeout=30
            )
            
            if login_response.status_code == 200:
                login_result = login_response.json()
                if "token" in login_result:
                    print("✅ User login successful")
                    print(f"   Token received: {login_result['token']['access_token'][:20]}...")
                    results.append(("User Login", True))
                else:
                    print("❌ Login response missing token")
                    results.append(("User Login", False))
            else:
                print(f"❌ User login failed: {login_response.status_code}")
                results.append(("User Login", False))
                
        else:
            print(f"❌ User registration failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            results.append(("User Registration", False))
            results.append(("User Login", False))
            
    except Exception as e:
        print(f"❌ Authentication test error: {e}")
        results.append(("User Registration", False))
        results.append(("User Login", False))
    
    # Test 6: Database Connectivity (via health check details)
    print("\n🔍 Testing database connectivity...")
    try:
        response = requests.get(f"{base_url}/health", timeout=30)
        if response.status_code == 200:
            data = response.json()
            db_status = data.get('database', 'unknown')
            if db_status == 'healthy':
                print("✅ Database connectivity confirmed")
                results.append(("Database Connectivity", True))
            else:
                print(f"❌ Database status: {db_status}")
                results.append(("Database Connectivity", False))
        else:
            print("❌ Could not check database status")
            results.append(("Database Connectivity", False))
    except Exception as e:
        print(f"❌ Database connectivity error: {e}")
        results.append(("Database Connectivity", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 RAILWAY DEPLOYMENT TEST RESULTS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 RAILWAY DEPLOYMENT SUCCESSFUL!")
        print("✅ All critical functionality working")
        print("✅ Authentication system operational")
        print("✅ Database connectivity confirmed")
        print("✅ API endpoints accessible")
        
        print(f"\n🔗 Your deployed API:")
        print(f"   Base URL: {base_url}")
        print(f"   Health: {base_url}/health")
        print(f"   Docs: {base_url}/docs")
        print(f"   API: {base_url}/api/v1/")
        
        return True
    else:
        print(f"\n❌ {total - passed} tests failed")
        print("🔧 Check Railway logs for detailed error information")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_railway_live.py <railway-url>")
        print("Example: python test_railway_live.py https://gallant-enchantment-production.up.railway.app")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    
    print(f"🚂 Railway Live Deployment Test")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Testing URL: {base_url}")
    
    success = test_railway_deployment(base_url)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
