"""
Vehicle Comparison Schemas

Pydantic schemas for vehicle comparison API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class ComparisonCriteria(str, Enum):
    """Available comparison criteria"""
    PRICE = "price"
    YEAR = "year"
    MILEAGE = "mileage"
    FUEL_TYPE = "fuel_type"
    TRANSMISSION = "transmission"
    ENGINE_POWER = "engine_power_hp"
    ENGINE_DISPLACEMENT = "engine_displacement"
    BODY_TYPE = "body_type"
    DOORS = "doors"
    SEATS = "seats"
    COLOR = "color_exterior"
    CONDITION = "condition"
    LOCATION = "city"
    DEALER = "dealer_name"


class ComparisonDisplayMode(str, Enum):
    """Display modes for comparisons"""
    TABLE = "table"
    CARDS = "cards"
    DETAILED = "detailed"


class VehicleComparisonItemCreate(BaseModel):
    """Schema for creating a comparison item"""
    vehicle_id: int
    notes: Optional[str] = None
    rating: Optional[float] = Field(None, ge=1, le=5)


class VehicleComparisonItemUpdate(BaseModel):
    """Schema for updating a comparison item"""
    notes: Optional[str] = None
    rating: Optional[float] = Field(None, ge=1, le=5)
    position: Optional[int] = Field(None, ge=0)


class VehicleComparisonItemResponse(BaseModel):
    """Schema for comparison item response"""
    id: int
    vehicle_id: int
    position: int
    notes: Optional[str] = None
    rating: Optional[float] = None
    overall_score: Optional[float] = None
    price_score: Optional[float] = None
    feature_score: Optional[float] = None
    condition_score: Optional[float] = None
    added_at: datetime
    updated_at: Optional[datetime] = None
    
    # Vehicle details (populated from relationship)
    vehicle: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class VehicleComparisonCreate(BaseModel):
    """Schema for creating a vehicle comparison"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    comparison_criteria: List[ComparisonCriteria] = Field(default_factory=list)
    is_public: bool = False
    vehicle_ids: List[int] = Field(default_factory=list, max_items=10)


class VehicleComparisonUpdate(BaseModel):
    """Schema for updating a vehicle comparison"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    comparison_criteria: Optional[List[ComparisonCriteria]] = None
    is_public: Optional[bool] = None
    is_favorite: Optional[bool] = None


class VehicleComparisonResponse(BaseModel):
    """Schema for comparison response"""
    id: int
    name: str
    description: Optional[str] = None
    comparison_criteria: List[str] = []
    is_public: bool = False
    is_favorite: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    
    # Items in the comparison
    comparison_items: List[VehicleComparisonItemResponse] = []
    
    # Statistics
    item_count: int = 0

    class Config:
        from_attributes = True


class VehicleComparisonListResponse(BaseModel):
    """Schema for comparison list response"""
    comparisons: List[VehicleComparisonResponse]
    total: int
    page: int
    limit: int
    has_more: bool


class ComparisonTemplateResponse(BaseModel):
    """Schema for comparison template response"""
    id: int
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    comparison_fields: List[str] = []
    scoring_weights: Dict[str, float] = {}
    display_settings: Dict[str, Any] = {}
    usage_count: int = 0
    is_system: bool = False

    class Config:
        from_attributes = True


class ComparisonAnalysis(BaseModel):
    """Schema for comparison analysis results"""
    best_value: Optional[Dict[str, Any]] = None
    best_performance: Optional[Dict[str, Any]] = None
    best_condition: Optional[Dict[str, Any]] = None
    price_range: Dict[str, float] = {}
    average_specs: Dict[str, Any] = {}
    recommendations: List[str] = []


class DetailedComparisonResponse(BaseModel):
    """Schema for detailed comparison with analysis"""
    comparison: VehicleComparisonResponse
    analysis: ComparisonAnalysis
    comparison_matrix: List[Dict[str, Any]] = []
    scoring_breakdown: Dict[str, Dict[str, float]] = {}


class ComparisonShareCreate(BaseModel):
    """Schema for creating a comparison share"""
    share_name: Optional[str] = None
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)
    requires_password: bool = False
    password: Optional[str] = Field(None, min_length=4)
    max_views: Optional[int] = Field(None, ge=1)


class ComparisonShareResponse(BaseModel):
    """Schema for comparison share response"""
    id: int
    share_token: str
    share_name: Optional[str] = None
    share_url: str
    expires_at: Optional[datetime] = None
    is_active: bool = True
    requires_password: bool = False
    max_views: Optional[int] = None
    view_count: int = 0
    last_viewed: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ComparisonShareAccess(BaseModel):
    """Schema for accessing a shared comparison"""
    password: Optional[str] = None


class ComparisonStats(BaseModel):
    """Schema for comparison statistics"""
    total_comparisons: int
    public_comparisons: int
    favorite_comparisons: int
    total_views: int
    most_compared_vehicles: List[Dict[str, Any]] = []
    popular_criteria: List[Dict[str, Any]] = []


class BulkComparisonAction(BaseModel):
    """Schema for bulk comparison actions"""
    comparison_ids: List[int]
    action: str = Field(..., pattern="^(delete|favorite|unfavorite|make_public|make_private)$")


class ComparisonExport(BaseModel):
    """Schema for comparison export"""
    format: str = Field(..., pattern="^(json|csv|pdf)$")
    include_images: bool = False
    include_analysis: bool = True


class QuickComparisonRequest(BaseModel):
    """Schema for quick comparison request"""
    vehicle_ids: List[int] = Field(..., min_items=2, max_items=5)
    criteria: List[ComparisonCriteria] = Field(default_factory=lambda: [
        ComparisonCriteria.PRICE,
        ComparisonCriteria.YEAR,
        ComparisonCriteria.MILEAGE,
        ComparisonCriteria.FUEL_TYPE
    ])


class ComparisonRecommendation(BaseModel):
    """Schema for comparison recommendations"""
    vehicle_id: int
    score: float
    reasons: List[str]
    pros: List[str]
    cons: List[str]
    recommendation_type: str  # "best_value", "best_performance", "best_condition"


class ComparisonInsights(BaseModel):
    """Schema for comparison insights"""
    market_position: Dict[str, Any]
    price_competitiveness: float
    feature_completeness: float
    condition_assessment: float
    depreciation_estimate: Optional[float] = None
    similar_vehicles: List[Dict[str, Any]] = []



