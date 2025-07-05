"""
Comprehensive tests for the notification system

This module tests the complete notification system including alert matching,
notification delivery, and API endpoints.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.models.scout import Alert, User
from app.models.automotive import VehicleListing
from app.models.notifications import (
    Notification, NotificationPreferences, NotificationTemplate,
    NotificationQueue, NotificationStatus, NotificationType, NotificationFrequency
)
from app.services.enhanced_alert_matcher import EnhancedAlertMatchingEngine
from app.services.enhanced_notification_delivery import NotificationService
from app.services.scraping_integration import ScrapingIntegrationService


class TestAlertMatching:
    """Test alert matching functionality"""

    def test_exact_match(self, db_session: Session, sample_user: User):
        """Test exact vehicle match"""
        # Create alert
        alert = Alert(
            user_id=sample_user.id,
            name="BMW 3 Series Alert",
            make="BMW",
            model="3 Series",
            min_price=20000,
            max_price=40000,
            min_min_year=2018,
            max_year=2018,
            max_min_year=2022,
            max_year=2022,
            is_active=True
        )
        db_session.add(alert)
        db_session.commit()

        # Create matching listing
        listing = VehicleListing(
            make="BMW",
            model="3 Series",
            min_year=2020,
            max_year=2020,
            price=30000,
            mileage=50000,
            fuel_type="Petrol",
            transmission="Automatic",
            city="Munich",
            listing_url="https://example.com/listing/1",
            is_active=True,
            scraped_at=datetime.utcnow()
        )
        db_session.add(listing)
        db_session.commit()

        # Test matching
        matcher = EnhancedAlertMatchingEngine(db_session)
        match_result = matcher.check_alert_match(alert, listing)

        assert match_result is not None
        assert match_result["match_score"] > 0.8
        assert "make" in match_result["matched_criteria"]
        assert "model" in match_result["matched_criteria"]
        assert "price" in match_result["matched_criteria"]
        assert "year" in match_result["matched_criteria"]

    def test_partial_match(self, db_session: Session, sample_user: User):
        """Test partial vehicle match"""
        # Create alert with specific criteria
        alert = Alert(
            user_id=sample_user.id,
            name="Audi Alert",
            make="Audi",
            min_price=25000,
            max_price=50000,
            fuel_type="Diesel",
            is_active=True
        )
        db_session.add(alert)
        db_session.commit()

        # Create partially matching listing
        listing = VehicleListing(
            make="Audi",
            model="A4",
            min_year=2019,
            max_year=2019,
            price=35000,
            fuel_type="Petrol",  # Different fuel type
            transmission="Manual",
            city="Berlin",
            is_active=True,
            scraped_at=datetime.utcnow()
        )
        db_session.add(listing)
        db_session.commit()

        # Test matching
        matcher = EnhancedAlertMatchingEngine(db_session)
        match_result = matcher.check_alert_match(alert, listing)

        assert match_result is not None
        assert 0.4 < match_result["match_score"] < 0.8
        assert "make" in match_result["matched_criteria"]
        assert "price" in match_result["matched_criteria"]
        assert "fuel_type" not in match_result["matched_criteria"]

    def test_no_match(self, db_session: Session, sample_user: User):
        """Test when listing doesn't match alert"""
        # Create alert
        alert = Alert(
            user_id=sample_user.id,
            name="Mercedes Alert",
            make="Mercedes",
            min_price=50000,
            max_price=80000,
            is_active=True
        )
        db_session.add(alert)
        db_session.commit()

        # Create non-matching listing
        listing = VehicleListing(
            make="Toyota",
            model="Corolla",
            min_year=2020,
            max_year=2020,
            price=20000,
            fuel_type="Petrol",
            city="Hamburg",
            is_active=True,
            scraped_at=datetime.utcnow()
        )
        db_session.add(listing)
        db_session.commit()

        # Test matching
        matcher = EnhancedAlertMatchingEngine(db_session)
        match_result = matcher.check_alert_match(alert, listing)

        assert match_result is None

    def test_price_tolerance(self, db_session: Session, sample_user: User):
        """Test price matching with tolerance"""
        # Create alert with price range
        alert = Alert(
            user_id=sample_user.id,
            name="Price Tolerance Test",
            make="Volkswagen",
            min_price=20000,
            max_price=30000,
            is_active=True
        )
        db_session.add(alert)
        db_session.commit()

        # Create listing slightly outside price range
        listing = VehicleListing(
            make="Volkswagen",
            model="Golf",
            min_year=2020,
            max_year=2020,
            price=31500,  # 5% over max price
            fuel_type="Petrol",
            city="Frankfurt",
            is_active=True,
            scraped_at=datetime.utcnow()
        )
        db_session.add(listing)
        db_session.commit()

        # Test matching
        matcher = EnhancedAlertMatchingEngine(db_session)
        match_result = matcher.check_alert_match(alert, listing)

        assert match_result is not None
        assert match_result["match_score"] > 0.5  # Should still match with tolerance


