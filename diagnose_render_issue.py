#!/usr/bin/env python3
"""
Render Deployment Diagnostic Tool
Helps diagnose why the backend service is returning 502 errors
"""

import requests
import json
import sys
from datetime import datetime

def test_endpoint(url, description, timeout=30):
    """Test a specific endpoint and return detailed results"""
    print(f"\n🔍 Testing: {description}")
    print(f"URL: {url}")
    print("-" * 60)
    
    try:
        response = requests.get(url, timeout=timeout)
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Response Time: {response.elapsed.total_seconds():.2f}s")
        
        # Print headers
        print("\n📋 Response Headers:")
        for key, value in response.headers.items():
            print(f"   {key}: {value}")
        
        # Try to parse JSON response
        try:
            json_data = response.json()
            print(f"\n📄 JSON Response:")
            print(json.dumps(json_data, indent=2))
            return True, json_data
        except:
            print(f"\n📄 Raw Response:")
            print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
            return response.status_code == 200, response.text
            
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after {timeout} seconds")
        return False, "Timeout"
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False, str(e)
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False, str(e)

def main():
    print("🚀 Auto Scouter Backend Diagnostic Tool")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test different endpoints
    base_url = "https://auto-scouter-backend.onrender.com"
    
    tests = [
        (f"{base_url}", "Root endpoint"),
        (f"{base_url}/health", "Health check endpoint"),
        (f"{base_url}/docs", "API documentation"),
        (f"{base_url}/api/v1/automotive/vehicles/simple?limit=1", "Vehicle API endpoint"),
        (f"{base_url}/api/v1/alerts/", "Alerts API endpoint"),
    ]
    
    results = []
    
    for url, description in tests:
        success, data = test_endpoint(url, description)
        results.append({
            'url': url,
            'description': description,
            'success': success,
            'data': data
        })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    successful_tests = sum(1 for r in results if r['success'])
    total_tests = len(results)
    
    print(f"Tests passed: {successful_tests}/{total_tests}")
    
    if successful_tests == 0:
        print("\n❌ ALL TESTS FAILED - Backend service is not responding")
        print("\n🔧 TROUBLESHOOTING STEPS:")
        print("1. Check Render dashboard for deployment status")
        print("2. Review Render deployment logs for errors")
        print("3. Verify environment variables are set correctly")
        print("4. Check if database connection is working")
        print("5. Ensure all dependencies are installed correctly")
        
    elif successful_tests < total_tests:
        print(f"\n⚠️  PARTIAL SUCCESS - {total_tests - successful_tests} tests failed")
        print("\n🔧 ISSUES FOUND:")
        for result in results:
            if not result['success']:
                print(f"   ❌ {result['description']}: {result['data']}")
                
    else:
        print("\n✅ ALL TESTS PASSED - Backend service is working correctly!")
        print("The connection issue might be on the mobile app side.")
    
    # Specific recommendations
    print("\n🎯 NEXT STEPS:")
    if successful_tests == 0:
        print("1. Go to render.com dashboard")
        print("2. Find your 'auto-scouter-backend' service")
        print("3. Check the 'Logs' tab for error messages")
        print("4. Look for Python/FastAPI startup errors")
        print("5. Verify DATABASE_URL environment variable is set")
    else:
        print("1. Test the mobile app connection again")
        print("2. Check mobile app network settings")
        print("3. Verify API URL in mobile app configuration")
        print("4. Clear mobile app cache if necessary")

if __name__ == "__main__":
    main()
