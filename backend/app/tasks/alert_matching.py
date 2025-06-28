"""
Celery tasks for alert matching and processing
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from celery import current_task
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.models.base import SessionLocal
from app.models.scout import Alert, User
from app.models.automotive import VehicleListing
from app.models.notifications import Notification, NotificationQueue, AlertMatchLog
from app.services.alert_matcher import AlertMatchingEngine
from app.services.notification_delivery import NotificationDeliveryService

logger = logging.getLogger(__name__)


def get_db():
    """Get database session for tasks"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Don't close here, let the task handle it


@celery_app.task(bind=True, max_retries=3)
def run_alert_matching_task(self, check_since_minutes: int = 5, max_listings: Optional[int] = None):
    """
    Celery task to run alert matching for new vehicle listings
    
    Args:
        check_since_minutes: Check listings added in the last N minutes
        max_listings: Maximum number of listings to process
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting alert matching task {self.request.id}")
        
        # Calculate check_since timestamp
        check_since = datetime.utcnow() - timedelta(minutes=check_since_minutes)
        
        # Initialize alert matching engine
        matcher = AlertMatchingEngine(db)
        
        # Run alert matching
        match_log = matcher.run_alert_matching(
            check_since=check_since,
            max_listings=max_listings
        )
        
        logger.info(
            f"Alert matching completed. Run ID: {match_log.run_id}, "
            f"Matches found: {match_log.matches_found}, "
            f"Notifications created: {match_log.notifications_created}"
        )
        
        return {
            "run_id": match_log.run_id,
            "status": match_log.status,
            "alerts_processed": match_log.alerts_processed,
            "listings_checked": match_log.listings_checked,
            "matches_found": match_log.matches_found,
            "notifications_created": match_log.notifications_created,
            "processing_time_seconds": match_log.processing_time_seconds
        }
        
    except Exception as exc:
        logger.error(f"Alert matching task failed: {str(exc)}")
        
        # Retry with exponential backoff
        countdown = 2 ** self.request.retries * 60  # 1min, 2min, 4min
        raise self.retry(exc=exc, countdown=countdown)
        
    finally:
        db.close()


@celery_app.task(bind=True)
def match_single_alert_task(self, alert_id: int, listing_ids: Optional[List[int]] = None):
    """
    Match a single alert against specific listings or all recent listings
    
    Args:
        alert_id: ID of the alert to match
        listing_ids: Optional list of specific listing IDs to check
    """
    db = SessionLocal()
    try:
        logger.info(f"Matching single alert {alert_id}")
        
        # Get the alert
        alert = db.query(Alert).filter(Alert.id == alert_id, Alert.is_active == True).first()
        if not alert:
            logger.warning(f"Alert {alert_id} not found or inactive")
            return {"status": "alert_not_found"}
        
        # Initialize matcher
        matcher = AlertMatchingEngine(db)
        
        # Get listings to check
        if listing_ids:
            listings = db.query(VehicleListing).filter(
                VehicleListing.id.in_(listing_ids),
                VehicleListing.is_active == True
            ).all()
        else:
            # Check listings from last hour
            since = datetime.utcnow() - timedelta(hours=1)
            listings = db.query(VehicleListing).filter(
                VehicleListing.scraped_at >= since,
                VehicleListing.is_active == True
            ).limit(1000).all()
        
        matches = []
        for listing in listings:
            if matcher.check_alert_match(alert, listing):
                # Create notification
                notification = matcher.create_notification(alert, listing)
                if notification:
                    matches.append({
                        "listing_id": listing.id,
                        "notification_id": notification.id
                    })
        
        logger.info(f"Single alert matching completed. Alert: {alert_id}, Matches: {len(matches)}")
        
        return {
            "status": "completed",
            "alert_id": alert_id,
            "listings_checked": len(listings),
            "matches_found": len(matches),
            "matches": matches
        }
        
    except Exception as exc:
        logger.error(f"Single alert matching failed: {str(exc)}")
        raise
        
    finally:
        db.close()


@celery_app.task
def cleanup_old_match_logs(days_to_keep: int = 30):
    """
    Clean up old alert match logs
    
    Args:
        days_to_keep: Number of days of logs to keep
    """
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        deleted_count = db.query(AlertMatchLog).filter(
            AlertMatchLog.started_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} old alert match logs")
        
        return {
            "status": "completed",
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Match log cleanup failed: {str(exc)}")
        raise
        
    finally:
        db.close()


@celery_app.task(bind=True)
def test_alert_matching(self):
    """Test task for alert matching system"""
    logger.info("Testing alert matching system")
    
    db = SessionLocal()
    try:
        # Count active alerts
        active_alerts = db.query(Alert).filter(Alert.is_active == True).count()
        
        # Count recent listings
        since = datetime.utcnow() - timedelta(hours=24)
        recent_listings = db.query(VehicleListing).filter(
            VehicleListing.scraped_at >= since
        ).count()
        
        return {
            "status": "test_completed",
            "task_id": self.request.id,
            "active_alerts": active_alerts,
            "recent_listings_24h": recent_listings,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    finally:
        db.close()
