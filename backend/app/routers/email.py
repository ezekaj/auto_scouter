"""
Email Management API Router

This module provides API endpoints for email functionality including:
- Email configuration testing
- Sending test emails
- Email template management
- Email notification preferences
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, EmailStr

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.scout import User
from app.models.notifications import NotificationTemplate, NotificationPreferences, NotificationType
from app.services.email_service import EmailService

router = APIRouter()


class EmailTestRequest(BaseModel):
    """Request model for email testing"""
    to_email: EmailStr
    test_type: str = "basic"  # basic, template, notification


class EmailConfigResponse(BaseModel):
    """Response model for email configuration"""
    enabled: bool
    test_mode: bool
    smtp_host: str
    smtp_port: int
    from_email: str
    from_name: str
    connection_status: Dict[str, Any]


class EmailPreferencesRequest(BaseModel):
    """Request model for updating email preferences"""
    email_enabled: bool = True
    email_frequency: str = "immediate"  # immediate, hourly, daily, weekly
    include_images: bool = True
    include_full_details: bool = True
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"
    max_notifications_per_day: int = 10


@router.get("/config", response_model=EmailConfigResponse)
async def get_email_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get email service configuration and status"""
    email_service = EmailService(db)
    connection_test = email_service.test_connection()
    
    return EmailConfigResponse(
        enabled=email_service.enabled,
        test_mode=email_service.test_mode,
        smtp_host=email_service.smtp_config['host'],
        smtp_port=email_service.smtp_config['port'],
        from_email=email_service.smtp_config['from_email'],
        from_name=email_service.smtp_config['from_name'],
        connection_status=connection_test
    )


@router.post("/test")
async def send_test_email(
    request: EmailTestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send test email to verify configuration"""
    email_service = EmailService(db)
    
    if request.test_type == "basic":
        result = email_service.send_test_email(request.to_email)
    elif request.test_type == "template":
        # Test with a sample template
        result = await _send_template_test_email(email_service, request.to_email, db)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid test type. Use 'basic' or 'template'"
        )
    
    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test email: {result['message']}"
        )
    
    return {
        "message": "Test email sent successfully",
        "details": result,
        "sent_to": request.to_email
    }


@router.get("/templates")
async def get_email_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all email templates"""
    templates = db.query(NotificationTemplate).filter(
        NotificationTemplate.notification_type == NotificationType.EMAIL
    ).all()
    
    return {
        "templates": [
            {
                "id": template.id,
                "name": template.name,
                "language": template.language,
                "subject_template": template.subject_template,
                "is_active": template.is_active,
                "created_at": template.created_at,
                "updated_at": template.updated_at
            }
            for template in templates
        ]
    }


@router.get("/preferences")
async def get_email_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's email notification preferences"""
    preferences = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == current_user.id
    ).first()
    
    if not preferences:
        # Create default preferences
        preferences = NotificationPreferences(
            user_id=current_user.id,
            email_enabled=True,
            email_frequency="immediate"
        )
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    
    return {
        "email_enabled": preferences.email_enabled,
        "email_frequency": preferences.email_frequency,
        "include_images": preferences.include_images,
        "include_full_details": preferences.include_full_details,
        "quiet_hours_enabled": preferences.quiet_hours_enabled,
        "quiet_hours_start": preferences.quiet_hours_start,
        "quiet_hours_end": preferences.quiet_hours_end,
        "max_notifications_per_day": preferences.max_notifications_per_day
    }


@router.put("/preferences")
async def update_email_preferences(
    request: EmailPreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's email notification preferences"""
    preferences = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == current_user.id
    ).first()
    
    if not preferences:
        preferences = NotificationPreferences(user_id=current_user.id)
        db.add(preferences)
    
    # Update preferences
    preferences.email_enabled = request.email_enabled
    preferences.email_frequency = request.email_frequency
    preferences.include_images = request.include_images
    preferences.include_full_details = request.include_full_details
    preferences.quiet_hours_enabled = request.quiet_hours_enabled
    preferences.quiet_hours_start = request.quiet_hours_start
    preferences.quiet_hours_end = request.quiet_hours_end
    preferences.max_notifications_per_day = request.max_notifications_per_day
    
    db.commit()
    
    return {
        "message": "Email preferences updated successfully",
        "preferences": {
            "email_enabled": preferences.email_enabled,
            "email_frequency": preferences.email_frequency,
            "include_images": preferences.include_images,
            "include_full_details": preferences.include_full_details,
            "quiet_hours_enabled": preferences.quiet_hours_enabled,
            "quiet_hours_start": preferences.quiet_hours_start,
            "quiet_hours_end": preferences.quiet_hours_end,
            "max_notifications_per_day": preferences.max_notifications_per_day
        }
    }


@router.post("/send-notification/{user_id}")
async def send_email_notification(
    user_id: int,
    title: str,
    message: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send email notification to a specific user (admin only)"""
    # Check if current user is admin (you may need to implement admin check)
    # For now, allow any authenticated user
    
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not target_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no email address"
        )
    
    email_service = EmailService(db)
    
    # Send simple email
    result = email_service.send_email(
        to_email=target_user.email,
        subject=title,
        text_content=message,
        html_content=f"<p>{message}</p>"
    )
    
    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {result['message']}"
        )
    
    return {
        "message": "Email notification sent successfully",
        "sent_to": target_user.email,
        "sent_at": result['sent_at']
    }


async def _send_template_test_email(email_service: EmailService, to_email: str, db: Session) -> Dict[str, Any]:
    """Send test email using template"""
    # Get a sample template
    template = db.query(NotificationTemplate).filter(
        NotificationTemplate.notification_type == NotificationType.EMAIL,
        NotificationTemplate.is_active == True
    ).first()
    
    if not template:
        return {
            'success': False,
            'message': 'No email template found'
        }
    
    # Create sample context
    context = {
        'user': {'username': 'Test User', 'email': to_email},
        'notification': {'title': 'Test Notification', 'message': 'This is a test message'},
        'listing': {
            'make': 'BMW',
            'model': '3 Series',
            'year': 2020,
            'price': 25000,
            'city': 'Munich',
            'listing_url': 'https://example.com/listing/123'
        },
        'alert': {'name': 'Test Alert'},
        'settings': {
            'app_name': 'Auto Scouter',
            'app_url': 'https://autoscouter.com'
        }
    }
    
    try:
        rendered = email_service.render_template(template, context)
        
        return email_service.send_email(
            to_email=to_email,
            subject=f"[TEST] {rendered['subject']}",
            text_content=rendered['text_content'],
            html_content=rendered['html_content']
        )
    except Exception as e:
        return {
            'success': False,
            'message': f'Template rendering failed: {str(e)}'
        }
