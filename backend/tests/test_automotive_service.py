"""
Tests for Automotive Service
"""

import pytest
from datetime import datetime, timedelta

from app.services.automotive_service import AutomotiveService
from app.models.automotive import VehicleListing, VehicleImage, PriceHistory


class TestAutomotiveService:
    """Test cases for AutomotiveService"""
    
    def test_create_vehicle_listing(self, db_session, sample_vehicle_data):
        """Test creating a new vehicle listing"""
        service = AutomotiveService(db_session)
        
        vehicle = service.create_vehicle_listing(sample_vehicle_data)
        
        assert vehicle is not None
        assert vehicle.make == "Volkswagen"
        assert vehicle.model == "Golf"
        assert vehicle.price == 18500.0
        assert vehicle.external_id == "test-vehicle-123"
        
        # Check that images were created
        assert len(vehicle.images) == 1
        assert vehicle.images[0].image_url == "https://example.com/image1.jpg"
        
        # Check that price history was created
        assert len(vehicle.price_history) == 1
        assert vehicle.price_history[0].price == 18500.0
    
    def test_find_duplicate_listing_by_external_id(self, db_session, sample_vehicle_data):
        """Test finding duplicate by external_id"""
        service = AutomotiveService(db_session)
        
        # Create first vehicle
        vehicle1 = service.create_vehicle_listing(sample_vehicle_data)
        
        # Try to create duplicate
        duplicate_data = sample_vehicle_data.copy()
        duplicate_data["price"] = 19000.0  # Different price
        
        duplicate = service.find_duplicate_listing(duplicate_data)
        
        assert duplicate is not None
        assert duplicate.id == vehicle1.id
    
    def test_find_duplicate_listing_by_url(self, db_session, sample_vehicle_data):
        """Test finding duplicate by listing URL"""
        service = AutomotiveService(db_session)
        
        # Create first vehicle
        vehicle1 = service.create_vehicle_listing(sample_vehicle_data)
        
        # Try to find by URL
        duplicate_data = {
            "listing_url": sample_vehicle_data["listing_url"],
            "make": "Different Make",
            "model": "Different Model"
        }
        
        duplicate = service.find_duplicate_listing(duplicate_data)
        
        assert duplicate is not None
        assert duplicate.id == vehicle1.id
    
    def test_update_vehicle_listing(self, db_session, sample_vehicle_data):
        """Test updating an existing vehicle listing"""
        service = AutomotiveService(db_session)
        
        # Create vehicle
        vehicle = service.create_vehicle_listing(sample_vehicle_data)
        original_price = vehicle.price
        
        # Update data
        update_data = {
            "price": 17500.0,
            "mileage": 46000,
            "images": [
                {
                    "image_url": "https://example.com/new-image.jpg",
                    "image_type": "interior",
                    "image_order": 0
                }
            ]
        }
        
        updated_vehicle = service.update_vehicle_listing(vehicle.id, update_data)
        
        assert updated_vehicle is not None
        assert updated_vehicle.price == 17500.0
        assert updated_vehicle.mileage == 46000
        
        # Check price history
        db_session.refresh(updated_vehicle)
        assert len(updated_vehicle.price_history) == 2  # Original + update
        
        # Check images were updated
        assert len(updated_vehicle.images) == 1
        assert updated_vehicle.images[0].image_url == "https://example.com/new-image.jpg"
    
    def test_search_vehicles_by_make(self, db_session, sample_vehicle_data):
        """Test searching vehicles by make"""
        service = AutomotiveService(db_session)
        
        # Create test vehicles
        vw_data = sample_vehicle_data.copy()
        vw_data["external_id"] = "vw-1"
        service.create_vehicle_listing(vw_data)
        
        peugeot_data = sample_vehicle_data.copy()
        peugeot_data["external_id"] = "peugeot-1"
        peugeot_data["make"] = "Peugeot"
        peugeot_data["model"] = "208"
        service.create_vehicle_listing(peugeot_data)
        
        # Search for Volkswagen
        from app.schemas.automotive import VehicleSearchFilters
        filters = VehicleSearchFilters(make="Volkswagen")
        
        vehicles, total_count = service.search_vehicles(filters)
        
        assert total_count == 1
        assert len(vehicles) == 1
        assert vehicles[0].make == "Volkswagen"
    
    def test_search_vehicles_by_price_range(self, db_session, sample_vehicle_data):
        """Test searching vehicles by price range"""
        service = AutomotiveService(db_session)
        
        # Create vehicles with different prices
        cheap_data = sample_vehicle_data.copy()
        cheap_data["external_id"] = "cheap-1"
        cheap_data["price"] = 10000.0
        service.create_vehicle_listing(cheap_data)
        
        expensive_data = sample_vehicle_data.copy()
        expensive_data["external_id"] = "expensive-1"
        expensive_data["price"] = 30000.0
        service.create_vehicle_listing(expensive_data)
        
        # Search for vehicles under 20000
        from app.schemas.automotive import VehicleSearchFilters
        filters = VehicleSearchFilters(price_max=20000.0)
        
        vehicles, total_count = service.search_vehicles(filters)
        
        assert total_count == 2  # Original + cheap
        for vehicle in vehicles:
            assert vehicle.price <= 20000.0
    
    def test_deactivate_old_listings(self, db_session, sample_vehicle_data):
        """Test deactivating old listings"""
        service = AutomotiveService(db_session)
        
        # Create vehicle
        vehicle = service.create_vehicle_listing(sample_vehicle_data)
        
        # Manually set old last_updated date
        old_date = datetime.utcnow() - timedelta(days=35)
        vehicle.last_updated = old_date
        db_session.commit()
        
        # Deactivate old listings
        deactivated_count = service.deactivate_old_listings(days_old=30)
        
        assert deactivated_count == 1
        
        # Check vehicle is deactivated
        db_session.refresh(vehicle)
        assert vehicle.is_active == False
    
    def test_get_data_quality_metrics(self, db_session, sample_vehicle_data):
        """Test getting data quality metrics"""
        service = AutomotiveService(db_session)
        
        # Create some test vehicles
        for i in range(5):
            data = sample_vehicle_data.copy()
            data["external_id"] = f"test-{i}"
            if i == 0:
                data["fuel_type"] = None  # Missing fuel type
            if i == 1:
                data["mileage"] = None  # Missing mileage
            service.create_vehicle_listing(data)
        
        metrics = service.get_data_quality_metrics()
        
        assert metrics["total_vehicles"] == 5
        assert metrics["active_vehicles"] == 5
        assert "completeness_scores" in metrics
        assert "average_price" in metrics
        
        # Check completeness scores
        completeness = metrics["completeness_scores"]
        assert completeness["make"] == 100.0  # All have make
        assert completeness["fuel_type"] == 80.0  # 4/5 have fuel type
        assert completeness["mileage"] == 80.0  # 4/5 have mileage
    
    def test_cleanup_old_data(self, db_session, sample_vehicle_data):
        """Test cleaning up old data"""
        service = AutomotiveService(db_session)
        
        # Create vehicle with old data
        vehicle = service.create_vehicle_listing(sample_vehicle_data)
        
        # Create old scraping log
        from app.models.automotive import ScrapingLog
        old_date = datetime.utcnow() - timedelta(days=400)
        old_log = ScrapingLog(
            session_id="old-session",
            source_url="https://example.com",
            status="success",
            started_at=old_date
        )
        db_session.add(old_log)
        db_session.commit()
        
        # Run cleanup
        cleanup_stats = service.cleanup_old_data(retention_days=365)
        
        assert "old_logs_deleted" in cleanup_stats
        assert cleanup_stats["old_logs_deleted"] >= 1
