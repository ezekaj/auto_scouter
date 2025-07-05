#!/usr/bin/env python3
"""
Rate Limiting System Test Script

This script tests the rate limiting functionality including:
- In-memory rate limiting
- Rate limit enforcement
- Rate limit headers
- Different rate limit policies
- Rate limit reset functionality
"""

import os
import sys
import time
import asyncio
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.middleware.rate_limiting import (
    InMemoryRateLimiter, RateLimitConfig, RateLimitMiddleware, RateLimitService
)


def test_in_memory_rate_limiter():
    """Test the in-memory rate limiter"""
    print("\n🧠 Testing In-Memory Rate Limiter")
    print("=" * 50)
    
    try:
        limiter = InMemoryRateLimiter()
        
        # Test basic rate limiting
        key = "test_user_1"
        limit = 5
        window = 60  # 60 seconds
        
        # Make requests up to the limit
        for i in range(limit):
            allowed, info = limiter.is_allowed(key, limit, window)
            print(f"   Request {i+1}: {'✅ Allowed' if allowed else '❌ Blocked'} (Remaining: {info['remaining']})")
            assert allowed, f"Request {i+1} should be allowed"
        
        # Next request should be blocked
        allowed, info = limiter.is_allowed(key, limit, window)
        print(f"   Request {limit+1}: {'✅ Allowed' if allowed else '❌ Blocked'} (Remaining: {info['remaining']})")
        assert not allowed, "Request should be blocked after limit exceeded"
        
        print(f"   Rate limit info: {info}")
        
        return True
        
    except Exception as e:
        print(f"❌ In-memory rate limiter test failed: {str(e)}")
        return False


def test_rate_limit_config():
    """Test rate limit configuration"""
    print("\n⚙️ Testing Rate Limit Configuration")
    print("=" * 50)
    
    try:
        config = RateLimitConfig()
        
        # Test default limits
        anonymous_limit = config.get_user_limit('anonymous')
        authenticated_limit = config.get_user_limit('authenticated')
        premium_limit = config.get_user_limit('premium')
        
        print(f"   Anonymous limit: {anonymous_limit['limit']} requests per {anonymous_limit['window']} seconds")
        print(f"   Authenticated limit: {authenticated_limit['limit']} requests per {authenticated_limit['window']} seconds")
        print(f"   Premium limit: {premium_limit['limit']} requests per {premium_limit['window']} seconds")
        
        assert anonymous_limit['limit'] < authenticated_limit['limit'], "Authenticated users should have higher limits"
        assert authenticated_limit['limit'] < premium_limit['limit'], "Premium users should have highest limits"
        
        # Test endpoint-specific limits
        login_limit = config.get_endpoint_limit('/api/v1/auth/login')
        search_limit = config.get_endpoint_limit('/api/v1/automotive/search')
        
        print(f"   Login endpoint limit: {login_limit}")
        print(f"   Search endpoint limit: {search_limit}")
        
        assert login_limit is not None, "Login endpoint should have specific limits"
        assert login_limit['limit'] < authenticated_limit['limit'], "Login should have stricter limits"
        
        # Test IP limits
        default_ip_limit = config.get_ip_limit('192.168.1.1')
        suspicious_ip_limit = config.get_ip_limit('192.168.1.1', is_suspicious=True)
        
        print(f"   Default IP limit: {default_ip_limit}")
        print(f"   Suspicious IP limit: {suspicious_ip_limit}")
        
        assert suspicious_ip_limit['limit'] < default_ip_limit['limit'], "Suspicious IPs should have stricter limits"
        
        return True
        
    except Exception as e:
        print(f"❌ Rate limit configuration test failed: {str(e)}")
        return False


def test_rate_limit_window():
    """Test rate limit window behavior"""
    print("\n⏰ Testing Rate Limit Window")
    print("=" * 50)
    
    try:
        limiter = InMemoryRateLimiter()
        
        key = "test_window"
        limit = 3
        window = 2  # 2 seconds window
        
        # Make requests up to limit
        for i in range(limit):
            allowed, info = limiter.is_allowed(key, limit, window)
            assert allowed, f"Request {i+1} should be allowed"
        
        # Next request should be blocked
        allowed, info = limiter.is_allowed(key, limit, window)
        assert not allowed, "Request should be blocked"
        print("   ✅ Rate limit enforced correctly")
        
        # Wait for window to expire
        print("   ⏳ Waiting for rate limit window to reset...")
        time.sleep(window + 0.1)  # Wait a bit longer than the window
        
        # Should be allowed again
        allowed, info = limiter.is_allowed(key, limit, window)
        assert allowed, "Request should be allowed after window reset"
        print("   ✅ Rate limit window reset correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Rate limit window test failed: {str(e)}")
        return False


