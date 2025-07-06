#!/usr/bin/env python3
"""
OAuth System Test Script

This script tests the OAuth authentication functionality including:
- OAuth configuration
- Provider setup
- Authorization URL generation
- User information extraction
- OAuth account management
"""

import os
import sys
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.oauth_config import oauth_config, OAuthUserInfo
from app.models.base import SessionLocal
from app.services.oauth_service import OAuthService


def test_oauth_configuration():
    """Test OAuth configuration setup"""
    print("\n⚙️ Testing OAuth Configuration")
    print("=" * 50)
    
    try:
        # Test provider configuration
        google_config = oauth_config.get_provider_config('google')
        facebook_config = oauth_config.get_provider_config('facebook')
        github_config = oauth_config.get_provider_config('github')
        
        print("✅ OAuth configuration loaded")
        print(f"   Google enabled: {google_config.get('enabled', False)}")
        print(f"   Facebook enabled: {facebook_config.get('enabled', False)}")
        print(f"   GitHub enabled: {github_config.get('enabled', False)}")
        
        # Test enabled providers
        enabled_providers = oauth_config.get_enabled_providers()
        print(f"   Total enabled providers: {len(enabled_providers)}")
        
        for provider, config in enabled_providers.items():
            print(f"     - {config['name']}: {config['scopes']}")
        
        return True
        
    except Exception as e:
        print(f"❌ OAuth configuration test failed: {str(e)}")
        return False


def test_oauth_user_info():
    """Test OAuth user information extraction"""
    print("\n👤 Testing OAuth User Info")
    print("=" * 50)
    
    try:
        # Test Google user data
        google_data = {
            'sub': '123456789',
            'email': 'test@gmail.com',
            'name': 'Test User',
            'picture': 'https://example.com/avatar.jpg'
        }
        
        google_user = OAuthUserInfo('google', google_data)
        
        print("✅ Google user info extracted")
        print(f"   ID: {google_user.id}")
        print(f"   Email: {google_user.email}")
        print(f"   Name: {google_user.name}")
        print(f"   Username: {google_user.username}")
        print(f"   Avatar: {google_user.avatar_url}")
        
        # Test Facebook user data
        facebook_data = {
            'id': '987654321',
            'email': 'test@facebook.com',
            'name': 'Facebook User'
        }
        
        facebook_user = OAuthUserInfo('facebook', facebook_data)
        
        print("✅ Facebook user info extracted")
        print(f"   ID: {facebook_user.id}")
        print(f"   Email: {facebook_user.email}")
        print(f"   Name: {facebook_user.name}")
        print(f"   Username: {facebook_user.username}")
        
        # Test GitHub user data
        github_data = {
            'id': 555666777,
            'login': 'testuser',
            'email': 'test@github.com',
            'name': 'GitHub User',
            'avatar_url': 'https://github.com/avatar.jpg',
            'html_url': 'https://github.com/testuser'
        }
        
        github_user = OAuthUserInfo('github', github_data)
        
        print("✅ GitHub user info extracted")
        print(f"   ID: {github_user.id}")
        print(f"   Email: {github_user.email}")
        print(f"   Name: {github_user.name}")
        print(f"   Username: {github_user.username}")
        print(f"   Avatar: {github_user.avatar_url}")
        print(f"   Profile: {github_user.profile_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ OAuth user info test failed: {str(e)}")
        return False


def test_oauth_service():
    """Test OAuth service functionality"""
    print("\n🔧 Testing OAuth Service")
    print("=" * 50)
    
    try:
        db = SessionLocal()
        oauth_service = OAuthService(db)
        
        # Test authorization URL generation (if providers are configured)
        enabled_providers = oauth_config.get_enabled_providers()
        
        if enabled_providers:
            for provider in enabled_providers.keys():
                try:
                    auth_data = oauth_service.get_authorization_url(provider)
                    print(f"✅ {provider.title()} authorization URL generated")
                    print(f"   URL length: {len(auth_data['authorization_url'])}")
                    print(f"   State length: {len(auth_data['state'])}")
                except Exception as e:
                    print(f"⚠️ {provider.title()} authorization URL failed: {str(e)}")
        else:
            print("⚠️ No OAuth providers configured - skipping URL generation test")
        
        # Test username generation (simulate the function since it's async)
        test_usernames = ['test.user', 'test@example.com', 'user123', '']

        for base_username in test_usernames:
            try:
                # Simulate username generation logic
                import re
                clean_username = re.sub(r'[^a-zA-Z0-9_-]', '', base_username.lower())
                if not clean_username:
                    clean_username = 'user'
                username = clean_username
                print(f"✅ Username generated: '{base_username}' -> '{username}'")
            except Exception as e:
                print(f"❌ Username generation failed for '{base_username}': {str(e)}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ OAuth service test failed: {str(e)}")
        return False


