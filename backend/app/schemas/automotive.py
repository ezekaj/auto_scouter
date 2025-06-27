"""
Automotive Data Schemas

This module contains Pydantic schemas for automotive data validation
and API serialization.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class FuelType(str, Enum):
    GASOLINE = "gasoline"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    PLUG_IN_HYBRID = "plug_in_hybrid"
    LPG = "lpg"
    CNG = "cng"
    HYDROGEN = "hydrogen"


class TransmissionType(str, Enum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    CVT = "cvt"
    SEQUENTIAL = "sequential"


class ConditionType(str, Enum):
    NEW = "new"
    USED = "used"
    DEMO = "demo"


class BodyType(str, Enum):
    SEDAN = "sedan"
    HATCHBACK = "hatchback"
    SUV = "suv"
    COUPE = "coupe"
    CONVERTIBLE = "convertible"
    WAGON = "wagon"
    PICKUP = "pickup"
    VAN = "van"
    MINIVAN = "minivan"


# Base schemas
class VehicleImageBase(BaseModel):
    image_url: str
    image_type: Optional[str] = None
    image_order: int = 0
    alt_text: Optional[str] = None


class VehicleImageCreate(VehicleImageBase):
    pass


class VehicleImageUpdate(BaseModel):
    image_url: Optional[str] = None
    image_type: Optional[str] = None
    image_order: Optional[int] = None
    alt_text: Optional[str] = None


class VehicleImage(VehicleImageBase):
    id: int
    vehicle_id: int
    local_path: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PriceHistoryBase(BaseModel):
    price: float
    currency: str = "EUR"
    price_change: Optional[float] = None
    change_percentage: Optional[float] = None


class PriceHistoryCreate(PriceHistoryBase):
    pass


class PriceHistory(PriceHistoryBase):
    id: int
    vehicle_id: int
    recorded_at: datetime

    class Config:
        from_attributes = True


class VehicleListingBase(BaseModel):
    # Identifiers
    external_id: Optional[str] = None
    vin: Optional[str] = None
    listing_url: str
    
    # Vehicle identification
    make: str = Field(..., min_length=1, max_length=50)
    model: str = Field(..., min_length=1, max_length=100)
    variant: Optional[str] = Field(None, max_length=200)
    year: Optional[int] = Field(None, ge=1900, le=2030)
    registration_date: Optional[datetime] = None
    
    # Pricing
    price: float = Field(..., gt=0)
    currency: str = Field(default="EUR", max_length=3)
    original_price: Optional[float] = Field(None, gt=0)
    price_type: Optional[str] = Field(default="fixed", max_length=20)
    
    # Technical specs
    mileage: Optional[int] = Field(None, ge=0)
    fuel_type: Optional[FuelType] = None
    transmission: Optional[TransmissionType] = None
    engine_displacement: Optional[int] = Field(None, gt=0)
    engine_power_kw: Optional[int] = Field(None, gt=0)
    engine_power_hp: Optional[int] = Field(None, gt=0)
    cylinders: Optional[int] = Field(None, ge=1, le=16)
    gears: Optional[int] = Field(None, ge=1, le=10)
    
    # Vehicle characteristics
    body_type: Optional[BodyType] = None
    doors: Optional[int] = Field(None, ge=2, le=6)
    seats: Optional[int] = Field(None, ge=1, le=9)
    color_exterior: Optional[str] = Field(None, max_length=50)
    color_interior: Optional[str] = Field(None, max_length=50)
    
    # Condition
    condition: ConditionType = ConditionType.USED
    accident_history: bool = False
    service_history: bool = True
    previous_owners: Optional[int] = Field(None, ge=0)
    
    # Location
    dealer_name: Optional[str] = Field(None, max_length=200)
    dealer_location: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    country: str = Field(default="IT", max_length=50)
    
    # Content
    primary_image_url: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    features: Optional[str] = None  # JSON string
    
    # Metadata
    source_website: str = Field(default="gruppoautouno.it", max_length=100)

    @validator('vin')
    def validate_vin(cls, v):
        if v and len(v) != 17:
            raise ValueError('VIN must be exactly 17 characters')
        return v

    @validator('price', 'original_price')
    def validate_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Price must be greater than 0')
        return v


class VehicleListingCreate(VehicleListingBase):
    pass


class VehicleListingUpdate(BaseModel):
    # All fields optional for updates
    external_id: Optional[str] = None
    vin: Optional[str] = None
    listing_url: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    year: Optional[int] = None
    registration_date: Optional[datetime] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    original_price: Optional[float] = None
    price_type: Optional[str] = None
    mileage: Optional[int] = None
    fuel_type: Optional[FuelType] = None
    transmission: Optional[TransmissionType] = None
    engine_displacement: Optional[int] = None
    engine_power_kw: Optional[int] = None
    engine_power_hp: Optional[int] = None
    cylinders: Optional[int] = None
    gears: Optional[int] = None
    body_type: Optional[BodyType] = None
    doors: Optional[int] = None
    seats: Optional[int] = None
    color_exterior: Optional[str] = None
    color_interior: Optional[str] = None
    condition: Optional[ConditionType] = None
    accident_history: Optional[bool] = None
    service_history: Optional[bool] = None
    previous_owners: Optional[int] = None
    dealer_name: Optional[str] = None
    dealer_location: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    primary_image_url: Optional[str] = None
    description: Optional[str] = None
    features: Optional[str] = None
    is_active: Optional[bool] = None


class VehicleListing(VehicleListingBase):
    id: int
    scraped_at: datetime
    last_updated: Optional[datetime] = None
    is_active: bool = True
    
    # Relationships
    images: List[VehicleImage] = []
    price_history: List[PriceHistory] = []

    class Config:
        from_attributes = True


class VehicleListingWithStats(VehicleListing):
    """Vehicle listing with additional statistics"""
    price_changes: int = 0
    days_on_market: int = 0
    average_price: Optional[float] = None
    price_trend: Optional[str] = None  # "increasing", "decreasing", "stable"


# Search and filter schemas
class VehicleSearchFilters(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    year_min: Optional[int] = Field(None, ge=1900)
    year_max: Optional[int] = Field(None, le=2030)
    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)
    mileage_max: Optional[int] = Field(None, ge=0)
    fuel_type: Optional[FuelType] = None
    transmission: Optional[TransmissionType] = None
    body_type: Optional[BodyType] = None
    condition: Optional[ConditionType] = None
    city: Optional[str] = None
    region: Optional[str] = None
    is_active: bool = True


class VehicleSearchResponse(BaseModel):
    vehicles: List[VehicleListing]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    filters_applied: VehicleSearchFilters


# Scraping related schemas
class ScrapingLogBase(BaseModel):
    source_url: str
    status: str
    action: Optional[str] = None
    error_message: Optional[str] = None
    response_code: Optional[int] = None
    response_time: Optional[float] = None
    fields_extracted: int = 0
    fields_missing: int = 0
    data_quality_score: Optional[float] = None


class ScrapingLogCreate(ScrapingLogBase):
    session_id: str
    external_id: Optional[str] = None


class ScrapingLog(ScrapingLogBase):
    id: int
    session_id: str
    vehicle_id: Optional[int] = None
    external_id: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScrapingSessionBase(BaseModel):
    source_website: str
    scraper_version: Optional[str] = None
    user_agent: Optional[str] = None


class ScrapingSessionCreate(ScrapingSessionBase):
    session_id: str


class ScrapingSession(ScrapingSessionBase):
    id: int
    session_id: str
    total_pages_scraped: int = 0
    total_vehicles_found: int = 0
    total_vehicles_new: int = 0
    total_vehicles_updated: int = 0
    total_errors: int = 0
    average_response_time: Optional[float] = None
    total_data_transferred: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    status: str = "running"
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


# Analytics schemas
class VehicleAnalytics(BaseModel):
    total_vehicles: int
    active_vehicles: int
    average_price: float
    price_range: Dict[str, float]  # min, max
    most_common_make: str
    most_common_fuel_type: str
    average_mileage: float
    newest_listing: datetime
    oldest_listing: datetime


class PriceAnalytics(BaseModel):
    make: str
    model: str
    average_price: float
    median_price: float
    price_trend: str
    sample_size: int
    last_updated: datetime
