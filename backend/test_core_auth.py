#!/usr/bin/env python3
"""
Core authentication test - focuses on the critical components that caused Rust compilation issues
"""

def test_no_rust_dependencies():
    """Verify that no Rust compilation is required"""
    print("🔍 Testing for Rust-free dependencies...")
    
    # Test PyJWT (pure Python)
    import jwt
    print(f"✅ PyJWT {jwt.__version__} - Pure Python JWT library")
    
    # Test Passlib with PBKDF2 (pure Python)
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    print("✅ Passlib with PBKDF2 - Pure Python password hashing")
    
    # Test password operations
    test_password = "render_deployment_test"
    hashed = pwd_context.hash(test_password)
    verified = pwd_context.verify(test_password, hashed)
    
    if verified:
        print("✅ Password hashing and verification working")
    else:
        raise Exception("Password verification failed")
    
    # Test JWT operations
    from datetime import datetime, timedelta
    token_data = {"sub": "render_test", "exp": datetime.utcnow() + timedelta(minutes=30)}
    token = jwt.encode(token_data, "test_secret", algorithm="HS256")
    decoded = jwt.decode(token, "test_secret", algorithms=["HS256"])
    
    if decoded["sub"] == "render_test":
        print("✅ JWT creation and verification working")
    else:
        raise Exception("JWT verification failed")
    
    print("\n🎉 SUCCESS: All authentication components work without Rust compilation!")
    return True

if __name__ == "__main__":
    try:
        test_no_rust_dependencies()
        print("\n✅ READY FOR RENDER DEPLOYMENT")
        print("📝 Commit and push these changes to deploy")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