class TestNotificationDelivery:
    """Test notification delivery functionality"""

    def test_email_notification_creation(self, db_session: Session, sample_user: User):
        """Test email notification creation and rendering"""
        # Create notification preferences
        prefs = NotificationPreferences(
            user_id=sample_user.id,
            email_enabled=True,
            email_frequency=NotificationFrequency.IMMEDIATE
        )
        db_session.add(prefs)

        # Create email template
        template = NotificationTemplate(
            name="test_email",
            notification_type=NotificationType.EMAIL,
            language="en",
            subject_template="Test: {{ notification.title }}",
            message_template="Hello {{ user.username }}, {{ notification.message }}",
            html_template="<h1>{{ notification.title }}</h1><p>{{ notification.message }}</p>",
            is_active=True
        )
        db_session.add(template)
        db_session.commit()

        # Create notification
        notification = Notification(
            user_id=sample_user.id,
            notification_type=NotificationType.EMAIL,
            title="Test Notification",
            message="This is a test message",
            priority=2
        )
        db_session.add(notification)
        db_session.commit()

        # Test notification service
        service = NotificationService(db_session)
        
        # Mock email sending
        with patch.object(service, '_send_email', return_value=True) as mock_send:
            success = service.send_notification(notification)
            
            assert success
            assert notification.status == NotificationStatus.SENT
            assert notification.sent_at is not None
            mock_send.assert_called_once()

    def test_rate_limiting(self, db_session: Session, sample_user: User):
        """Test notification rate limiting"""
        # Create notification preferences with low limits
        prefs = NotificationPreferences(
            user_id=sample_user.id,
            max_notifications_per_day=2,
            max_notifications_per_alert_per_day=1
        )
        db_session.add(prefs)

        # Create alert
        alert = Alert(
            user_id=sample_user.id,
            name="Rate Limit Test",
            make="BMW",
            is_active=True
        )
        db_session.add(alert)
        db_session.commit()

        # Create matcher
        matcher = EnhancedAlertMatchingEngine(db_session)

        # Create first notification (should succeed)
        listing1 = VehicleListing(
            make="BMW",
            model="X5",
            price=50000,
            is_active=True,
            scraped_at=datetime.utcnow()
        )
        db_session.add(listing1)
        db_session.commit()

        match_result1 = matcher.check_alert_match(alert, listing1)
        notification1 = matcher.create_notification(alert, listing1, match_result1)
        
        assert notification1 is not None

        # Create second notification for same alert (should be blocked)
        listing2 = VehicleListing(
            make="BMW",
            model="X3",
            price=45000,
            is_active=True,
            scraped_at=datetime.utcnow()
        )
        db_session.add(listing2)
        db_session.commit()

        match_result2 = matcher.check_alert_match(alert, listing2)
        notification2 = matcher.create_notification(alert, listing2, match_result2)
        
        assert notification2 is None  # Should be blocked by rate limit

    def test_quiet_hours(self, db_session: Session, sample_user: User):
        """Test quiet hours functionality"""
        # Create notification preferences with quiet hours
        prefs = NotificationPreferences(
            user_id=sample_user.id,
            quiet_hours_enabled=True,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00"
        )
        db_session.add(prefs)
        db_session.commit()

        # Create notification
        notification = Notification(
            user_id=sample_user.id,
            notification_type=NotificationType.EMAIL,
            title="Quiet Hours Test",
            message="This should be delayed",
            priority=2
        )
        db_session.add(notification)
        db_session.commit()

        # Test notification service
        service = NotificationService(db_session)
        
        # Mock current time to be in quiet hours
        with patch('app.services.enhanced_notification_delivery.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime.strptime("23:30", "%H:%M").replace(
                min_year=2024,
            max_year=2024, month=1, day=1
            )
            mock_datetime.strftime = datetime.strftime
            
            # Mock scheduling
            with patch.object(service, '_schedule_for_later', return_value=True) as mock_schedule:
                result = service.send_notification(notification)
                
                assert result  # Should return True for scheduled
                mock_schedule.assert_called_once()


