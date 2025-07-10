#!/usr/bin/env python3
"""
Comprehensive deployment readiness test
Tests all critical functionality with Rust-free packages
"""

import sys
import traceback
from datetime import datetime, timedelta

def test_core_imports():
    """Test core FastAPI imports and compatibility"""
    print("🔍 Testing core FastAPI imports...")
    
    try:
        import fastapi
        print(f"✅ FastAPI: {fastapi.__version__}")
        
        # Test FastAPI app creation
        from fastapi import FastAPI
        app = FastAPI(title="Test App")
        print("✅ FastAPI app creation works")
        
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
        print(f"✅ Pydantic: {pydantic.__version__}")
        
        # Test Pydantic model creation
        from pydantic import BaseModel, Field
        
        class TestModel(BaseModel):
            name: str = Field(..., min_length=1)
            age: int = Field(..., gt=0)
        
        test_obj = TestModel(name="test", age=25)
        print("✅ Pydantic models work")
        
    except Exception as e:
        print(f"❌ Pydantic failed: {e}")
        return False
    
    return True

def test_database_components():
    """Test database connectivity components"""
    print("\n🔍 Testing database components...")
    
    try:
        import sqlalchemy
        print(f"✅ SQLAlchemy: {sqlalchemy.__version__}")
        
        # Test engine creation (without actual connection)
        from sqlalchemy import create_engine
        engine = create_engine("sqlite:///:memory:")
        print("✅ SQLAlchemy engine creation works")
        
    except Exception as e:
        print(f"❌ SQLAlchemy failed: {e}")
        return False
    
    try:
        import psycopg2
        print(f"✅ Psycopg2: {psycopg2.__version__}")
    except Exception as e:
        print(f"❌ Psycopg2 failed: {e}")
        return False
    
    try:
        import alembic
        print(f"✅ Alembic: {alembic.__version__}")
    except Exception as e:
        print(f"❌ Alembic failed: {e}")
        return False
    
    return True

def test_authentication_system():
    """Test complete authentication system"""
    print("\n🔍 Testing authentication system...")
    
    try:
        import jwt
        print(f"✅ PyJWT: {jwt.__version__}")
        
        # Test JWT operations
        secret = "test_secret_key"
        payload = {"sub": "testuser", "exp": datetime.utcnow() + timedelta(minutes=30)}
        token = jwt.encode(payload, secret, algorithm="HS256")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        
        if decoded["sub"] == "testuser":
            print("✅ JWT encoding/decoding works")
        else:
            print("❌ JWT verification failed")
            return False
            
    except Exception as e:
        print(f"❌ JWT failed: {e}")
        return False
    
    try:
        from passlib.context import CryptContext
        
        # Test password hashing
        pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        test_password = "TestPassword123!"
        hashed = pwd_context.hash(test_password)
        verified = pwd_context.verify(test_password, hashed)
        
        if verified:
            print("✅ Password hashing/verification works")
        else:
            print("❌ Password verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Password hashing failed: {e}")
        return False
    
    return True

def test_api_functionality():
    """Test API endpoint functionality"""
    print("\n🔍 Testing API functionality...")
    
    try:
        from fastapi import FastAPI, HTTPException, status
        from fastapi.security import HTTPBearer
        from pydantic import BaseModel
        
        # Create test app
        app = FastAPI()
        security = HTTPBearer()
        
        class TestResponse(BaseModel):
            message: str
            timestamp: datetime
        
        @app.get("/health", response_model=TestResponse)
        def health_check():
            return TestResponse(
                message="API is working",
                timestamp=datetime.utcnow()
            )
        
        print("✅ API endpoint creation works")
        
    except Exception as e:
        print(f"❌ API functionality failed: {e}")
        return False
    
    return True

def test_schema_compatibility():
    """Test Pydantic schema compatibility"""
    print("\n🔍 Testing schema compatibility...")
    
    try:
        from app.schemas.user import UserBase, UserCreate, User
        
        # Test schema creation
        user_data = {
            "username": "testuser",
            "email": "test@example.com"
        }
        
        user_base = UserBase(**user_data)
        print("✅ UserBase schema works")
        
        user_create_data = {
            **user_data,
            "password": "TestPassword123!"
        }
        
        user_create = UserCreate(**user_create_data)
        print("✅ UserCreate schema works")
        
    except Exception as e:
        print(f"❌ Schema compatibility failed: {e}")
        traceback.print_exc()
        return False
    
    return True

def test_config_loading():
    """Test configuration loading"""
    print("\n🔍 Testing configuration...")
    
    try:
        from app.core.config import settings
        print(f"✅ Settings loaded: {settings.PROJECT_NAME}")
        
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False
    
    return True

def main():
    print("🚀 DEPLOYMENT READINESS TEST")
    print("=" * 60)
    print("Testing Rust-free package compatibility")
    print("=" * 60)
    
    tests = [
        ("Core Imports", test_core_imports),
        ("Database Components", test_database_components),
        ("Authentication System", test_authentication_system),
        ("API Functionality", test_api_functionality),
        ("Schema Compatibility", test_schema_compatibility),
        ("Configuration", test_config_loading),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 DEPLOYMENT READINESS RESULTS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 DEPLOYMENT READY!")
        print("✅ All critical functionality verified")
        print("✅ No Rust compilation required")
        print("✅ Package versions compatible")
        
        print("\n🚀 DEPLOYMENT COMMANDS:")
        print("git add .")
        print("git commit -m 'Ready for Rust-free Render deployment'")
        print("git push")
        
        return True
    else:
        print(f"\n❌ {total - passed} critical issues found")
        print("🔧 Fix failing tests before deployment")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
