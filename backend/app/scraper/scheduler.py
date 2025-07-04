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
from app.scraper.multi_source_scraper import multi_source_scraper
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
        """Add enhanced 24/7 scraping jobs to the scheduler"""
        if not scraper_settings.SCRAPING_ENABLED:
            logger.info("Scraping is disabled in configuration")
            return

        # 24/7 Continuous scraping - every 2 hours for comprehensive coverage
        continuous_trigger = IntervalTrigger(hours=2)

        self.scheduler.add_job(
            func=self.run_comprehensive_scraping_task,
            trigger=continuous_trigger,
            id='continuous_scraping_job',
            name='24/7 Comprehensive Scraping Job',
            max_instances=1,  # Prevent overlapping runs
            coalesce=True,    # Combine missed runs
            misfire_grace_time=1800  # 30 minute grace period
        )

        # Peak hours intensive scraping (8 AM - 10 PM) - every 30 minutes
        peak_hours_trigger = CronTrigger(
            hour='8-22',  # 8 AM to 10 PM
            minute='*/30'  # Every 30 minutes
        )

        self.scheduler.add_job(
            func=self.run_peak_hours_scraping,
            trigger=peak_hours_trigger,
            id='peak_hours_scraping_job',
            name='Peak Hours Intensive Scraping',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=900  # 15 minute grace period
        )

        # Off-peak hours light scraping (10 PM - 8 AM) - every 4 hours
        off_peak_trigger = CronTrigger(
            hour='22-7',  # 10 PM to 8 AM
            minute=0
        )

        self.scheduler.add_job(
            func=self.run_off_peak_scraping,
            trigger=off_peak_trigger,
            id='off_peak_scraping_job',
            name='Off-Peak Hours Light Scraping',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=1800  # 30 minute grace period
        )

        # Real-time monitoring scraping - every 10 minutes for new listings
        realtime_trigger = IntervalTrigger(minutes=10)

        self.scheduler.add_job(
            func=self.run_realtime_monitoring,
            trigger=realtime_trigger,
            id='realtime_monitoring_job',
            name='Real-time New Listings Monitor',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300  # 5 minute grace period
        )

        logger.info("Scheduled 24/7 automated scraping jobs:")
        logger.info("- Comprehensive scraping: Every 2 hours")
        logger.info("- Peak hours intensive: Every 30 minutes (8 AM - 10 PM)")
        logger.info("- Off-peak light: Every 4 hours (10 PM - 8 AM)")
        logger.info("- Real-time monitoring: Every 10 minutes")
    
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

    def run_comprehensive_scraping_task(self):
        """Execute comprehensive 24/7 scraping from all sources"""
        if self.current_session_id:
            logger.warning("Scraping session already in progress, skipping comprehensive scraping")
            return

        session_id = str(uuid.uuid4())
        self.current_session_id = session_id

        logger.info(f"Starting comprehensive scraping session: {session_id}")

        try:
            # Use multi-source scraper for comprehensive coverage
            results = multi_source_scraper.scrape_all_sources(max_vehicles=200)

            total_vehicles = sum(result.vehicles_count for result in results if result.success)
            successful_sources = [result.source for result in results if result.success]
            failed_sources = [result.source for result in results if not result.success]

            logger.info(f"Comprehensive scraping completed: {total_vehicles} vehicles from {len(successful_sources)} sources")

            if failed_sources:
                logger.warning(f"Failed sources: {failed_sources}")

        except Exception as e:
            logger.error(f"Error in comprehensive scraping task: {e}")
        finally:
            self.current_session_id = None

    def run_peak_hours_scraping(self):
        """Execute intensive scraping during peak hours (8 AM - 10 PM)"""
        if self.current_session_id:
            logger.warning("Scraping session already in progress, skipping peak hours scraping")
            return

        session_id = str(uuid.uuid4())
        self.current_session_id = session_id

        logger.info(f"Starting peak hours intensive scraping: {session_id}")

        try:
            # Focus on high-activity sources during peak hours
            priority_sources = ['autoscout24', 'mobile_de', 'gruppoautouno']

            results = []
            for source in priority_sources:
                if source in multi_source_scraper.enabled_sources:
                    result = multi_source_scraper.scrape_source(source, max_vehicles=100)
                    results.append(result)

                    if result.success:
                        logger.info(f"Peak hours scraping - {source}: {result.vehicles_count} vehicles")

            total_vehicles = sum(result.vehicles_count for result in results if result.success)
            logger.info(f"Peak hours scraping completed: {total_vehicles} vehicles")

        except Exception as e:
            logger.error(f"Error in peak hours scraping: {e}")
        finally:
            self.current_session_id = None

    def run_off_peak_scraping(self):
        """Execute light scraping during off-peak hours (10 PM - 8 AM)"""
        if self.current_session_id:
            logger.warning("Scraping session already in progress, skipping off-peak scraping")
            return

        session_id = str(uuid.uuid4())
        self.current_session_id = session_id

        logger.info(f"Starting off-peak light scraping: {session_id}")

        try:
            # Light scraping with reduced load during off-peak hours
            results = multi_source_scraper.scrape_all_sources(max_vehicles=50)

            total_vehicles = sum(result.vehicles_count for result in results if result.success)
            logger.info(f"Off-peak scraping completed: {total_vehicles} vehicles")

        except Exception as e:
            logger.error(f"Error in off-peak scraping: {e}")
        finally:
            self.current_session_id = None

    def run_realtime_monitoring(self):
        """Execute real-time monitoring for new listings every 10 minutes"""
        logger.info("Starting real-time monitoring for new listings")

        try:
            # Quick check for new listings from all sources
            # Focus on recently added vehicles (last 2 hours)
            from datetime import datetime, timedelta

            cutoff_time = datetime.utcnow() - timedelta(hours=2)

            # Use a lightweight scraping approach for real-time monitoring
            results = multi_source_scraper.scrape_all_sources(max_vehicles=20)

            new_vehicles = 0
            for result in results:
                if result.success:
                    new_vehicles += result.vehicles_count

            if new_vehicles > 0:
                logger.info(f"Real-time monitoring found {new_vehicles} new vehicles")

        except Exception as e:
            logger.error(f"Error in real-time monitoring: {e}")

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
