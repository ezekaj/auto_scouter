"""
Admin Monitoring API Endpoints

This module provides admin endpoints for monitoring notification system health and statistics.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import psutil
import os

from app.models.base import get_db
from app.models.scout import User
from app.models.notifications import (
    Notification, NotificationQueue, AlertMatchLog, NotificationPreferences,
    NotificationStatus, NotificationType
)
from app.schemas.notifications import (
    NotificationSystemHealth, NotificationDeliveryReport, NotificationStats,
    AlertMatchRunSummary
)
from app.services.background_tasks import get_task_manager
from app.core.auth import get_current_active_user

router = APIRouter()


# TODO: Add proper admin role checking
def verify_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Verify that the current user has admin privileges"""
    # For now, just check if user is active
    # In production, you should implement proper role-based access control
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/health", response_model=NotificationSystemHealth)
def get_notification_system_health(
    admin_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive health status of the notification system"""
    try:
        # Get queue size
        queue_size = db.query(NotificationQueue).filter(
            NotificationQueue.status == "queued"
        ).count()
        
        # Get failed notifications in last hour
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        failed_notifications_last_hour = db.query(Notification).filter(
            and_(
                Notification.status == NotificationStatus.FAILED,
                Notification.created_at >= hour_ago
            )
        ).count()
        
        # Get average processing time
        recent_completed = db.query(NotificationQueue).filter(
            and_(
                NotificationQueue.status == "completed",
                NotificationQueue.processing_completed_at.isnot(None),
                NotificationQueue.processing_started_at.isnot(None),
                NotificationQueue.processing_completed_at >= hour_ago
            )
        ).all()
        
        if recent_completed:
            processing_times = [
                (item.processing_completed_at - item.processing_started_at).total_seconds()
                for item in recent_completed
            ]
            avg_processing_time = sum(processing_times) / len(processing_times)
        else:
            avg_processing_time = 0.0
        
        # Get last successful alert run
        last_alert_run = db.query(AlertMatchLog).filter(
            AlertMatchLog.status == "completed"
        ).order_by(desc(AlertMatchLog.completed_at)).first()
        
        last_successful_alert_run = last_alert_run.completed_at if last_alert_run else None
        
        # Get system metrics
        system_load = psutil.cpu_percent(interval=1)
        
        # Get task manager status
        task_manager = get_task_manager()
        job_status = task_manager.get_job_status()
        active_workers = 1 if task_manager.is_running else 0
        
        # Determine overall health status
        issues = []
        if queue_size > 100:
            issues.append(f"High queue size: {queue_size} notifications pending")
        
        if failed_notifications_last_hour > 10:
            issues.append(f"High failure rate: {failed_notifications_last_hour} failed in last hour")
        
        if not task_manager.is_running:
            issues.append("Background task scheduler is not running")
        
        if last_successful_alert_run and (datetime.utcnow() - last_successful_alert_run).total_seconds() > 3600:
            issues.append("No successful alert matching run in the last hour")
        
        if system_load > 80:
            issues.append(f"High system load: {system_load}%")
        
        # Determine status
        if len(issues) == 0:
            health_status = "healthy"
        elif len(issues) <= 2:
            health_status = "warning"
        else:
            health_status = "critical"
        
        return NotificationSystemHealth(
            status=health_status,
            queue_size=queue_size,
            failed_notifications_last_hour=failed_notifications_last_hour,
            average_processing_time_seconds=avg_processing_time,
            last_successful_alert_run=last_successful_alert_run,
            active_workers=active_workers,
            system_load=system_load,
            issues=issues
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting system health: {str(e)}"
        )


@router.get("/stats", response_model=NotificationStats)
def get_notification_statistics(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    admin_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive notification statistics"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total notifications
        total_notifications = db.query(Notification).filter(
            Notification.created_at >= start_date
        ).count()
        
        # Notifications by type
        type_stats = db.query(
            Notification.notification_type,
            func.count(Notification.id).label('count')
        ).filter(
            Notification.created_at >= start_date
        ).group_by(Notification.notification_type).all()
        
        notifications_by_type = {
            notification_type: count for notification_type, count in type_stats
        }
        
        # Notifications by status
        status_stats = db.query(
            Notification.status,
            func.count(Notification.id).label('count')
        ).filter(
            Notification.created_at >= start_date
        ).group_by(Notification.status).all()
        
        notifications_by_status = {
            status: count for status, count in status_stats
        }
        
        # Recent notifications (last 24 hours)
        day_ago = datetime.utcnow() - timedelta(hours=24)
        recent_notifications_24h = db.query(Notification).filter(
            Notification.created_at >= day_ago
        ).count()
        
        # Failed notifications (last 24 hours)
        failed_notifications_24h = db.query(Notification).filter(
            and_(
                Notification.created_at >= day_ago,
                Notification.status == NotificationStatus.FAILED
            )
        ).count()
        
        # Average delivery time
        delivered_notifications = db.query(Notification).filter(
            and_(
                Notification.created_at >= start_date,
                Notification.sent_at.isnot(None),
                Notification.delivered_at.isnot(None)
            )
        ).all()
        
        if delivered_notifications:
            delivery_times = [
                (notif.delivered_at - notif.sent_at).total_seconds() / 60
                for notif in delivered_notifications
            ]
            average_delivery_time_minutes = sum(delivery_times) / len(delivery_times)
        else:
            average_delivery_time_minutes = None
        
        return NotificationStats(
            total_notifications=total_notifications,
            notifications_by_type=notifications_by_type,
            notifications_by_status=notifications_by_status,
            recent_notifications_24h=recent_notifications_24h,
            failed_notifications_24h=failed_notifications_24h,
            average_delivery_time_minutes=average_delivery_time_minutes
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting notification statistics: {str(e)}"
        )


@router.get("/delivery-report", response_model=NotificationDeliveryReport)
def get_delivery_report(
    start_date: datetime = Query(..., description="Report start date"),
    end_date: datetime = Query(..., description="Report end date"),
    admin_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """Get detailed delivery report for a specific time period"""
    try:
        # Total sent notifications
        total_sent = db.query(Notification).filter(
            and_(
                Notification.sent_at >= start_date,
                Notification.sent_at <= end_date,
                Notification.status.in_([
                    NotificationStatus.SENT,
                    NotificationStatus.DELIVERED,
                    NotificationStatus.OPENED,
                    NotificationStatus.CLICKED
                ])
            )
        ).count()
        
        # Delivered notifications
        delivered = db.query(Notification).filter(
            and_(
                Notification.sent_at >= start_date,
                Notification.sent_at <= end_date,
                Notification.delivered_at.isnot(None)
            )
        ).count()
        
        # Opened notifications
        opened = db.query(Notification).filter(
            and_(
                Notification.sent_at >= start_date,
                Notification.sent_at <= end_date,
                Notification.opened_at.isnot(None)
            )
        ).count()
        
        # Clicked notifications
        clicked = db.query(Notification).filter(
            and_(
                Notification.sent_at >= start_date,
                Notification.sent_at <= end_date,
                Notification.clicked_at.isnot(None)
            )
        ).count()
        
        # Failed notifications
        failed = db.query(Notification).filter(
            and_(
                Notification.created_at >= start_date,
                Notification.created_at <= end_date,
                Notification.status == NotificationStatus.FAILED
            )
        ).count()
        
        # Calculate rates
        delivery_rate = (delivered / total_sent * 100) if total_sent > 0 else 0
        open_rate = (opened / delivered * 100) if delivered > 0 else 0
        click_rate = (clicked / opened * 100) if opened > 0 else 0
        bounce_rate = (failed / (total_sent + failed) * 100) if (total_sent + failed) > 0 else 0
        
        # Delivery times by type
        delivery_times_by_type = {}
        for notification_type in NotificationType:
            type_notifications = db.query(Notification).filter(
                and_(
                    Notification.sent_at >= start_date,
                    Notification.sent_at <= end_date,
                    Notification.notification_type == notification_type,
                    Notification.delivered_at.isnot(None)
                )
            ).all()
            
            if type_notifications:
                times = [
                    (notif.delivered_at - notif.sent_at).total_seconds()
                    for notif in type_notifications
                ]
                delivery_times_by_type[notification_type] = sum(times) / len(times)
            else:
                delivery_times_by_type[notification_type] = 0.0
        
        return NotificationDeliveryReport(
            period_start=start_date,
            period_end=end_date,
            total_sent=total_sent,
            delivery_rate=delivery_rate,
            open_rate=open_rate,
            click_rate=click_rate,
            bounce_rate=bounce_rate,
            delivery_times_by_type=delivery_times_by_type
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating delivery report: {str(e)}"
        )


@router.get("/alert-runs", response_model=List[AlertMatchRunSummary])
def get_alert_matching_runs(
    limit: int = Query(20, ge=1, le=100, description="Number of runs to return"),
    admin_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """Get recent alert matching run summaries"""
    try:
        runs = db.query(AlertMatchLog).order_by(
            desc(AlertMatchLog.started_at)
        ).limit(limit).all()
        
        return [
            AlertMatchRunSummary(
                run_id=run.run_id,
                started_at=run.started_at,
                completed_at=run.completed_at,
                status=run.status,
                alerts_processed=run.alerts_processed,
                listings_checked=run.listings_checked,
                matches_found=run.matches_found,
                notifications_created=run.notifications_created,
                processing_time_seconds=run.processing_time_seconds,
                error_message=run.error_message
            )
            for run in runs
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting alert runs: {str(e)}"
        )


@router.post("/trigger-alert-matching", response_model=dict)
def trigger_alert_matching(
    admin_user: User = Depends(verify_admin_user)
):
    """Manually trigger alert matching process"""
    try:
        task_manager = get_task_manager()
        result = task_manager.trigger_alert_matching()
        
        return {
            "message": result,
            "triggered_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering alert matching: {str(e)}"
        )


@router.post("/trigger-notification-processing", response_model=dict)
def trigger_notification_processing(
    admin_user: User = Depends(verify_admin_user)
):
    """Manually trigger notification processing"""
    try:
        task_manager = get_task_manager()
        result = task_manager.trigger_notification_processing()
        
        return {
            "message": result,
            "triggered_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering notification processing: {str(e)}"
        )


@router.get("/jobs", response_model=dict)
def get_background_jobs_status(
    admin_user: User = Depends(verify_admin_user)
):
    """Get status of all background jobs"""
    try:
        task_manager = get_task_manager()
        return task_manager.get_job_status()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting job status: {str(e)}"
        )


@router.post("/jobs/{job_id}/pause", response_model=dict)
def pause_background_job(
    job_id: str,
    admin_user: User = Depends(verify_admin_user)
):
    """Pause a specific background job"""
    try:
        task_manager = get_task_manager()
        success = task_manager.pause_job(job_id)
        
        if success:
            return {"message": f"Job {job_id} paused successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to pause job {job_id}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error pausing job: {str(e)}"
        )


@router.post("/jobs/{job_id}/resume", response_model=dict)
def resume_background_job(
    job_id: str,
    admin_user: User = Depends(verify_admin_user)
):
    """Resume a specific background job"""
    try:
        task_manager = get_task_manager()
        success = task_manager.resume_job(job_id)
        
        if success:
            return {"message": f"Job {job_id} resumed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to resume job {job_id}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resuming job: {str(e)}"
        )
