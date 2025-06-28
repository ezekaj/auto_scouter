"""
Celery tasks for data cleanup and maintenance
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.models.base import SessionLocal
from app.models.notifications import Notification, NotificationQueue, AlertMatchLog
from app.models.automotive import ScrapingLog, ScrapingSession

logger = logging.getLogger(__name__)


@celery_app.task
def cleanup_old_notifications(days_to_keep: int = 90):
    """
    Clean up old notifications and related data
    
    Args:
        days_to_keep: Number of days of data to keep
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


@celery_app.task
def cleanup_old_logs(days_to_keep: int = 30):
    """
    Clean up old system logs
    
    Args:
        days_to_keep: Number of days of logs to keep
    """
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Delete old alert match logs
        deleted_match_logs = db.query(AlertMatchLog).filter(
            AlertMatchLog.started_at < cutoff_date
        ).delete()
        
        # Delete old scraping logs
        deleted_scraping_logs = db.query(ScrapingLog).filter(
            ScrapingLog.started_at < cutoff_date
        ).delete()
        
        # Delete old scraping sessions
        deleted_sessions = db.query(ScrapingSession).filter(
            ScrapingSession.started_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(
            f"Cleaned up {deleted_match_logs} match logs, "
            f"{deleted_scraping_logs} scraping logs, "
            f"and {deleted_sessions} scraping sessions"
        )
        
        return {
            "status": "completed",
            "deleted_match_logs": deleted_match_logs,
            "deleted_scraping_logs": deleted_scraping_logs,
            "deleted_sessions": deleted_sessions,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Log cleanup failed: {str(exc)}")
        raise
        
    finally:
        db.close()


@celery_app.task
def optimize_database():
    """
    Perform database optimization tasks
    """
    db = SessionLocal()
    try:
        # For SQLite, run VACUUM to reclaim space
        if "sqlite" in str(db.bind.url):
            db.execute("VACUUM")
            db.execute("ANALYZE")
        
        logger.info("Database optimization completed")
        
        return {
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Database optimization failed: {str(exc)}")
        raise
        
    finally:
        db.close()
