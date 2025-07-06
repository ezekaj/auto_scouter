"""
Simple Background Scraper for Car Scouting

This module runs a background task every 5 minutes to scrape new car listings
from MerrJep.com and check for matches against user criteria.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.models.base import SessionLocal
from app.models.automotive import VehicleListing
from app.scraper.autoscout24_scraper import AutoScout24Scraper
from app.scraper.autouno_scraper import AutoUnoScraper
from app.services.automotive_service import AutomotiveService
from app.services.matching_service import VehicleMatchingService

logger = logging.getLogger(__name__)


class BackgroundScraper:
    """Simple background scraper that runs every 5 minutes"""
    
    def __init__(self):
        self.autoscout_scraper = AutoScout24Scraper()
        self.autouno_scraper = AutoUnoScraper()
        self.running = False
        self.last_run = None
        
    async def start(self):
        """Start the background scraping loop"""
        self.running = True
        logger.info("Starting background scraper - will run every 5 minutes")
        
        while self.running:
            try:
                await self.run_scraping_cycle()
                
                # Wait 5 minutes (300 seconds)
                logger.info("Waiting 5 minutes until next scraping cycle...")
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in background scraper: {e}")
                # Wait 1 minute before retrying on error
                await asyncio.sleep(60)
    
    def stop(self):
        """Stop the background scraper"""
        self.running = False
        logger.info("Background scraper stopped")
    
    async def run_scraping_cycle(self):
        """Run a single scraping cycle"""
        start_time = datetime.utcnow()
        logger.info(f"Starting scraping cycle at {start_time}")
        
        db = SessionLocal()
        try:
            # Scrape vehicles from multiple sources
            logger.info("Scraping vehicles from AutoScout24...")
            autoscout_vehicles = self.autoscout_scraper.scrape_all_listings(max_vehicles=3)

            logger.info("Scraping vehicles from AutoUno...")
            autouno_vehicles = self.autouno_scraper.generate_test_data(count=3)  # Using test data for now

            # Combine vehicles from all sources
            vehicles = autoscout_vehicles + autouno_vehicles
            
            if not vehicles:
                logger.info("No vehicles found in this cycle")
                return
            
            # Process and save vehicles
            automotive_service = AutomotiveService(db)
            matching_service = VehicleMatchingService(db)
            new_count = 0
            updated_count = 0
            notifications_sent = 0
            
            for vehicle_data in vehicles:
                try:
                    # Filter data to only include valid model fields
                    valid_fields = {
                        'external_id', 'listing_url', 'make', 'model', 'year', 'price', 'currency',
                        'mileage', 'fuel_type', 'transmission', 'condition', 'city', 'country',
                        'source_website', 'source_country', 'scraped_at', 'is_active',
                        'confidence_score', 'data_quality_score', 'accident_history',
                        'service_history', 'dealer_name', 'description', 'primary_image_url'
                    }

                    filtered_data = {k: v for k, v in vehicle_data.items() if k in valid_fields}

                    # Check if vehicle already exists
                    existing = db.query(VehicleListing).filter(
                        VehicleListing.external_id == filtered_data.get('external_id')
                    ).first()

                    if existing:
                        # Update existing vehicle
                        for key, value in filtered_data.items():
                            if hasattr(existing, key) and value is not None:
                                setattr(existing, key, value)
                        updated_count += 1
                    else:
                        # Create new vehicle listing
                        vehicle = VehicleListing(**filtered_data)
                        db.add(vehicle)
                        db.flush()  # Get the vehicle ID
                        new_count += 1

                        # Process notifications for new vehicle
                        try:
                            notifications_created = matching_service.process_new_vehicle_matches(vehicle)
                            notifications_sent += notifications_created
                        except Exception as e:
                            logger.error(f"Error processing notifications for vehicle {vehicle.external_id}: {e}")

                except Exception as e:
                    logger.error(f"Error processing vehicle: {e}")
                    continue
            
            # Commit changes
            db.commit()
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Scraping cycle completed in {duration:.2f}s: "
                       f"{new_count} new, {updated_count} updated vehicles, "
                       f"{notifications_sent} notifications sent")
            
            self.last_run = end_time
            
            # Check for user matches (if user criteria system exists)
            await self.check_user_matches(new_count)
            
        except Exception as e:
            logger.error(f"Error in scraping cycle: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def check_user_matches(self, new_vehicles_count: int):
        """Check if new vehicles match user criteria and send notifications"""
        if new_vehicles_count == 0:
            return
            
        # This is a placeholder for user matching logic
        # In a real implementation, you would:
        # 1. Get user search criteria from database
        # 2. Check new vehicles against criteria
        # 3. Send push notifications for matches
        
        logger.info(f"Checking {new_vehicles_count} new vehicles for user matches")
        
        # For now, just log that we found new vehicles
        logger.info(f"Found {new_vehicles_count} new vehicles - "
                   "notification system would alert users here")


# Global instance
background_scraper = BackgroundScraper()


async def start_background_scraper():
    """Start the background scraper"""
    await background_scraper.start()


def stop_background_scraper():
    """Stop the background scraper"""
    background_scraper.stop()


def get_scraper_status() -> Dict[str, Any]:
    """Get current status of the background scraper"""
    return {
        "running": background_scraper.running,
        "last_run": background_scraper.last_run.isoformat() if background_scraper.last_run else None,
        "next_run": (background_scraper.last_run + timedelta(minutes=5)).isoformat() 
                   if background_scraper.last_run else None
    }


if __name__ == "__main__":
    # For testing - run the scraper directly
    import asyncio
    
    async def test_scraper():
        scraper = BackgroundScraper()
        await scraper.run_scraping_cycle()
    
    asyncio.run(test_scraper())
