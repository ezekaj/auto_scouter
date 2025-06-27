"""
Notification Delivery System Tests

This module contains tests for notification delivery functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.models.scout import User
from app.models.notifications import (
    Notification, NotificationPreferences, NotificationQueue,
    NotificationStatus, NotificationType
)
from app.services.notification_delivery import NotificationDeliveryService
from app.core.auth import get_password_hash


class TestNotificationDeliveryService:
    """Test notification delivery service functionality"""
    
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
    def test_notification(self, db_session: Session, test_user: User):
        """Create a test notification"""
        notification = Notification(
            user_id=test_user.id,
            notification_type=NotificationType.IN_APP,
            title="Test Notification",
            message="This is a test notification",
            content_data={"test": "data"}
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)
        return notification
    
    @pytest.fixture
    def delivery_service(self, db_session: Session):
        """Create notification delivery service"""
        return NotificationDeliveryService(db_session)
    
    def test_queue_notification(self, delivery_service: NotificationDeliveryService, 
                               test_notification: Notification, db_session: Session):
        """Test queuing a notification for delivery"""
        success = delivery_service.queue_notification(test_notification, priority=2)
        
        assert success is True
        
        # Verify queue item was created
        queue_item = db_session.query(NotificationQueue).filter(
            NotificationQueue.notification_id == test_notification.id
        ).first()
        
        assert queue_item is not None
        assert queue_item.priority == 2
        assert queue_item.status == "queued"
    
    def test_in_app_notification_delivery(self, delivery_service: NotificationDeliveryService,
                                        test_notification: Notification, db_session: Session):
        """Test in-app notification delivery"""
        success = delivery_service._deliver_notification(test_notification)
        
        assert success is True
        assert test_notification.status == NotificationStatus.SENT
        assert test_notification.sent_at is not None
    
    @patch('smtplib.SMTP')
    def test_email_notification_delivery(self, mock_smtp, delivery_service: NotificationDeliveryService,
                                       test_user: User, db_session: Session):
        """Test email notification delivery"""
        # Create email notification
        email_notification = Notification(
            user_id=test_user.id,
            notification_type=NotificationType.EMAIL,
            title="Test Email",
            message="This is a test email notification"
        )
        db_session.add(email_notification)
        db_session.commit()
        
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        success = delivery_service._deliver_notification(email_notification)
        
        assert success is True
        assert email_notification.status == NotificationStatus.SENT
        assert email_notification.sent_at is not None
        
        # Verify SMTP was called
        mock_smtp.assert_called_once()
        mock_server.send_message.assert_called_once()
    
    def test_notification_preferences_check(self, delivery_service: NotificationDeliveryService,
                                          test_user: User, db_session: Session):
        """Test notification delivery based on user preferences"""
        # Create preferences with email disabled
        prefs = NotificationPreferences(
            user_id=test_user.id,
            email_enabled=False,
            in_app_enabled=True
        )
        db_session.add(prefs)
        db_session.commit()
        
        # Test email notification (should be blocked)
        email_notification = Notification(
            user_id=test_user.id,
            notification_type=NotificationType.EMAIL,
            title="Test Email",
            message="Test"
        )
        
        should_send = delivery_service._should_send_notification(email_notification)
        assert should_send is False
        
        # Test in-app notification (should be allowed)
        in_app_notification = Notification(
            user_id=test_user.id,
            notification_type=NotificationType.IN_APP,
            title="Test In-App",
            message="Test"
        )
        
        should_send = delivery_service._should_send_notification(in_app_notification)
        assert should_send is True
    
    def test_quiet_hours_check(self, delivery_service: NotificationDeliveryService,
                             test_user: User, db_session: Session):
        """Test quiet hours functionality"""
        # Create preferences with quiet hours enabled
        prefs = NotificationPreferences(
            user_id=test_user.id,
            quiet_hours_enabled=True,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00"
        )
        db_session.add(prefs)
        db_session.commit()
        
        notification = Notification(
            user_id=test_user.id,
            notification_type=NotificationType.EMAIL,
            title="Test",
            message="Test"
        )
        
        # Mock current time to be in quiet hours (23:00)
        with patch('app.services.notification_delivery.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value.time.return_value = datetime.strptime("23:00", "%H:%M").time()
            mock_datetime.strptime = datetime.strptime
            
            should_send = delivery_service._should_send_notification(notification)
            assert should_send is False
        
        # Mock current time to be outside quiet hours (10:00)
        with patch('app.services.notification_delivery.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value.time.return_value = datetime.strptime("10:00", "%H:%M").time()
            mock_datetime.strptime = datetime.strptime
            
            should_send = delivery_service._should_send_notification(notification)
            assert should_send is True
    
    def test_process_notification_queue(self, delivery_service: NotificationDeliveryService,
                                      test_notification: Notification, db_session: Session):
        """Test processing notification queue"""
        # Queue the notification
        delivery_service.queue_notification(test_notification)
        
        # Process queue
        stats = delivery_service.process_notification_queue(max_notifications=10)
        
        assert stats["processed"] == 1
        assert stats["sent"] == 1
        assert stats["failed"] == 0
        
        # Verify queue item was marked as completed
        queue_item = db_session.query(NotificationQueue).filter(
            NotificationQueue.notification_id == test_notification.id
        ).first()
        
        assert queue_item.status == "completed"
        assert queue_item.processing_completed_at is not None
    
    def test_notification_retry_logic(self, delivery_service: NotificationDeliveryService,
                                    test_user: User, db_session: Session):
        """Test notification retry logic for failed deliveries"""
        # Create notification that will fail
        notification = Notification(
            user_id=test_user.id,
            notification_type=NotificationType.EMAIL,
            title="Test",
            message="Test"
        )
        db_session.add(notification)
        db_session.commit()
        
        # Queue notification
        delivery_service.queue_notification(notification)
        
        # Mock email delivery to fail
        with patch.object(delivery_service, '_send_email_notification', return_value=False):
            stats = delivery_service.process_notification_queue()
        
        # Check that retry was scheduled
        queue_item = db_session.query(NotificationQueue).filter(
            NotificationQueue.notification_id == notification.id
        ).first()
        
        assert queue_item.retry_count == 1
        assert queue_item.status == "queued"
        assert queue_item.scheduled_for is not None
    
    def test_notification_max_retries(self, delivery_service: NotificationDeliveryService,
                                    test_user: User, db_session: Session):
        """Test notification max retries limit"""
        notification = Notification(
            user_id=test_user.id,
            notification_type=NotificationType.EMAIL,
            title="Test",
            message="Test"
        )
        db_session.add(notification)
        db_session.commit()
        
        # Create queue item with max retries reached
        queue_item = NotificationQueue(
            notification_id=notification.id,
            retry_count=3,
            status="queued"
        )
        db_session.add(queue_item)
        db_session.commit()
        
        # Mock email delivery to fail
        with patch.object(delivery_service, '_send_email_notification', return_value=False):
            stats = delivery_service.process_notification_queue()
        
        # Should be marked as failed
        db_session.refresh(queue_item)
        assert queue_item.status == "failed"
        assert notification.status == NotificationStatus.FAILED
    
    def test_create_and_queue_notification(self, delivery_service: NotificationDeliveryService,
                                         test_user: User, db_session: Session):
        """Test creating and queuing notification in one operation"""
        notification = delivery_service.create_and_queue_notification(
            user_id=test_user.id,
            notification_type=NotificationType.IN_APP,
            title="Test Notification",
            message="Test message",
            content_data={"key": "value"},
            priority=2
        )
        
        assert notification is not None
        assert notification.user_id == test_user.id
        assert notification.title == "Test Notification"
        
        # Verify it was queued
        queue_item = db_session.query(NotificationQueue).filter(
            NotificationQueue.notification_id == notification.id
        ).first()
        
        assert queue_item is not None
        assert queue_item.priority == 2
    
    def test_default_html_content_generation(self, delivery_service: NotificationDeliveryService,
                                           test_user: User):
        """Test default HTML email content generation"""
        notification = Notification(
            user_id=test_user.id,
            notification_type=NotificationType.EMAIL,
            title="New Car Alert",
            message="Found a matching car",
            content_data={
                "listing": {
                    "make": "Volkswagen",
                    "model": "Golf",
                    "year": 2020,
                    "price": 18500,
                    "mileage": 45000,
                    "fuel_type": "diesel",
                    "city": "Napoli",
                    "listing_url": "https://example.com/car1"
                }
            }
        )
        
        html_content = delivery_service._generate_default_html_content(notification, test_user)
        
        assert "New Car Alert" in html_content
        assert "Volkswagen Golf" in html_content
        assert "€18,500" in html_content
        assert "45,000 km" in html_content
        assert "https://example.com/car1" in html_content
        assert test_user.username in html_content


class TestNotificationTemplates:
    """Test notification template functionality"""
    
    def test_template_rendering(self, db_session: Session):
        """Test notification template rendering"""
        from app.models.notifications import NotificationTemplate
        
        # Create template
        template = NotificationTemplate(
            name="alert_match",
            notification_type=NotificationType.EMAIL,
            subject_template="New {{listing.make}} {{listing.model}} Alert",
            title_template="Car Alert: {{listing.make}} {{listing.model}}",
            message_template="Found a {{listing.make}} {{listing.model}} for €{{listing.price}}",
            html_template="<h1>{{title}}</h1><p>{{message}}</p>",
            variables=["listing", "user"]
        )
        db_session.add(template)
        db_session.commit()
        
        # Test template exists
        assert template.id is not None
        assert template.name == "alert_match"
        assert "{{listing.make}}" in template.subject_template
