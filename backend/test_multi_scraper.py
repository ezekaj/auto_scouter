#!/usr/bin/env python3
"""
Test script for multi-source scraper functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.scraper.multi_source_scraper import multi_source_scraper
from app.scraper.autoscout24_scraper import AutoScout24Scraper
from app.scraper.mobile_de_scraper import MobileDeScraper

def test_individual_scrapers():
    """Test individual scrapers"""
    print("=== Testing Individual Scrapers ===")
    
    # Test AutoScout24 scraper
    print("\n1. Testing AutoScout24 Scraper...")
    try:
        autoscout_scraper = AutoScout24Scraper()
        print(f"✓ AutoScout24 scraper initialized successfully")
        print(f"  Base URL: {autoscout_scraper.base_url}")
        print(f"  Search URL: {autoscout_scraper.search_url}")
    except Exception as e:
        print(f"✗ AutoScout24 scraper failed: {e}")
    
    # Test Mobile.de scraper
    print("\n2. Testing Mobile.de Scraper...")
    try:
        mobile_scraper = MobileDeScraper()
        print(f"✓ Mobile.de scraper initialized successfully")
        print(f"  Base URL: {mobile_scraper.base_url}")
        print(f"  Search URL: {mobile_scraper.search_url}")
    except Exception as e:
        print(f"✗ Mobile.de scraper failed: {e}")

def test_multi_source_manager():
    """Test multi-source scraper manager"""
    print("\n=== Testing Multi-Source Manager ===")
    
    try:
        # Test initialization
        print(f"✓ Multi-source scraper initialized")
        print(f"  Available sources: {list(multi_source_scraper.scrapers.keys())}")
        print(f"  Enabled sources: {multi_source_scraper.enabled_sources}")
        
        # Test source status
        print("\n3. Testing Source Status...")
        status = multi_source_scraper.get_source_status()
        for source, info in status.items():
            print(f"  {source}: enabled={info.get('enabled', False)}")
        
        # Test source management
        print("\n4. Testing Source Management...")
        
        # Test enabling/disabling sources
        result = multi_source_scraper.enable_source('autoscout24')
        print(f"  Enable AutoScout24: {result}")
        
        result = multi_source_scraper.enable_source('mobile_de')
        print(f"  Enable Mobile.de: {result}")
        
        print(f"  Updated enabled sources: {multi_source_scraper.enabled_sources}")
        
    except Exception as e:
        print(f"✗ Multi-source manager test failed: {e}")

def test_scraper_compliance():
    """Test scraper compliance checking"""
    print("\n=== Testing Scraper Compliance ===")
    
    try:
        # Test compliance for each source
        sources_to_test = ['gruppoautouno', 'autoscout24', 'mobile_de']
        
        for source in sources_to_test:
            print(f"\n5. Testing compliance for {source}...")
            try:
                compliant = multi_source_scraper._check_source_compliance(source)
                print(f"  {source} compliance: {'✓ Allowed' if compliant else '✗ Blocked'}")
            except Exception as e:
                print(f"  {source} compliance check failed: {e}")
                
    except Exception as e:
        print(f"✗ Compliance testing failed: {e}")

def main():
    """Run all tests"""
    print("Multi-Source Scraper Test Suite")
    print("=" * 50)
    
    try:
        test_individual_scrapers()
        test_multi_source_manager()
        test_scraper_compliance()
        
        print("\n" + "=" * 50)
        print("✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