def test_multiple_keys():
    """Test rate limiting with multiple keys"""
    print("\n🔑 Testing Multiple Keys")
    print("=" * 50)
    
    try:
        limiter = InMemoryRateLimiter()
        
        limit = 3
        window = 60
        
        # Test different users
        users = ["user1", "user2", "user3"]
        
        for user in users:
            key = f"user:{user}"
            
            # Each user should have their own limit
            for i in range(limit):
                allowed, info = limiter.is_allowed(key, limit, window)
                assert allowed, f"Request {i+1} for {user} should be allowed"
            
            # Next request should be blocked for this user
            allowed, info = limiter.is_allowed(key, limit, window)
            assert not allowed, f"Request should be blocked for {user}"
            
            print(f"   ✅ Rate limiting working correctly for {user}")
        
        return True
        
    except Exception as e:
        print(f"❌ Multiple keys test failed: {str(e)}")
        return False


def test_rate_limit_service():
    """Test rate limit service functionality"""
    print("\n🔧 Testing Rate Limit Service")
    print("=" * 50)
    
    try:
        # Create middleware and service
        middleware = RateLimitMiddleware()
        service = RateLimitService(middleware)
        
        # Test getting rate limit status
        client_ip = "192.168.1.100"
        user_id = "test_user_123"
        
        status = service.get_rate_limit_status(client_ip, user_id)
        
        print(f"   Rate limit status retrieved:")
        print(f"     IP limit: {status['ip']['limit']} requests per {status['ip']['window']} seconds")
        print(f"     IP remaining: {status['ip']['remaining']}")
        
        if 'user' in status:
            print(f"     User limit: {status['user']['limit']} requests per {status['user']['window']} seconds")
            print(f"     User remaining: {status['user']['remaining']}")
        
        # Test getting stats
        stats = service.get_rate_limit_stats()
        print(f"   Storage type: {stats['storage_type']}")
        print(f"   Config loaded: {'default_limits' in stats['config']}")
        
        # Test reset functionality
        test_key = "test:reset:key"
        success = service.reset_rate_limit(test_key)
        print(f"   Rate limit reset: {'✅ Success' if success else '❌ Failed'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Rate limit service test failed: {str(e)}")
        return False


def test_rate_limit_headers():
    """Test rate limit header information"""
    print("\n📋 Testing Rate Limit Headers")
    print("=" * 50)
    
    try:
        limiter = InMemoryRateLimiter()
        
        key = "test_headers"
        limit = 5
        window = 60
        
        # Make a few requests and check headers
        for i in range(3):
            allowed, info = limiter.is_allowed(key, limit, window)
            
            print(f"   Request {i+1}:")
            print(f"     Allowed: {allowed}")
            print(f"     Limit: {info['limit']}")
            print(f"     Remaining: {info['remaining']}")
            print(f"     Reset Time: {info['reset_time']}")
            print(f"     Retry After: {info['retry_after']}")
            
            assert 'limit' in info, "Rate limit info should include limit"
            assert 'remaining' in info, "Rate limit info should include remaining"
            assert 'reset_time' in info, "Rate limit info should include reset_time"
        
        return True
        
    except Exception as e:
        print(f"❌ Rate limit headers test failed: {str(e)}")
        return False


def test_edge_cases():
    """Test edge cases and error conditions"""
    print("\n🔍 Testing Edge Cases")
    print("=" * 50)
    
    try:
        limiter = InMemoryRateLimiter()
        
        # Test with zero limit
        allowed, info = limiter.is_allowed("zero_limit", 0, 60)
        assert not allowed, "Zero limit should always block"
        print("   ✅ Zero limit handled correctly")
        
        # Test with very short window
        allowed, info = limiter.is_allowed("short_window", 1, 1)
        assert allowed, "First request should be allowed"
        
        allowed, info = limiter.is_allowed("short_window", 1, 1)
        assert not allowed, "Second request should be blocked"
        print("   ✅ Short window handled correctly")
        
        # Test with very large limit
        allowed, info = limiter.is_allowed("large_limit", 1000000, 60)
        assert allowed, "Large limit should allow requests"
        print("   ✅ Large limit handled correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Edge cases test failed: {str(e)}")
        return False


def main():
    """Main test function"""
    print("🚀 Rate Limiting System Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests
    tests = [
        ("In-Memory Rate Limiter", test_in_memory_rate_limiter),
        ("Rate Limit Configuration", test_rate_limit_config),
        ("Rate Limit Window", test_rate_limit_window),
        ("Multiple Keys", test_multiple_keys),
        ("Rate Limit Service", test_rate_limit_service),
        ("Rate Limit Headers", test_rate_limit_headers),
        ("Edge Cases", test_edge_cases)
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
        print("🎉 All tests passed! Rate limiting system is working correctly.")
    else:
        print("⚠️ Some tests failed. Check implementation and logs.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
