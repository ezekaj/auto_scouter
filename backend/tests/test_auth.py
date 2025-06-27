"""
Authentication API Tests

This module contains tests for user authentication endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.scout import User
from app.core.auth import get_password_hash


class TestUserRegistration:
    """Test user registration functionality"""
    
    def test_register_user_success(self, client: TestClient):
        """Test successful user registration"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "password" not in data
        assert data["is_active"] is True
        assert data["is_verified"] is False
    
    def test_register_user_duplicate_username(self, client: TestClient, db_session: Session):
        """Test registration with duplicate username"""
        # Create existing user
        existing_user = User(
            username="testuser",
            email="existing@example.com",
            password_hash=get_password_hash("password123")
        )
        db_session.add(existing_user)
        db_session.commit()
        
        user_data = {
            "username": "testuser",
            "email": "new@example.com",
            "password": "TestPassword123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]
    
    def test_register_user_duplicate_email(self, client: TestClient, db_session: Session):
        """Test registration with duplicate email"""
        # Create existing user
        existing_user = User(
            username="existinguser",
            email="test@example.com",
            password_hash=get_password_hash("password123")
        )
        db_session.add(existing_user)
        db_session.commit()
        
        user_data = {
            "username": "newuser",
            "email": "test@example.com",
            "password": "TestPassword123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_register_user_invalid_password(self, client: TestClient):
        """Test registration with invalid password"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422
        assert "Password must be at least 8 characters long" in str(response.json())


class TestUserLogin:
    """Test user login functionality"""
    
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
    
    def test_login_success_with_username(self, client: TestClient, test_user: User):
        """Test successful login with username"""
        login_data = {
            "username": "testuser",
            "password": "TestPassword123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "token" in data
        assert data["user"]["username"] == "testuser"
        assert data["token"]["token_type"] == "bearer"
        assert "access_token" in data["token"]
    
    def test_login_success_with_email(self, client: TestClient, test_user: User):
        """Test successful login with email"""
        login_data = {
            "username": "test@example.com",
            "password": "TestPassword123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "test@example.com"
    
    def test_login_invalid_credentials(self, client: TestClient, test_user: User):
        """Test login with invalid credentials"""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with nonexistent user"""
        login_data = {
            "username": "nonexistent",
            "password": "TestPassword123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_inactive_user(self, client: TestClient, db_session: Session):
        """Test login with inactive user"""
        user = User(
            username="inactiveuser",
            email="inactive@example.com",
            password_hash=get_password_hash("TestPassword123"),
            is_active=False
        )
        db_session.add(user)
        db_session.commit()
        
        login_data = {
            "username": "inactiveuser",
            "password": "TestPassword123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 400
        assert "Inactive user account" in response.json()["detail"]


class TestUserProfile:
    """Test user profile management"""
    
    @pytest.fixture
    def authenticated_client(self, client: TestClient, db_session: Session):
        """Create an authenticated client"""
        # Create and login user
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
        return client
    
    def test_get_current_user_profile(self, authenticated_client: TestClient):
        """Test getting current user profile"""
        response = authenticated_client.get("/api/v1/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "alerts" in data
    
    def test_update_user_profile(self, authenticated_client: TestClient):
        """Test updating user profile"""
        update_data = {
            "username": "updateduser"
        }
        
        response = authenticated_client.put("/api/v1/auth/me", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updateduser"
    
    def test_change_password(self, authenticated_client: TestClient):
        """Test changing password"""
        password_data = {
            "current_password": "TestPassword123",
            "new_password": "NewPassword456"
        }
        
        response = authenticated_client.post("/api/v1/auth/change-password", json=password_data)
        
        assert response.status_code == 200
        assert "Password updated successfully" in response.json()["message"]
    
    def test_change_password_wrong_current(self, authenticated_client: TestClient):
        """Test changing password with wrong current password"""
        password_data = {
            "current_password": "WrongPassword",
            "new_password": "NewPassword456"
        }
        
        response = authenticated_client.post("/api/v1/auth/change-password", json=password_data)
        
        assert response.status_code == 400
        assert "Incorrect current password" in response.json()["detail"]
    
    def test_unauthorized_access(self, client: TestClient):
        """Test accessing protected endpoint without authentication"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]
