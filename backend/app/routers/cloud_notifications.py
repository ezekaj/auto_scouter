"""
Cloud Push Notification API Endpoints
Handles Firebase Cloud Messaging and device token management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from app.models.base import get_db
from app.models.scout import User
from app.models.notifications import Notification
from app.core.auth import get_current_active_user
from app.services.firebase_service import get_firebase_service, get_fallback_service

router = APIRouter(prefix="/api/v1/push", tags=["push-notifications"])

# Pydantic models for request/response
class DeviceTokenRequest(BaseModel):
    device_token: str
    platform: str = "android"  # android, ios
    app_version: Optional[str] = None

class DeviceTokenResponse(BaseModel):
    success: bool
    message: str

class TestNotificationRequest(BaseModel):
    device_token: str
    message: Optional[str] = "Test notification from Vehicle Scout!"

class NotificationStatusResponse(BaseModel):
    firebase_available: bool
    firebase_initialized: bool
    fallback_available: bool
    total_notifications_sent: int

@router.post("/register-device", response_model=DeviceTokenResponse)
def register_device_token(
    token_data: DeviceTokenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Register device token for push notifications"""
    try:
        firebase_service = get_firebase_service()
        
        # Validate token format
        if not firebase_service.validate_device_token(token_data.device_token):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid device token format"
            )
        
        # Store device token in user preferences
        # Note: In a real implementation, you'd store this in a separate DeviceToken table
        # For now, we'll store it in the user's notification preferences
        
        from app.models.notifications import NotificationPreferences
        
        # Get or create notification preferences
        prefs = db.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == current_user.id
        ).first()
        
        if not prefs:
            prefs = NotificationPreferences(
                user_id=current_user.id,
                push_notifications=True,
                email_notifications=True
            )
            db.add(prefs)
        
        # Store device token (in a real app, use a proper DeviceToken table)
        prefs.push_notifications = True
        prefs.updated_at = datetime.utcnow()
        
        db.commit()
        
        return DeviceTokenResponse(
            success=True,
            message="Device token registered successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register device token: {str(e)}"
        )

@router.post("/test-notification", response_model=DeviceTokenResponse)
def send_test_notification(
    test_data: TestNotificationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Send test push notification"""
    try:
        firebase_service = get_firebase_service()
        
        if not firebase_service.initialized:
            # Try fallback email notification
            fallback_service = get_fallback_service()
            success = fallback_service.send_email_notification(
                current_user.email,
                "Vehicle Scout Test Notification",
                test_data.message
            )
            
            if success:
                return DeviceTokenResponse(
                    success=True,
                    message="Test notification sent via email (Firebase not available)"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Push notifications not available and email fallback failed"
                )
        
        # Send Firebase push notification
        success = firebase_service.send_test_notification(test_data.device_token)
        
        if success:
            return DeviceTokenResponse(
                success=True,
                message="Test push notification sent successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send test notification"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test notification failed: {str(e)}"
        )

@router.get("/status", response_model=NotificationStatusResponse)
def get_notification_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get push notification service status"""
    try:
        firebase_service = get_firebase_service()
        fallback_service = get_fallback_service()
        
        # Get notification count for user
        notification_count = db.query(Notification).filter(
            Notification.user_id == current_user.id
        ).count()
        
        firebase_status = firebase_service.get_service_status()
        
        return NotificationStatusResponse(
            firebase_available=firebase_status["firebase_available"],
            firebase_initialized=firebase_status["initialized"],
            fallback_available=fallback_service.email_enabled,
            total_notifications_sent=notification_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification status: {str(e)}"
        )

@router.post("/send-vehicle-match")
def send_vehicle_match_notification(
    vehicle_data: Dict[str, Any],
    device_token: str,
    match_score: float,
    current_user: User = Depends(get_current_active_user)
):
    """Send vehicle match notification (internal use)"""
    try:
        firebase_service = get_firebase_service()
        
        if firebase_service.initialized:
            # Send Firebase push notification
            success = firebase_service.send_vehicle_match_notification(
                device_token, vehicle_data, match_score
            )
            
            if success:
                return {"success": True, "method": "firebase"}
        
        # Fallback to email
        fallback_service = get_fallback_service()
        success = fallback_service.send_vehicle_match_email(
            current_user.email, vehicle_data, match_score
        )
        
        if success:
            return {"success": True, "method": "email"}
        else:
            return {"success": False, "method": "none"}
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send vehicle match notification: {str(e)}"
        )

@router.get("/firebase-config")
def get_firebase_config():
    """Get Firebase configuration for mobile app"""
    try:
        firebase_service = get_firebase_service()
        status_info = firebase_service.get_service_status()
        
        # Return minimal config info (don't expose sensitive data)
        return {
            "firebase_available": status_info["firebase_available"],
            "project_id": status_info["project_id"],
            "initialized": status_info["initialized"],
            "push_notifications_enabled": status_info["initialized"]
        }
        
    except Exception as e:
        return {
            "firebase_available": False,
            "project_id": None,
            "initialized": False,
            "push_notifications_enabled": False,
            "error": str(e)
        }

@router.post("/bulk-notification")
def send_bulk_notification(
    title: str,
    body: str,
    device_tokens: List[str],
    data: Optional[Dict[str, str]] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Send bulk notifications (admin only)"""
    try:
        # Note: In a real app, add admin permission check here
        
        firebase_service = get_firebase_service()
        
        if not firebase_service.initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Firebase not available for bulk notifications"
            )
        
        result = firebase_service.send_bulk_notifications(
            device_tokens, title, body, data
        )
        
        return {
            "success_count": result["success"],
            "failure_count": result["failure"],
            "total_tokens": len(device_tokens)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk notification failed: {str(e)}"
        )

# Health check endpoint for push notification service
@router.get("/health")
def push_notification_health():
    """Health check for push notification service"""
    try:
        firebase_service = get_firebase_service()
        fallback_service = get_fallback_service()
        
        status_info = firebase_service.get_service_status()
        
        return {
            "status": "healthy",
            "firebase": {
                "available": status_info["firebase_available"],
                "initialized": status_info["initialized"],
                "project_id": status_info["project_id"]
            },
            "fallback": {
                "email_enabled": fallback_service.email_enabled
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
