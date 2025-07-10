#!/usr/bin/env python3
"""
Test script to diagnose startup issues
Run this to see what might be failing during app startup
"""

import os
import sys
import traceback

def test_imports():
    """Test if all required imports work"""
    print("🔍 Testing imports...")
    
    try:
        import fastapi
        print(f"✅ FastAPI: {fastapi.__version__}")
    except Exception as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        print(f"✅ Uvicorn: {uvicorn.__version__}")
    except Exception as e:
        print(f"❌ Uvicorn import failed: {e}")
        return False
    
    try:
        import sqlalchemy
        print(f"✅ SQLAlchemy: {sqlalchemy.__version__}")
    except Exception as e:
        print(f"❌ SQLAlchemy import failed: {e}")
        return False
    
    try:
        import psycopg2
        print(f"✅ Psycopg2: {psycopg2.__version__}")
    except Exception as e:
        print(f"❌ Psycopg2 import failed: {e}")
        return False
    
    return True

def test_environment():
    """Test environment variables"""
    print("\n🔍 Testing environment variables...")
    
    required_vars = ['PORT']
    optional_vars = ['DATABASE_URL', 'SECRET_KEY', 'ENVIRONMENT']
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set (REQUIRED)")
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'SECRET' in var or 'PASSWORD' in var or 'URL' in var:
                masked = value[:10] + "..." if len(value) > 10 else "***"
                print(f"✅ {var}: {masked}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: Not set (optional)")

def test_app_import():
    """Test if the main app can be imported"""
    print("\n🔍 Testing app import...")
    
    try:
        from app.main_cloud import app
        print("✅ Successfully imported app from app.main_cloud")
        return True
    except Exception as e:
        print(f"❌ Failed to import app from app.main_cloud: {e}")
        traceback.print_exc()
        return False

def test_database_connection():
    """Test database connection"""
    print("\n🔍 Testing database connection...")
    
    try:
        from app.core.cloud_config import get_cloud_settings
        settings = get_cloud_settings()
        
        print(f"Database URL configured: {'Yes' if settings.database_url else 'No'}")
        print(f"Is cloud deployed: {settings.is_cloud_deployed}")
        print(f"Environment: {settings.environment}")
        
        # Try to create engine
        from app.models.cloud_base import engine
        print("✅ Database engine created successfully")
        
        # Try a simple connection test
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Database connection test successful")
        
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        traceback.print_exc()
        return False

def main():
    print("🚀 Auto Scouter Backend Startup Diagnostic")
    print("=" * 50)
    
    # Test each component
    imports_ok = test_imports()
    test_environment()
    app_ok = test_app_import()
    db_ok = test_database_connection()
    
    print("\n" + "=" * 50)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    if imports_ok and app_ok:
        print("✅ Basic startup should work")
        if not db_ok:
            print("⚠️  Database issues detected - app may start but have limited functionality")
    else:
        print("❌ Critical startup issues detected")
        print("\n🔧 RECOMMENDED ACTIONS:")
        if not imports_ok:
            print("1. Check requirements.txt and ensure all dependencies are installed")
        if not app_ok:
            print("2. Fix import errors in the application code")
        if not db_ok:
            print("3. Check database configuration and connection")

if __name__ == "__main__":
    main()
