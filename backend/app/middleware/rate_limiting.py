"""
Rate Limiting Middleware

This module provides comprehensive rate limiting functionality including:
- Request rate limiting per IP and per user
- Different rate limits for different endpoints
- Redis-based storage for distributed systems
- Graceful fallback to in-memory storage
- Configurable rate limit policies
- Rate limit headers in responses
"""

import time
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
import hashlib
import json

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """In-memory rate limiter for single-instance deployments"""
    
    def __init__(self):
        self.requests = defaultdict(deque)
        self.blocked_until = defaultdict(float)
    
    def is_allowed(self, key: str, limit: int, window: int) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed and return rate limit info"""
        now = time.time()
        
        # Check if currently blocked
        if key in self.blocked_until and now < self.blocked_until[key]:
            remaining_block_time = int(self.blocked_until[key] - now)
            return False, {
                'allowed': False,
                'limit': limit,
                'remaining': 0,
                'reset_time': int(self.blocked_until[key]),
                'retry_after': remaining_block_time,
                'blocked': True
            }
        
        # Clean old requests outside the window
        window_start = now - window
        request_times = self.requests[key]
        
        while request_times and request_times[0] < window_start:
            request_times.popleft()
        
        # Check if limit exceeded
        if len(request_times) >= limit:
            # Block for the remaining window time
            if request_times:
                oldest_request = request_times[0]
                reset_time = oldest_request + window
            else:
                reset_time = now + window
            self.blocked_until[key] = reset_time

            return False, {
                'allowed': False,
                'limit': limit,
                'remaining': 0,
                'reset_time': int(reset_time),
                'retry_after': int(reset_time - now),
                'blocked': False
            }
        
        # Allow request and record it
        request_times.append(now)
        remaining = limit - len(request_times)
        
        return True, {
            'allowed': True,
            'limit': limit,
            'remaining': remaining,
            'reset_time': int(now + window),
            'retry_after': 0,
            'blocked': False
        }


class RedisRateLimiter:
    """Redis-based rate limiter for distributed deployments"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def is_allowed(self, key: str, limit: int, window: int) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed using Redis sliding window"""
        try:
            now = time.time()
            pipeline = self.redis.pipeline()
            
            # Remove old entries
            pipeline.zremrangebyscore(key, 0, now - window)
            
            # Count current requests
            pipeline.zcard(key)
            
            # Add current request
            pipeline.zadd(key, {str(now): now})
            
            # Set expiration
            pipeline.expire(key, window + 1)
            
            results = pipeline.execute()
            current_requests = results[1]
            
            if current_requests >= limit:
                # Get the oldest request to calculate reset time
                oldest = self.redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    reset_time = oldest[0][1] + window
                else:
                    reset_time = now + window
                
                return False, {
                    'allowed': False,
                    'limit': limit,
                    'remaining': 0,
                    'reset_time': int(reset_time),
                    'retry_after': int(reset_time - now),
                    'blocked': False
                }
            
            remaining = limit - current_requests - 1  # -1 for the current request
            
            return True, {
                'allowed': True,
                'limit': limit,
                'remaining': max(0, remaining),
                'reset_time': int(now + window),
                'retry_after': 0,
                'blocked': False
            }
            
        except Exception as e:
            logger.error(f"Redis rate limiter error: {str(e)}")
            # Fallback to allowing the request
            return True, {
                'allowed': True,
                'limit': limit,
                'remaining': limit - 1,
                'reset_time': int(time.time() + window),
                'retry_after': 0,
                'blocked': False,
                'error': 'redis_unavailable'
            }


