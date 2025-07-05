"""
Alert Matching Engine Tests

This module contains tests for the alert matching functionality.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.scout import User, Alert
from app.models.automotive import VehicleListing
from app.models.notifications import Notification, NotificationPreferences
from app.services.alert_matcher import AlertMatchingEngine
from app.core.auth import get_password_hash


class TestAlertMatchingEngine:
    """Test alert matching engine functionality"""
    
    @pytest.fixture
    def test_user(self, db_session: Session):
        """Create a test user"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=get_password_hash("TestPassword123")
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def test_alert(self, db_session: Session, test_user: User):
        """Create a test alert"""
        alert = Alert(
            user_id=test_user.id,
            name="Test Alert",
            make="Volkswagen",
            model="Golf",
            min_price=15000,
            max_price=25000,
            min_min_year=2020,
            max_year=2020,
            max_min_year=2022,
            max_year=2022,
            fuel_type="diesel",
            transmission="manual",
            city="Napoli"
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        return alert
    
    @pytest.fixture
    def matching_listing(self, db_session: Session):
        """Create a car listing that matches the test alert"""
        listing = VehicleListing(
            external_id="match-car-1",
            listing_url="https://example.com/match-car-1",
            make="Volkswagen",
            model="Golf",
            min_year=2020,
            max_year=2020,
            price=18500.0,
            mileage=45000,
            fuel_type="diesel",
            transmission="manual",
            city="Napoli",
            source_website="test_source",
            is_active=True,
            scraped_at=datetime.utcnow(
        )
        )
        db_session.add(listing)
        db_session.commit()
        db_session.refresh(listing)
        return listing
    
    @pytest.fixture
    def non_matching_listing(self, db_session: Session):
        """Create a car listing that doesn't match the test alert"""
        listing = VehicleListing(
            external_id="no-match-car-1",
            listing_url="https://example.com/no-match-car-1",
            make="BMW",
            model="X3",
            min_year=2019,
            max_year=2019,
            price=35000.0,
            mileage=30000,
            fuel_type="gasoline",
            transmission="automatic",
            city="Milano",
            source_website="test_source",
            is_active=True,
            scraped_at=datetime.utcnow(
        )
        )
        db_session.add(listing)
        db_session.commit()
        db_session.refresh(listing)
        return listing
    
    def test_exact_match(self, db_session: Session, test_alert: Alert, matching_listing: VehicleListing):
        """Test exact match between alert and listing"""
        matcher = AlertMatchingEngine(db_session)
        
        match_result = matcher._calculate_match_score(test_alert, matching_listing)
        
        assert match_result is not None
        assert match_result.alert_id == test_alert.id
        assert match_result.listing_id == matching_listing.id
        assert match_result.match_score >= 0.7
        assert "make" in match_result.matched_criteria
        assert "model" in match_result.matched_criteria
        assert "price" in match_result.matched_criteria
        assert "year" in match_result.matched_criteria
    
    def test_no_match(self, db_session: Session, test_alert: Alert, non_matching_listing: VehicleListing):
        """Test no match between alert and listing"""
        matcher = AlertMatchingEngine(db_session)
        
        match_result = matcher._calculate_match_score(test_alert, non_matching_listing)
        
        assert match_result is None
    
    def test_partial_match(self, db_session: Session, test_user: User):
        """Test partial match with only some criteria matching"""
        # Create alert with only make and price range
        alert = Alert(
            user_id=test_user.id,
            name="Test Alert",
            make="Volkswagen",
            min_price=15000,
            max_price=25000
        )
        db_session.add(alert)
        db_session.commit()
        
        # Create listing that matches make and price but not other criteria
        listing = VehicleListing(
            external_id="partial-match-1",
            listing_url="https://example.com/partial-match-1",
            make="Volkswagen",
            model="Passat",  # Different model
            min_year=2019,
            max_year=2019,       # Different year
            price=20000.0,   # Matches price range
            source_website="test_source",
            is_active=True,
            scraped_at=datetime.utcnow(
        )
        )
        db_session.add(listing)
        db_session.commit()
        
        matcher = AlertMatchingEngine(db_session)
        match_result = matcher._calculate_match_score(alert, listing)
        
        assert match_result is not None
        assert "make" in match_result.matched_criteria
        assert "price" in match_result.matched_criteria
        assert match_result.match_score >= 0.7
    
    def test_price_range_matching(self, db_session: Session):
        """Test price range matching logic"""
        matcher = AlertMatchingEngine(db_session)
        
        # Create alert with price range
        alert = Alert(min_price=15000, max_price=25000)
        
        # Test listing within range
        listing_in_range = VehicleListing(
            price=20000.0,
            source_website="test_source"
        )
        assert matcher._match_price_range(alert, listing_in_range) is True
        
        # Test listing below range
        listing_below = VehicleListing(
            price=10000.0,
            source_website="test_source"
        )
        assert matcher._match_price_range(alert, listing_below) is False
        
        # Test listing above range
        listing_above = VehicleListing(
            price=30000.0,
            source_website="test_source"
        )
        assert matcher._match_price_range(alert, listing_above) is False
        
        # Test edge cases
        listing_min = VehicleListing(
            price=15000.0,
            source_website="test_source"
        )
        assert matcher._match_price_range(alert, listing_min) is True
        
        listing_max = VehicleListing(
            price=25000.0,
            source_website="test_source"
        )
        assert matcher._match_price_range(alert, listing_max) is True
    
    def test_make_model_fuzzy_matching(self, db_session: Session):
        """Test fuzzy matching for make and model"""
        matcher = AlertMatchingEngine(db_session)
        
        # Test exact match
        assert matcher._match_make("Volkswagen", "Volkswagen") is True
        assert matcher._match_model("Golf", "Golf") is True
        
        # Test case insensitive
        assert matcher._match_make("volkswagen", "Volkswagen") is True
        assert matcher._match_model("golf", "Golf") is True
        
        # Test partial match
        assert matcher._match_make("VW", "Volkswagen") is True
        assert matcher._match_make("Volkswagen", "VW") is True
        assert matcher._match_model("Golf GTI", "Golf") is True
        
        # Test no match
        assert matcher._match_make("BMW", "Volkswagen") is False
        assert matcher._match_model("Passat", "Golf") is False
    
    def test_rate_limiting(self, db_session: Session, test_user: User, test_alert: Alert):
        """Test notification rate limiting"""
        # Create notification preferences with low limits
        prefs = NotificationPreferences(
            user_id=test_user.id,
            max_notifications_per_day=2,
            max_notifications_per_alert_per_day=1
        )
        db_session.add(prefs)
        db_session.commit()
        
        matcher = AlertMatchingEngine(db_session)
        
        # First notification should be allowed
        assert matcher._check_rate_limits(test_user.id, test_alert.id) is True
        
        # Create a notification for today
        notification = Notification(
            user_id=test_user.id,
            alert_id=test_alert.id,
            notification_type="in_app",
            title="Test",
            message="Test",
            created_at=datetime.utcnow()
        )
        db_session.add(notification)
        db_session.commit()
        
        # Second notification for same alert should be blocked
        assert matcher._check_rate_limits(test_user.id, test_alert.id) is False
    
    def test_duplicate_notification_prevention(self, db_session: Session, test_alert: Alert, matching_listing: VehicleListing):
        """Test that duplicate notifications are not created"""
        matcher = AlertMatchingEngine(db_session)
        
        # Create existing notification
        existing_notification = Notification(
            user_id=test_alert.user_id,
            alert_id=test_alert.id,
            listing_id=matching_listing.id,
            notification_type="in_app",
            title="Test",
            message="Test"
        )
        db_session.add(existing_notification)
        db_session.commit()
        
        # Create match result
        from app.schemas.notifications import AlertMatchResult
        match = AlertMatchResult(
            alert_id=test_alert.id,
            listing_id=matching_listing.id,
            match_score=0.9,
            matched_criteria=["make", "model", "price"]
        )
        
        # Should not create notification
        assert matcher._should_create_notification(test_alert, match) is False
    
    def test_full_alert_matching_run(self, db_session: Session, test_alert: Alert, matching_listing: VehicleListing):
        """Test complete alert matching run"""
        matcher = AlertMatchingEngine(db_session)
        
        # Run alert matching
        match_log = matcher.run_alert_matching()
        
        assert match_log.status == "completed"
        assert match_log.alerts_processed >= 1
        assert match_log.listings_checked >= 1
        assert match_log.matches_found >= 1
        assert match_log.notifications_created >= 1
        
        # Verify notification was created
        notification = db_session.query(Notification).filter(
            Notification.alert_id == test_alert.id,
            Notification.listing_id == matching_listing.id
        ).first()
        
        assert notification is not None
        assert notification.user_id == test_alert.user_id
        assert "Volkswagen Golf" in notification.title
    
    def test_alert_matching_with_time_filter(self, db_session: Session, test_alert: Alert):
        """Test alert matching with time-based filtering"""
        # Create old listing (should be ignored)
        old_listing = VehicleListing(
            external_id="old-car",
            listing_url="https://example.com/old-car",
            make="Volkswagen",
            model="Golf",
            min_year=2020,
            max_year=2020,
            price=18500.0,
            source_website="test_source",
            is_active=True,
            scraped_at=datetime.utcnow(
        ) - timedelta(hours=3)
        )
        db_session.add(old_listing)
        
        # Create new listing (should be processed)
        new_listing = VehicleListing(
            external_id="new-car",
            listing_url="https://example.com/new-car",
            make="Volkswagen",
            model="Golf",
            min_year=2020,
            max_year=2020,
            price=18500.0,
            source_website="test_source",
            is_active=True,
            scraped_at=datetime.utcnow(
        )
        )
        db_session.add(new_listing)
        db_session.commit()
        
        matcher = AlertMatchingEngine(db_session)
        
        # Run with time filter (last 1 hour)
        check_since = datetime.utcnow() - timedelta(hours=1)
        match_log = matcher.run_alert_matching(check_since=check_since)
        
        # Should only process the new listing
        assert match_log.listings_checked == 1
        
        # Verify only new listing generated notification
        notifications = db_session.query(Notification).filter(
            Notification.alert_id == test_alert.id
        ).all()
        
        assert len(notifications) == 1
        assert notifications[0].listing_id == new_listing.id
    
    def test_inactive_alert_ignored(self, db_session: Session, test_user: User, matching_listing: VehicleListing):
        """Test that inactive alerts are ignored"""
        # Create inactive alert
        inactive_alert = Alert(
            user_id=test_user.id,
            name="Test Alert",
            make="Volkswagen",
            model="Golf",
            is_active=False
        )
        db_session.add(inactive_alert)
        db_session.commit()
        
        matcher = AlertMatchingEngine(db_session)
        match_log = matcher.run_alert_matching()
        
        # Should not process inactive alert
        notifications = db_session.query(Notification).filter(
            Notification.alert_id == inactive_alert.id
        ).all()
        
        assert len(notifications) == 0
    
    def test_inactive_user_alerts_ignored(self, db_session: Session, matching_listing: VehicleListing):
        """Test that alerts from inactive users are ignored"""
        # Create inactive user
        inactive_user = User(
            username="inactiveuser",
            email="inactive@example.com",
            password_hash=get_password_hash("TestPassword123"),
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()
        
        # Create alert for inactive user
        alert = Alert(
            user_id=inactive_user.id,
            name="Test Alert",
            make="Volkswagen",
            model="Golf"
        )
        db_session.add(alert)
        db_session.commit()
        
        matcher = AlertMatchingEngine(db_session)
        match_log = matcher.run_alert_matching()
        
        # Should not process alerts from inactive users
        notifications = db_session.query(Notification).filter(
            Notification.alert_id == alert.id
        ).all()
        
        assert len(notifications) == 0
