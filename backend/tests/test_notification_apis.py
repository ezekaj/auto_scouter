"""
Notification Management API Tests

This module contains tests for notification management endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.scout import User
from app.models.notifications import Notification, NotificationPreferences, NotificationType
from app.core.auth import get_password_hash


class TestNotificationAPIs:
    """Test notification management API endpoints"""
    
    @pytest.fixture
    def authenticated_client(self, client: TestClient, db_session: Session):
        """Create an authenticated client with test user"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=get_password_hash("TestPassword123")
        )
        db_session.add(user)
        db_session.commit()
        
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "TestPassword123"
        })
        
        token = login_response.json()["token"]["access_token"]
        client.headers.update({"Authorization": f"Bearer {token}"})
        return client, user
    
    def test_get_user_notifications(self, authenticated_client, db_session: Session):
        """Test getting user notifications"""
        client, user = authenticated_client
        
        # Create test notifications
        notifications = [
            Notification(
                user_id=user.id,
                notification_type=NotificationType.IN_APP,
                title="Test Notification 1",
                message="Message 1",
                is_read=False,
                created_at=datetime.utcnow()
            ),
            Notification(
                user_id=user.id,
                notification_type=NotificationType.EMAIL,
                title="Test Notification 2",
                message="Message 2",
                is_read=True,
                created_at=datetime.utcnow() - timedelta(hours=1)
            )
        ]
        db_session.add_all(notifications)
        db_session.commit()
        
        response = client.get("/api/v1/notifications/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "notifications" in data
        assert "total_count" in data
        assert "unread_count" in data
        assert data["total_count"] == 2
        assert data["unread_count"] == 1
        assert len(data["notifications"]) == 2
    
    def test_get_notifications_with_filters(self, authenticated_client, db_session: Session):
        """Test getting notifications with filters"""
        client, user = authenticated_client
        
        # Create notifications of different types
        email_notification = Notification(
            user_id=user.id,
            notification_type=NotificationType.EMAIL,
            title="Email Notification",
            message="Email message"
        )
        in_app_notification = Notification(
            user_id=user.id,
            notification_type=NotificationType.IN_APP,
            title="In-App Notification",
            message="In-app message"
        )
        db_session.add_all([email_notification, in_app_notification])
        db_session.commit()
        
        # Filter by notification type
        response = client.get("/api/v1/notifications/?notification_type=email")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 1
        assert data["notifications"][0]["notification_type"] == "email"
    
    def test_get_notification_details(self, authenticated_client, db_session: Session):
        """Test getting specific notification details"""
        client, user = authenticated_client
        
        notification = Notification(
            user_id=user.id,
            notification_type=NotificationType.IN_APP,
            title="Test Notification",
            message="Test message",
            is_read=False
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)
        
        response = client.get(f"/api/v1/notifications/{notification.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == notification.id
        assert data["title"] == "Test Notification"
        
        # Check that in-app notification was marked as read
        db_session.refresh(notification)
        assert notification.is_read is True
        assert notification.opened_at is not None
    
    def test_mark_notification_read(self, authenticated_client, db_session: Session):
        """Test marking notification as read"""
        client, user = authenticated_client
        
        notification = Notification(
            user_id=user.id,
            notification_type=NotificationType.EMAIL,
            title="Test Notification",
            message="Test message",
            is_read=False
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)
        
        response = client.post(f"/api/v1/notifications/{notification.id}/mark-read")
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_read"] is True
        
        # Verify in database
        db_session.refresh(notification)
        assert notification.is_read is True
        assert notification.opened_at is not None
    
    def test_mark_all_notifications_read(self, authenticated_client, db_session: Session):
        """Test marking all notifications as read"""
        client, user = authenticated_client
        
        # Create multiple unread notifications
        notifications = [
            Notification(
                user_id=user.id,
                notification_type=NotificationType.IN_APP,
                title=f"Test Notification {i}",
                message=f"Message {i}",
                is_read=False
            )
            for i in range(3)
        ]
        db_session.add_all(notifications)
        db_session.commit()
        
        response = client.post("/api/v1/notifications/mark-all-read")
        
        assert response.status_code == 200
        data = response.json()
        assert data["updated_count"] == 3
        
        # Verify all notifications are marked as read
        for notification in notifications:
            db_session.refresh(notification)
            assert notification.is_read is True
    
    def test_delete_notification(self, authenticated_client, db_session: Session):
        """Test deleting a notification"""
        client, user = authenticated_client
        
        notification = Notification(
            user_id=user.id,
            notification_type=NotificationType.IN_APP,
            title="Test Notification",
            message="Test message"
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)
        
        response = client.delete(f"/api/v1/notifications/{notification.id}")
        
        assert response.status_code == 204
        
        # Verify notification was deleted
        deleted_notification = db_session.query(Notification).filter(
            Notification.id == notification.id
        ).first()
        assert deleted_notification is None
    
    def test_get_notification_preferences(self, authenticated_client, db_session: Session):
        """Test getting notification preferences"""
        client, user = authenticated_client
        
        response = client.get("/api/v1/notifications/preferences/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should create default preferences if none exist
        assert data["user_id"] == user.id
        assert data["email_enabled"] is True
        assert data["in_app_enabled"] is True
        assert data["max_notifications_per_day"] == 10
    
    def test_update_notification_preferences(self, authenticated_client, db_session: Session):
        """Test updating notification preferences"""
        client, user = authenticated_client
        
        update_data = {
            "email_enabled": False,
            "max_notifications_per_day": 5,
            "quiet_hours_enabled": True,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "08:00"
        }
        
        response = client.put("/api/v1/notifications/preferences/", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["email_enabled"] is False
        assert data["max_notifications_per_day"] == 5
        assert data["quiet_hours_enabled"] is True
        assert data["quiet_hours_start"] == "22:00"
    
    def test_get_notification_stats(self, authenticated_client, db_session: Session):
        """Test getting notification statistics"""
        client, user = authenticated_client
        
        # Create test notifications
        notifications = [
            Notification(
                user_id=user.id,
                notification_type=NotificationType.IN_APP,
                title="Test 1",
                message="Message 1",
                is_read=False,
                created_at=datetime.utcnow()
            ),
            Notification(
                user_id=user.id,
                notification_type=NotificationType.EMAIL,
                title="Test 2",
                message="Message 2",
                is_read=True,
                created_at=datetime.utcnow() - timedelta(days=2)
            ),
            Notification(
                user_id=user.id,
                notification_type=NotificationType.IN_APP,
                title="Test 3",
                message="Message 3",
                is_read=False,
                created_at=datetime.utcnow() - timedelta(hours=12)
            )
        ]
        db_session.add_all(notifications)
        db_session.commit()
        
        response = client.get("/api/v1/notifications/stats/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == user.id
        assert data["total_notifications"] == 3
        assert data["unread_notifications"] == 2
        assert data["notifications_last_7_days"] == 3
    
    def test_cleanup_old_notifications(self, authenticated_client, db_session: Session):
        """Test cleaning up old notifications"""
        client, user = authenticated_client
        
        # Create old notification
        old_notification = Notification(
            user_id=user.id,
            notification_type=NotificationType.IN_APP,
            title="Old Notification",
            message="Old message",
            created_at=datetime.utcnow() - timedelta(days=100)
        )
        
        # Create recent notification
        recent_notification = Notification(
            user_id=user.id,
            notification_type=NotificationType.IN_APP,
            title="Recent Notification",
            message="Recent message",
            created_at=datetime.utcnow()
        )
        
        db_session.add_all([old_notification, recent_notification])
        db_session.commit()
        
        response = client.post("/api/v1/notifications/cleanup?days_old=90")
        
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 1
        
        # Verify only old notification was deleted
        remaining_notifications = db_session.query(Notification).filter(
            Notification.user_id == user.id
        ).all()
        assert len(remaining_notifications) == 1
        assert remaining_notifications[0].title == "Recent Notification"
    
    def test_track_notification_click(self, authenticated_client, db_session: Session):
        """Test tracking notification clicks"""
        client, user = authenticated_client
        
        notification = Notification(
            user_id=user.id,
            notification_type=NotificationType.EMAIL,
            title="Test Notification",
            message="Test message"
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)
        
        response = client.post(f"/api/v1/notifications/{notification.id}/track-click")
        
        assert response.status_code == 200
        data = response.json()
        assert "clicked_at" in data
        
        # Verify click was tracked
        db_session.refresh(notification)
        assert notification.clicked_at is not None
        assert notification.status == "clicked"
    
    def test_cross_user_notification_access(self, client: TestClient, db_session: Session):
        """Test that users cannot access other users' notifications"""
        # Create two users
        user1 = User(
            username="user1",
            email="user1@example.com",
            password_hash=get_password_hash("TestPassword123")
        )
        user2 = User(
            username="user2",
            email="user2@example.com",
            password_hash=get_password_hash("TestPassword123")
        )
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Create notification for user1
        notification = Notification(
            user_id=user1.id,
            notification_type=NotificationType.IN_APP,
            title="User1 Notification",
            message="Private message"
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)
        
        # Login as user2
        login_response = client.post("/api/v1/auth/login", json={
            "username": "user2",
            "password": "TestPassword123"
        })
        token = login_response.json()["token"]["access_token"]
        client.headers.update({"Authorization": f"Bearer {token}"})
        
        # Try to access user1's notification
        response = client.get(f"/api/v1/notifications/{notification.id}")
        
        assert response.status_code == 404
        assert "Notification not found" in response.json()["detail"]
    
    def test_unauthorized_notification_access(self, client: TestClient):
        """Test accessing notifications without authentication"""
        response = client.get("/api/v1/notifications/")
        
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]