class RateLimitConfig:
    """Rate limit configuration"""
    
    def __init__(self):
        # Default rate limits (requests per minute)
        self.default_limits = {
            'anonymous': {'limit': 60, 'window': 60},  # 60 requests per minute
            'authenticated': {'limit': 300, 'window': 60},  # 300 requests per minute
            'premium': {'limit': 1000, 'window': 60}  # 1000 requests per minute
        }
        
        # Endpoint-specific limits
        self.endpoint_limits = {
            '/api/v1/auth/login': {'limit': 5, 'window': 300},  # 5 login attempts per 5 minutes
            '/api/v1/auth/register': {'limit': 3, 'window': 3600},  # 3 registrations per hour
            '/api/v1/auth/reset-password': {'limit': 3, 'window': 3600},  # 3 password resets per hour
            '/api/v1/automotive/search': {'limit': 100, 'window': 60},  # 100 searches per minute
            '/api/v1/email/test': {'limit': 5, 'window': 300},  # 5 test emails per 5 minutes
            '/api/v1/analytics/export': {'limit': 10, 'window': 3600},  # 10 exports per hour
        }
        
        # IP-based limits (stricter for unknown IPs)
        self.ip_limits = {
            'default': {'limit': 1000, 'window': 3600},  # 1000 requests per hour per IP
            'strict': {'limit': 100, 'window': 3600}  # 100 requests per hour for suspicious IPs
        }
    
    def get_user_limit(self, user_type: str) -> Dict[str, int]:
        """Get rate limit for user type"""
        return self.default_limits.get(user_type, self.default_limits['anonymous'])
    
    def get_endpoint_limit(self, endpoint: str) -> Optional[Dict[str, int]]:
        """Get specific limit for endpoint"""
        return self.endpoint_limits.get(endpoint)
    
    def get_ip_limit(self, ip: str, is_suspicious: bool = False) -> Dict[str, int]:
        """Get rate limit for IP address"""
        if is_suspicious:
            return self.ip_limits['strict']
        return self.ip_limits['default']


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, redis_client=None):
        self.config = RateLimitConfig()
        
        # Try to use Redis, fallback to in-memory
        if redis_client:
            try:
                redis_client.ping()
                self.limiter = RedisRateLimiter(redis_client)
                self.storage_type = "redis"
                logger.info("Rate limiting using Redis storage")
            except Exception as e:
                logger.warning(f"Redis unavailable, using in-memory storage: {str(e)}")
                self.limiter = InMemoryRateLimiter()
                self.storage_type = "memory"
        else:
            self.limiter = InMemoryRateLimiter()
            self.storage_type = "memory"
            logger.info("Rate limiting using in-memory storage")
    
    async def __call__(self, request: Request, call_next):
        """Process request with rate limiting"""
        
        # Skip rate limiting for health checks and static files
        if self._should_skip_rate_limiting(request):
            return await call_next(request)
        
        # Get client information
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id(request)
        endpoint = self._normalize_endpoint(request.url.path)
        
        # Check rate limits
        rate_limit_result = await self._check_rate_limits(
            request, client_ip, user_id, endpoint
        )
        
        if not rate_limit_result['allowed']:
            return self._create_rate_limit_response(rate_limit_result)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        self._add_rate_limit_headers(response, rate_limit_result)
        
        return response
    
    def _should_skip_rate_limiting(self, request: Request) -> bool:
        """Check if rate limiting should be skipped for this request"""
        skip_paths = ['/health', '/docs', '/redoc', '/openapi.json', '/favicon.ico']
        return any(request.url.path.startswith(path) for path in skip_paths)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        # Check for forwarded headers (for reverse proxies)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else 'unknown'
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request (if authenticated)"""
        # This would typically extract from JWT token or session
        # For now, we'll check if there's an Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            # In a real implementation, you'd decode the JWT here
            # For now, we'll create a hash of the token
            token = auth_header[7:]  # Remove 'Bearer '
            return hashlib.md5(token.encode()).hexdigest()[:16]
        return None
    
    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for rate limiting"""
        # Remove query parameters and trailing slashes
        path = path.rstrip('/')
        
        # Replace path parameters with placeholders
        # This is a simple implementation - in production you might want more sophisticated path normalization
        import re
        path = re.sub(r'/\d+', '/{id}', path)
        
        return path
    
    async def _check_rate_limits(self, request: Request, client_ip: str, 
                                user_id: Optional[str], endpoint: str) -> Dict[str, Any]:
        """Check all applicable rate limits"""
        
        # 1. Check endpoint-specific limits first
        endpoint_limit = self.config.get_endpoint_limit(endpoint)
        if endpoint_limit:
            key = f"endpoint:{endpoint}:{client_ip}"
            allowed, info = self.limiter.is_allowed(
                key, endpoint_limit['limit'], endpoint_limit['window']
            )
            if not allowed:
                info['limit_type'] = 'endpoint'
                info['endpoint'] = endpoint
                return info
        
        # 2. Check user-specific limits
        if user_id:
            user_type = self._get_user_type(user_id)
            user_limit = self.config.get_user_limit(user_type)
            key = f"user:{user_id}"
            allowed, info = self.limiter.is_allowed(
                key, user_limit['limit'], user_limit['window']
            )
            if not allowed:
                info['limit_type'] = 'user'
                info['user_type'] = user_type
                return info
        
        # 3. Check IP-based limits
        is_suspicious = self._is_suspicious_ip(client_ip)
        ip_limit = self.config.get_ip_limit(client_ip, is_suspicious)
        key = f"ip:{client_ip}"
        allowed, info = self.limiter.is_allowed(
            key, ip_limit['limit'], ip_limit['window']
        )
        info['limit_type'] = 'ip'
        info['ip'] = client_ip
        
        return info
    
    def _get_user_type(self, user_id: str) -> str:
        """Determine user type for rate limiting"""
        # In a real implementation, you'd query the database
        # For now, return 'authenticated' for all users
        return 'authenticated'
    
    def _is_suspicious_ip(self, ip: str) -> bool:
        """Check if IP address is suspicious"""
        # In a real implementation, you might check against:
        # - Known bot IPs
        # - IPs with recent violations
        # - Geolocation-based rules
        # - Threat intelligence feeds
        return False
    
    def _create_rate_limit_response(self, rate_limit_info: Dict[str, Any]) -> JSONResponse:
        """Create rate limit exceeded response"""
        
        message = "Rate limit exceeded"
        if rate_limit_info.get('limit_type') == 'endpoint':
            message = f"Rate limit exceeded for endpoint {rate_limit_info.get('endpoint', 'unknown')}"
        elif rate_limit_info.get('limit_type') == 'user':
            message = f"Rate limit exceeded for user ({rate_limit_info.get('user_type', 'unknown')} tier)"
        elif rate_limit_info.get('limit_type') == 'ip':
            message = f"Rate limit exceeded for IP address"
        
        response_data = {
            "error": "rate_limit_exceeded",
            "message": message,
            "limit": rate_limit_info['limit'],
            "remaining": rate_limit_info['remaining'],
            "reset_time": rate_limit_info['reset_time'],
            "retry_after": rate_limit_info['retry_after']
        }
        
        headers = {
            "X-RateLimit-Limit": str(rate_limit_info['limit']),
            "X-RateLimit-Remaining": str(rate_limit_info['remaining']),
            "X-RateLimit-Reset": str(rate_limit_info['reset_time']),
            "Retry-After": str(rate_limit_info['retry_after'])
        }
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=response_data,
            headers=headers
        )
    
    def _add_rate_limit_headers(self, response: Response, rate_limit_info: Dict[str, Any]):
        """Add rate limit headers to successful responses"""
        response.headers["X-RateLimit-Limit"] = str(rate_limit_info['limit'])
        response.headers["X-RateLimit-Remaining"] = str(rate_limit_info['remaining'])
        response.headers["X-RateLimit-Reset"] = str(rate_limit_info['reset_time'])
        
        if self.storage_type:
            response.headers["X-RateLimit-Storage"] = self.storage_type


