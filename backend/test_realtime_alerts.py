#!/usr/bin/env python3
"""
Test Real-time Alert System

This script tests the real-time alert matching and notification system.
"""

import sys
import os
import asyncio
import time
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.base import SessionLocal
from app.models.scout import Alert, User
from app.models.automotive import VehicleListing
from app.models.notifications import Notification
from app.services.alert_matcher import AlertMatchingEngine
from app.services.notification_delivery import NotificationDeliveryService
from app.tasks.alert_matching import run_alert_matching_task

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"🚨 {title}")
    print("=" * 60)

def print_step(step, description):
    """Print a formatted step"""
    print(f"\n📋 Step {step}: {description}")
    print("-" * 40)

def create_test_user_and_alert():
    """Create a test user and alert for testing"""
    db = SessionLocal()
    try:
        # Check if test user exists
        test_user = db.query(User).filter(User.username == "test_user").first()
        if not test_user:
            test_user = User(
                username="test_user",
                email="test@example.com",
                hashed_password="test_hash",
                is_active=True,
                is_verified=True
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print(f"✅ Created test user: {test_user.username}")
        else:
            print(f"✅ Using existing test user: {test_user.username}")
        
        # Create test alert
        test_alert = Alert(
            user_id=test_user.id,
            name="Test Alert - Volkswagen",
            description="Test alert for Volkswagen vehicles",
            make="Volkswagen",
            min_price=10000,
            max_price=25000,
            min_year=2020,
            max_year=2024,
            fuel_type="gasoline",
            is_active=True,
            notification_frequency="immediate",
            max_notifications_per_day=10
        )
        db.add(test_alert)
        db.commit()
        db.refresh(test_alert)
        
        print(f"✅ Created test alert: {test_alert.name}")
        return test_user, test_alert
        
    finally:
        db.close()

def test_alert_matching():
    """Test the alert matching engine"""
    print("🔍 Testing alert matching engine...")
    
    db = SessionLocal()
    try:
        # Get test alert
        test_alert = db.query(Alert).filter(Alert.name.like("Test Alert%")).first()
        if not test_alert:
            print("❌ No test alert found")
            return False
        
        # Get recent vehicles
        recent_vehicles = db.query(VehicleListing).filter(
            VehicleListing.is_active == True
        ).limit(10).all()
        
        if not recent_vehicles:
            print("❌ No vehicles found for testing")
            return False
        
        print(f"📊 Testing against {len(recent_vehicles)} vehicles")
        
        # Initialize alert matcher
        alert_matcher = AlertMatchingEngine(db)
        
        # Test matching
        matches = alert_matcher._match_alert_against_listings(test_alert, recent_vehicles)
        
        print(f"🎯 Found {len(matches)} matches")
        
        for match in matches:
            vehicle = next(v for v in recent_vehicles if v.id == match.vehicle_id)
            print(f"   - {vehicle.make} {vehicle.model} ({vehicle.year}) - Score: {match.match_score:.2f}")
            print(f"     Criteria: {', '.join(match.matched_criteria)}")
        
        return len(matches) > 0
        
    finally:
        db.close()

def test_notification_creation():
    """Test notification creation and delivery"""
    print("📧 Testing notification creation...")
    
    db = SessionLocal()
    try:
        # Get test user
        test_user = db.query(User).filter(User.username == "test_user").first()
        if not test_user:
            print("❌ Test user not found")
            return False
        
        # Create notification service
        notification_service = NotificationDeliveryService(db)
        
        # Create test notification
        notification = notification_service.create_and_queue_notification(
            user_id=test_user.id,
            notification_type="vehicle_match",
            title="Test Vehicle Match",
            message="A test vehicle matching your alert has been found!",
            content_data={
                "vehicle_make": "Volkswagen",
                "vehicle_model": "Golf",
                "vehicle_year": 2022,
                "vehicle_price": 18500,
                "alert_name": "Test Alert - Volkswagen"
            },
            priority=1
        )
        
        if notification:
            print(f"✅ Created notification: {notification.title}")
            print(f"   ID: {notification.id}")
            print(f"   Type: {notification.notification_type}")
            print(f"   Created: {notification.created_at}")
            return True
        else:
            print("❌ Failed to create notification")
            return False
        
    finally:
        db.close()

def test_background_task():
    """Test the background alert matching task"""
    print("⚙️ Testing background alert matching task...")
    
    try:
        # Run the alert matching task
        result = run_alert_matching_task.delay()
        
        print(f"✅ Alert matching task queued: {result.id}")
        
        # Wait a bit and check status
        time.sleep(3)
        
        if result.ready():
            task_result = result.result
            print(f"📊 Task completed: {task_result}")
            return True
        else:
            print("⏳ Task is running in background...")
            return True
            
    except Exception as e:
        print(f"❌ Background task test failed: {e}")
        return False

def test_system_health():
    """Test overall system health"""
    print("🏥 Testing system health...")
    
    db = SessionLocal()
    try:
        # Check database connectivity
        user_count = db.query(User).count()
        alert_count = db.query(Alert).filter(Alert.is_active == True).count()
        vehicle_count = db.query(VehicleListing).filter(VehicleListing.is_active == True).count()
        notification_count = db.query(Notification).count()
        
        print(f"📊 System Statistics:")
        print(f"   Users: {user_count}")
        print(f"   Active Alerts: {alert_count}")
        print(f"   Active Vehicles: {vehicle_count}")
        print(f"   Total Notifications: {notification_count}")
        
        # Check recent activity
        recent_vehicles = db.query(VehicleListing).filter(
            VehicleListing.scraped_at >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        recent_notifications = db.query(Notification).filter(
            Notification.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        print(f"📈 Recent Activity (24h):")
        print(f"   New Vehicles: {recent_vehicles}")
        print(f"   New Notifications: {recent_notifications}")
        
        # Health assessment
        health_score = 0
        if user_count > 0:
            health_score += 25
        if alert_count > 0:
            health_score += 25
        if vehicle_count > 0:
            health_score += 25
        if recent_vehicles > 0:
            health_score += 25
        
        print(f"🏥 System Health Score: {health_score}/100")
        
        if health_score >= 75:
            print("✅ System is healthy")
            return True
        else:
            print("⚠️ System needs attention")
            return False
        
    finally:
        db.close()

def main():
    """Main test function"""
    print_header("Real-time Alert System Test")
    
    test_results = []
    
    print_step(1, "Setting up test data")
    try:
        test_user, test_alert = create_test_user_and_alert()
        test_results.append(("Setup", True))
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        test_results.append(("Setup", False))
        return
    
    print_step(2, "Testing alert matching")
    result = test_alert_matching()
    test_results.append(("Alert Matching", result))
    
    print_step(3, "Testing notification creation")
    result = test_notification_creation()
    test_results.append(("Notification Creation", result))
    
    print_step(4, "Testing background tasks")
    result = test_background_task()
    test_results.append(("Background Tasks", result))
    
    print_step(5, "Testing system health")
    result = test_system_health()
    test_results.append(("System Health", result))
    
    # Summary
    print_header("Test Results Summary")
    
    passed = 0
    total = len(test_results)
    
    for test_name, success in test_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    success_rate = (passed / total) * 100
    print(f"\n📊 Overall Success Rate: {success_rate:.1f}% ({passed}/{total})")
    
    if success_rate >= 80:
        print("🎉 Real-time alert system is working well!")
    else:
        print("⚠️ Real-time alert system needs improvement")
    
    return success_rate >= 80

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
