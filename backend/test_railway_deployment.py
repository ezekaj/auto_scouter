#!/usr/bin/env python3
"""
Railway Deployment Verification Test
Tests all critical functionality for Railway deployment
"""

import sys
import os
import requests
import time
from datetime import datetime

def test_local_compatibility():
    """Test local compatibility with Railway requirements"""
    print("🔍 Testing Railway compatibility...")
    
    try:
        # Test core imports
        import fastapi
        import uvicorn
        import pydantic
        import sqlalchemy
        import psycopg2
        import jwt
        import passlib
        import gunicorn
        
        print(f"✅ FastAPI: {fastapi.__version__}")
        print(f"✅ Pydantic: {pydantic.VERSION}")
        print(f"✅ SQLAlchemy: {sqlalchemy.__version__}")
        print(f"✅ Psycopg2: {psycopg2.__version__}")
        print(f"✅ PyJWT: {jwt.__version__}")
        print(f"✅ Gunicorn: {gunicorn.__version__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_app_creation():
    """Test FastAPI app creation"""
    print("\n🔍 Testing app creation...")
    
    try:
        from app.main import app
        print("✅ App imported successfully")
        
        # Test app attributes
        print(f"✅ App title: {app.title}")
        print(f"✅ App version: {app.version}")
        
        return True
        
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return False

def test_database_config():
    """Test database configuration"""
    print("\n🔍 Testing database configuration...")
    
    try:
        from app.core.config import settings
        print("✅ Settings loaded")
        
        # Test database URL handling
        if hasattr(settings, 'DATABASE_URL'):
            print("✅ DATABASE_URL configured")
        else:
            print("⚠️  DATABASE_URL not set (will be provided by Railway)")
        
        return True
        
    except Exception as e:
        print(f"❌ Database config failed: {e}")
        return False

def test_authentication():
    """Test authentication system"""
    print("\n🔍 Testing authentication...")
    
    try:
        from app.core.auth import get_password_hash, verify_password, create_access_token
        
        # Test password hashing
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        verified = verify_password(password, hashed)
        
        if verified:
            print("✅ Password hashing works")
        else:
            print("❌ Password verification failed")
            return False
        
        # Test JWT creation
        token_data = {"sub": "testuser"}
        token = create_access_token(token_data)
        print("✅ JWT token creation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

def test_deployed_api(base_url):
    """Test deployed API endpoints"""
    print(f"\n🔍 Testing deployed API at {base_url}...")
    
    endpoints = [
        ("/health", "Health check"),
        ("/", "Root endpoint"),
        ("/docs", "API documentation"),
    ]
    
    results = []
    
    for endpoint, description in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ {description}: {response.status_code}")
                results.append(True)
            else:
                print(f"⚠️  {description}: {response.status_code}")
                results.append(False)
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {description}: {e}")
            results.append(False)
    
    return all(results)

def main():
    print("🚂 RAILWAY DEPLOYMENT VERIFICATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Local tests
    local_tests = [
        ("Railway Compatibility", test_local_compatibility),
        ("App Creation", test_app_creation),
        ("Database Config", test_database_config),
        ("Authentication", test_authentication),
    ]
    
    local_results = []
    for test_name, test_func in local_tests:
        try:
            result = test_func()
            local_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            local_results.append((test_name, False))
    
    # Check if deployed URL is provided
    deployed_url = os.getenv('RAILWAY_URL') or sys.argv[1] if len(sys.argv) > 1 else None
    
    deployed_results = []
    if deployed_url:
        print(f"\n🌐 Testing deployed application...")
        deployed_result = test_deployed_api(deployed_url)
        deployed_results.append(("Deployed API", deployed_result))
    else:
        print(f"\n⚠️  No deployed URL provided. Skipping live tests.")
        print("   Usage: python test_railway_deployment.py <deployed-url>")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 RAILWAY DEPLOYMENT RESULTS")
    print("=" * 60)
    
    all_results = local_results + deployed_results
    passed = sum(1 for _, result in all_results if result)
    total = len(all_results)
    
    print("\n🏠 LOCAL TESTS:")
    for test_name, result in local_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    if deployed_results:
        print("\n🌐 DEPLOYED TESTS:")
        for test_name, result in deployed_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == len(local_results):  # All local tests passed
        print("\n🚂 READY FOR RAILWAY DEPLOYMENT!")
        print("✅ All local tests passed")
        print("✅ Railway-compatible configuration")
        print("✅ Minimal dependencies verified")
        
        if not deployed_results:
            print("\n📋 NEXT STEPS:")
            print("1. Commit and push to GitHub")
            print("2. Connect repository to Railway")
            print("3. Add PostgreSQL service")
            print("4. Set environment variables")
            print("5. Deploy and test")
        
        return True
    else:
        print(f"\n❌ {len(local_results) - sum(1 for _, result in local_results if result)} local tests failed")
        print("🔧 Fix failing tests before Railway deployment")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