class RateLimitService:
    """Service for managing and monitoring rate limits"""

    def __init__(self, middleware: RateLimitMiddleware):
        self.middleware = middleware
        self.config = middleware.config
        self.limiter = middleware.limiter

    def get_rate_limit_status(self, client_ip: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current rate limit status for a client"""
        status = {}

        # IP-based limits
        ip_limit = self.config.get_ip_limit(client_ip)
        key = f"ip:{client_ip}"
        allowed, info = self.limiter.is_allowed(key, ip_limit['limit'], ip_limit['window'])
        status['ip'] = {
            'limit': ip_limit['limit'],
            'window': ip_limit['window'],
            'remaining': info['remaining'],
            'reset_time': info['reset_time']
        }

        # User-based limits
        if user_id:
            user_type = self.middleware._get_user_type(user_id)
            user_limit = self.config.get_user_limit(user_type)
            key = f"user:{user_id}"
            allowed, info = self.limiter.is_allowed(key, user_limit['limit'], user_limit['window'])
            status['user'] = {
                'type': user_type,
                'limit': user_limit['limit'],
                'window': user_limit['window'],
                'remaining': info['remaining'],
                'reset_time': info['reset_time']
            }

        return status

    def reset_rate_limit(self, key: str) -> bool:
        """Reset rate limit for a specific key (admin function)"""
        try:
            if hasattr(self.limiter, 'redis'):
                # Redis implementation
                self.limiter.redis.delete(key)
            else:
                # In-memory implementation
                if key in self.limiter.requests:
                    del self.limiter.requests[key]
                if key in self.limiter.blocked_until:
                    del self.limiter.blocked_until[key]
            return True
        except Exception as e:
            logger.error(f"Failed to reset rate limit for key {key}: {str(e)}")
            return False

    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        stats = {
            'storage_type': self.middleware.storage_type,
            'config': {
                'default_limits': self.config.default_limits,
                'endpoint_limits': self.config.endpoint_limits,
                'ip_limits': self.config.ip_limits
            }
        }

        if hasattr(self.limiter, 'redis'):
            try:
                # Redis stats
                info = self.limiter.redis.info()
                stats['redis'] = {
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory': info.get('used_memory_human', 'unknown'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                }
            except Exception as e:
                stats['redis'] = {'error': str(e)}
        else:
            # In-memory stats
            stats['memory'] = {
                'active_keys': len(self.limiter.requests),
                'blocked_keys': len(self.limiter.blocked_until)
            }

        return stats