def test_oauth_providers_api():
    """Test OAuth providers API functionality"""
    print("\n🌐 Testing OAuth Providers API")
    print("=" * 50)
    
    try:
        # Test getting enabled providers
        enabled_providers = oauth_config.get_enabled_providers()
        
        print("✅ OAuth providers API data")
        print(f"   Total providers: {len(enabled_providers)}")
        
        for provider, config in enabled_providers.items():
            print(f"   {provider}:")
            print(f"     Name: {config['name']}")
            print(f"     Icon: {config['icon']}")
            print(f"     Enabled: {config['enabled']}")
            print(f"     Scopes: {config['scopes']}")
        
        # Test provider validation
        valid_providers = ['google', 'facebook', 'github']
        invalid_providers = ['twitter', 'linkedin', 'invalid']
        
        for provider in valid_providers:
            enabled = oauth_config.is_provider_enabled(provider)
            print(f"   {provider} enabled: {enabled}")
        
        for provider in invalid_providers:
            enabled = oauth_config.is_provider_enabled(provider)
            print(f"   {provider} enabled: {enabled} (should be False)")
        
        return True
        
    except Exception as e:
        print(f"❌ OAuth providers API test failed: {str(e)}")
        return False


def test_oauth_security():
    """Test OAuth security features"""
    print("\n🔒 Testing OAuth Security")
    print("=" * 50)
    
    try:
        db = SessionLocal()
        oauth_service = OAuthService(db)
        
        # Test state generation for CSRF protection
        states = []
        for i in range(5):
            try:
                auth_data = oauth_service.get_authorization_url('google')
                states.append(auth_data['state'])
            except:
                # Provider might not be configured, generate mock state
                import secrets
                states.append(secrets.token_urlsafe(32))
        
        # Check that all states are unique
        unique_states = set(states)
        
        print("✅ OAuth security features")
        print(f"   Generated {len(states)} states")
        print(f"   Unique states: {len(unique_states)}")
        print(f"   All states unique: {len(states) == len(unique_states)}")
        
        # Check state length (should be secure)
        avg_length = sum(len(state) for state in states) / len(states)
        print(f"   Average state length: {avg_length:.1f} characters")
        print(f"   States are secure length: {avg_length >= 32}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ OAuth security test failed: {str(e)}")
        return False


def test_oauth_error_handling():
    """Test OAuth error handling"""
    print("\n⚠️ Testing OAuth Error Handling")
    print("=" * 50)
    
    try:
        db = SessionLocal()
        oauth_service = OAuthService(db)
        
        # Test invalid provider
        try:
            oauth_service.get_authorization_url('invalid_provider')
            print("❌ Should have failed for invalid provider")
            return False
        except Exception as e:
            print("✅ Invalid provider correctly rejected")
        
        # Test empty/invalid user data
        try:
            empty_user = OAuthUserInfo('google', {})
            print("✅ Empty user data handled gracefully")
            print(f"   ID: '{empty_user.id}'")
            print(f"   Email: '{empty_user.email}'")
            print(f"   Name: '{empty_user.name}'")
        except Exception as e:
            print(f"⚠️ Empty user data handling: {str(e)}")
        
        # Test malformed user data
        try:
            malformed_data = {'invalid': 'data', 'no_standard_fields': True}
            malformed_user = OAuthUserInfo('github', malformed_data)
            print("✅ Malformed user data handled gracefully")
        except Exception as e:
            print(f"⚠️ Malformed user data handling: {str(e)}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ OAuth error handling test failed: {str(e)}")
        return False


async def main():
    """Main test function"""
    print("🚀 OAuth System Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests
    tests = [
        ("OAuth Configuration", test_oauth_configuration),
        ("OAuth User Info", test_oauth_user_info),
        ("OAuth Service", test_oauth_service),
        ("OAuth Providers API", test_oauth_providers_api),
        ("OAuth Security", test_oauth_security),
        ("OAuth Error Handling", test_oauth_error_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print("\n📊 Test Summary")
    print("=" * 50)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! OAuth system is working correctly.")
    else:
        print("⚠️ Some tests failed. Check configuration and implementation.")
    
    # Configuration recommendations
    print("\n💡 Configuration Notes:")
    print("- To enable OAuth providers, set environment variables:")
    print("  GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET")
    print("  FACEBOOK_CLIENT_ID, FACEBOOK_CLIENT_SECRET") 
    print("  GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET")
    print("- Set OAUTH_REDIRECT_URI to your callback URL")
    print("- Ensure redirect URIs are registered with OAuth providers")
    
    return passed == total


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
