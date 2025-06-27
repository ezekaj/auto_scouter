#!/usr/bin/env python3
"""
Quick implementation test script to verify the API works correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported correctly"""
    try:
        print("Testing imports...")
        
        # Test core imports
        from app.models.base import Base, engine
        print("✅ Base models imported successfully")
        
        # Test user and alert models
        from app.models.scout import User, Alert
        print("✅ User and Alert models imported successfully")
        
        # Test automotive models
        from app.models.automotive import VehicleListing
        print("✅ Automotive models imported successfully")
        
        # Test authentication
        from app.core.auth import get_password_hash, verify_password
        print("✅ Authentication utilities imported successfully")
        
        # Test schemas
        from app.schemas.user import UserCreate, AlertCreate
        print("✅ User schemas imported successfully")
        
        # Test routers
        from app.routers.auth import router as auth_router
        from app.routers.alerts import router as alerts_router
        from app.routers.cars import router as cars_router
        print("✅ All routers imported successfully")
        
        # Test main app
        from app.main import app
        print("✅ Main FastAPI app imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_database_creation():
    """Test database table creation"""
    try:
        print("\nTesting database creation...")
        
        from app.models.base import engine, Base
        from app.models.scout import User, Alert
        from app.models.automotive import VehicleListing
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Database creation error: {e}")
        return False

def test_password_hashing():
    """Test password hashing functionality"""
    try:
        print("\nTesting password hashing...")
        
        from app.core.auth import get_password_hash, verify_password
        
        password = "TestPassword123"
        hashed = get_password_hash(password)
        
        # Verify correct password
        assert verify_password(password, hashed), "Password verification failed"
        
        # Verify incorrect password
        assert not verify_password("WrongPassword", hashed), "Wrong password should not verify"
        
        print("✅ Password hashing works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Password hashing error: {e}")
        return False

def test_user_creation():
    """Test user model creation"""
    try:
        print("\nTesting user creation...")
        
        from app.models.scout import User
        from app.core.auth import get_password_hash
        
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=get_password_hash("TestPassword123")
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active == True
        
        print("✅ User model creation works correctly")
        return True
        
    except Exception as e:
        print(f"❌ User creation error: {e}")
        return False

def test_alert_creation():
    """Test alert model creation"""
    try:
        print("\nTesting alert creation...")
        
        from app.models.scout import Alert
        
        alert = Alert(
            user_id=1,
            make="Volkswagen",
            model="Golf",
            min_price=15000,
            max_price=25000,
            year=2020
        )
        
        assert alert.make == "Volkswagen"
        assert alert.model == "Golf"
        assert alert.min_price == 15000
        assert alert.is_active == True
        
        print("✅ Alert model creation works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Alert creation error: {e}")
        return False

def main():
    """Run all tests"""
    print("🔧 Auto Scouter API Implementation Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_database_creation,
        test_password_hashing,
        test_user_creation,
        test_alert_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The implementation is working correctly.")
        print("\n🚀 You can now start the server with:")
        print("   cd backend")
        print("   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("\n📖 API Documentation will be available at:")
        print("   http://localhost:8000/docs")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
