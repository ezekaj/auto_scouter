"""
Celery tasks for notification delivery
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from celery import current_task
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.celery_app import celery_app
from app.models.base import SessionLocal
from app.models.scout import User
from app.models.notifications import (
    Notification, NotificationQueue, NotificationPreferences,
    NotificationStatus, NotificationType, NotificationFrequency
)
from app.services.notification_delivery import NotificationDeliveryService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_notification_queue(self, batch_size: int = 50):
    """
    Process pending notifications in the queue
    
    Args:
        batch_size: Number of notifications to process in this batch
    """
    db = SessionLocal()
    try:
        logger.info(f"Processing notification queue, batch size: {batch_size}")
        
        # Get pending notifications from queue
        pending_notifications = db.query(NotificationQueue).filter(
            NotificationQueue.status == "queued",
            or_(
                NotificationQueue.scheduled_for.is_(None),
                NotificationQueue.scheduled_for <= datetime.utcnow()
            )
        ).order_by(
            NotificationQueue.priority.desc(),
            NotificationQueue.created_at.asc()
        ).limit(batch_size).all()
        
        if not pending_notifications:
            logger.info("No pending notifications to process")
            return {"status": "no_notifications", "processed": 0}
        
        notification_service = NotificationService(db)
        processed_count = 0
        failed_count = 0
        
        for queue_item in pending_notifications:
            try:
                # Mark as processing
                queue_item.status = "processing"
                queue_item.processing_started_at = datetime.utcnow()
                queue_item.worker_id = self.request.id
                db.commit()
                
                # Get the notification
                notification = db.query(Notification).filter(
                    Notification.id == queue_item.notification_id
                ).first()
                
                if not notification:
                    logger.warning(f"Notification {queue_item.notification_id} not found")
                    queue_item.status = "failed"
                    queue_item.error_message = "Notification not found"
                    continue
                
                # Send notification
                success = notification_service.send_notification(notification)
                
                if success:
                    queue_item.status = "completed"
                    queue_item.processing_completed_at = datetime.utcnow()
                    processed_count += 1
                    logger.info(f"Successfully sent notification {notification.id}")
                else:
                    queue_item.status = "failed"
                    queue_item.error_message = "Delivery failed"
                    queue_item.retry_count += 1
                    failed_count += 1
                    logger.error(f"Failed to send notification {notification.id}")
                
                db.commit()
                
            except Exception as exc:
                logger.error(f"Error processing notification queue item {queue_item.id}: {str(exc)}")
                queue_item.status = "failed"
                queue_item.error_message = str(exc)
                queue_item.retry_count += 1
                failed_count += 1
                db.commit()
        
        logger.info(f"Notification queue processing completed. Processed: {processed_count}, Failed: {failed_count}")
        
        return {
            "status": "completed",
            "processed": processed_count,
            "failed": failed_count,
            "total_in_batch": len(pending_notifications)
        }
        
    except Exception as exc:
        logger.error(f"Notification queue processing failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)
        
    finally:
        db.close()


@celery_app.task(bind=True)
def send_single_notification(self, notification_id: int):
    """
    Send a single notification immediately
    
    Args:
        notification_id: ID of the notification to send
    """
    db = SessionLocal()
    try:
        notification = db.query(Notification).filter(
            Notification.id == notification_id
        ).first()
        
        if not notification:
            logger.error(f"Notification {notification_id} not found")
            return {"status": "not_found"}
        
        notification_service = NotificationService(db)
        success = notification_service.send_notification(notification)
        
        if success:
            logger.info(f"Successfully sent notification {notification_id}")
            return {"status": "sent", "notification_id": notification_id}
        else:
            logger.error(f"Failed to send notification {notification_id}")
            return {"status": "failed", "notification_id": notification_id}
        
    except Exception as exc:
        logger.error(f"Single notification sending failed: {str(exc)}")
        raise
        
    finally:
        db.close()


@celery_app.task
def generate_daily_digest(target_hour: int = 8):
    """
    Generate and send daily digest notifications for users who prefer them
    
    Args:
        target_hour: Hour of day to send digest (0-23)
    """
    db = SessionLocal()
    try:
        logger.info("Generating daily digest notifications")
        
        # Get users who want daily digest
        users_for_digest = db.query(User).join(NotificationPreferences).filter(
            and_(
                NotificationPreferences.email_enabled == True,
                NotificationPreferences.email_frequency == NotificationFrequency.DAILY
            )
        ).all()
        
        notification_service = NotificationService(db)
        digest_count = 0
        
        for user in users_for_digest:
            try:
                # Get unread notifications from last 24 hours
                yesterday = datetime.utcnow() - timedelta(days=1)
                unread_notifications = db.query(Notification).filter(
                    and_(
                        Notification.user_id == user.id,
                        Notification.is_read == False,
                        Notification.created_at >= yesterday,
                        Notification.notification_type == NotificationType.IN_APP
                    )
                ).all()
                
                if unread_notifications:
                    # Create digest notification
                    digest_notification = notification_service.create_digest_notification(
                        user, unread_notifications
                    )
                    
                    if digest_notification:
                        # Queue for sending
                        queue_item = NotificationQueue(
                            notification_id=digest_notification.id,
                            priority=2,  # Medium priority
                            scheduled_for=datetime.utcnow()
                        )
                        db.add(queue_item)
                        digest_count += 1
                
            except Exception as exc:
                logger.error(f"Error creating digest for user {user.id}: {str(exc)}")
                continue
        
        db.commit()
        
        logger.info(f"Generated {digest_count} daily digest notifications")
        
        return {
            "status": "completed",
            "digest_count": digest_count,
            "users_checked": len(users_for_digest)
        }
        
    except Exception as exc:
        logger.error(f"Daily digest generation failed: {str(exc)}")
        raise
        
    finally:
        db.close()


@celery_app.task
def retry_failed_notifications(max_retries: int = 3, retry_after_hours: int = 1):
    """
    Retry failed notifications that haven't exceeded max retry count
    
    Args:
        max_retries: Maximum number of retries allowed
        retry_after_hours: Hours to wait before retrying
    """
    db = SessionLocal()
    try:
        retry_cutoff = datetime.utcnow() - timedelta(hours=retry_after_hours)
        
        # Get failed notifications eligible for retry
        failed_queue_items = db.query(NotificationQueue).filter(
            and_(
                NotificationQueue.status == "failed",
                NotificationQueue.retry_count < max_retries,
                NotificationQueue.updated_at <= retry_cutoff
            )
        ).all()
        
        retried_count = 0
        
        for queue_item in failed_queue_items:
            # Reset status to queued for retry
            queue_item.status = "queued"
            queue_item.scheduled_for = datetime.utcnow()
            retried_count += 1
        
        db.commit()
        
        logger.info(f"Queued {retried_count} failed notifications for retry")
        
        return {
            "status": "completed",
            "retried_count": retried_count
        }
        
    except Exception as exc:
        logger.error(f"Failed notification retry failed: {str(exc)}")
        raise
        
    finally:
        db.close()


@celery_app.task
def cleanup_old_notifications(days_to_keep: int = 90):
    """
    Clean up old notifications and queue items
    
    Args:
        days_to_keep: Number of days of notifications to keep
    """
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Delete old notifications
        deleted_notifications = db.query(Notification).filter(
            Notification.created_at < cutoff_date
        ).delete()
        
        # Delete old queue items
        deleted_queue_items = db.query(NotificationQueue).filter(
            NotificationQueue.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(
            f"Cleaned up {deleted_notifications} old notifications "
            f"and {deleted_queue_items} old queue items"
        )
        
        return {
            "status": "completed",
            "deleted_notifications": deleted_notifications,
            "deleted_queue_items": deleted_queue_items,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Notification cleanup failed: {str(exc)}")
        raise
        
    finally:
        db.close()
