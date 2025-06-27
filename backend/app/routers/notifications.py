"""
Notification Management API Endpoints

This module provides REST API endpoints for notification history, preferences, and management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional
from datetime import datetime, timedelta
import math

from app.models.base import get_db
from app.models.scout import User
from app.models.notifications import (
    Notification, NotificationPreferences, NotificationTemplate,
    NotificationStatus, NotificationType
)
from app.schemas.notifications import (
    NotificationResponse, NotificationWithDetails, NotificationHistoryResponse,
    NotificationPreferencesResponse, NotificationPreferencesUpdate,
    NotificationStats, UserNotificationStats, NotificationUpdate
)
from app.core.auth import get_current_active_user

router = APIRouter()


@router.get("/", response_model=NotificationHistoryResponse)
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
        
        # Get unread count
        unread_count = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).count()
        
        # Apply pagination and ordering
        offset = (page - 1) * page_size
        notifications = query.order_by(desc(Notification.created_at)).offset(offset).limit(page_size).all()
        
        # Calculate pagination info
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0
        
        return NotificationHistoryResponse(
            notifications=notifications,
            total_count=total_count,
            unread_count=unread_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving notifications: {str(e)}"
        )


@router.get("/{notification_id}", response_model=NotificationWithDetails)
def get_notification_details(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific notification"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Mark as read if it's an in-app notification and not already read
    if (notification.notification_type == NotificationType.IN_APP and 
        not notification.is_read):
        notification.is_read = True
        notification.opened_at = datetime.utcnow()
        db.commit()
    
    # Prepare response with related data
    response_data = notification.__dict__.copy()
    
    # Add alert details if available
    if notification.alert:
        response_data["alert"] = {
            "id": notification.alert.id,
            "make": notification.alert.make,
            "model": notification.alert.model,
            "min_price": notification.alert.min_price,
            "max_price": notification.alert.max_price,
            "year": notification.alert.year,
            "fuel_type": notification.alert.fuel_type,
            "transmission": notification.alert.transmission,
            "city": notification.alert.city
        }
    
    # Add listing details if available
    if notification.listing:
        response_data["listing"] = {
            "id": notification.listing.id,
            "make": notification.listing.make,
            "model": notification.listing.model,
            "year": notification.listing.year,
            "price": notification.listing.price,
            "mileage": notification.listing.mileage,
            "fuel_type": notification.listing.fuel_type,
            "transmission": notification.listing.transmission,
            "city": notification.listing.city,
            "listing_url": notification.listing.listing_url,
            "primary_image_url": notification.listing.primary_image_url
        }
    
    return NotificationWithDetails(**response_data)


@router.post("/{notification_id}/mark-read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
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


@router.post("/mark-all-read", response_model=dict)
def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark all user notifications as read"""
    try:
        updated_count = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).update({
            "is_read": True,
            "opened_at": datetime.utcnow()
        })
        
        db.commit()
        
        return {
            "message": f"Marked {updated_count} notifications as read",
            "updated_count": updated_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking notifications as read: {str(e)}"
        )


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a specific notification"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    db.delete(notification)
    db.commit()
    
    return None


@router.get("/preferences/", response_model=NotificationPreferencesResponse)
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


@router.put("/preferences/", response_model=NotificationPreferencesResponse)
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
        # Create new preferences
        preferences = NotificationPreferences(user_id=current_user.id)
        db.add(preferences)
    
    # Update preferences
    update_data = preferences_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preferences, field, value)
    
    db.commit()
    db.refresh(preferences)
    
    return preferences


@router.get("/stats/summary", response_model=UserNotificationStats)
def get_user_notification_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get notification statistics for the current user"""
    try:
        # Total notifications
        total_notifications = db.query(Notification).filter(
            Notification.user_id == current_user.id
        ).count()
        
        # Unread notifications
        unread_notifications = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).count()
        
        # Notifications in last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        notifications_last_7_days = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.created_at >= week_ago
        ).count()
        
        # Most common alert type (based on notifications with alert_id)
        from sqlalchemy import func
        most_common_result = db.query(
            Notification.alert_id,
            func.count(Notification.id).label('count')
        ).filter(
            Notification.user_id == current_user.id,
            Notification.alert_id.isnot(None)
        ).group_by(Notification.alert_id).order_by(
            func.count(Notification.id).desc()
        ).first()
        
        most_common_alert_type = None
        if most_common_result:
            # Get the alert details
            from app.models.scout import Alert
            alert = db.query(Alert).filter(Alert.id == most_common_result.alert_id).first()
            if alert:
                most_common_alert_type = f"{alert.make or 'Any'} {alert.model or 'Any'}"
        
        return UserNotificationStats(
            user_id=current_user.id,
            total_notifications=total_notifications,
            unread_notifications=unread_notifications,
            notifications_last_7_days=notifications_last_7_days,
            most_common_alert_type=most_common_alert_type
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting notification stats: {str(e)}"
        )


@router.post("/cleanup", response_model=dict)
def cleanup_old_notifications(
    days_old: int = Query(90, ge=30, le=365, description="Delete notifications older than this many days"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Clean up old notifications for the current user"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        deleted_count = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        return {
            "message": f"Deleted {deleted_count} notifications older than {days_old} days",
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning up notifications: {str(e)}"
        )


@router.post("/{notification_id}/track-click", response_model=dict)
def track_notification_click(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Track when a user clicks on a notification link"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Update click tracking
    if not notification.clicked_at:
        notification.clicked_at = datetime.utcnow()
        notification.status = NotificationStatus.CLICKED
        db.commit()
    
    return {
        "message": "Click tracked successfully",
        "notification_id": notification_id,
        "clicked_at": notification.clicked_at.isoformat()
    }
