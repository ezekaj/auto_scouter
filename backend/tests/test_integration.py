"""
Integration Tests for Automotive Scraper System

These tests verify the complete workflow from scraping to API access.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from app.services.automotive_service import AutomotiveService
from app.scraper.automotive_scraper import GruppoAutoUnoScraper
from app.scraper.compliance import ComplianceManager
from app.scraper.monitoring import ScraperMonitor


class TestIntegration:
    """Integration test cases"""
    
    @patch('app.scraper.automotive_scraper.GruppoAutoUnoScraper.get_page')
    def test_complete_scraping_workflow(self, mock_get_page, db_session):
        """Test complete workflow from scraping to database storage"""
        
        # Mock HTML response
        mock_response = Mock()
        mock_response.text = """
        <html>
        <body>
            <h1>Volkswagen Golf 1.6 TDI</h1>
            <div class="price">€ 18.500</div>
            <div>Immatricolazione: 03/2020</div>
            <div>Km: 45.000</div>
            <div>Alimentazione: Diesel</div>
            <div>Cambio: Manuale</div>
            <div>Potenza: 85 kW</div>
            <div>5 Porte</div>
            <div>5 Posti</div>
            <img src="/images/golf-1.jpg" alt="Golf">
        </body>
        </html>
        """
        mock_get_page.return_value = mock_response
        
        # Initialize scraper and service
        scraper = GruppoAutoUnoScraper()
        service = AutomotiveService(db_session)
        
        # Scrape vehicle detail
        url = "https://gruppoautouno.it/usato/volkswagen-golf-123/"
        vehicle_data = scraper.scrape_vehicle_detail(url)
        
        # Verify scraped data
        assert vehicle_data is not None
        assert vehicle_data["make"] == "Volkswagen"
        assert vehicle_data["model"] == "Golf"
        assert vehicle_data["price"] == 18500.0
        assert vehicle_data["fuel_type"] == "diesel"
        
        # Store in database
        vehicle = service.create_vehicle_listing(vehicle_data)
        
        # Verify database storage
        assert vehicle is not None
        assert vehicle.make == "Volkswagen"
        assert vehicle.model == "Golf"
        assert vehicle.price == 18500.0
        assert len(vehicle.images) > 0
        assert len(vehicle.price_history) == 1
        
        # Test duplicate detection
        duplicate_data = vehicle_data.copy()
        duplicate_data["price"] = 19000.0  # Different price
        
        existing = service.find_duplicate_listing(duplicate_data)
        assert existing is not None
        assert existing.id == vehicle.id
        
        # Test update instead of create
        updated_vehicle = service.update_vehicle_listing(vehicle.id, {"price": 19000.0})
        assert updated_vehicle.price == 19000.0
        assert len(updated_vehicle.price_history) == 2  # Original + update
    
    def test_api_integration_with_data(self, client, db_session):
        """Test API endpoints with real data flow"""
        
        # Create test data through service
        service = AutomotiveService(db_session)
        
        vehicle_data = {
            "external_id": "integration-test-1",
            "listing_url": "https://gruppoautouno.it/usato/integration-test-1/",
            "make": "Volkswagen",
            "model": "Golf",
            "year": 2020,
            "price": 18500.0,
            "mileage": 45000,
            "fuel_type": "diesel",
            "transmission": "manual",
            "city": "Napoli",
            "images": [
                {
                    "image_url": "https://example.com/image1.jpg",
                    "image_type": "exterior",
                    "image_order": 0
                }
            ]
        }
        
        vehicle = service.create_vehicle_listing(vehicle_data)
        
        # Test search API
        response = client.get("/api/v1/automotive/vehicles")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["vehicles"][0]["make"] == "Volkswagen"
        
        # Test get by ID API
        response = client.get(f"/api/v1/automotive/vehicles/{vehicle.id}")
        assert response.status_code == 200
        vehicle_detail = response.json()
        assert vehicle_detail["id"] == vehicle.id
        assert len(vehicle_detail["images"]) == 1
        assert len(vehicle_detail["price_history"]) == 1
        
        # Test analytics API
        response = client.get("/api/v1/automotive/analytics")
        assert response.status_code == 200
        analytics = response.json()
        assert analytics["data_quality"]["total_vehicles"] == 1
        assert analytics["overview"]["totals"]["total_vehicles"] == 1
        
        # Test makes API
        response = client.get("/api/v1/automotive/makes")
        assert response.status_code == 200
        makes = response.json()
        assert len(makes) == 1
        assert makes[0]["make"] == "Volkswagen"
        assert makes[0]["count"] == 1
    
    def test_compliance_integration(self):
        """Test compliance manager integration"""
        
        compliance = ComplianceManager()
        
        # Test URL compliance check
        test_url = "https://gruppoautouno.it/usato/test-vehicle/"
        compliance_result = compliance.check_url_compliance(test_url)
        
        assert "url" in compliance_result
        assert "allowed" in compliance_result
        assert "reasons" in compliance_result
        
        # Test rate limiting
        for i in range(5):
            compliance.record_request(test_url, 200, 1.0)
        
        status = compliance.get_compliance_status()
        assert "rate_limiting" in status
        assert status["rate_limiting"]["requests_last_minute"] == 5
        
        # Test compliance score
        score = compliance.calculate_compliance_score()
        assert 0 <= score <= 100
    
    def test_monitoring_integration(self, db_session):
        """Test monitoring system integration"""
        
        monitor = ScraperMonitor()
        
        # Test system health
        health = monitor.get_system_health()
        assert "timestamp" in health
        assert "system" in health
        assert "services" in health
        assert "overall_status" in health
        
        # Test data overview
        overview = monitor.get_data_overview(db_session)
        assert "totals" in overview
        assert "pricing" in overview
        
        # Test monitoring report
        report = monitor.generate_monitoring_report(db_session)
        assert "system_health" in report
        assert "data_overview" in report
        assert "alerts" in report
    
    def test_data_quality_workflow(self, db_session):
        """Test data quality monitoring workflow"""
        
        service = AutomotiveService(db_session)
        
        # Create vehicles with varying data quality
        vehicles_data = [
            {
                "external_id": "quality-test-1",
                "listing_url": "https://example.com/1/",
                "make": "Volkswagen",
                "model": "Golf",
                "price": 18500.0,
                "year": 2020,
                "mileage": 45000,
                "fuel_type": "diesel"
            },
            {
                "external_id": "quality-test-2",
                "listing_url": "https://example.com/2/",
                "make": "Peugeot",
                "model": "208",
                "price": 15000.0,
                "year": 2019,
                # Missing mileage and fuel_type
            },
            {
                "external_id": "quality-test-3",
                "listing_url": "https://example.com/3/",
                "make": "Citroën",
                "model": "C3",
                "price": 12000.0,
                # Missing year, mileage, fuel_type
            }
        ]
        
        for vehicle_data in vehicles_data:
            service.create_vehicle_listing(vehicle_data)
        
        # Get data quality metrics
        metrics = service.get_data_quality_metrics()
        
        assert metrics["total_vehicles"] == 3
        assert metrics["active_vehicles"] == 3
        
        # Check completeness scores
        completeness = metrics["completeness_scores"]
        assert completeness["make"] == 100.0  # All have make
        assert completeness["model"] == 100.0  # All have model
        assert completeness["price"] == 100.0  # All have price
        assert completeness["year"] == 66.67  # 2/3 have year (rounded)
        assert completeness["mileage"] == 33.33  # 1/3 have mileage (rounded)
        assert completeness["fuel_type"] == 33.33  # 1/3 have fuel_type (rounded)
        
        # Test overall completeness calculation
        expected_overall = sum(completeness.values()) / len(completeness)
        assert abs(metrics["overall_completeness"] - expected_overall) < 0.1
    
    def test_error_handling_workflow(self, db_session):
        """Test error handling throughout the system"""
        
        service = AutomotiveService(db_session)
        
        # Test invalid vehicle data
        invalid_data = {
            "external_id": "invalid-test",
            "listing_url": "invalid-url",
            # Missing required fields
        }
        
        # Should handle gracefully
        vehicle = service.create_vehicle_listing(invalid_data)
        assert vehicle is None or vehicle.make == "Unknown"
        
        # Test duplicate handling
        valid_data = {
            "external_id": "duplicate-test",
            "listing_url": "https://example.com/duplicate/",
            "make": "Test",
            "model": "Vehicle",
            "price": 10000.0
        }
        
        # Create first vehicle
        vehicle1 = service.create_vehicle_listing(valid_data)
        assert vehicle1 is not None
        
        # Try to create duplicate
        vehicle2 = service.create_vehicle_listing(valid_data)
        
        # Should update existing instead of creating new
        assert vehicle2 is not None
        assert vehicle2.id == vehicle1.id
    
    def test_pagination_and_filtering_integration(self, client, db_session):
        """Test pagination and filtering with large dataset"""
        
        service = AutomotiveService(db_session)
        
        # Create multiple vehicles with different attributes
        makes = ["Volkswagen", "Peugeot", "Citroën", "Opel"]
        fuel_types = ["diesel", "gasoline", "hybrid"]
        
        for i in range(50):
            vehicle_data = {
                "external_id": f"pagination-test-{i}",
                "listing_url": f"https://example.com/pagination-{i}/",
                "make": makes[i % len(makes)],
                "model": f"Model{i}",
                "price": 10000.0 + (i * 1000),
                "year": 2015 + (i % 8),
                "fuel_type": fuel_types[i % len(fuel_types)]
            }
            service.create_vehicle_listing(vehicle_data)
        
        # Test pagination
        response = client.get("/api/v1/automotive/vehicles?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 50
        assert len(data["vehicles"]) == 10
        assert data["total_pages"] == 5
        
        # Test filtering by make
        response = client.get("/api/v1/automotive/vehicles?make=Volkswagen")
        assert response.status_code == 200
        data = response.json()
        # Should have roughly 50/4 = 12-13 Volkswagen vehicles
        assert 10 <= data["total_count"] <= 15
        
        # Test price range filtering
        response = client.get("/api/v1/automotive/vehicles?price_min=20000&price_max=30000")
        assert response.status_code == 200
        data = response.json()
        for vehicle in data["vehicles"]:
            assert 20000 <= vehicle["price"] <= 30000
        
        # Test combined filters
        response = client.get("/api/v1/automotive/vehicles?make=Peugeot&fuel_type=diesel&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["vehicles"]) <= 5
        for vehicle in data["vehicles"]:
            assert vehicle["make"] == "Peugeot"
            assert vehicle["fuel_type"] == "diesel"
