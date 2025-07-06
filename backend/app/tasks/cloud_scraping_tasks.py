"""
Cloud Scraping Tasks for 24/7 Operation
Automated scraping tasks that run continuously in the cloud
"""

from celery import current_task
import logging
from datetime import datetime
from typing import List, Dict

from app.tasks.celery_app import celery_app
from app.core.cloud_config import get_cloud_settings

logger = logging.getLogger(__name__)
cloud_settings = get_cloud_settings()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def cloud_scrape_autouno_task(self):
    """
    Cloud-optimized AutoUno scraping task
    Runs every 5 minutes automatically
    """
    try:
        logger.info("🌐 Starting cloud AutoUno scraping...")
        
        # Import here to avoid circular imports
        from app.models.cloud_base import SessionLocal
        from app.models.automotive import VehicleListing
        from app.scraper.autouno_scraper import AutoUnoScraper
        from app.services.matching_service import VehicleMatchingService
        
        # Initialize scraper
        scraper = AutoUnoScraper()
        
        # Generate test data (replace with real scraping when ready)
        vehicles = scraper.generate_test_data(count=3)
        
        if not vehicles:
            logger.warning("⚠️  No vehicles found during cloud AutoUno scraping")
            return {"status": "completed", "vehicles_found": 0}
        
        # Process vehicles
        processed_count = 0
        new_count = 0
        notifications_sent = 0
        
        db = SessionLocal()
        try:
            matching_service = VehicleMatchingService(db)
            
            for vehicle_data in vehicles:
                try:
                    # Check if vehicle already exists
                    existing = db.query(VehicleListing).filter(
                        VehicleListing.external_id == vehicle_data["external_id"]
                    ).first()
                    
                    if not existing:
                        # Create new vehicle
                        vehicle = VehicleListing(**vehicle_data)
                        db.add(vehicle)
                        db.flush()  # Get the ID
                        
                        # Process notifications for new vehicle
                        notifications = matching_service.process_new_vehicle_matches(vehicle)
                        notifications_sent += notifications
                        
                        new_count += 1
                        logger.info(f"✅ New vehicle: {vehicle.make} {vehicle.model} ({notifications} notifications)")
                    
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error processing vehicle: {e}")
                    continue
            
            db.commit()
            
        finally:
            db.close()
        
        result = {
            "status": "completed",
            "vehicles_found": len(vehicles),
            "vehicles_processed": processed_count,
            "new_vehicles": new_count,
            "notifications_sent": notifications_sent,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"🎯 Cloud AutoUno scraping completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Cloud AutoUno scraping failed: {e}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)
            logger.info(f"🔄 Retrying in {countdown} seconds (attempt {self.request.retries + 1})")
            raise self.retry(countdown=countdown)
        
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@celery_app.task
def cloud_health_check():
    """Health check for cloud scraping system"""
    try:
        from app.models.cloud_base import test_cloud_database_connection, get_database_info
        
        # Test database connection
        db_healthy = test_cloud_database_connection()
        db_info = get_database_info()
        
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "database": db_info,
            "cloud_settings": {
                "environment": cloud_settings.environment,
                "scraping_interval": cloud_settings.scraping_interval_minutes,
                "is_production": cloud_settings.is_production
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Cloud health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@celery_app.task
def cloud_scraping_stats():
    """Get cloud scraping statistics"""
    try:
        from app.models.cloud_base import SessionLocal
        from app.models.automotive import VehicleListing
        
        db = SessionLocal()
        try:
            # Get statistics
            total_vehicles = db.query(VehicleListing).count()
            
            # Vehicles by source
            autouno_count = db.query(VehicleListing).filter(
                VehicleListing.source_website == "autouno.al"
            ).count()
            
            autoscout_count = db.query(VehicleListing).filter(
                VehicleListing.source_website == "autoscout24.com"
            ).count()
            
            # Recent vehicles (last 24 hours)
            from datetime import timedelta
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_count = db.query(VehicleListing).filter(
                VehicleListing.scraped_at >= yesterday
            ).count()
            
            return {
                "total_vehicles": total_vehicles,
                "sources": {
                    "autouno": autouno_count,
                    "autoscout24": autoscout_count
                },
                "recent_24h": recent_count,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Error getting scraping stats: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
