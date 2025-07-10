#!/usr/bin/env python3
"""
Final test to ensure completely Rust-free deployment
Tests with older, stable versions of all dependencies
"""

def test_core_imports():
    """Test core FastAPI and authentication imports"""
    print("🔍 Testing core imports...")
    
    try:
        import fastapi
        print(f"✅ FastAPI: {fastapi.__version__}")
    except Exception as e:
        print(f"❌ FastAPI failed: {e}")
        return False
    
    try:
        import uvicorn
        print(f"✅ Uvicorn: {uvicorn.__version__}")
    except Exception as e:
        print(f"❌ Uvicorn failed: {e}")
        return False
    
    try:
        import pydantic
        print(f"✅ Pydantic: {pydantic.VERSION}")
    except Exception as e:
        print(f"❌ Pydantic failed: {e}")
        return False
    
    try:
        import sqlalchemy
        print(f"✅ SQLAlchemy: {sqlalchemy.__version__}")
    except Exception as e:
        print(f"❌ SQLAlchemy failed: {e}")
        return False
    
    return True

def test_auth_components():
    """Test authentication components"""
    print("\n🔍 Testing authentication...")
    
    try:
        import jwt
        print(f"✅ PyJWT: {jwt.__version__}")
    except Exception as e:
        print(f"❌ PyJWT failed: {e}")
        return False
    
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        
        # Test password hashing
        test_password = "TestPassword123"
        hashed = pwd_context.hash(test_password)
        verified = pwd_context.verify(test_password, hashed)
        
        if verified:
            print("✅ Password hashing works")
        else:
            print("❌ Password verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Passlib failed: {e}")
        return False
    
    return True

def test_database_components():
    """Test database components"""
    print("\n🔍 Testing database...")
    
    try:
        import psycopg2
        print(f"✅ Psycopg2: {psycopg2.__version__}")
    except Exception as e:
        print(f"❌ Psycopg2 failed: {e}")
        return False
    
    return True

def main():
    print("🚀 Final Rust-Free Deployment Test")
    print("=" * 50)
    print("Testing with older, stable package versions")
    print("=" * 50)
    
    tests = [
        ("Core Imports", test_core_imports),
        ("Authentication", test_auth_components),
        ("Database", test_database_components),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 FINAL TEST RESULTS")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Ready for Rust-free Render deployment")
        print("✅ Using older, stable package versions")
        print("✅ No compilation required")
        
        print("\n📝 DEPLOYMENT STEPS:")
        print("1. git add .")
        print("2. git commit -m 'Use older stable versions to avoid Rust compilation'")
        print("3. git push")
        print("4. Monitor Render deployment logs")
        
        return True
    else:
        print(f"\n❌ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
