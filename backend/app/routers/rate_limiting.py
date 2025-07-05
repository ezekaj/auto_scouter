"""
Rate Limiting Management API Router

This module provides API endpoints for managing and monitoring rate limits.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.models.base import get_db
from app.models.scout import User

router = APIRouter()

# Global rate limit service instance (will be set by main app)
rate_limit_service = None


class RateLimitStatusResponse(BaseModel):
    """Response model for rate limit status"""
    ip: Dict[str, Any]
    user: Optional[Dict[str, Any]] = None


class RateLimitStatsResponse(BaseModel):
    """Response model for rate limit statistics"""
    storage_type: str
    config: Dict[str, Any]
    redis: Optional[Dict[str, Any]] = None
    memory: Optional[Dict[str, Any]] = None


class RateLimitResetRequest(BaseModel):
    """Request model for resetting rate limits"""
    key_type: str = Field(..., pattern="^(ip|user|endpoint)$")
    identifier: str = Field(..., min_length=1)


@router.get("/status", response_model=RateLimitStatusResponse)
async def get_rate_limit_status(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current rate limit status for the requesting client"""
    if not rate_limit_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting service not available"
        )
    
    # Get client IP
    client_ip = request.client.host if request.client else 'unknown'
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        client_ip = forwarded_for.split(',')[0].strip()
    
    # Get rate limit status
    status_info = rate_limit_service.get_rate_limit_status(
        client_ip=client_ip,
        user_id=str(current_user.id)
    )
    
    return RateLimitStatusResponse(**status_info)


@router.get("/stats", response_model=RateLimitStatsResponse)
async def get_rate_limit_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get rate limiting system statistics (admin only)"""
    # TODO: Add admin check
    # For now, allow all authenticated users
    
    if not rate_limit_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting service not available"
        )
    
    stats = rate_limit_service.get_rate_limit_stats()
    return RateLimitStatsResponse(**stats)


@router.post("/reset")
async def reset_rate_limit(
    reset_request: RateLimitResetRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset rate limit for a specific key (admin only)"""
    # TODO: Add admin check
    # For now, allow all authenticated users to reset their own limits
    
    if not rate_limit_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting service not available"
        )
    
    # Construct the key based on type
    if reset_request.key_type == "ip":
        key = f"ip:{reset_request.identifier}"
    elif reset_request.key_type == "user":
        # Only allow users to reset their own limits (unless admin)
        if reset_request.identifier != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only reset your own rate limits"
            )
        key = f"user:{reset_request.identifier}"
    elif reset_request.key_type == "endpoint":
        key = f"endpoint:{reset_request.identifier}"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid key type"
        )
    
    success = rate_limit_service.reset_rate_limit(key)
    
    if success:
        return {
            "message": f"Rate limit reset successfully for {reset_request.key_type}: {reset_request.identifier}",
            "key": key
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset rate limit"
        )


@router.get("/config")
async def get_rate_limit_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get rate limiting configuration"""
    if not rate_limit_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting service not available"
        )
    
    config = rate_limit_service.config
    
    return {
        "default_limits": config.default_limits,
        "endpoint_limits": config.endpoint_limits,
        "ip_limits": config.ip_limits,
        "storage_type": rate_limit_service.middleware.storage_type
    }


@router.get("/health")
async def get_rate_limit_health():
    """Get rate limiting system health status"""
    if not rate_limit_service:
        return {
            "status": "unavailable",
            "message": "Rate limiting service not initialized"
        }
    
    health_status = {
        "status": "healthy",
        "storage_type": rate_limit_service.middleware.storage_type,
        "timestamp": "2025-07-06T01:25:00Z"
    }
    
    # Check Redis health if using Redis
    if hasattr(rate_limit_service.limiter, 'redis'):
        try:
            rate_limit_service.limiter.redis.ping()
            health_status["redis_status"] = "connected"
        except Exception as e:
            health_status["status"] = "degraded"
            health_status["redis_status"] = "disconnected"
            health_status["redis_error"] = str(e)
    
    return health_status


@router.post("/test")
async def test_rate_limit(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test rate limiting by making a request that counts against limits"""
    if not rate_limit_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiting service not available"
        )
    
    # Get client information
    client_ip = request.client.host if request.client else 'unknown'
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        client_ip = forwarded_for.split(',')[0].strip()
    
    # Check current status before test
    status_before = rate_limit_service.get_rate_limit_status(
        client_ip=client_ip,
        user_id=str(current_user.id)
    )
    
    # Simulate a rate-limited request
    user_limit = rate_limit_service.config.get_user_limit('authenticated')
    key = f"test:user:{current_user.id}"
    allowed, info = rate_limit_service.limiter.is_allowed(
        key, user_limit['limit'], user_limit['window']
    )
    
    return {
        "test_result": {
            "allowed": allowed,
            "limit_info": info
        },
        "status_before": status_before,
        "client_ip": client_ip,
        "user_id": current_user.id,
        "test_key": key
    }


def set_rate_limit_service(service):
    """Set the global rate limit service instance"""
    global rate_limit_service
    rate_limit_service = service
