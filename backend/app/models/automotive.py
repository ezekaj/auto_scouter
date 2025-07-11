"""
Automotive Data Models

This module contains SQLAlchemy models for storing automotive data
scraped from various dealership websites.
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
import uuid


class VehicleListing(Base):
    """Main vehicle listing model"""
    __tablename__ = "vehicle_listings"

    id = Column(Integer, primary_key=True, index=True)
    
    # Unique identifiers
    external_id = Column(String(100), unique=True, index=True)  # Dealer's listing ID
    vin = Column(String(17), index=True, nullable=True)  # Vehicle Identification Number
    listing_url = Column(String(500), unique=True, index=True)
    
    # Vehicle identification
    make = Column(String(50), nullable=False, index=True)
    model = Column(String(100), nullable=False, index=True)
    variant = Column(String(200))  # Model variant/trim
    year = Column(Integer, index=True)
    registration_date = Column(DateTime)
    
    # Pricing information
    price = Column(Float, nullable=False, index=True)
    currency = Column(String(3), default="EUR")
    original_price = Column(Float)  # If discounted
    price_type = Column(String(20))  # "fixed", "negotiable", "on_request"
    
    # Technical specifications
    mileage = Column(Integer, index=True)  # in kilometers
    fuel_type = Column(String(20), index=True)  # gasoline, diesel, electric, hybrid, etc.
    transmission = Column(String(20), index=True)  # manual, automatic, cvt
    engine_displacement = Column(Integer)  # in cc
    engine_power_kw = Column(Integer)  # in kilowatts
    engine_power_hp = Column(Integer)  # in horsepower
    cylinders = Column(Integer)
    gears = Column(Integer)
    
    # Vehicle characteristics
    body_type = Column(String(30))  # sedan, hatchback, suv, etc.
    doors = Column(Integer)
    seats = Column(Integer)
    color_exterior = Column(String(50))
    color_interior = Column(String(50))
    
    # Condition and history
    condition = Column(String(20), default="used")  # new, used, demo
    accident_history = Column(Boolean, default=False)
    service_history = Column(Boolean, default=True)
    previous_owners = Column(Integer)
    
    # Location information
    dealer_name = Column(String(200))
    dealer_location = Column(String(200))
    city = Column(String(100), index=True)
    region = Column(String(100))
    country = Column(String(50), default="IT")
    
    # Media and content
    primary_image_url = Column(String(500))
    description = Column(Text)
    features = Column(Text)  # JSON string of features list
    
    # Metadata
    source_website = Column(String(100), nullable=False, index=True)  # autoscout24, mobile_de, gruppoautouno
    source = Column(String(50), default="unknown")  # Short source identifier
    source_country = Column(String(3), default="IT")  # IT, DE, etc.
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True, index=True)

    # Data quality and deduplication
    data_quality_score = Column(Float, default=0.0)  # 0.0 to 1.0
    duplicate_hash = Column(String(64))  # Hash for duplicate detection
    duplicate_of = Column(Integer, ForeignKey("vehicle_listings.id"), nullable=True)  # Reference to master record
    is_duplicate = Column(Boolean, default=False, index=True)
    confidence_score = Column(Float, default=1.0)  # Confidence in data accuracy
    
    # Relationships
    images = relationship("VehicleImage", back_populates="vehicle", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="vehicle", cascade="all, delete-orphan")
    scraping_logs = relationship("ScrapingLog", back_populates="vehicle")

    # Self-referential relationship for duplicates
    duplicates = relationship("VehicleListing", remote_side=[id], backref="master_record")

    # Indexes for common queries
    __table_args__ = (
        Index('idx_make_model', 'make', 'model'),
        Index('idx_price_range', 'price', 'year'),
        Index('idx_location', 'city', 'region'),
        Index('idx_specs', 'fuel_type', 'transmission'),
        Index('idx_active_listings', 'is_active', 'scraped_at'),
        Index('idx_source_website', 'source_website', 'is_active'),
        Index('idx_source_country', 'source_country', 'source_website'),
        Index('idx_duplicates', 'is_duplicate', 'duplicate_of'),
        Index('idx_data_quality', 'data_quality_score', 'confidence_score'),
        Index('idx_external_source', 'external_id', 'source_website'),
    )


class VehicleImage(Base):
    """Vehicle images model"""
    __tablename__ = "vehicle_images"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicle_listings.id"), nullable=False)
    
    image_url = Column(String(500), nullable=False)
    image_type = Column(String(20))  # exterior, interior, engine, detail
    image_order = Column(Integer, default=0)
    alt_text = Column(String(200))
    
    # Local storage info (if images are downloaded)
    local_path = Column(String(500))
    file_size = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    vehicle = relationship("VehicleListing", back_populates="images")


class PriceHistory(Base):
    """Price change tracking model"""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicle_listings.id"), nullable=False)

    # Price information
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="EUR")
    price_change = Column(Float)  # Change from previous price
    change_percentage = Column(Float)  # Percentage change

    # Price context
    original_price = Column(Float, nullable=True)  # Original listing price
    discount_amount = Column(Float, nullable=True)  # Discount from original
    price_type = Column(String(20), default="fixed")  # fixed, negotiable, on_request

    # Market context
    market_position = Column(String(20), nullable=True)  # above_market, below_market, at_market
    days_on_market = Column(Integer, default=0)  # Days since first listing

    # Source information
    source_website = Column(String(100), nullable=True)
    source_url = Column(String(500), nullable=True)

    # Metadata
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    is_active = Column(Boolean, default=True)  # Whether this price is still current

    # Relationships
    vehicle = relationship("VehicleListing", back_populates="price_history")

    # Indexes
    __table_args__ = (
        Index('idx_vehicle_price_history', 'vehicle_id', 'recorded_at'),
        Index('idx_price_changes', 'price_change', 'recorded_at'),
        Index('idx_active_prices', 'is_active', 'recorded_at'),
    )


class ScrapingLog(Base):
    """Scraping activity log model"""
    __tablename__ = "scraping_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Session information
    session_id = Column(String(36), default=lambda: str(uuid.uuid4()), index=True)
    source_url = Column(String(500), nullable=False)
    
    # Vehicle reference (optional)
    vehicle_id = Column(Integer, ForeignKey("vehicle_listings.id"), nullable=True)
    external_id = Column(String(100))  # Dealer's listing ID
    
    # Scraping details
    status = Column(String(20), nullable=False)  # success, error, skipped
    action = Column(String(50))  # scrape_listing, scrape_detail, download_image
    error_message = Column(Text)
    response_code = Column(Integer)
    response_time = Column(Float)  # in seconds
    
    # Data quality metrics
    fields_extracted = Column(Integer, default=0)
    fields_missing = Column(Integer, default=0)
    data_quality_score = Column(Float)  # 0.0 to 1.0
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    vehicle = relationship("VehicleListing", back_populates="scraping_logs")

    # Indexes
    __table_args__ = (
        Index('idx_session_status', 'session_id', 'status'),
        Index('idx_scraping_time', 'started_at', 'status'),
    )


class ScrapingSession(Base):
    """Scraping session summary model"""
    __tablename__ = "scraping_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), unique=True, index=True)
    
    # Session metadata
    source_website = Column(String(100), nullable=False, index=True)
    source_country = Column(String(3), default="IT")
    scraper_version = Column(String(20))
    user_agent = Column(String(500))
    session_type = Column(String(20), default="single")  # single, multi_source, scheduled
    
    # Session statistics
    total_pages_scraped = Column(Integer, default=0)
    total_vehicles_found = Column(Integer, default=0)
    total_vehicles_new = Column(Integer, default=0)
    total_vehicles_updated = Column(Integer, default=0)
    total_vehicles_skipped = Column(Integer, default=0)
    total_duplicates_found = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)
    
    # Performance metrics
    average_response_time = Column(Float)
    total_data_transferred = Column(Integer)  # in bytes
    
    # Session timing
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    
    # Status
    status = Column(String(20), default="running")  # running, completed, failed, cancelled
    error_message = Column(Text)


class DataQualityMetric(Base):
    """Data quality tracking model"""
    __tablename__ = "data_quality_metrics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Metric identification
    metric_name = Column(String(100), nullable=False)
    metric_type = Column(String(50))  # completeness, accuracy, consistency
    
    # Metric values
    total_records = Column(Integer, default=0)
    valid_records = Column(Integer, default=0)
    invalid_records = Column(Integer, default=0)
    missing_records = Column(Integer, default=0)
    
    # Calculated scores
    completeness_score = Column(Float)  # 0.0 to 1.0
    accuracy_score = Column(Float)  # 0.0 to 1.0
    overall_score = Column(Float)  # 0.0 to 1.0
    
    # Time period
    measurement_date = Column(DateTime(timezone=True), server_default=func.now())
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))


class MultiSourceSession(Base):
    """Multi-source scraping session coordination model"""
    __tablename__ = "multi_source_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), unique=True, index=True)

    # Session metadata
    session_type = Column(String(20), default="multi_source")  # multi_source, scheduled_multi
    trigger_type = Column(String(20), default="manual")  # manual, scheduled, api
    max_vehicles_per_source = Column(Integer, default=50)

    # Source coordination
    sources_requested = Column(Text)  # JSON array of source names
    sources_completed = Column(Text)  # JSON array of completed sources
    sources_failed = Column(Text)  # JSON array of failed sources

    # Aggregated statistics
    total_sources = Column(Integer, default=0)
    completed_sources = Column(Integer, default=0)
    failed_sources = Column(Integer, default=0)
    total_vehicles_found = Column(Integer, default=0)
    total_vehicles_new = Column(Integer, default=0)
    total_vehicles_updated = Column(Integer, default=0)
    total_duplicates_found = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)

    # Performance metrics
    total_duration_seconds = Column(Integer)
    average_source_duration = Column(Float)
    fastest_source_duration = Column(Float)
    slowest_source_duration = Column(Float)

    # Session timing
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Status
    status = Column(String(20), default="running")  # running, completed, failed, cancelled
    error_message = Column(Text)

    # Indexes
    __table_args__ = (
        Index('idx_multi_session_status', 'status', 'started_at'),
        Index('idx_multi_session_type', 'session_type', 'trigger_type'),
    )
    
    # Additional details
    details = Column(Text)  # JSON string with detailed metrics
