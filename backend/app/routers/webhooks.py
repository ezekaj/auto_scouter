"""
Webhook endpoints for external system integration

This module provides webhook endpoints for integrating with the vehicle scraping system
and other external services.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import hmac
import hashlib
import json

from app.models.base import get_db
from app.services.scraping_integration import (
    handle_new_listing_webhook, 
    handle_scraping_session_webhook,
    ScrapingIntegrationService
)
from app.core.config import settings

router = APIRouter()


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature for security"""
    if not signature or not secret:
        return False
    
    try:
        # Remove 'sha256=' prefix if present
        if signature.startswith('sha256='):
            signature = signature[7:]
        
        # Calculate expected signature
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(signature, expected_signature)
        
    except Exception:
        return False


@router.post("/scraping/new-listing")
async def new_listing_webhook(
    request: Request,
    x_webhook_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint for new vehicle listing notifications
    
    This endpoint is called by the scraping system when new listings are added.
    """
    try:
        # Get request body
        body = await request.body()
        
        # Verify signature if webhook secret is configured
        webhook_secret = getattr(settings, 'WEBHOOK_SECRET', None)
        if webhook_secret and x_webhook_signature:
            if not verify_webhook_signature(body, x_webhook_signature, webhook_secret):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
        
        # Parse JSON payload
        try:
            payload = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
        
        # Validate payload structure
        if 'listing' not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'listing' in payload"
            )
        
        # Handle the webhook
        result = handle_new_listing_webhook(payload['listing'], db)
        
        if result.get('status') == 'error':
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Unknown error')
            )
        
        return {
            "status": "success",
            "message": "New listing processed successfully",
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


@router.post("/scraping/session-complete")
async def scraping_session_complete_webhook(
    request: Request,
    x_webhook_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint for scraping session completion notifications
    
    This endpoint is called when a scraping session is completed.
    """
    try:
        # Get request body
        body = await request.body()
        
        # Verify signature if webhook secret is configured
        webhook_secret = getattr(settings, 'WEBHOOK_SECRET', None)
        if webhook_secret and x_webhook_signature:
            if not verify_webhook_signature(body, x_webhook_signature, webhook_secret):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
        
        # Parse JSON payload
        try:
            payload = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
        
        # Validate payload structure
        if 'session' not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'session' in payload"
            )
        
        # Handle the webhook
        result = handle_scraping_session_webhook(payload['session'], db)
        
        if result.get('status') == 'error':
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Unknown error')
            )
        
        return {
            "status": "success",
            "message": "Scraping session processed successfully",
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


@router.post("/scraping/batch-listings")
async def batch_listings_webhook(
    request: Request,
    x_webhook_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint for batch listing notifications
    
    This endpoint is called when multiple listings are added in a batch.
    """
    try:
        # Get request body
        body = await request.body()
        
        # Verify signature if webhook secret is configured
        webhook_secret = getattr(settings, 'WEBHOOK_SECRET', None)
        if webhook_secret and x_webhook_signature:
            if not verify_webhook_signature(body, x_webhook_signature, webhook_secret):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
        
        # Parse JSON payload
        try:
            payload = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
        
        # Validate payload structure
        if 'listing_ids' not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'listing_ids' in payload"
            )
        
        listing_ids = payload['listing_ids']
        if not isinstance(listing_ids, list) or not listing_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'listing_ids' must be a non-empty list"
            )
        
        # Process batch listings
        integration_service = ScrapingIntegrationService(db)
        result = integration_service.process_new_listings(
            listing_ids, 
            trigger_immediate_matching=payload.get('trigger_immediate', False)
        )
        
        if result.get('status') == 'error':
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Unknown error')
            )
        
        return {
            "status": "success",
            "message": f"Processed {len(listing_ids)} listings successfully",
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


@router.get("/scraping/stats")
def get_scraping_integration_stats(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """
    Get statistics about scraping integration and alert matching
    """
    try:
        integration_service = ScrapingIntegrationService(db)
        stats = integration_service.get_alert_matching_stats(days)
        
        return {
            "status": "success",
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.get("/scraping/optimization")
def get_optimization_recommendations(
    db: Session = Depends(get_db)
):
    """
    Get optimization recommendations for alert matching schedule
    """
    try:
        integration_service = ScrapingIntegrationService(db)
        recommendations = integration_service.optimize_alert_matching_schedule()
        
        return {
            "status": "success",
            "recommendations": recommendations
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )


@router.post("/test/trigger-alert-matching")
def trigger_test_alert_matching(
    check_since_minutes: int = 5,
    db: Session = Depends(get_db)
):
    """
    Manually trigger alert matching for testing purposes
    """
    try:
        integration_service = ScrapingIntegrationService(db)
        result = integration_service.trigger_batch_alert_matching(check_since_minutes)
        
        return {
            "status": "success",
            "message": "Alert matching triggered successfully",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger alert matching: {str(e)}"
        )


@router.get("/health")
def webhook_health_check():
    """Health check endpoint for webhook system"""
    return {
        "status": "healthy",
        "service": "webhook_handler",
        "timestamp": "2024-01-01T00:00:00Z"
    }
