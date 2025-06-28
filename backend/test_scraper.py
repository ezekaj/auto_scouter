#!/usr/bin/env python3
"""
Test script for the automotive scraper
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.scraper.automotive_scraper import GruppoAutoUnoScraper
from app.models.base import engine, Base
from app.models.automotive import VehicleListing
from sqlalchemy.orm import sessionmaker

def test_scraper():
    """Test the scraper functionality"""
    print("🚗 Testing Auto Scouter Scraper")
    print("=" * 50)
    
    # Create database session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Initialize scraper
        print("📡 Initializing scraper...")
        scraper = GruppoAutoUnoScraper()
        
        # Test scraping a few listings
        print("🔍 Testing scraper (limited to 3 vehicles)...")
        vehicles = scraper.scrape_all_listings()
        
        if vehicles:
            print(f"✅ Successfully scraped {len(vehicles)} vehicles")
            
            # Show first vehicle as example
            if len(vehicles) > 0:
                vehicle = vehicles[0]
                print(f"\n📋 Example vehicle:")
                print(f"   Make: {vehicle.get('make', 'N/A')}")
                print(f"   Model: {vehicle.get('model', 'N/A')}")
                print(f"   Year: {vehicle.get('year', 'N/A')}")
                print(f"   Price: €{vehicle.get('price', 'N/A')}")
                print(f"   Location: {vehicle.get('location', 'N/A')}")
                
            # Save to database
            print(f"\n💾 Saving vehicles to database...")
            saved_count = 0
            
            for vehicle_data in vehicles[:3]:  # Limit to 3 for testing
                try:
                    # Check if vehicle already exists
                    existing = db.query(VehicleListing).filter(
                        VehicleListing.external_id == vehicle_data.get('external_id')
                    ).first()
                    
                    if not existing:
                        vehicle = VehicleListing(**vehicle_data)
                        db.add(vehicle)
                        saved_count += 1
                        
                except Exception as e:
                    print(f"⚠️  Error saving vehicle: {e}")
                    continue
            
            db.commit()
            print(f"✅ Saved {saved_count} new vehicles to database")
            
        else:
            print("❌ No vehicles found")
            
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        db.rollback()
        
    finally:
        db.close()
        
    print("\n🎉 Scraper test completed!")

if __name__ == "__main__":
    test_scraper()
