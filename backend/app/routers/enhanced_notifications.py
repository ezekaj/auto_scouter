"""
Enhanced Notification Management API Endpoints

This module provides comprehensive REST API endpoints for notification management,
preferences, templates, and delivery tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from app.models.base import get_db
from app.models.scout import User
from app.models.notifications import (
    Notification, NotificationPreferences, NotificationTemplate,
    NotificationQueue, NotificationStatus, NotificationType, NotificationFrequency
)
from app.schemas.notifications import (
    NotificationResponse, NotificationPreferencesResponse, NotificationPreferencesUpdate,
    NotificationStats, NotificationTemplateResponse, NotificationQueueResponse
)
from app.core.auth import get_current_active_user
from app.services.enhanced_notification_delivery import NotificationService
from app.tasks.notification_delivery import send_single_notification

router = APIRouter()


@router.get("/", response_model=dict)
def get_user_notifications(
    notification_type: Optional[NotificationType] = Query(None, description="Filter by notification type"),
    status: Optional[NotificationStatus] = Query(None, description="Filter by status"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's notification history with filtering and pagination"""
    try:
        # Build query
        query = db.query(Notification).filter(Notification.user_id == current_user.id)

        # Apply filters
        if notification_type:
            query = query.filter(Notification.notification_type == notification_type)
        
        if status:
            query = query.filter(Notification.status == status)
        
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)
        
        if date_from:
            query = query.filter(Notification.created_at >= date_from)
        
        if date_to:
            query = query.filter(Notification.created_at <= date_to)

        # Get total count
        total_count = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        notifications = query.order_by(desc(Notification.created_at)).offset(offset).limit(page_size).all()

        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size

        return {
            "notifications": notifications,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve notifications: {str(e)}"
        )


@router.get("/unread", response_model=List[NotificationResponse])
def get_unread_notifications(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of notifications"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get unread notifications for the current user"""
    notifications = db.query(Notification).filter(
        and_(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
    ).order_by(desc(Notification.created_at)).limit(limit).all()

    return notifications


@router.post("/{notification_id}/mark-read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    notification = db.query(Notification).filter(
        and_(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    notification.is_read = True
    if not notification.opened_at:
        notification.opened_at = datetime.utcnow()

    db.commit()
    db.refresh(notification)

    return notification


@router.post("/mark-all-read")
def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read for the current user"""
    updated_count = db.query(Notification).filter(
        and_(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
    ).update({
        "is_read": True,
        "opened_at": datetime.utcnow()
    })

    db.commit()

    return {"message": f"Marked {updated_count} notifications as read"}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a notification"""
    notification = db.query(Notification).filter(
        and_(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    db.delete(notification)
    db.commit()

    return {"message": "Notification deleted successfully"}


@router.get("/preferences", response_model=NotificationPreferencesResponse)
def get_notification_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's notification preferences"""
    preferences = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == current_user.id
    ).first()

    if not preferences:
        # Create default preferences
        preferences = NotificationPreferences(user_id=current_user.id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)

    return preferences


@router.put("/preferences", response_model=NotificationPreferencesResponse)
def update_notification_preferences(
    preferences_update: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user's notification preferences"""
    preferences = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == current_user.id
    ).first()

    if not preferences:
        preferences = NotificationPreferences(user_id=current_user.id)
        db.add(preferences)

    # Update preferences
    update_data = preferences_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preferences, field, value)

    db.commit()
    db.refresh(preferences)

    return preferences


@router.get("/stats", response_model=NotificationStats)
def get_notification_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get notification statistics for the current user"""
    since_date = datetime.utcnow() - timedelta(days=days)

    # Total notifications
    total_notifications = db.query(Notification).filter(
        and_(
            Notification.user_id == current_user.id,
            Notification.created_at >= since_date
        )
    ).count()

    # Unread notifications
    unread_notifications = db.query(Notification).filter(
        and_(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
    ).count()

    # Notifications by type
    type_stats = db.query(
        Notification.notification_type,
        func.count(Notification.id).label('count')
    ).filter(
        and_(
            Notification.user_id == current_user.id,
            Notification.created_at >= since_date
        )
    ).group_by(Notification.notification_type).all()

    # Notifications by status
    status_stats = db.query(
        Notification.status,
        func.count(Notification.id).label('count')
    ).filter(
        and_(
            Notification.user_id == current_user.id,
            Notification.created_at >= since_date
        )
    ).group_by(Notification.status).all()

    return {
        "total_notifications": total_notifications,
        "unread_notifications": unread_notifications,
        "notifications_by_type": {item.notification_type: item.count for item in type_stats},
        "notifications_by_status": {item.status: item.count for item in status_stats},
        "period_days": days
    }


@router.post("/{notification_id}/resend")
def resend_notification(
    notification_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Resend a failed notification"""
    notification = db.query(Notification).filter(
        and_(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    if notification.status not in [NotificationStatus.FAILED, NotificationStatus.PENDING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only failed or pending notifications can be resent"
        )

    # Reset notification status
    notification.status = NotificationStatus.PENDING
    notification.retry_count = 0
    notification.error_message = None

    # Queue for background sending
    background_tasks.add_task(send_single_notification.delay, notification_id)

    db.commit()

    return {"message": "Notification queued for resending"}


@router.get("/templates", response_model=List[NotificationTemplateResponse])
def get_notification_templates(
    notification_type: Optional[NotificationType] = Query(None, description="Filter by type"),
    language: str = Query("en", description="Template language"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get available notification templates (admin only for now)"""
    query = db.query(NotificationTemplate).filter(
        and_(
            NotificationTemplate.language == language,
            NotificationTemplate.is_active == True
        )
    )

    if notification_type:
        query = query.filter(NotificationTemplate.notification_type == notification_type)

    templates = query.all()
    return templates


@router.get("/queue", response_model=List[NotificationQueueResponse])
def get_notification_queue_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get notification queue status for user's notifications"""
    queue_items = db.query(NotificationQueue).join(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(desc(NotificationQueue.created_at)).limit(50).all()

    return queue_items


@router.post("/test")
def send_test_notification(
    notification_type: NotificationType = NotificationType.EMAIL,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a test notification to the current user"""
    try:
        # Create test notification
        test_notification = Notification(
            user_id=current_user.id,
            notification_type=notification_type,
            title="Test Notification",
            message="This is a test notification from Auto Scouter.",
            content_data={
                "test": True,
                "timestamp": datetime.utcnow().isoformat()
            },
            priority=1
        )

        db.add(test_notification)
        db.commit()
        db.refresh(test_notification)

        # Send immediately
        notification_service = NotificationService(db)
        success = notification_service.send_notification(test_notification)

        if success:
            return {"message": "Test notification sent successfully", "notification_id": test_notification.id}
        else:
            return {"message": "Test notification failed to send", "notification_id": test_notification.id}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test notification: {str(e)}"
        )
