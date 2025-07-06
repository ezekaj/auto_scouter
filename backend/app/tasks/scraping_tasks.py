"""
Celery tasks for automated vehicle data scraping
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
from celery import current_task
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.models.base import SessionLocal
from app.models.automotive import VehicleListing, ScrapingSession, ScrapingLog
from app.scraper.autoscout24_scraper import AutoScout24Scraper
from app.scraper.multi_source_scraper import multi_source_scraper
from app.services.automotive_service import AutomotiveService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def comprehensive_scraping_task(self):
    """
    24/7 Comprehensive scraping task - runs every 2 hours
    Scrapes vehicle data from all configured sources with maximum coverage
    """
    session_id = str(uuid.uuid4())
    task_id = self.request.id

    logger.info(f"Starting comprehensive 24/7 scraping task {task_id} with session {session_id}")

    try:
        from app.scraper.multi_source_scraper import multi_source_scraper

        # Comprehensive scraping with high vehicle count
        results = multi_source_scraper.scrape_all_sources(max_vehicles=200)

        total_vehicles = sum(result.vehicles_count for result in results if result.success)
        successful_sources = [result.source for result in results if result.success]
        failed_sources = [result.source for result in results if not result.success]

        logger.info(f"Comprehensive scraping completed: {total_vehicles} vehicles from {len(successful_sources)} sources")

        if failed_sources:
            logger.warning(f"Failed sources in comprehensive scraping: {failed_sources}")

        return {
            "session_id": session_id,
            "task_id": task_id,
            "total_vehicles": total_vehicles,
            "successful_sources": successful_sources,
            "failed_sources": failed_sources,
            "status": "completed"
        }

    except Exception as e:
        logger.error(f"Error in comprehensive scraping task {task_id}: {e}")
        raise self.retry(countdown=300, max_retries=3)  # Retry after 5 minutes


@celery_app.task(bind=True)
def peak_hours_scraping_task(self):
    """
    Peak hours intensive scraping task - runs every 30 minutes (8 AM - 10 PM)
    Focuses on high-activity sources during peak hours
    """
    session_id = str(uuid.uuid4())
    task_id = self.request.id

    logger.info(f"Starting peak hours scraping task {task_id} with session {session_id}")

    try:
        from app.scraper.multi_source_scraper import multi_source_scraper

        # Focus on priority sources during peak hours
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

        return {
            "session_id": session_id,
            "task_id": task_id,
            "total_vehicles": total_vehicles,
            "sources_scraped": len(results),
            "status": "completed"
        }

    except Exception as e:
        logger.error(f"Error in peak hours scraping task {task_id}: {e}")
        raise self.retry(countdown=180, max_retries=3)  # Retry after 3 minutes


@celery_app.task(bind=True)
def off_peak_scraping_task(self):
    """
    Off-peak light scraping task - runs every 4 hours (10 PM - 8 AM)
    Light scraping with reduced load during off-peak hours
    """
    session_id = str(uuid.uuid4())
    task_id = self.request.id

    logger.info(f"Starting off-peak scraping task {task_id} with session {session_id}")

    try:
        from app.scraper.multi_source_scraper import multi_source_scraper

        # Light scraping with reduced load
        results = multi_source_scraper.scrape_all_sources(max_vehicles=50)

        total_vehicles = sum(result.vehicles_count for result in results if result.success)
        logger.info(f"Off-peak scraping completed: {total_vehicles} vehicles")

        return {
            "session_id": session_id,
            "task_id": task_id,
            "total_vehicles": total_vehicles,
            "status": "completed"
        }

    except Exception as e:
        logger.error(f"Error in off-peak scraping task {task_id}: {e}")
        raise self.retry(countdown=600, max_retries=2)  # Retry after 10 minutes


@celery_app.task(bind=True)
def realtime_monitoring_task(self):
    """
    Real-time monitoring task - runs every 10 minutes
    Quick check for new listings from all sources
    """
    task_id = self.request.id

    logger.info(f"Starting real-time monitoring task {task_id}")

    try:
        from app.scraper.multi_source_scraper import multi_source_scraper

        # Lightweight scraping for real-time monitoring
        results = multi_source_scraper.scrape_all_sources(max_vehicles=20)

        new_vehicles = sum(result.vehicles_count for result in results if result.success)

        if new_vehicles > 0:
            logger.info(f"Real-time monitoring found {new_vehicles} new vehicles")

        return {
            "task_id": task_id,
            "new_vehicles": new_vehicles,
            "status": "completed"
        }

    except Exception as e:
        logger.error(f"Error in real-time monitoring task {task_id}: {e}")
        # Don't retry real-time monitoring to avoid queue buildup
        return {"task_id": task_id, "status": "failed", "error": str(e)}


@celery_app.task(bind=True)
def scrape_all_sources(self):
    """
    Legacy scraping task - maintained for compatibility
    Scrapes vehicle data from all configured sources
    """
    session_id = str(uuid.uuid4())
    task_id = self.request.id

    logger.info(f"Starting legacy scraping task {task_id} with session {session_id}")
    
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
        scraper = AutoScout24Scraper()
        
        # Track statistics
        stats = {
            'total_vehicles_found': 0,
            'total_vehicles_new': 0,
            'total_vehicles_updated': 0,
            'total_errors': 0,
            'start_time': datetime.utcnow()
        }
        
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Initializing scraper', 'progress': 0}
        )
        
        # Scrape vehicles (limit to prevent overload)
        logger.info("Starting vehicle scraping...")
        vehicles = scraper.scrape_all_listings(max_vehicles=100)  # Limit for 5-min intervals
        
        stats['total_vehicles_found'] = len(vehicles)
        
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Processing vehicles', 'progress': 50}
        )
        
        # Process and save vehicles
        for i, vehicle_data in enumerate(vehicles):
            try:
                # Check if vehicle already exists
                existing = db.query(VehicleListing).filter(
                    VehicleListing.external_id == vehicle_data.get('external_id')
                ).first()
                
                if existing:
                    # Update existing vehicle
                    for key, value in vehicle_data.items():
                        if hasattr(existing, key) and value is not None:
                            setattr(existing, key, value)
                    existing.last_updated = datetime.utcnow()
                    stats['total_vehicles_updated'] += 1
                else:
                    # Create new vehicle
                    vehicle = VehicleListing(**vehicle_data)
                    db.add(vehicle)
                    stats['total_vehicles_new'] += 1
                
                # Update progress every 10 vehicles
                if i % 10 == 0:
                    progress = 50 + (i / len(vehicles)) * 40
                    self.update_state(
                        state='PROGRESS',
                        meta={'status': f'Processed {i}/{len(vehicles)} vehicles', 'progress': progress}
                    )
                
            except Exception as e:
                logger.error(f"Error processing vehicle {vehicle_data.get('external_id', 'unknown')}: {e}")
                stats['total_errors'] += 1
                continue
        
        # Commit all changes
        db.commit()
        
        # Update session with final stats
        stats['end_time'] = datetime.utcnow()
        stats['duration_seconds'] = (stats['end_time'] - stats['start_time']).total_seconds()
        
        session.total_vehicles_found = stats['total_vehicles_found']
        session.total_vehicles_new = stats['total_vehicles_new']
        session.total_vehicles_updated = stats['total_vehicles_updated']
        session.total_errors = stats['total_errors']
        session.duration_seconds = int(stats['duration_seconds'])
        session.completed_at = stats['end_time']
        session.status = 'completed'
        
        db.commit()
        
        logger.info(f"Scraping completed: {stats}")
        
        return {
            'status': 'completed',
            'session_id': session_id,
            'task_id': task_id,
            'statistics': stats,
            'vehicles_found': stats['total_vehicles_found'],
            'vehicles_new': stats['total_vehicles_new'],
            'vehicles_updated': stats['total_vehicles_updated'],
            'errors': stats['total_errors'],
            'duration_seconds': stats['duration_seconds']
        }
        
    except Exception as e:
        logger.error(f"Scraping task failed: {e}")
        
        # Update session status
        if 'session' in locals():
            session.status = 'failed'
            session.error_message = str(e)
            session.completed_at = datetime.utcnow()
            db.commit()
        
        # Re-raise for Celery to handle
        raise e
        
    finally:
        db.close()


@celery_app.task
def scrape_single_source(source_name: str, max_vehicles: int = 50):
    """
    Scrape a single source with limited vehicles
    Useful for testing or targeted scraping
    """
    logger.info(f"Starting single source scraping: {source_name}")
    
    db = SessionLocal()
    try:
        if source_name.lower() == 'autoscout24':
            scraper = AutoScout24Scraper()
            vehicles = scraper.scrape_all_listings(max_vehicles=max_vehicles)
            
            new_count = 0
            updated_count = 0
            
            for vehicle_data in vehicles:
                try:
                    existing = db.query(VehicleListing).filter(
                        VehicleListing.external_id == vehicle_data.get('external_id')
                    ).first()
                    
                    if existing:
                        for key, value in vehicle_data.items():
                            if hasattr(existing, key) and value is not None:
                                setattr(existing, key, value)
                        existing.last_updated = datetime.utcnow()
                        updated_count += 1
                    else:
                        vehicle = VehicleListing(**vehicle_data)
                        db.add(vehicle)
                        new_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing vehicle: {e}")
                    continue
            
            db.commit()
            
            return {
                'source': source_name,
                'vehicles_found': len(vehicles),
                'vehicles_new': new_count,
                'vehicles_updated': updated_count
            }
        else:
            raise ValueError(f"Unknown source: {source_name}")
            
    finally:
        db.close()


@celery_app.task(bind=True, name="scrape_all_sources")
def scrape_all_sources_task(self, max_vehicles_per_source: int = 50):
    """
    Scrape vehicles from all enabled sources

    Args:
        max_vehicles_per_source: Maximum vehicles to scrape per source

    Returns:
        Dictionary with scraping results
    """
    session_id = str(uuid.uuid4())
    start_time = datetime.utcnow()

    logger.info(f"Starting multi-source scraping task {session_id}")

    try:
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Starting multi-source scraping', 'progress': 0}
        )

        # Perform multi-source scraping
        results = multi_source_scraper.scrape_all_sources(
            max_vehicles_per_source=max_vehicles_per_source
        )

        # Process results and save to database
        db = SessionLocal()
        total_new = 0
        total_updated = 0
        source_results = {}

        try:
            for i, result in enumerate(results):
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'status': f'Processing {result.source} results',
                        'progress': int((i / len(results)) * 100)
                    }
                )

                source_results[result.source] = {
                    'success': result.success,
                    'vehicles_count': result.vehicles_count,
                    'error': result.error_message,
                    'duration_seconds': result.duration_seconds
                }

                if result.success:
                    total_new += result.vehicles_count

        finally:
            db.close()

        return {
            'status': 'completed',
            'session_id': session_id,
            'total_new_vehicles': total_new,
            'total_updated_vehicles': total_updated,
            'sources_processed': len(results),
            'source_results': source_results,
            'duration_seconds': (datetime.utcnow() - start_time).total_seconds()
        }

    except Exception as e:
        logger.error(f"Error in scrape_all_sources_task: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'session_id': session_id
        }


@celery_app.task
def cleanup_inactive_listings(days_old: int = 7):
    """
    Mark old listings as inactive if they haven't been updated recently
    """
    logger.info(f"Cleaning up listings older than {days_old} days")
    
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Find listings that haven't been updated recently
        old_listings = db.query(VehicleListing).filter(
            VehicleListing.last_updated < cutoff_date,
            VehicleListing.is_active == True
        ).all()
        
        deactivated_count = 0
        for listing in old_listings:
            listing.is_active = False
            deactivated_count += 1
        
        db.commit()
        
        logger.info(f"Deactivated {deactivated_count} old listings")
        
        return {
            'deactivated_count': deactivated_count,
            'cutoff_date': cutoff_date.isoformat()
        }
        
    finally:
        db.close()


@celery_app.task
def health_check_scraping():
    """
    Health check task for scraping system
    """
    db = SessionLocal()
    try:
        # Check recent scraping activity
        recent_sessions = db.query(ScrapingSession).filter(
            ScrapingSession.started_at >= datetime.utcnow() - timedelta(hours=1)
        ).count()
        
        # Check total active listings
        active_listings = db.query(VehicleListing).filter(
            VehicleListing.is_active == True
        ).count()
        
        # Check recent listings
        recent_listings = db.query(VehicleListing).filter(
            VehicleListing.scraped_at >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        return {
            'status': 'healthy',
            'recent_sessions_1h': recent_sessions,
            'active_listings': active_listings,
            'recent_listings_24h': recent_listings,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    finally:
        db.close()


@celery_app.task(bind=True)
def performance_monitoring_task(self):
    """
    Performance monitoring task - runs every hour
    Monitors scraping performance and system health
    """
    task_id = self.request.id

    logger.info(f"Starting performance monitoring task {task_id}")

    try:
        db = SessionLocal()

        # Get recent scraping sessions (last 24 hours)
        from datetime import datetime, timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        # Query recent sessions and calculate performance metrics
        recent_sessions = db.execute(
            "SELECT COUNT(*) as session_count, "
            "AVG(total_vehicles_found) as avg_vehicles, "
            "AVG(duration_seconds) as avg_duration, "
            "SUM(total_errors) as total_errors "
            "FROM scraping_sessions "
            "WHERE created_at >= %s",
            (cutoff_time,)
        ).fetchone()

        # Calculate success rate
        success_rate = 100.0
        if recent_sessions and recent_sessions[0] > 0:
            error_rate = (recent_sessions[3] or 0) / max(recent_sessions[1] or 1, 1)
            success_rate = max(0, 100 - (error_rate * 100))

        performance_metrics = {
            "session_count_24h": recent_sessions[0] if recent_sessions else 0,
            "avg_vehicles_per_session": recent_sessions[1] if recent_sessions else 0,
            "avg_duration_seconds": recent_sessions[2] if recent_sessions else 0,
            "total_errors_24h": recent_sessions[3] if recent_sessions else 0,
            "success_rate_percent": success_rate,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"Performance metrics: {performance_metrics}")

        # Alert if performance is degraded
        if success_rate < 80:
            logger.warning(f"Low success rate detected: {success_rate}%")

        if recent_sessions and recent_sessions[2] and recent_sessions[2] > 300:  # > 5 minutes
            logger.warning(f"High average duration detected: {recent_sessions[2]} seconds")

        db.close()

        return {
            "task_id": task_id,
            "performance_metrics": performance_metrics,
            "status": "completed"
        }

    except Exception as e:
        logger.error(f"Error in performance monitoring task {task_id}: {e}")
        return {"task_id": task_id, "status": "failed", "error": str(e)}


@celery_app.task(bind=True)
def data_quality_check_task(self):
    """
    Data quality check task - runs weekly
    Checks data quality and performs cleanup
    """
    task_id = self.request.id

    logger.info(f"Starting data quality check task {task_id}")

    try:
        db = SessionLocal()

        # Check for duplicate vehicles
        duplicate_count = db.execute(
            "SELECT COUNT(*) FROM ("
            "SELECT external_id, source, COUNT(*) as cnt "
            "FROM vehicles "
            "GROUP BY external_id, source "
            "HAVING COUNT(*) > 1"
            ") as duplicates"
        ).scalar()

        # Check for vehicles with missing critical data
        missing_data_count = db.execute(
            "SELECT COUNT(*) FROM vehicles "
            "WHERE make IS NULL OR model IS NULL OR price IS NULL"
        ).scalar()

        # Check for very old vehicles (> 1 year without updates)
        from datetime import datetime, timedelta
        old_cutoff = datetime.utcnow() - timedelta(days=365)

        old_vehicles_count = db.execute(
            "SELECT COUNT(*) FROM vehicles "
            "WHERE last_updated < %s",
            (old_cutoff,)
        ).scalar()

        quality_metrics = {
            "duplicate_vehicles": duplicate_count,
            "missing_critical_data": missing_data_count,
            "old_vehicles": old_vehicles_count,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"Data quality metrics: {quality_metrics}")

        # Perform cleanup if needed
        cleanup_actions = []

        if duplicate_count > 0:
            logger.info(f"Found {duplicate_count} duplicate vehicles - cleanup recommended")
            cleanup_actions.append("duplicate_cleanup_needed")

        if old_vehicles_count > 1000:
            logger.info(f"Found {old_vehicles_count} old vehicles - archival recommended")
            cleanup_actions.append("archival_needed")

        db.close()

        return {
            "task_id": task_id,
            "quality_metrics": quality_metrics,
            "cleanup_actions": cleanup_actions,
            "status": "completed"
        }

    except Exception as e:
        logger.error(f"Error in data quality check task {task_id}: {e}")
        return {"task_id": task_id, "status": "failed", "error": str(e)}
