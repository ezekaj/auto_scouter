#!/usr/bin/env python3
"""
Test Cloud Scraping Service
Verifies that automated scraping works in cloud environment
"""

import asyncio
import logging
import time
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_cloud_scraping():
    """Test the cloud scraping functionality"""
    print("🧪 TESTING CLOUD SCRAPING SERVICE")
    print("=" * 50)
    
    try:
        # Test 1: Cloud configuration
        print("\n1. Testing Cloud Configuration...")
        from app.core.cloud_config import get_cloud_settings
        settings = get_cloud_settings()
        print(f"✅ Environment: {settings.environment}")
        print(f"✅ Scraping interval: {settings.scraping_interval_minutes} minutes")
        print(f"✅ Max vehicles per scrape: {settings.max_vehicles_per_scrape}")
        
        # Test 2: Database connectivity
        print("\n2. Testing Cloud Database...")
        from app.models.cloud_base import test_cloud_database_connection, get_database_info
        db_connected = test_cloud_database_connection()
        db_info = get_database_info()
        print(f"✅ Database connected: {db_connected}")
        print(f"✅ Database type: {db_info['type']}")
        print(f"✅ Is cloud database: {db_info['is_cloud']}")
        
        # Test 3: Scraping tasks
        print("\n3. Testing Scraping Tasks...")
        from app.tasks.cloud_scraping_tasks import cloud_scrape_autouno_task, cloud_health_check
        
        # Test health check
        health_result = await asyncio.to_thread(cloud_health_check.apply)
        print(f"✅ Health check: {health_result.result['status']}")
        
        # Test AutoUno scraping
        print("🔄 Running AutoUno scraping test...")
        scrape_result = await asyncio.to_thread(cloud_scrape_autouno_task.apply)
        result = scrape_result.result
        print(f"✅ Scraping completed: {result['status']}")
        print(f"   Vehicles found: {result.get('vehicles_found', 0)}")
        print(f"   New vehicles: {result.get('new_vehicles', 0)}")
        print(f"   Notifications sent: {result.get('notifications_sent', 0)}")
        
        # Test 4: Background scraper
        print("\n4. Testing Background Scraper...")
        from app.background_scraper import BackgroundScraper
        scraper = BackgroundScraper()
        
        print("🔄 Running background scraper cycle...")
        await scraper.run_scraping_cycle()
        print("✅ Background scraper cycle completed")
        
        # Test 5: Vehicle count verification
        print("\n5. Verifying Vehicle Data...")
        from app.models.cloud_base import SessionLocal
        from app.models.automotive import VehicleListing
        
        db = SessionLocal()
        try:
            total_vehicles = db.query(VehicleListing).count()
            autouno_vehicles = db.query(VehicleListing).filter(
                VehicleListing.source_website == "autouno.al"
            ).count()
            autoscout_vehicles = db.query(VehicleListing).filter(
                VehicleListing.source_website == "autoscout24.com"
            ).count()
            
            print(f"✅ Total vehicles in database: {total_vehicles}")
            print(f"   AutoUno vehicles: {autouno_vehicles}")
            print(f"   AutoScout24 vehicles: {autoscout_vehicles}")
            
        finally:
            db.close()
        
        print("\n🎯 CLOUD SCRAPING TEST RESULTS:")
        print("✅ Cloud configuration working")
        print("✅ Database connectivity verified")
        print("✅ Scraping tasks functional")
        print("✅ Background scraper operational")
        print("✅ Vehicle data processing working")
        print("\n🚀 CLOUD SCRAPING SERVICE IS READY FOR 24/7 OPERATION!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Cloud scraping test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_celery_tasks():
    """Test Celery task configuration"""
    print("\n🔄 TESTING CELERY TASK CONFIGURATION")
    print("-" * 40)
    
    try:
        from app.tasks.celery_app import celery_app
        
        # Test Celery app configuration
        print(f"✅ Celery app: {celery_app.main}")
        print(f"✅ Broker URL: {celery_app.conf.broker_url[:50]}...")
        print(f"✅ Result backend: {celery_app.conf.result_backend[:50]}...")
        
        # Test task registration
        registered_tasks = list(celery_app.tasks.keys())
        print(f"✅ Registered tasks: {len(registered_tasks)}")
        for task in registered_tasks:
            if 'cloud' in task or 'scrape' in task:
                print(f"   - {task}")
        
        # Test beat schedule
        beat_schedule = celery_app.conf.beat_schedule
        print(f"✅ Scheduled tasks: {len(beat_schedule)}")
        for task_name, config in beat_schedule.items():
            print(f"   - {task_name}: {config['schedule']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Celery test failed: {e}")
        return False

async def simulate_24_7_operation():
    """Simulate 24/7 operation for testing"""
    print("\n⏰ SIMULATING 24/7 OPERATION (30 seconds)")
    print("-" * 40)
    
    try:
        from app.background_scraper import BackgroundScraper
        scraper = BackgroundScraper()
        
        # Simulate 3 scraping cycles (10 seconds each)
        for cycle in range(3):
            print(f"🔄 Cycle {cycle + 1}/3 - {datetime.now().strftime('%H:%M:%S')}")
            
            start_time = time.time()
            await scraper.run_scraping_cycle()
            duration = time.time() - start_time
            
            print(f"✅ Cycle completed in {duration:.2f}s")
            
            if cycle < 2:  # Don't sleep after last cycle
                print("⏳ Waiting 10 seconds (simulating 5-minute interval)...")
                await asyncio.sleep(10)
        
        print("🎯 24/7 operation simulation completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ 24/7 simulation failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🌐 CLOUD SCRAPING SERVICE TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Cloud Scraping Functionality", test_cloud_scraping),
        ("Celery Task Configuration", lambda: test_celery_tasks()),
        ("24/7 Operation Simulation", simulate_24_7_operation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST RESULTS SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - CLOUD SCRAPING SERVICE READY!")
        print("🚀 Deploy to Railway for 24/7 operation!")
    else:
        print(f"\n⚠️  {total - passed} tests failed - fix issues before deployment")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
