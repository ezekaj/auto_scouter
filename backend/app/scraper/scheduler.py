"""
Scraper Scheduler

This module handles automated scheduling of scraping tasks using APScheduler.
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from app.scraper.config import scraper_settings
from app.scraper.automotive_scraper import GruppoAutoUnoScraper
from app.services.automotive_service import AutomotiveService
from app.models.base import SessionLocal

logger = logging.getLogger(__name__)


class ScraperScheduler:
    """Scheduler for automated scraping tasks"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        self.current_session_id = None
        self.setup_scheduler()
    
    def setup_scheduler(self):
        """Configure the scheduler with event listeners"""
        self.scheduler.add_listener(self.job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self.job_error, EVENT_JOB_ERROR)
    
    def start(self):
        """Start the scheduler"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("Scraper scheduler started")
            
            # Add the main scraping job
            self.add_scraping_job()
            
            # Add maintenance jobs
            self.add_maintenance_jobs()
    
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scraper scheduler stopped")
    
    def add_scraping_job(self):
        """Add the main scraping job to the scheduler"""
        if not scraper_settings.SCRAPING_ENABLED:
            logger.info("Scraping is disabled in configuration")
            return
        
        # Schedule scraping every X hours
        trigger = IntervalTrigger(hours=scraper_settings.SCRAPING_INTERVAL_HOURS)
        
        self.scheduler.add_job(
            func=self.run_scraping_task,
            trigger=trigger,
            id='main_scraping_job',
            name='Main Automotive Scraping Job',
            max_instances=1,  # Prevent overlapping runs
            coalesce=True,    # Combine missed runs
            misfire_grace_time=3600  # 1 hour grace period
        )
        
        logger.info(f"Scheduled scraping job to run every {scraper_settings.SCRAPING_INTERVAL_HOURS} hours")
    
    def add_maintenance_jobs(self):
        """Add maintenance and cleanup jobs"""
        
        # Daily cleanup job at 3 AM
        self.scheduler.add_job(
            func=self.run_cleanup_task,
            trigger=CronTrigger(hour=3, minute=0),
            id='daily_cleanup_job',
            name='Daily Data Cleanup Job',
            max_instances=1
        )
        
        # Weekly data quality check on Sundays at 4 AM
        self.scheduler.add_job(
            func=self.run_data_quality_check,
            trigger=CronTrigger(day_of_week=6, hour=4, minute=0),
            id='weekly_quality_check',
            name='Weekly Data Quality Check',
            max_instances=1
        )
        
        # Deactivate old listings daily at 2 AM
        self.scheduler.add_job(
            func=self.deactivate_old_listings,
            trigger=CronTrigger(hour=2, minute=0),
            id='deactivate_old_listings',
            name='Deactivate Old Listings',
            max_instances=1
        )
        
        logger.info("Scheduled maintenance jobs")
    
    def run_scraping_task(self):
        """Execute the main scraping task"""
        session_id = str(uuid.uuid4())
        self.current_session_id = session_id
        
        logger.info(f"Starting scraping session {session_id}")
        
        db = SessionLocal()
        try:
            # Create scraping session record
            automotive_service = AutomotiveService(db)
            session_data = {
                'session_id': session_id,
                'source_website': 'gruppoautouno.it',
                'scraper_version': '1.0.0',
                'status': 'running'
            }
            session = automotive_service.create_scraping_session(session_data)
            
            # Initialize scraper
            scraper = GruppoAutoUnoScraper()
            
            # Track statistics
            stats = {
                'total_vehicles_found': 0,
                'total_vehicles_new': 0,
                'total_vehicles_updated': 0,
                'total_errors': 0,
                'start_time': datetime.utcnow()
            }
            
            # Scrape all listings
            vehicles_data = scraper.scrape_all_listings()
            stats['total_vehicles_found'] = len(vehicles_data)
            
            # Process each vehicle
            for vehicle_data in vehicles_data:
                try:
                    # Check if vehicle exists
                    existing = automotive_service.find_duplicate_listing(vehicle_data)
                    
                    if existing:
                        # Update existing vehicle
                        updated_vehicle = automotive_service.update_vehicle_listing(
                            existing.id, vehicle_data
                        )
                        if updated_vehicle:
                            stats['total_vehicles_updated'] += 1
                    else:
                        # Create new vehicle
                        new_vehicle = automotive_service.create_vehicle_listing(vehicle_data)
                        if new_vehicle:
                            stats['total_vehicles_new'] += 1
                    
                    # Log successful processing
                    log_data = {
                        'session_id': session_id,
                        'source_url': vehicle_data.get('listing_url', ''),
                        'external_id': vehicle_data.get('external_id'),
                        'status': 'success',
                        'action': 'scrape_vehicle',
                        'fields_extracted': len([v for v in vehicle_data.values() if v is not None])
                    }
                    automotive_service.create_scraping_log(log_data)
                    
                except Exception as e:
                    stats['total_errors'] += 1
                    logger.error(f"Error processing vehicle {vehicle_data.get('external_id')}: {e}")
                    
                    # Log error
                    log_data = {
                        'session_id': session_id,
                        'source_url': vehicle_data.get('listing_url', ''),
                        'external_id': vehicle_data.get('external_id'),
                        'status': 'error',
                        'action': 'scrape_vehicle',
                        'error_message': str(e)
                    }
                    automotive_service.create_scraping_log(log_data)
            
            # Update session with final statistics
            end_time = datetime.utcnow()
            duration = (end_time - stats['start_time']).total_seconds()
            
            session_update = {
                'total_vehicles_found': stats['total_vehicles_found'],
                'total_vehicles_new': stats['total_vehicles_new'],
                'total_vehicles_updated': stats['total_vehicles_updated'],
                'total_errors': stats['total_errors'],
                'completed_at': end_time,
                'duration_seconds': int(duration),
                'status': 'completed'
            }
            
            automotive_service.update_scraping_session(session_id, session_update)
            
            logger.info(f"Scraping session {session_id} completed successfully")
            logger.info(f"Statistics: {stats}")
            
        except Exception as e:
            logger.error(f"Error in scraping session {session_id}: {e}")
            
            # Update session with error status
            if 'automotive_service' in locals():
                session_update = {
                    'status': 'failed',
                    'error_message': str(e),
                    'completed_at': datetime.utcnow()
                }
                automotive_service.update_scraping_session(session_id, session_update)
        
        finally:
            db.close()
            self.current_session_id = None
    
    def run_cleanup_task(self):
        """Execute data cleanup task"""
        logger.info("Starting daily cleanup task")
        
        db = SessionLocal()
        try:
            automotive_service = AutomotiveService(db)
            
            # Clean up old data
            cleanup_stats = automotive_service.cleanup_old_data(
                retention_days=scraper_settings.DATA_RETENTION_DAYS
            )
            
            logger.info(f"Cleanup completed: {cleanup_stats}")
            
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
        finally:
            db.close()
    
    def run_data_quality_check(self):
        """Execute data quality check"""
        logger.info("Starting data quality check")
        
        db = SessionLocal()
        try:
            automotive_service = AutomotiveService(db)
            
            # Get data quality metrics
            metrics = automotive_service.get_data_quality_metrics()
            
            # Log metrics
            logger.info(f"Data quality metrics: {metrics}")
            
            # Check for quality issues
            overall_completeness = metrics.get('overall_completeness', 0)
            if overall_completeness < 80:
                logger.warning(f"Data completeness below threshold: {overall_completeness}%")
            
        except Exception as e:
            logger.error(f"Error in data quality check: {e}")
        finally:
            db.close()
    
    def deactivate_old_listings(self):
        """Deactivate old vehicle listings"""
        logger.info("Starting old listings deactivation")
        
        db = SessionLocal()
        try:
            automotive_service = AutomotiveService(db)
            
            # Deactivate listings older than 30 days
            deactivated_count = automotive_service.deactivate_old_listings(days_old=30)
            
            logger.info(f"Deactivated {deactivated_count} old listings")
            
        except Exception as e:
            logger.error(f"Error deactivating old listings: {e}")
        finally:
            db.close()
    
    def job_executed(self, event):
        """Handle job execution events"""
        logger.info(f"Job {event.job_id} executed successfully")
    
    def job_error(self, event):
        """Handle job error events"""
        logger.error(f"Job {event.job_id} failed: {event.exception}")
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get status of all scheduled jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return {
            'scheduler_running': self.is_running,
            'current_session_id': self.current_session_id,
            'jobs': jobs
        }
    
    def trigger_manual_scrape(self) -> str:
        """Trigger a manual scraping run"""
        if self.current_session_id:
            raise ValueError("Scraping session already in progress")
        
        # Add a one-time job
        job = self.scheduler.add_job(
            func=self.run_scraping_task,
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=5),
            id=f'manual_scrape_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            name='Manual Scraping Job'
        )
        
        logger.info(f"Manual scraping job scheduled: {job.id}")
        return job.id


# Global scheduler instance
scraper_scheduler = ScraperScheduler()
