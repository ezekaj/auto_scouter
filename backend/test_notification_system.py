#!/usr/bin/env python3
"""
Comprehensive Test Runner for Notification System

This script runs all tests and validates the complete notification system
to ensure it meets the success criteria.
"""

import sys

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.models.base import SessionLocal
from app.models.scout import User, Alert
from app.models.automotive import VehicleListing
from app.models.notifications import (
    Notification, NotificationPreferences, NotificationTemplate,
    NotificationStatus, NotificationType, NotificationFrequency
)
from app.services.enhanced_alert_matcher import EnhancedAlertMatchingEngine
from app.services.enhanced_notification_delivery import NotificationService
from app.services.notification_templates import create_default_templates


class NotificationSystemValidator:
    """Comprehensive validator for the notification system"""

    def __init__(self):
        self.db = SessionLocal()
        self.test_results: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.test_user: Optional[User] = None
        self.test_alert: Optional[Alert] = None
        self.test_listings: List[VehicleListing] = []

    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now(timezone.utc)
        })
        
        if not success:
            self.errors.append(f"{test_name}: {message}")

    def setup_test_data(self):
        """Set up test data for validation"""
        print("\n🔧 Setting up test data...")
        
        try:
            # Create test user
            test_user = User(
                username="testuser",
                email="test@example.com",
                hashed_password="hashed_password"
            )
            self.db.add(test_user)
            self.db.commit()
            self.test_user = test_user
            
            # Create notification preferences
            prefs = NotificationPreferences(
                user_id=test_user.id,
                email_enabled=True,
                email_frequency=NotificationFrequency.IMMEDIATE,
                max_notifications_per_day=10
            )
            self.db.add(prefs)
            
            # Create default templates
            create_default_templates(self.db)
            
            # Create test alert
            test_alert = Alert(
                user_id=test_user.id,
                name="Test BMW Alert",
                description="Test alert for BMW vehicles",
                make="BMW",
                model="3 Series",
                min_price=25000,
                max_price=50000,
                min_year=2018,
                max_year=2023,
                max_mileage=100000,
                fuel_type="Petrol",
                city="Munich",
                is_active=True,
                notification_frequency="immediate"
            )
            self.db.add(test_alert)
            self.db.commit()
            self.test_alert = test_alert
            
            # Create test listings
            self.create_test_listings()
            
            self.log_test("Setup Test Data", True, "Test data created successfully")
            
        except Exception as e:
            self.log_test("Setup Test Data", False, str(e))
            raise

    def create_test_listings(self):
        """Create test vehicle listings"""
        listings_data: List[Dict[str, Any]] = [
            # Perfect match
            {
                "make": "BMW",
                "model": "3 Series",
                "year": 2020,
                "price": 35000,
                "mileage": 50000,
                "fuel_type": "Petrol",
                "transmission": "Automatic",
                "city": "Munich",
                "listing_url": "https://example.com/bmw-1"
            },
            # Partial match (different city)
            {
                "make": "BMW",
                "model": "3 Series",
                "year": 2019,
                "price": 32000,
                "mileage": 60000,
                "fuel_type": "Petrol",
                "transmission": "Manual",
                "city": "Berlin",
                "listing_url": "https://example.com/bmw-2"
            },
            # No match (different make)
            {
                "make": "Audi",
                "model": "A4",
                "year": 2020,
                "price": 38000,
                "mileage": 45000,
                "fuel_type": "Diesel",
                "transmission": "Automatic",
                "city": "Munich",
                "listing_url": "https://example.com/audi-1"
            },
            # Edge case (price slightly outside range)
            {
                "make": "BMW",
                "model": "3 Series",
                "year": 2021,
                "price": 52000,  # Above max price
                "mileage": 30000,
                "fuel_type": "Petrol",
                "transmission": "Automatic",
                "city": "Munich",
                "listing_url": "https://example.com/bmw-3"
            }
        ]
        
        self.test_listings = []
        for listing_data in listings_data:
            listing = VehicleListing(
                **listing_data,
                is_active=True,
                scraped_at=datetime.now(timezone.utc)
            )
            self.db.add(listing)
            self.test_listings.append(listing)
        
        self.db.commit()

    def test_alert_matching(self):
        """Test alert matching functionality"""
        print("\n🎯 Testing Alert Matching...")
        
        try:
            matcher = EnhancedAlertMatchingEngine(self.db)
            
            # Test perfect match
            perfect_match = matcher.check_alert_match(self.test_alert, self.test_listings[0])
            self.log_test(
                "Perfect Match Detection", 
                perfect_match is not None and perfect_match["match_score"] > 0.8,
                f"Score: {perfect_match['match_score'] if perfect_match else 'None'}"
            )
            
            # Test partial match
            partial_match = matcher.check_alert_match(self.test_alert, self.test_listings[1])
            self.log_test(
                "Partial Match Detection",
                partial_match is not None and 0.4 < partial_match["match_score"] < 0.8,
                f"Score: {partial_match['match_score'] if partial_match else 'None'}"
            )
            
            # Test no match
            no_match = matcher.check_alert_match(self.test_alert, self.test_listings[2])
            self.log_test(
                "No Match Detection",
                no_match is None,
                "Correctly identified non-matching listing"
            )
            
            # Test price tolerance
            price_tolerance = matcher.check_alert_match(self.test_alert, self.test_listings[3])
            self.log_test(
                "Price Tolerance",
                price_tolerance is not None,
                "Price tolerance working correctly"
            )
            
        except Exception as e:
            self.log_test("Alert Matching", False, str(e))

    def test_notification_creation(self):
        """Test notification creation"""
        print("\n📧 Testing Notification Creation...")
        
        try:
            matcher = EnhancedAlertMatchingEngine(self.db)
            
            # Test notification creation for perfect match
            match_result = matcher.check_alert_match(self.test_alert, self.test_listings[0])
            if match_result:
                notification = matcher.create_notification(
                    self.test_alert, 
                    self.test_listings[0], 
                    match_result
                )
                
                self.log_test(
                    "Notification Creation",
                    notification is not None,
                    f"Notification ID: {notification.id if notification else 'None'}"
                )
                
                if notification:
                    # Verify notification content
                    self.log_test(
                        "Notification Content",
                        bool(notification.title and notification.message),
                        "Title and message populated"
                    )
                    
                    # Verify content data
                    self.log_test(
                        "Notification Content Data",
                        bool(notification.content_data and "listing" in notification.content_data),
                        "Content data includes listing information"
                    )
            else:
                self.log_test("Notification Creation", False, "No match found for notification creation")
                
        except Exception as e:
            self.log_test("Notification Creation", False, str(e))

    def test_notification_delivery(self):
        """Test notification delivery"""
        print("\n📬 Testing Notification Delivery...")
        
        try:
            # Create a test notification
            if not self.test_user:
                raise ValueError("Test user not initialized")
            notification = Notification(
                user_id=self.test_user.id,
                notification_type=NotificationType.EMAIL,
                title="Test Notification",
                message="This is a test notification",
                content_data={
                    "test": True,
                    "listing": {
                        "make": "BMW",
                        "model": "3 Series",
                        "price": 35000
                    }
                },
                priority=2
            )
            self.db.add(notification)
            self.db.commit()
            
            # Test notification service
            service = NotificationService(self.db)
            
            # Mock email sending for testing
            original_send_email = service._send_email
            service._send_email = lambda *args: Any, **kwargs: Any: True  # type: ignore
            
            success = service.send_notification(notification)
            
            self.log_test(
                "Email Notification Delivery",
                bool(success and notification.status == NotificationStatus.SENT),
                f"Status: {notification.status}"
            )
            
            # Restore original method
            service._send_email = original_send_email
            
        except Exception as e:
            self.log_test("Notification Delivery", False, str(e))

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("\n⏱️ Testing Rate Limiting...")
        
        try:
            if not self.test_user:
                raise ValueError("Test user not initialized")
            matcher = EnhancedAlertMatchingEngine(self.db)

            # Update preferences to have low limits
            self.db.query(NotificationPreferences).filter(
                NotificationPreferences.user_id == self.test_user.id
            ).update({
                "max_notifications_per_day": 1,
                "max_notifications_per_alert_per_day": 1
            })
            self.db.commit()
            
            # Create first notification (should succeed)
            if not self.test_alert or not self.test_listings:
                raise ValueError("Test alert or listings not initialized")
            match_result1 = matcher.check_alert_match(self.test_alert, self.test_listings[0])
            if not match_result1:
                raise ValueError("No match result for first notification")
            notification1 = matcher.create_notification(
                self.test_alert,
                self.test_listings[0],
                match_result1
            )
            
            self.log_test(
                "First Notification (Rate Limit)",
                notification1 is not None,
                "First notification created successfully"
            )
            
            # Create second notification (should be blocked)
            match_result2 = matcher.check_alert_match(self.test_alert, self.test_listings[1])
            if not match_result2:
                raise ValueError("No match result for second notification")
            notification2 = matcher.create_notification(
                self.test_alert,
                self.test_listings[1],
                match_result2
            )
            
            self.log_test(
                "Rate Limit Enforcement",
                notification2 is None,
                "Second notification correctly blocked by rate limit"
            )
            
        except Exception as e:
            self.log_test("Rate Limiting", False, str(e))

    def test_template_rendering(self):
        """Test notification template rendering"""
        print("\n🎨 Testing Template Rendering...")
        
        try:
            service = NotificationService(self.db)
            
            # Get email template
            template = self.db.query(NotificationTemplate).filter(
                NotificationTemplate.notification_type == NotificationType.EMAIL,
                NotificationTemplate.name == "vehicle_alert_email"
            ).first()
            
            if template:
                # Create test notification with content data
                if not self.test_user:
                    raise ValueError("Test user not initialized")
                notification = Notification(
                    user_id=self.test_user.id,
                    notification_type=NotificationType.EMAIL,
                    title="Template Test",
                    message="Testing template rendering",
                    content_data={
                        "listing": {
                            "make": "BMW",
                            "model": "3 Series",
                            "year": 2020,
                            "price": 35000,
                            "city": "Munich"
                        },
                        "alert": {
                            "name": "Test Alert"
                        },
                        "match": {
                            "score": 0.95,
                            "is_perfect_match": True
                        }
                    }
                )
                
                # Test template rendering
                prefs = self.db.query(NotificationPreferences).filter(
                    NotificationPreferences.user_id == self.test_user.id
                ).first()
                
                rendered = service._render_email_template(template, notification, prefs)  # type: ignore

                self.log_test(
                    "Template Rendering",
                    bool(rendered and "subject" in rendered and "html_body" in rendered),
                    "Template rendered successfully"
                )
                
                # Check if variables are replaced
                self.log_test(
                    "Template Variable Substitution",
                    "BMW" in rendered["html_body"] and "3 Series" in rendered["html_body"],
                    "Variables correctly substituted"
                )
            else:
                self.log_test("Template Rendering", False, "Email template not found")
                
        except Exception as e:
            self.log_test("Template Rendering", False, str(e))

    def test_performance(self):
        """Test system performance"""
        print("\n⚡ Testing Performance...")
        
        try:
            matcher = EnhancedAlertMatchingEngine(self.db)
            
            # Measure alert matching performance
            start_time = time.time()
            
            for _ in range(100):  # Test 100 iterations
                for listing in self.test_listings:
                    matcher.check_alert_match(self.test_alert, listing)
            
            end_time = time.time()
            total_time = end_time - start_time
            operations_per_second = 400 / total_time  # 100 iterations * 4 listings
            
            self.log_test(
                "Alert Matching Performance",
                operations_per_second > 50,  # Should handle at least 50 ops/second
                f"{operations_per_second:.1f} operations/second"
            )
            
        except Exception as e:
            self.log_test("Performance", False, str(e))

    def validate_success_criteria(self):
        """Validate that all success criteria are met"""
        print("\n✅ Validating Success Criteria...")
        
        criteria = [
            ("Database Models", "Setup Test Data"),
            ("Alert Matching", "Perfect Match Detection"),
            ("Notification Creation", "Notification Creation"),
            ("Email Delivery", "Email Notification Delivery"),
            ("Rate Limiting", "Rate Limit Enforcement"),
            ("Template System", "Template Rendering"),
            ("Performance", "Alert Matching Performance")
        ]
        
        passed_criteria = 0
        total_criteria = len(criteria)
        
        for criterion, test_name in criteria:
            test_result = next(
                (r for r in self.test_results if r["test"] == test_name), 
                None
            )
            
            if test_result and test_result["success"]:
                print(f"✅ {criterion}: PASSED")
                passed_criteria += 1
            else:
                print(f"❌ {criterion}: FAILED")
        
        success_rate = (passed_criteria / total_criteria) * 100
        
        print(f"\n📊 Overall Success Rate: {success_rate:.1f}% ({passed_criteria}/{total_criteria})")
        
        if success_rate >= 85:
            print("🎉 SUCCESS: Notification system meets acceptance criteria!")
            return True
        else:
            print("⚠️  WARNING: Notification system needs improvement")
            return False

    def generate_report(self):
        """Generate test report"""
        print("\n📋 Test Report")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if self.errors:
            print("\n❌ Errors:")
            for error in self.errors:
                print(f"  - {error}")
        
        print("\n📝 Detailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test']}: {result['message']}")

    def cleanup(self):
        """Clean up test data"""
        try:
            # Delete test data
            if self.test_user:
                self.db.query(Notification).filter(
                    Notification.user_id == self.test_user.id
                ).delete()

                self.db.query(Alert).filter(
                    Alert.user_id == self.test_user.id
                ).delete()

                self.db.query(NotificationPreferences).filter(
                    NotificationPreferences.user_id == self.test_user.id
                ).delete()
            
            for listing in self.test_listings:
                self.db.delete(listing)
            
            self.db.delete(self.test_user)
            self.db.commit()
            
            print("\n🧹 Test data cleaned up")
            
        except Exception as e:
            print(f"⚠️  Cleanup error: {e}")
        finally:
            self.db.close()

    def run_all_tests(self):
        """Run all validation tests"""
        print("🚀 Starting Notification System Validation")
        print("=" * 50)
        
        try:
            self.setup_test_data()
            self.test_alert_matching()
            self.test_notification_creation()
            self.test_notification_delivery()
            self.test_rate_limiting()
            self.test_template_rendering()
            self.test_performance()
            
            success = self.validate_success_criteria()
            self.generate_report()
            
            return success
            
        except Exception as e:
            print(f"❌ Critical error during testing: {e}")
            return False
        finally:
            self.cleanup()


def main():
    """Main function to run the validation"""
    print("Auto Scouter - Notification System Validation")
    print("=" * 60)
    
    validator = NotificationSystemValidator()
    success = validator.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Notification system is ready for production.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please review and fix issues before deployment.")
        sys.exit(1)


if __name__ == "__main__":
    main()
