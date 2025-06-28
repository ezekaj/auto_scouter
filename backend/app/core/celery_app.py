"""
Celery Configuration for Auto Scouter

This module configures Celery for background task processing including
alert matching and notification delivery.
"""

from celery import Celery
from app.core.config import settings
import os

# Create Celery instance
celery_app = Celery(
    "auto_scouter",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.alert_matching",
        "app.tasks.notification_delivery",
        "app.tasks.data_cleanup",
        "app.tasks.scraping_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "app.tasks.alert_matching.*": {"queue": "alert_matching"},
        "app.tasks.notification_delivery.*": {"queue": "notifications"},
        "app.tasks.data_cleanup.*": {"queue": "maintenance"},
        "app.tasks.scraping_tasks.*": {"queue": "scraping"},
    },
    
    # Task execution settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task result settings
    result_expires=3600,  # 1 hour
    task_track_started=True,
    task_send_sent_event=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "scrape-all-sources": {
            "task": "app.tasks.scraping_tasks.scrape_all_sources",
            "schedule": 300.0,  # Every 5 minutes
            "options": {"queue": "scraping"}
        },
        "run-alert-matching": {
            "task": "app.tasks.alert_matching.run_alert_matching_task",
            "schedule": 300.0,  # Every 5 minutes
            "options": {"queue": "alert_matching"}
        },
        "process-notification-queue": {
            "task": "app.tasks.notification_delivery.process_notification_queue",
            "schedule": 60.0,  # Every minute
            "options": {"queue": "notifications"}
        },
        "cleanup-old-notifications": {
            "task": "app.tasks.data_cleanup.cleanup_old_notifications",
            "schedule": 3600.0,  # Every hour
            "options": {"queue": "maintenance"}
        },
        "cleanup-inactive-listings": {
            "task": "app.tasks.scraping_tasks.cleanup_inactive_listings",
            "schedule": 86400.0,  # Daily
            "options": {"queue": "maintenance"}
        },
        "generate-daily-digest": {
            "task": "app.tasks.notification_delivery.generate_daily_digest",
            "schedule": "0 8 * * *",  # Daily at 8 AM
            "options": {"queue": "notifications"}
        },
    },
    
    # Queue configuration
    task_default_queue="default",
    task_create_missing_queues=True,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_events=True,
)

# Optional: Configure logging
celery_app.conf.update(
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
)


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f"Request: {self.request!r}")
    return "Celery is working!"


# Health check task
@celery_app.task
def health_check():
    """Simple health check task"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}


if __name__ == "__main__":
    celery_app.start()
