"""
Background Task Processing System

This module handles periodic tasks for alert matching and notification processing.
"""

import logging
import atexit
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import sessionmaker

from app.models.base import engine
from app.services.alert_matcher import AlertMatchingEngine
from app.services.notification_delivery import NotificationDeliveryService
from app.models.notifications import AlertMatchLog
from app.core.config import settings

logger = logging.getLogger(__name__)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class BackgroundTaskManager:
    """Manager for background tasks and scheduling"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        
        # Configure scheduler
        self.scheduler.configure(
            timezone='UTC',
            job_defaults={
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 300  # 5 minutes
            }
        )
        
        # Register shutdown handler
        atexit.register(self.shutdown)
    
    def start(self):
        """Start the background task scheduler"""
        if self.is_running:
            logger.warning("Background task manager is already running")
            return
        
        try:
            # Add periodic jobs
            self._add_alert_matching_job()
            self._add_notification_processing_job()
            self._add_cleanup_jobs()
            
            # Start scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.info("Background task manager started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start background task manager: {str(e)}")
            raise
    
    def shutdown(self):
        """Shutdown the background task scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("Background task manager shut down")
    
    def _add_alert_matching_job(self):
        """Add periodic alert matching job"""
        # Run alert matching every 20 minutes
        self.scheduler.add_job(
            func=self._run_alert_matching,
            trigger=IntervalTrigger(minutes=20),
            id='alert_matching',
            name='Alert Matching Job',
            replace_existing=True
        )
        
        logger.info("Added alert matching job (every 20 minutes)")
    
    def _add_notification_processing_job(self):
        """Add periodic notification processing job"""
        # Process notification queue every 2 minutes
        self.scheduler.add_job(
            func=self._process_notification_queue,
            trigger=IntervalTrigger(minutes=2),
            id='notification_processing',
            name='Notification Processing Job',
            replace_existing=True
        )
        
        logger.info("Added notification processing job (every 2 minutes)")
    
    def _add_cleanup_jobs(self):
        """Add periodic cleanup jobs"""
        # Clean up old notifications daily at 2 AM
        self.scheduler.add_job(
            func=self._cleanup_old_notifications,
            trigger=CronTrigger(hour=2, minute=0),
            id='notification_cleanup',
            name='Notification Cleanup Job',
            replace_existing=True
        )
        
        # Clean up old match logs weekly on Sunday at 3 AM
        self.scheduler.add_job(
            func=self._cleanup_old_match_logs,
            trigger=CronTrigger(day_of_week=6, hour=3, minute=0),
            id='match_log_cleanup',
            name='Match Log Cleanup Job',
            replace_existing=True
        )
        
        logger.info("Added cleanup jobs (daily and weekly)")
    
    def _run_alert_matching(self):
        """Run alert matching process"""
        db = SessionLocal()
        try:
            logger.info("Starting scheduled alert matching run")
            
            # Get last successful run time
            last_run = self._get_last_successful_alert_run(db)
            check_since = last_run - timedelta(minutes=5) if last_run else None
            
            # Run alert matching
            matcher = AlertMatchingEngine(db)
            match_log = matcher.run_alert_matching(
                check_since=check_since,
                max_listings=1000  # Limit to prevent overload
            )
            
            logger.info(f"Alert matching completed: {match_log.matches_found} matches, "
                       f"{match_log.notifications_created} notifications created")
            
        except Exception as e:
            logger.error(f"Error in scheduled alert matching: {str(e)}")
        finally:
            db.close()
    
    def _process_notification_queue(self):
        """Process pending notifications in the queue"""
        db = SessionLocal()
        try:
            logger.debug("Processing notification queue")
            
            delivery_service = NotificationDeliveryService(db)
            stats = delivery_service.process_notification_queue(max_notifications=50)
            
            if stats["processed"] > 0:
                logger.info(f"Processed {stats['processed']} notifications: "
                           f"{stats['sent']} sent, {stats['failed']} failed, "
                           f"{stats['skipped']} skipped")
            
        except Exception as e:
            logger.error(f"Error processing notification queue: {str(e)}")
        finally:
            db.close()
    
    def _cleanup_old_notifications(self):
        """Clean up old notifications"""
        db = SessionLocal()
        try:
            logger.info("Starting notification cleanup")
            
            # Delete notifications older than 90 days
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            
            from app.models.notifications import Notification
            deleted_count = db.query(Notification).filter(
                Notification.created_at < cutoff_date
            ).delete()
            
            db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old notifications")
            
        except Exception as e:
            logger.error(f"Error in notification cleanup: {str(e)}")
        finally:
            db.close()
    
    def _cleanup_old_match_logs(self):
        """Clean up old alert match logs"""
        db = SessionLocal()
        try:
            logger.info("Starting match log cleanup")
            
            # Delete match logs older than 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            deleted_count = db.query(AlertMatchLog).filter(
                AlertMatchLog.started_at < cutoff_date
            ).delete()
            
            db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old match logs")
            
        except Exception as e:
            logger.error(f"Error in match log cleanup: {str(e)}")
        finally:
            db.close()
    
    def _get_last_successful_alert_run(self, db) -> Optional[datetime]:
        """Get the timestamp of the last successful alert matching run"""
        last_log = db.query(AlertMatchLog).filter(
            AlertMatchLog.status == "completed"
        ).order_by(AlertMatchLog.completed_at.desc()).first()
        
        return last_log.completed_at if last_log else None
    
    def trigger_alert_matching(self) -> str:
        """Manually trigger alert matching job"""
        try:
            job = self.scheduler.get_job('alert_matching')
            if job:
                job.modify(next_run_time=datetime.utcnow())
                return "Alert matching job triggered successfully"
            else:
                return "Alert matching job not found"
        except Exception as e:
            logger.error(f"Error triggering alert matching: {str(e)}")
            return f"Error triggering alert matching: {str(e)}"
    
    def trigger_notification_processing(self) -> str:
        """Manually trigger notification processing job"""
        try:
            job = self.scheduler.get_job('notification_processing')
            if job:
                job.modify(next_run_time=datetime.utcnow())
                return "Notification processing job triggered successfully"
            else:
                return "Notification processing job not found"
        except Exception as e:
            logger.error(f"Error triggering notification processing: {str(e)}")
            return f"Error triggering notification processing: {str(e)}"
    
    def get_job_status(self) -> dict:
        """Get status of all scheduled jobs"""
        jobs = []
        
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
                "pending": job.pending
            })
        
        return {
            "scheduler_running": self.scheduler.running,
            "jobs": jobs,
            "total_jobs": len(jobs)
        }
    
    def pause_job(self, job_id: str) -> bool:
        """Pause a specific job"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {str(e)}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """Resume a specific job"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {str(e)}")
            return False


# Global instance
background_task_manager = BackgroundTaskManager()


def start_background_tasks():
    """Start background tasks (called from main application)"""
    background_task_manager.start()


def stop_background_tasks():
    """Stop background tasks"""
    background_task_manager.shutdown()


def get_task_manager() -> BackgroundTaskManager:
    """Get the global task manager instance"""
    return background_task_manager
