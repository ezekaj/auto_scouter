#!/usr/bin/env python3
"""
Quick test of scraper functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_scraper_import():
    """Test if scraper can be imported and basic functionality works"""
    print("🚗 Quick Scraper Test")
    print("=" * 30)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from app.scraper.automotive_scraper import GruppoAutoUnoScraper
        from app.models.automotive import VehicleListing
        print("✅ Imports successful")
        
        # Test scraper initialization
        print("🔧 Testing scraper initialization...")
        scraper = GruppoAutoUnoScraper()
        print("✅ Scraper initialized")
        
        # Test database connection
        print("💾 Testing database connection...")
        from app.models.base import engine
        connection = engine.connect()
        connection.close()
        print("✅ Database connection successful")
        
        # Test basic scraper methods
        print("🔍 Testing scraper methods...")
        base_url = scraper.base_url
        print(f"   Base URL: {base_url}")
        print("✅ Scraper methods accessible")
        
        print("\n🎉 All tests passed! Scraper is ready.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_scraper_import()
    sys.exit(0 if success else 1)
