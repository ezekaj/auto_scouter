#!/usr/bin/env python3
"""
Quick Railway Deployment Test
Run this after your Railway deployment completes
"""

import requests
import sys

def quick_test(url):
    """Quick test of Railway deployment"""
    print(f"🚂 Testing Railway deployment: {url}")
    print("=" * 50)
    
    # Test 1: Health Check
    try:
        print("🔍 Testing health endpoint...")
        response = requests.get(f"{url}/health", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health: {data.get('status')} | Database: {data.get('database')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Root endpoint
    try:
        print("🔍 Testing root endpoint...")
        response = requests.get(f"{url}/", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root: {data.get('message')} v{data.get('version')}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        return False
    
    # Test 3: API docs
    try:
        print("🔍 Testing API documentation...")
        response = requests.get(f"{url}/docs", timeout=30)
        if response.status_code == 200:
            print("✅ API docs accessible")
        else:
            print(f"❌ API docs failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API docs error: {e}")
        return False
    
    print("\n🎉 RAILWAY DEPLOYMENT SUCCESSFUL!")
    print(f"🔗 Your API is live at: {url}")
    print(f"📚 Documentation: {url}/docs")
    print(f"❤️  Health check: {url}/health")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_railway_test.py <your-railway-url>")
        print("Example: python quick_railway_test.py https://gallant-enchantment-production.up.railway.app")
        sys.exit(1)
    
    url = sys.argv[1].rstrip('/')
    success = quick_test(url)
    sys.exit(0 if success else 1)
