"""
Tests for Automotive API Endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestAutomotiveAPI:
    """Test cases for Automotive API endpoints"""
    
    def test_search_vehicles_empty_database(self, client):
        """Test searching vehicles in empty database"""
        response = client.get("/api/v1/automotive/vehicles")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert data["vehicles"] == []
        assert data["page"] == 1
        assert data["page_size"] == 20
    
    def test_search_vehicles_with_data(self, client, db_session, sample_vehicle_data):
        """Test searching vehicles with data"""
        from app.services.automotive_service import AutomotiveService
        
        # Create test vehicle
        service = AutomotiveService(db_session)
        service.create_vehicle_listing(sample_vehicle_data)
        
        response = client.get("/api/v1/automotive/vehicles")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["vehicles"]) == 1
        assert data["vehicles"][0]["make"] == "Volkswagen"
        assert data["vehicles"][0]["model"] == "Golf"
    
    def test_search_vehicles_with_filters(self, client, db_session, sample_vehicle_data):
        """Test searching vehicles with filters"""
        from app.services.automotive_service import AutomotiveService
        
        service = AutomotiveService(db_session)
        
        # Create multiple test vehicles
        vw_data = sample_vehicle_data.copy()
        vw_data["external_id"] = "vw-1"
        service.create_vehicle_listing(vw_data)
        
        peugeot_data = sample_vehicle_data.copy()
        peugeot_data["external_id"] = "peugeot-1"
        peugeot_data["make"] = "Peugeot"
        peugeot_data["model"] = "208"
        peugeot_data["price"] = 15000.0
        service.create_vehicle_listing(peugeot_data)
        
        # Test filter by make
        response = client.get("/api/v1/automotive/vehicles?make=Volkswagen")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["vehicles"][0]["make"] == "Volkswagen"
        
        # Test filter by price range
        response = client.get("/api/v1/automotive/vehicles?price_max=16000")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["vehicles"][0]["make"] == "Peugeot"
    
    def test_get_vehicle_by_id(self, client, db_session, sample_vehicle_data):
        """Test getting vehicle by ID"""
        from app.services.automotive_service import AutomotiveService
        
        service = AutomotiveService(db_session)
        vehicle = service.create_vehicle_listing(sample_vehicle_data)
        
        response = client.get(f"/api/v1/automotive/vehicles/{vehicle.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == vehicle.id
        assert data["make"] == "Volkswagen"
        assert data["model"] == "Golf"
        assert len(data["images"]) == 1
        assert len(data["price_history"]) == 1
    
    def test_get_vehicle_not_found(self, client):
        """Test getting non-existent vehicle"""
        response = client.get("/api/v1/automotive/vehicles/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_analytics(self, client, db_session, sample_vehicle_data):
        """Test getting analytics"""
        from app.services.automotive_service import AutomotiveService
        
        service = AutomotiveService(db_session)
        service.create_vehicle_listing(sample_vehicle_data)
        
        response = client.get("/api/v1/automotive/analytics")
        
        assert response.status_code == 200
        data = response.json()
        assert "data_quality" in data
        assert "overview" in data
        assert "timestamp" in data
        
        # Check data quality metrics
        quality = data["data_quality"]
        assert quality["total_vehicles"] == 1
        assert quality["active_vehicles"] == 1
        assert "completeness_scores" in quality
    
    def test_get_available_makes(self, client, db_session, sample_vehicle_data):
        """Test getting available makes"""
        from app.services.automotive_service import AutomotiveService
        
        service = AutomotiveService(db_session)
        
        # Create vehicles with different makes
        vw_data = sample_vehicle_data.copy()
        vw_data["external_id"] = "vw-1"
        service.create_vehicle_listing(vw_data)
        
        peugeot_data = sample_vehicle_data.copy()
        peugeot_data["external_id"] = "peugeot-1"
        peugeot_data["make"] = "Peugeot"
        service.create_vehicle_listing(peugeot_data)
        
        response = client.get("/api/v1/automotive/makes")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        makes = [item["make"] for item in data]
        assert "Volkswagen" in makes
        assert "Peugeot" in makes
    
    def test_get_available_models(self, client, db_session, sample_vehicle_data):
        """Test getting available models"""
        from app.services.automotive_service import AutomotiveService
        
        service = AutomotiveService(db_session)
        service.create_vehicle_listing(sample_vehicle_data)
        
        response = client.get("/api/v1/automotive/models")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["make"] == "Volkswagen"
        assert data[0]["model"] == "Golf"
        assert data[0]["count"] == 1
    
    def test_get_available_models_filtered(self, client, db_session, sample_vehicle_data):
        """Test getting available models filtered by make"""
        from app.services.automotive_service import AutomotiveService
        
        service = AutomotiveService(db_session)
        
        # Create vehicles with different makes
        vw_data = sample_vehicle_data.copy()
        vw_data["external_id"] = "vw-1"
        service.create_vehicle_listing(vw_data)
        
        peugeot_data = sample_vehicle_data.copy()
        peugeot_data["external_id"] = "peugeot-1"
        peugeot_data["make"] = "Peugeot"
        peugeot_data["model"] = "208"
        service.create_vehicle_listing(peugeot_data)
        
        response = client.get("/api/v1/automotive/models?make=Volkswagen")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["make"] == "Volkswagen"
        assert data[0]["model"] == "Golf"
    
    def test_get_scraper_status(self, client):
        """Test getting scraper status"""
        response = client.get("/api/v1/automotive/scraper/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "scheduler" in data
        assert "compliance" in data
        assert "timestamp" in data
    
    def test_get_scraper_health(self, client):
        """Test getting scraper health"""
        response = client.get("/api/v1/automotive/scraper/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "system_health" in data
        assert "scraping_metrics_24h" in data
    
    def test_get_scraping_sessions(self, client):
        """Test getting scraping sessions"""
        response = client.get("/api/v1/automotive/scraper/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_scraping_logs(self, client):
        """Test getting scraping logs"""
        response = client.get("/api/v1/automotive/scraper/logs")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_compliance_info(self, client):
        """Test getting compliance information"""
        response = client.get("/api/v1/automotive/scraper/compliance")
        
        assert response.status_code == 200
        data = response.json()
        assert "guidelines" in data
        assert "compliance_score" in data
        assert "recommendations" in data
    
    def test_run_data_cleanup(self, client):
        """Test running data cleanup"""
        response = client.post("/api/v1/automotive/maintenance/cleanup")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "statistics" in data
    
    def test_get_data_quality_report(self, client):
        """Test getting data quality report"""
        response = client.get("/api/v1/automotive/maintenance/quality")
        
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "alerts" in data
        assert "timestamp" in data
    
    def test_pagination(self, client, db_session, sample_vehicle_data):
        """Test pagination in vehicle search"""
        from app.services.automotive_service import AutomotiveService
        
        service = AutomotiveService(db_session)
        
        # Create multiple vehicles
        for i in range(25):
            data = sample_vehicle_data.copy()
            data["external_id"] = f"vehicle-{i}"
            service.create_vehicle_listing(data)
        
        # Test first page
        response = client.get("/api/v1/automotive/vehicles?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 25
        assert len(data["vehicles"]) == 10
        assert data["page"] == 1
        assert data["total_pages"] == 3
        
        # Test second page
        response = client.get("/api/v1/automotive/vehicles?page=2&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["vehicles"]) == 10
        assert data["page"] == 2
        
        # Test last page
        response = client.get("/api/v1/automotive/vehicles?page=3&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["vehicles"]) == 5
        assert data["page"] == 3
