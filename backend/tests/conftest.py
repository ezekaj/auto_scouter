"""
Test configuration and fixtures
"""

import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.models.base import Base
from app.main import app
from app.models.base import get_db
from app.models.scout import User, Alert
from app.models.automotive import VehicleListing


@pytest.fixture(scope="session")
def test_db():
    """Create a test database"""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Create engine and tables
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield TestingSessionLocal
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def db_session(test_db):
    """Create a database session for testing with proper cleanup"""
    session = test_db()
    try:
        yield session
    finally:
        # Clean up all data after each test
        session.rollback()
        # Delete all data from all tables
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()


@pytest.fixture
def client(test_db):
    """Create a test client"""
    def override_get_db():
        session = test_db()
        try:
            yield session
        finally:
            session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_vehicle_data():
    """Sample vehicle data for testing"""
    return {
        "external_id": "test-vehicle-123",
        "listing_url": "https://gruppoautouno.it/usato/test-vehicle-123/",
        "make": "Volkswagen",
        "model": "Golf",
        "variant": "Golf 1.6 TDI Comfortline",
        "year": 2020,
        "price": 18500.0,
        "currency": "EUR",
        "mileage": 45000,
        "fuel_type": "diesel",
        "transmission": "manual",
        "engine_displacement": 1598,
        "engine_power_kw": 85,
        "doors": 5,
        "seats": 5,
        "condition": "used",
        "city": "Napoli",
        "region": "Campania",
        "country": "IT",
        "dealer_name": "Autouno Group",
        "source_website": "gruppoautouno.it",
        "images": [
            {
                "image_url": "https://example.com/image1.jpg",
                "image_type": "exterior",
                "image_order": 0
            }
        ]
    }


@pytest.fixture
def sample_html_content():
    """Sample HTML content for scraper testing"""
    return """
    <html>
    <head><title>Volkswagen Golf</title></head>
    <body>
        <h1>Golf 1.6 TDI Comfortline</h1>
        <div class="price">€ 18.500</div>
        <div class="specs">
            <span>Immatricolazione: 03/2020</span>
            <span>Km: 45.000</span>
            <span>Alimentazione: Diesel</span>
            <span>Cambio: Manuale</span>
            <span>Potenza: 85 kW</span>
            <span>Cilindrata: 1.598 cc</span>
            <span>5 Porte</span>
            <span>5 Posti</span>
        </div>
        <ul class="features">
            <li>ABS</li>
            <li>ESP</li>
            <li>Air Conditioning</li>
        </ul>
        <img src="/images/golf-1.jpg" alt="Golf exterior">
        <img src="/images/golf-2.jpg" alt="Golf interior">
    </body>
    </html>
    """