class TestAPIEndpoints:
    """Test API endpoints"""

    def test_create_alert_endpoint(self, client, auth_headers):
        """Test alert creation endpoint"""
        alert_data = {
            "name": "Test Alert",
            "description": "Test description",
            "make": "BMW",
            "model": "3 Series",
            "min_price": 20000,
            "max_price": 40000,
            "min_year": 2018,
            "max_year": 2022,
            "notification_frequency": "immediate",
            "is_active": True
        }

        response = client.post("/api/v1/alerts/", json=alert_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == alert_data["name"]
        assert data["make"] == alert_data["make"]
        assert data["is_active"] == True

    def test_get_notifications_endpoint(self, client, auth_headers):
        """Test notifications retrieval endpoint"""
        response = client.get("/api/v1/notifications/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "pagination" in data

    def test_notification_preferences_endpoint(self, client, auth_headers):
        """Test notification preferences endpoint"""
        # Get current preferences
        response = client.get("/api/v1/notifications/preferences", headers=auth_headers)
        assert response.status_code == 200

        # Update preferences
        update_data = {
            "email_enabled": True,
            "email_frequency": "daily",
            "max_notifications_per_day": 5
        }

        response = client.put(
            "/api/v1/notifications/preferences", 
            json=update_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email_enabled"] == True
        assert data["email_frequency"] == "daily"

    def test_alert_test_endpoint(self, client, auth_headers, sample_alert):
        """Test alert testing endpoint"""
        test_data = {
            "test_days": 7,
            "max_listings": 100,
            "create_notifications": False
        }

        response = client.post(
            f"/api/v1/alerts/{sample_alert.id}/test",
            json=test_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "listings_tested" in data
        assert "matches_found" in data
        assert "would_trigger" in data


class TestScrapingIntegration:
    """Test scraping system integration"""

    def test_new_listing_processing(self, db_session: Session, sample_user: User):
        """Test processing of new listings"""
        # Create active alert
        alert = Alert(
            user_id=sample_user.id,
            name="Integration Test",
            make="Tesla",
            is_active=True
        )
        db_session.add(alert)
        db_session.commit()

        # Create new listing
        listing = VehicleListing(
            make="Tesla",
            model="Model 3",
            min_year=2022,
            max_year=2022,
            price=45000,
            is_active=True,
            scraped_at=datetime.utcnow()
        )
        db_session.add(listing)
        db_session.commit()

        # Test integration service
        integration_service = ScrapingIntegrationService(db_session)
        result = integration_service.process_new_listings([listing.id])

        assert result["status"] == "completed"
        assert result["processed_listings"] == 1
        assert result["total_matches"] >= 0

    def test_webhook_processing(self, db_session: Session):
        """Test webhook data processing"""
        from app.services.scraping_integration import handle_new_listing_webhook

        # Mock webhook data
        webhook_data = {
            "id": 123,
            "make": "Audi",
            "model": "A4",
            "year": 2021,
            "price": 35000
        }

        result = handle_new_listing_webhook(webhook_data, db_session)
        
        # Should handle gracefully even if listing doesn't exist in DB
        assert "status" in result


class TestSystemValidation:
    """Test complete system validation"""

    def test_end_to_end_workflow(self, db_session: Session, sample_user: User):
        """Test complete end-to-end workflow"""
        # 1. Create user preferences
        prefs = NotificationPreferences(
            user_id=sample_user.id,
            email_enabled=True,
            email_frequency=NotificationFrequency.IMMEDIATE
        )
        db_session.add(prefs)

        # 2. Create alert
        alert = Alert(
            user_id=sample_user.id,
            name="E2E Test Alert",
            make="Mercedes",
            min_price=30000,
            max_price=60000,
            is_active=True
        )
        db_session.add(alert)
        db_session.commit()

        # 3. Create matching listing
        listing = VehicleListing(
            make="Mercedes",
            model="C-Class",
            min_year=2021,
            max_year=2021,
            price=45000,
            fuel_type="Petrol",
            transmission="Automatic",
            city="Stuttgart",
            is_active=True,
            scraped_at=datetime.utcnow()
        )
        db_session.add(listing)
        db_session.commit()

        # 4. Run alert matching
        matcher = EnhancedAlertMatchingEngine(db_session)
        match_result = matcher.check_alert_match(alert, listing)
        
        assert match_result is not None
        assert match_result["match_score"] > 0.6

        # 5. Create notification
        notification = matcher.create_notification(alert, listing, match_result)
        
        assert notification is not None
        assert notification.user_id == sample_user.id
        assert notification.alert_id == alert.id
        assert notification.listing_id == listing.id

        # 6. Test notification delivery
        service = NotificationService(db_session)
        
        with patch.object(service, '_send_email', return_value=True):
            success = service.send_notification(notification)
            
            assert success
            assert notification.status == NotificationStatus.SENT

        # 7. Verify database state
        db_session.refresh(alert)
        assert alert.trigger_count == 1
        assert alert.last_triggered is not None

    def test_performance_benchmarks(self, db_session: Session):
        """Test system performance benchmarks"""
        import time
        
        # Create test data
        users = []
        alerts = []
        listings = []
        
        # Create 10 users with 5 alerts each
        for i in range(10):
            user = User(
                username=f"testuser{i}",
                email=f"test{i}@example.com",
                password_hash="hashed"
            )
            db_session.add(user)
            users.append(user)
        
        db_session.commit()
        
        for user in users:
            for j in range(5):
                alert = Alert(
            user_id=user.id,
                    name=f"Alert {j}",
                    make=["BMW", "Audi", "Mercedes", "Volkswagen", "Toyota"][j],
                    is_active=True
        )
                db_session.add(alert)
                alerts.append(alert)
        
        # Create 100 listings
        makes = ["BMW", "Audi", "Mercedes", "Volkswagen", "Toyota"]
        for i in range(100):
            listing = VehicleListing(
                make=makes[i % len(makes)],
                model=f"Model {i}",
                min_year=2020,
            max_year=2020 + (i % 3),
                price=20000 + (i * 500),
                is_active=True,
                scraped_at=datetime.utcnow()
            )
            db_session.add(listing)
            listings.append(listing)
        
        db_session.commit()
        
        # Benchmark alert matching
        matcher = EnhancedAlertMatchingEngine(db_session)
        
        start_time = time.time()
        total_matches = 0
        
        for alert in alerts:
            for listing in listings:
                match_result = matcher.check_alert_match(alert, listing)
                if match_result:
                    total_matches += 1
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Performance assertions
        assert processing_time < 10.0  # Should complete within 10 seconds
        assert total_matches > 0  # Should find some matches
        
        # Calculate throughput
        total_comparisons = len(alerts) * len(listings)
        comparisons_per_second = total_comparisons / processing_time
        
        assert comparisons_per_second > 100  # Should process at least 100 comparisons/second
