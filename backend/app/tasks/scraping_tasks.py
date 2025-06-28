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
from app.scraper.automotive_scraper import GruppoAutoUnoScraper
from app.services.automotive_service import AutomotiveService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def scrape_all_sources(self):
    """
    Main scraping task that runs every 5 minutes
    Scrapes vehicle data from all configured sources
    """
    session_id = str(uuid.uuid4())
    task_id = self.request.id
    
    logger.info(f"Starting scraping task {task_id} with session {session_id}")
    
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
        if source_name.lower() == 'gruppoautouno':
            scraper = GruppoAutoUnoScraper()
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
