"""
Celery Configuration for Cloud Background Tasks
Handles automated scraping and notifications in the cloud
"""

from celery import Celery
from celery.schedules import crontab
import logging
import os

from app.core.cloud_config import get_cloud_settings

logger = logging.getLogger(__name__)
cloud_settings = get_cloud_settings()

# Create Celery app
celery_app = Celery(
    "vehicle_scout",
    broker=cloud_settings.redis_url,
    backend=cloud_settings.redis_url,
    include=[
        "app.tasks.scraping_tasks",
        "app.tasks.notification_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "app.tasks.scraping_tasks.*": {"queue": "scraping"},
        "app.tasks.notification_tasks.*": {"queue": "notifications"},
    },
    
    # Task execution
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task retry configuration
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    
    # Result backend configuration
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    
    # Worker configuration
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "scrape-autouno-every-5-minutes": {
            "task": "app.tasks.scraping_tasks.scrape_autouno_task",
            "schedule": crontab(minute="*/5"),  # Every 5 minutes
            "options": {"queue": "scraping"}
        },
        "scrape-autoscout24-every-10-minutes": {
            "task": "app.tasks.scraping_tasks.scrape_autoscout24_task",
            "schedule": crontab(minute="*/10"),  # Every 10 minutes
            "options": {"queue": "scraping"}
        },
        "process-notifications-every-minute": {
            "task": "app.tasks.notification_tasks.process_pending_notifications",
            "schedule": crontab(minute="*"),  # Every minute
            "options": {"queue": "notifications"}
        },
        "cleanup-old-data-daily": {
            "task": "app.tasks.maintenance_tasks.cleanup_old_data",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
            "options": {"queue": "maintenance"}
        }
    },
    beat_schedule_filename="celerybeat-schedule",
)

# Configure logging
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks after Celery configuration"""
    logger.info("🔄 Celery periodic tasks configured")
    
    if cloud_settings.is_production:
        logger.info("✅ Production mode: All background tasks enabled")
    else:
        logger.info("🔧 Development mode: Limited background tasks")

@celery_app.on_after_finalize.connect
def setup_celery_logging(sender, **kwargs):
    """Setup Celery logging"""
    logger.info("📋 Celery app finalized and ready")

# Task error handling
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery functionality"""
    logger.info(f"Request: {self.request!r}")
    return "Celery is working!"

# Health check task
@celery_app.task
def health_check_task():
    """Health check task for monitoring"""
    try:
        from app.models.cloud_base import test_cloud_database_connection
        db_healthy = test_cloud_database_connection()
        
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "database": "connected" if db_healthy else "disconnected",
            "timestamp": "2025-07-06T20:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check task failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-07-06T20:00:00Z"
        }

if __name__ == "__main__":
    celery_app.start()
