"""
Vehicle Comparison Models

This module contains SQLAlchemy models for vehicle comparison functionality.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Float, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class VehicleComparison(Base):
    """Model for storing vehicle comparisons (single-user mode)"""
    __tablename__ = "vehicle_comparisons"

    id = Column(Integer, primary_key=True, index=True)

    # Comparison details
    name = Column(String(200), nullable=False)  # User-defined name for the comparison
    description = Column(Text, nullable=True)

    # Comparison settings
    comparison_criteria = Column(JSON, default=list)  # List of fields to compare
    is_public = Column(Boolean, default=False)  # Whether comparison can be shared
    is_favorite = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_accessed = Column(DateTime(timezone=True), nullable=True)

    # Relationships (simplified for single-user mode)
    comparison_items = relationship("VehicleComparisonItem", back_populates="comparison", cascade="all, delete-orphan")

    # Indexes (removed user-based indexes)
    __table_args__ = (
        Index('idx_comparisons_created', 'created_at'),
        Index('idx_public_comparisons', 'is_public', 'created_at'),
    )


class VehicleComparisonItem(Base):
    """Individual vehicles in a comparison"""
    __tablename__ = "vehicle_comparison_items"

    id = Column(Integer, primary_key=True, index=True)
    
    # References
    comparison_id = Column(Integer, ForeignKey("vehicle_comparisons.id"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicle_listings.id"), nullable=False, index=True)
    
    # Item details
    position = Column(Integer, default=0)  # Order in comparison
    notes = Column(Text, nullable=True)  # User notes about this vehicle
    rating = Column(Float, nullable=True)  # User rating (1-5 stars)
    
    # Comparison scores (calculated)
    overall_score = Column(Float, nullable=True)  # Overall comparison score
    price_score = Column(Float, nullable=True)  # Price competitiveness score
    feature_score = Column(Float, nullable=True)  # Feature completeness score
    condition_score = Column(Float, nullable=True)  # Condition score
    
    # Metadata
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    comparison = relationship("VehicleComparison", back_populates="comparison_items")
    vehicle = relationship("VehicleListing")
    
    # Indexes
    __table_args__ = (
        Index('idx_comparison_items', 'comparison_id', 'position'),
        Index('idx_vehicle_comparisons', 'vehicle_id'),
    )


class ComparisonTemplate(Base):
    """Predefined comparison templates"""
    __tablename__ = "comparison_templates"

    id = Column(Integer, primary_key=True, index=True)
    
    # Template details
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # "luxury", "economy", "suv", etc.
    
    # Template configuration
    comparison_fields = Column(JSON, default=list)  # Fields to compare
    scoring_weights = Column(JSON, default=dict)  # Weights for scoring
    display_settings = Column(JSON, default=dict)  # Display preferences
    
    # Template metadata
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # System vs user-created
    usage_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_template_category', 'category', 'is_active'),
        Index('idx_template_usage', 'usage_count', 'is_active'),
    )


class ComparisonShare(Base):
    """Shared comparison links"""
    __tablename__ = "comparison_shares"

    id = Column(Integer, primary_key=True, index=True)
    
    # References
    comparison_id = Column(Integer, ForeignKey("vehicle_comparisons.id"), nullable=False, index=True)
    shared_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Share details
    share_token = Column(String(64), unique=True, nullable=False, index=True)  # Unique share token
    share_name = Column(String(200), nullable=True)  # Custom name for share
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Access control
    is_active = Column(Boolean, default=True)
    requires_password = Column(Boolean, default=False)
    password_hash = Column(String(255), nullable=True)
    max_views = Column(Integer, nullable=True)  # Maximum number of views
    
    # Statistics
    view_count = Column(Integer, default=0)
    last_viewed = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    comparison = relationship("VehicleComparison")
    shared_by = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_share_token', 'share_token', 'is_active'),
        Index('idx_user_shares', 'shared_by_user_id', 'created_at'),
    )


class ComparisonView(Base):
    """Track comparison views for analytics"""
    __tablename__ = "comparison_views"

    id = Column(Integer, primary_key=True, index=True)
    
    # References
    comparison_id = Column(Integer, ForeignKey("vehicle_comparisons.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Null for anonymous views
    share_id = Column(Integer, ForeignKey("comparison_shares.id"), nullable=True, index=True)
    
    # View details
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    referrer = Column(String(500), nullable=True)
    
    # Session info
    session_duration = Column(Integer, nullable=True)  # Duration in seconds
    interactions = Column(Integer, default=0)  # Number of interactions
    
    # Metadata
    viewed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    comparison = relationship("VehicleComparison")
    user = relationship("User")
    share = relationship("ComparisonShare")
    
    # Indexes
    __table_args__ = (
        Index('idx_comparison_views', 'comparison_id', 'viewed_at'),
        Index('idx_user_views', 'user_id', 'viewed_at'),
        Index('idx_share_views', 'share_id', 'viewed_at'),
    )
