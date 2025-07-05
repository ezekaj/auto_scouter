"""
Alert Management API Tests

This module contains tests for alert management endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.scout import User, Alert
from app.core.auth import get_password_hash


class TestAlertManagement:
    """Test alert CRUD operations"""
    
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
    
    def test_create_alert_success(self, authenticated_client):
        """Test successful alert creation"""
        client, user = authenticated_client
        
        alert_data = {
            "make": "Volkswagen",
            "model": "Golf",
            "min_price": 15000,
            "max_price": 25000,
            "year": 2020
        }
        
        response = client.post("/api/v1/alerts/", json=alert_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["make"] == "Volkswagen"
        assert data["model"] == "Golf"
        assert data["min_price"] == 15000
        assert data["max_price"] == 25000
        assert data["year"] == 2020
        assert data["user_id"] == user.id
        assert data["is_active"] is True
    
    def test_create_alert_no_filters(self, authenticated_client):
        """Test alert creation with no filter criteria"""
        client, user = authenticated_client
        
        alert_data = {}
        
        response = client.post("/api/v1/alerts/", json=alert_data)
        
        assert response.status_code == 400
        assert "At least one filter criterion must be specified" in response.json()["detail"]
    
    def test_create_alert_invalid_price_range(self, authenticated_client):
        """Test alert creation with invalid price range"""
        client, user = authenticated_client
        
        alert_data = {
            "make": "Volkswagen",
            "min_price": 25000,
            "max_price": 15000
        }
        
        response = client.post("/api/v1/alerts/", json=alert_data)
        
        assert response.status_code == 400
        assert "Minimum price must be less than maximum price" in response.json()["detail"]
    
    def test_get_user_alerts(self, authenticated_client, db_session: Session):
        """Test getting user alerts"""
        client, user = authenticated_client
        
        # Create test alerts
        alert1 = Alert(
            user_id=user.id,
            name="Test Alert",
            make="Volkswagen",
            model="Golf",
            min_price=15000,
            max_price=25000
        )
        alert2 = Alert(
            user_id=user.id,
            name="Test Alert",
            make="BMW",
            model="X3",
            min_price=30000,
            max_price=50000,
            is_active=False
        )
        db_session.add_all([alert1, alert2])
        db_session.commit()
        
        # Test getting all alerts
        response = client.get("/api/v1/alerts/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1  # Only active alerts by default
        assert data[0]["make"] == "Volkswagen"
        
        # Test getting all alerts including inactive
        response = client.get("/api/v1/alerts/?active_only=false")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_get_specific_alert(self, authenticated_client, db_session: Session):
        """Test getting a specific alert"""
        client, user = authenticated_client
        
        alert = Alert(
            user_id=user.id,
            name="Test Alert",
            make="Volkswagen",
            model="Golf",
            min_price=15000,
            max_price=25000
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        
        response = client.get(f"/api/v1/alerts/{alert.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == alert.id
        assert data["make"] == "Volkswagen"
    
    def test_get_nonexistent_alert(self, authenticated_client):
        """Test getting a nonexistent alert"""
        client, user = authenticated_client
        
        response = client.get("/api/v1/alerts/999")
        
        assert response.status_code == 404
        assert "Alert not found" in response.json()["detail"]
    
    def test_update_alert(self, authenticated_client, db_session: Session):
        """Test updating an alert"""
        client, user = authenticated_client
        
        alert = Alert(
            user_id=user.id,
            name="Test Alert",
            make="Volkswagen",
            model="Golf",
            min_price=15000,
            max_price=25000
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        
        update_data = {
            "make": "BMW",
            "model": "X3",
            "min_price": 30000
        }
        
        response = client.put(f"/api/v1/alerts/{alert.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["make"] == "BMW"
        assert data["model"] == "X3"
        assert data["min_price"] == 30000
        assert data["max_price"] == 25000  # Unchanged
    
    def test_delete_alert(self, authenticated_client, db_session: Session):
        """Test deleting an alert"""
        client, user = authenticated_client
        
        alert = Alert(
            user_id=user.id,
            name="Test Alert",
            make="Volkswagen",
            model="Golf",
            min_price=15000,
            max_price=25000
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        
        response = client.delete(f"/api/v1/alerts/{alert.id}")
        
        assert response.status_code == 204
        
        # Verify alert is deleted
        response = client.get(f"/api/v1/alerts/{alert.id}")
        assert response.status_code == 404
    
    def test_toggle_alert_status(self, authenticated_client, db_session: Session):
        """Test toggling alert active status"""
        client, user = authenticated_client
        
        alert = Alert(
            user_id=user.id,
            name="Test Alert",
            make="Volkswagen",
            model="Golf",
            min_price=15000,
            max_price=25000,
            is_active=True
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        
        response = client.post(f"/api/v1/alerts/{alert.id}/toggle")
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        
        # Toggle again
        response = client.post(f"/api/v1/alerts/{alert.id}/toggle")
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True
    
    def test_get_alert_stats(self, authenticated_client, db_session: Session):
        """Test getting alert statistics"""
        client, user = authenticated_client
        
        # Create test alerts
        alert1 = Alert(
            user_id=user.id,
            name="Test Alert", make="Volkswagen", is_active=True
        )
        alert2 = Alert(
            user_id=user.id,
            name="Test Alert", make="BMW", is_active=True
        )
        alert3 = Alert(
            user_id=user.id,
            name="Test Alert", make="Audi", is_active=False
        )
        
        db_session.add_all([alert1, alert2, alert3])
        db_session.commit()
        
        response = client.get("/api/v1/alerts/stats/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_alerts"] == 3
        assert data["active_alerts"] == 2
        assert data["inactive_alerts"] == 1
    
    def test_unauthorized_alert_access(self, client: TestClient):
        """Test accessing alerts without authentication"""
        response = client.get("/api/v1/alerts/")
        
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]
    
    def test_cross_user_alert_access(self, client: TestClient, db_session: Session):
        """Test that users cannot access other users' alerts"""
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
        
        # Create alert for user1
        alert = Alert(
            user_id=user1.id,
            name="Test Alert",
            make="Volkswagen",
            model="Golf"
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        
        # Login as user2
        login_response = client.post("/api/v1/auth/login", json={
            "username": "user2",
            "password": "TestPassword123"
        })
        token = login_response.json()["token"]["access_token"]
        client.headers.update({"Authorization": f"Bearer {token}"})
        
        # Try to access user1's alert
        response = client.get(f"/api/v1/alerts/{alert.id}")
        
        assert response.status_code == 404
        assert "Alert not found" in response.json()["detail"]
