"""
Pydantic schemas for alert-related API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class AlertCreate(BaseModel):
    """Schema for creating alerts"""
    name: str = Field(..., min_length=1, max_length=200, description="Alert name")
    description: Optional[str] = Field(None, max_length=1000, description="Alert description")
    
    # Vehicle criteria
    make: Optional[str] = Field(None, max_length=50, description="Vehicle make")
    model: Optional[str] = Field(None, max_length=100, description="Vehicle model")
    min_price: Optional[int] = Field(None, ge=0, description="Minimum price in EUR")
    max_price: Optional[int] = Field(None, ge=0, description="Maximum price in EUR")
    min_year: Optional[int] = Field(None, ge=1900, le=2030, description="Minimum year")
    max_year: Optional[int] = Field(None, ge=1900, le=2030, description="Maximum year")
    max_mileage: Optional[int] = Field(None, ge=0, description="Maximum mileage in km")
    fuel_type: Optional[str] = Field(None, max_length=20, description="Fuel type")
    transmission: Optional[str] = Field(None, max_length=20, description="Transmission type")
    body_type: Optional[str] = Field(None, max_length=30, description="Body type")
    
    # Location criteria
    city: Optional[str] = Field(None, max_length=100, description="City")
    region: Optional[str] = Field(None, max_length=100, description="Region/State")
    location_radius: Optional[int] = Field(None, ge=0, le=500, description="Search radius in km")
    
    # Advanced criteria
    min_engine_power: Optional[int] = Field(None, ge=0, description="Minimum engine power in HP")
    max_engine_power: Optional[int] = Field(None, ge=0, description="Maximum engine power in HP")
    condition: Optional[str] = Field(None, pattern="^(new|used|demo)$", description="Vehicle condition")
    
    # Alert behavior
    notification_frequency: str = Field("immediate", pattern="^(immediate|daily|weekly)$")
    max_notifications_per_day: int = Field(5, ge=1, le=20, description="Max notifications per day")
    is_active: bool = Field(True, description="Whether alert is active")

    @validator('max_price')
    def validate_price_range(cls, v, values):
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('max_price must be greater than or equal to min_price')
        return v

    @validator('max_year')
    def validate_year_range(cls, v, values):
        if v is not None and 'min_year' in values and values['min_year'] is not None:
            if v < values['min_year']:
                raise ValueError('max_year must be greater than or equal to min_year')
        return v

    @validator('max_engine_power')
    def validate_power_range(cls, v, values):
        if v is not None and 'min_engine_power' in values and values['min_engine_power'] is not None:
            if v < values['min_engine_power']:
                raise ValueError('max_engine_power must be greater than or equal to min_engine_power')
        return v


class AlertUpdate(BaseModel):
    """Schema for updating alerts"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    
    # Vehicle criteria
    make: Optional[str] = Field(None, max_length=50)
    model: Optional[str] = Field(None, max_length=100)
    min_price: Optional[int] = Field(None, ge=0)
    max_price: Optional[int] = Field(None, ge=0)
    min_year: Optional[int] = Field(None, ge=1900, le=2030)
    max_year: Optional[int] = Field(None, ge=1900, le=2030)
    max_mileage: Optional[int] = Field(None, ge=0)
    fuel_type: Optional[str] = Field(None, max_length=20)
    transmission: Optional[str] = Field(None, max_length=20)
    body_type: Optional[str] = Field(None, max_length=30)
    
    # Location criteria
    city: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    location_radius: Optional[int] = Field(None, ge=0, le=500)
    
    # Advanced criteria
    min_engine_power: Optional[int] = Field(None, ge=0)
    max_engine_power: Optional[int] = Field(None, ge=0)
    condition: Optional[str] = Field(None, pattern="^(new|used|demo)$")
    
    # Alert behavior
    notification_frequency: Optional[str] = Field(None, pattern="^(immediate|daily|weekly)$")
    max_notifications_per_day: Optional[int] = Field(None, ge=1, le=20)
    is_active: Optional[bool] = None


class AlertResponse(BaseModel):
    """Response schema for alert data (single-user mode)"""
    id: int
    name: str
    description: Optional[str] = None
    
    # Vehicle criteria
    make: Optional[str] = None
    model: Optional[str] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    max_mileage: Optional[int] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    body_type: Optional[str] = None
    
    # Location criteria
    city: Optional[str] = None
    region: Optional[str] = None
    location_radius: Optional[int] = None
    
    # Advanced criteria
    min_engine_power: Optional[int] = None
    max_engine_power: Optional[int] = None
    condition: Optional[str] = None
    
    # Alert behavior
    is_active: bool
    notification_frequency: str
    last_triggered: Optional[datetime] = None
    trigger_count: int
    max_notifications_per_day: int
    
    # Metadata
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertTestRequest(BaseModel):
    """Schema for alert testing requests"""
    test_days: int = Field(7, ge=1, le=30, description="Days of listings to test against")
    max_listings: int = Field(1000, ge=1, le=5000, description="Maximum listings to test")
    create_notifications: bool = Field(False, description="Whether to create actual notifications")


class AlertTestResponse(BaseModel):
    """Schema for alert test results"""
    alert_id: int
    test_period_days: int
    listings_tested: int
    matches_found: int
    matches: List[Dict[str, Any]]
    would_trigger: bool


class AlertStats(BaseModel):
    """Schema for alert statistics"""
    alert_id: int
    alert_name: str
    is_active: bool
    created_at: datetime
    last_triggered: Optional[datetime] = None
    trigger_count: int
    notifications_in_period: int
    recent_notifications: List[Dict[str, Any]]
    period_days: int


class AlertSummary(BaseModel):
    """Schema for alert summary data"""
    id: int
    name: str
    is_active: bool
    trigger_count: int
    last_triggered: Optional[datetime] = None
    criteria_summary: str
    match_rate: Optional[float] = None  # Percentage of listings that match


class AlertBulkAction(BaseModel):
    """Schema for bulk alert actions"""
    alert_ids: List[int]
    action: str = Field(..., pattern="^(activate|deactivate|delete|test)$")


class AlertExport(BaseModel):
    """Schema for alert export requests"""
    format: str = Field("json", pattern="^(json|csv|excel)$")
    include_inactive: bool = False
    include_stats: bool = True


class AlertImport(BaseModel):
    """Schema for alert import requests"""
    alerts: List[AlertCreate]
    overwrite_existing: bool = False
    validate_only: bool = False


class AlertMatchPreview(BaseModel):
    """Schema for alert match preview"""
    alert_criteria: Dict[str, Any]
    sample_listings: List[Dict[str, Any]]
    estimated_matches_per_day: Optional[int] = None
    match_quality_distribution: Optional[Dict[str, int]] = None


class AlertPerformanceMetrics(BaseModel):
    """Schema for alert performance metrics"""
    alert_id: int
    total_matches: int
    unique_listings_matched: int
    average_match_score: float
    perfect_matches: int
    notification_delivery_rate: float
    user_engagement_rate: float  # Click-through rate
    false_positive_rate: Optional[float] = None
