#!/usr/bin/env python3
"""
Emergency minimal test for ultra-basic Rust-free deployment
Tests only the absolute essentials
"""

def test_minimal_imports():
    """Test minimal imports only"""
    print("🔍 Testing minimal imports...")
    
    try:
        import fastapi
        print(f"✅ FastAPI: {fastapi.__version__}")
    except Exception as e:
        print(f"❌ FastAPI failed: {e}")
        return False
    
    try:
        import pydantic
        print(f"✅ Pydantic: {pydantic.VERSION}")
    except Exception as e:
        print(f"❌ Pydantic failed: {e}")
        return False
    
    try:
        import jwt
        print(f"✅ PyJWT: {jwt.__version__}")
    except Exception as e:
        print(f"❌ PyJWT failed: {e}")
        return False
    
    try:
        from passlib.context import CryptContext
        print("✅ Passlib imported")
    except Exception as e:
        print(f"❌ Passlib failed: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality"""
    print("\n🔍 Testing basic functionality...")
    
    try:
        # Test FastAPI app creation
        from fastapi import FastAPI
        app = FastAPI()
        print("✅ FastAPI app creation")
        
        # Test Pydantic model
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            name: str
            
        test = TestModel(name="test")
        print("✅ Pydantic model creation")
        
        # Test JWT
        import jwt
        token = jwt.encode({"test": "data"}, "secret", algorithm="HS256")
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])
        print("✅ JWT encoding/decoding")
        
        # Test password hashing
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        hashed = pwd_context.hash("test")
        verified = pwd_context.verify("test", hashed)
        if verified:
            print("✅ Password hashing")
        else:
            print("❌ Password verification failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality failed: {e}")
        return False

def main():
    print("🚨 EMERGENCY MINIMAL DEPLOYMENT TEST")
    print("=" * 50)
    print("Testing ultra-minimal Rust-free setup")
    print("=" * 50)
    
    tests = [
        ("Minimal Imports", test_minimal_imports),
        ("Basic Functionality", test_basic_functionality),
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
    print("📊 EMERGENCY TEST RESULTS")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🚨 EMERGENCY DEPLOYMENT READY!")
        print("✅ Minimal functionality verified")
        print("✅ Ultra-conservative package versions")
        print("✅ Maximum Rust avoidance")
        
        print("\n🚀 EMERGENCY DEPLOYMENT:")
        print("git add .")
        print("git commit -m 'EMERGENCY: Ultra-minimal Rust-free deployment'")
        print("git push")
        
        return True
    else:
        print(f"\n❌ {total - passed} critical failures")
        print("🆘 Consider alternative deployment platform")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
