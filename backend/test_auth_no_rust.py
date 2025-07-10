#!/usr/bin/env python3
"""
Test script to verify authentication works with pure Python dependencies
No Rust compilation required
"""

import sys
import traceback
from datetime import timedelta

def test_imports():
    """Test that all authentication imports work without Rust dependencies"""
    print("🔍 Testing imports (no Rust compilation)...")
    
    try:
        import jwt
        print(f"✅ PyJWT: {jwt.__version__}")
    except Exception as e:
        print(f"❌ PyJWT import failed: {e}")
        return False
    
    try:
        from passlib.context import CryptContext
        print("✅ Passlib CryptContext imported successfully")
    except Exception as e:
        print(f"❌ Passlib import failed: {e}")
        return False
    
    try:
        # Test PBKDF2 context creation (pure Python)
        pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        print("✅ PBKDF2 context created successfully")
    except Exception as e:
        print(f"❌ PBKDF2 context creation failed: {e}")
        return False
    
    return True

def test_password_hashing():
    """Test password hashing and verification"""
    print("\n🔍 Testing password hashing...")
    
    try:
        from passlib.context import CryptContext
        
        # Create context with pure Python PBKDF2
        pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        
        # Test password hashing
        test_password = "test_password_123"
        hashed = pwd_context.hash(test_password)
        print(f"✅ Password hashed successfully: {hashed[:50]}...")
        
        # Test password verification
        is_valid = pwd_context.verify(test_password, hashed)
        if is_valid:
            print("✅ Password verification successful")
        else:
            print("❌ Password verification failed")
            return False
        
        # Test wrong password
        is_invalid = pwd_context.verify("wrong_password", hashed)
        if not is_invalid:
            print("✅ Wrong password correctly rejected")
        else:
            print("❌ Wrong password incorrectly accepted")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Password hashing test failed: {e}")
        traceback.print_exc()
        return False

def test_jwt_tokens():
    """Test JWT token creation and verification"""
    print("\n🔍 Testing JWT tokens...")
    
    try:
        import jwt
        from datetime import datetime, timedelta
        
        # Test data
        secret_key = "test_secret_key_for_testing"
        algorithm = "HS256"
        test_data = {"sub": "testuser", "exp": datetime.utcnow() + timedelta(minutes=30)}
        
        # Create token
        token = jwt.encode(test_data, secret_key, algorithm=algorithm)
        print(f"✅ JWT token created: {token[:50]}...")
        
        # Verify token
        decoded = jwt.decode(token, secret_key, algorithms=[algorithm])
        if decoded["sub"] == "testuser":
            print("✅ JWT token verification successful")
        else:
            print("❌ JWT token verification failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ JWT token test failed: {e}")
        traceback.print_exc()
        return False

def test_auth_module():
    """Test the actual auth module"""
    print("\n🔍 Testing auth module...")
    
    try:
        # Import the auth functions
        from app.core.auth import get_password_hash, verify_password, create_access_token
        
        # Test password functions
        test_password = "test_auth_password"
        hashed = get_password_hash(test_password)
        print(f"✅ Auth module password hashing works")
        
        # Test verification
        if verify_password(test_password, hashed):
            print("✅ Auth module password verification works")
        else:
            print("❌ Auth module password verification failed")
            return False
        
        # Test JWT creation
        token_data = {"sub": "testuser"}
        token = create_access_token(token_data, expires_delta=timedelta(minutes=30))
        print(f"✅ Auth module JWT creation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Auth module test failed: {e}")
        traceback.print_exc()
        return False

def main():
    print("🚀 Authentication Test Suite (No Rust Dependencies)")
    print("=" * 60)
    
    # Run all tests
    tests = [
        ("Import Test", test_imports),
        ("Password Hashing Test", test_password_hashing),
        ("JWT Token Test", test_jwt_tokens),
        ("Auth Module Test", test_auth_module),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Authentication system ready for Render deployment")
        print("✅ No Rust compilation required")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed")
        print("🔧 Fix the failing tests before deployment")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
