"""
Car Listings API Tests

This module contains tests for car listing endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.automotive import VehicleListing


class TestCarListings:
    """Test car listing endpoints"""
    
    @pytest.fixture
    def sample_cars(self, db_session: Session):
        """Create sample car data for testing"""
        cars = [
            VehicleListing(
            external_id="car1",
                listing_url="https://example.com/car1",
                make="Volkswagen",
                model="Golf",
                year=2020,
                price=18500.0,
                mileage=45000,
                fuel_type="diesel",
                transmission="manual",
                city="Napoli",
                source_website="test_source",
            is_active=True,
                scraped_at=datetime.utcnow(
        )
            ),
            VehicleListing(
            external_id="car2",
                listing_url="https://example.com/car2",
                make="BMW",
                model="X3",
                year=2019,
                price=35000.0,
                mileage=30000,
                fuel_type="gasoline",
                transmission="automatic",
                city="Milano",
                source_website="test_source",
            is_active=True,
                scraped_at=datetime.utcnow(
        )
            ),
            VehicleListing(
            external_id="car3",
                listing_url="https://example.com/car3",
                make="Volkswagen",
                model="Passat",
                year=2021,
                price=22000.0,
                mileage=25000,
                fuel_type="diesel",
                transmission="automatic",
                city="Roma",
                source_website="test_source",
            is_active=True,
                scraped_at=datetime.utcnow(
        ) - timedelta(hours=1)
            ),
            VehicleListing(
            external_id="car4",
                listing_url="https://example.com/car4",
                make="Audi",
                model="A4",
                year=2018,
                price=28000.0,
                mileage=60000,
                fuel_type="gasoline",
                transmission="automatic",
                city="Torino",
                source_website="test_source",
            is_active=False,  # Inactive car
                scraped_at=datetime.utcnow(
        ) - timedelta(days=2)
            )
        ]
        
        db_session.add_all(cars)
        db_session.commit()
        return cars
    
    def test_get_cars_no_filters(self, client: TestClient, sample_cars):
        """Test getting cars without filters"""
        response = client.get("/api/v1/cars/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "cars" in data
        assert "pagination" in data
        assert "filters_applied" in data
        
        # Should return only active cars
        assert len(data["cars"]) == 3
        assert data["pagination"]["total_count"] == 3
        assert data["pagination"]["current_page"] == 1
    
    def test_get_cars_with_make_filter(self, client: TestClient, sample_cars):
        """Test getting cars filtered by make"""
        response = client.get("/api/v1/cars/?make=Volkswagen")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["cars"]) == 2
        assert all(car["make"] == "Volkswagen" for car in data["cars"])
        assert data["filters_applied"]["make"] == "Volkswagen"
    
    def test_get_cars_with_model_filter(self, client: TestClient, sample_cars):
        """Test getting cars filtered by model"""
        response = client.get("/api/v1/cars/?model=Golf")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["cars"]) == 1
        assert data["cars"][0]["model"] == "Golf"
        assert data["filters_applied"]["model"] == "Golf"
    
    def test_get_cars_with_price_range(self, client: TestClient, sample_cars):
        """Test getting cars filtered by price range"""
        response = client.get("/api/v1/cars/?min_price=20000&max_price=30000")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["cars"]) == 1
        assert data["cars"][0]["price"] == 22000.0
        assert data["filters_applied"]["min_price"] == 20000
        assert data["filters_applied"]["max_price"] == 30000
    
    def test_get_cars_with_year_filter(self, client: TestClient, sample_cars):
        """Test getting cars filtered by year"""
        response = client.get("/api/v1/cars/?year=2020")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["cars"]) == 1
        assert data["cars"][0]["year"] == 2020
        assert data["filters_applied"]["year"] == 2020
    
    def test_get_cars_with_pagination(self, client: TestClient, sample_cars):
        """Test cars pagination"""
        response = client.get("/api/v1/cars/?limit=2&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["cars"]) == 2
        assert data["pagination"]["limit"] == 2
        assert data["pagination"]["offset"] == 0
        assert data["pagination"]["has_next"] is True
        assert data["pagination"]["has_previous"] is False
        
        # Test second page
        response = client.get("/api/v1/cars/?limit=2&offset=2")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["cars"]) == 1
        assert data["pagination"]["has_next"] is False
        assert data["pagination"]["has_previous"] is True
    
    def test_get_cars_combined_filters(self, client: TestClient, sample_cars):
        """Test getting cars with multiple filters"""
        response = client.get("/api/v1/cars/?make=Volkswagen&min_price=20000")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["cars"]) == 1
        assert data["cars"][0]["make"] == "Volkswagen"
        assert data["cars"][0]["price"] >= 20000
    
    def test_get_new_cars(self, client: TestClient, sample_cars):
        """Test getting recently added cars"""
        response = client.get("/api/v1/cars/new?hours=2")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "cars" in data
        assert "metadata" in data
        assert data["metadata"]["endpoint"] == "new_cars"
        
        # Should return cars added in the last 2 hours
        assert len(data["cars"]) == 3  # car1, car2, car3 (car4 is older and inactive)
        assert data["filters_applied"]["hours_back"] == 2
    
    def test_get_new_cars_with_filters(self, client: TestClient, sample_cars):
        """Test getting new cars with additional filters"""
        response = client.get("/api/v1/cars/new?hours=24&make=Volkswagen")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return only Volkswagen cars from the last 24 hours
        assert len(data["cars"]) == 2
        assert all(car["make"] == "Volkswagen" for car in data["cars"])
    
    def test_get_car_details(self, client: TestClient, sample_cars):
        """Test getting specific car details"""
        car = sample_cars[0]  # First active car
        
        response = client.get(f"/api/v1/cars/{car.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == car.id
        assert data["make"] == "Volkswagen"
        assert data["model"] == "Golf"
        assert data["price"] == 18500.0
    
    def test_get_car_details_not_found(self, client: TestClient):
        """Test getting details for nonexistent car"""
        response = client.get("/api/v1/cars/999")
        
        assert response.status_code == 404
        assert "Car not found" in response.json()["detail"]
    
    def test_get_car_details_inactive(self, client: TestClient, sample_cars):
        """Test getting details for inactive car"""
        inactive_car = sample_cars[3]  # Inactive car
        
        response = client.get(f"/api/v1/cars/{inactive_car.id}")
        
        assert response.status_code == 404
        assert "Car not found" in response.json()["detail"]
    
    def test_get_cars_stats(self, client: TestClient, sample_cars):
        """Test getting car statistics"""
        response = client.get("/api/v1/cars/stats/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_active_cars" in data
        assert "price_statistics" in data
        assert "top_makes" in data
        assert "recent_additions_24h" in data
        
        assert data["total_active_cars"] == 3
        assert data["price_statistics"]["min_price"] == 18500.0
        assert data["price_statistics"]["max_price"] == 35000.0
        
        # Check top makes
        top_makes = data["top_makes"]
        assert len(top_makes) > 0
        assert any(make["make"] == "Volkswagen" for make in top_makes)
    
    def test_get_cars_empty_result(self, client: TestClient, sample_cars):
        """Test getting cars with filters that return no results"""
        response = client.get("/api/v1/cars/?make=Ferrari")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["cars"]) == 0
        assert data["pagination"]["total_count"] == 0
        assert data["pagination"]["total_pages"] == 0
    
    def test_get_cars_invalid_parameters(self, client: TestClient):
        """Test getting cars with invalid parameters"""
        # Test negative price
        response = client.get("/api/v1/cars/?min_price=-1000")
        
        assert response.status_code == 422
        
        # Test invalid year
        response = client.get("/api/v1/cars/?year=1800")
        
        assert response.status_code == 422
        
        # Test invalid limit
        response = client.get("/api/v1/cars/?limit=0")
        
        assert response.status_code == 422
    
    def test_cars_ordering(self, client: TestClient, sample_cars):
        """Test that cars are ordered by scraped_at (newest first)"""
        response = client.get("/api/v1/cars/")
        
        assert response.status_code == 200
        data = response.json()
        
        cars = data["cars"]
        assert len(cars) >= 2
        
        # Check that cars are ordered by scraped_at descending
        for i in range(len(cars) - 1):
            current_time = datetime.fromisoformat(cars[i]["scraped_at"].replace('Z', '+00:00'))
            next_time = datetime.fromisoformat(cars[i + 1]["scraped_at"].replace('Z', '+00:00'))
            assert current_time >= next_time
