from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class User(Base):
    """User model for authentication and alert management"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    notification_preferences = relationship("NotificationPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    vehicle_comparisons = relationship("VehicleComparison", back_populates="user", cascade="all, delete-orphan")


class Scout(Base):
    __tablename__ = "scouts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    scout_reports = relationship("ScoutReport", back_populates="scout")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    team_number = Column(Integer, unique=True, index=True, nullable=False)
    team_name = Column(String(255), nullable=False)
    school = Column(String(255))
    city = Column(String(100))
    state = Column(String(50))
    country = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    scout_reports = relationship("ScoutReport", back_populates="team")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    match_number = Column(Integer, nullable=False)
    competition_level = Column(String(50))  # Qualification, Playoff, etc.
    red_alliance = Column(String(255))  # Team numbers separated by commas
    blue_alliance = Column(String(255))  # Team numbers separated by commas
    red_score = Column(Integer)
    blue_score = Column(Integer)
    match_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    scout_reports = relationship("ScoutReport", back_populates="match")


class ScoutReport(Base):
    __tablename__ = "scout_reports"

    id = Column(Integer, primary_key=True, index=True)
    scout_id = Column(Integer, ForeignKey("scouts.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    
    # Autonomous period data
    auto_mobility = Column(Boolean, default=False)
    auto_high_goals = Column(Integer, default=0)
    auto_low_goals = Column(Integer, default=0)
    
    # Teleop period data
    teleop_high_goals = Column(Integer, default=0)
    teleop_low_goals = Column(Integer, default=0)
    
    # Endgame data
    climb_attempted = Column(Boolean, default=False)
    climb_successful = Column(Boolean, default=False)
    
    # Additional notes
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    scout = relationship("Scout", back_populates="scout_reports")
    team = relationship("Team", back_populates="scout_reports")
    match = relationship("Match", back_populates="scout_reports")


class Alert(Base):
    """Enhanced Alert model for comprehensive vehicle notifications"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Alert identification
    name = Column(String(200), nullable=False)  # User-friendly name for the alert
    description = Column(Text, nullable=True)  # Optional description

    # Filter criteria (stored as individual columns for easier querying)
    make = Column(String(50), nullable=True, index=True)
    model = Column(String(100), nullable=True, index=True)
    min_price = Column(Integer, nullable=True, index=True)  # in EUR
    max_price = Column(Integer, nullable=True, index=True)  # in EUR
    min_year = Column(Integer, nullable=True, index=True)
    max_year = Column(Integer, nullable=True, index=True)
    max_mileage = Column(Integer, nullable=True, index=True)  # in kilometers
    fuel_type = Column(String(20), nullable=True, index=True)
    transmission = Column(String(20), nullable=True, index=True)
    body_type = Column(String(30), nullable=True, index=True)

    # Location criteria
    city = Column(String(100), nullable=True, index=True)
    region = Column(String(100), nullable=True, index=True)
    location_radius = Column(Integer, nullable=True)  # in kilometers

    # Advanced criteria
    min_engine_power = Column(Integer, nullable=True)  # in HP
    max_engine_power = Column(Integer, nullable=True)  # in HP
    condition = Column(String(20), nullable=True)  # new, used, demo

    # Alert behavior
    is_active = Column(Boolean, default=True, index=True)
    notification_frequency = Column(String(20), default="immediate")  # immediate, daily, weekly
    last_triggered = Column(DateTime(timezone=True), nullable=True)
    trigger_count = Column(Integer, default=0)
    max_notifications_per_day = Column(Integer, default=5)

    # Alert metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="alerts")
    notifications = relationship("Notification", back_populates="alert", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('idx_alert_user_active', 'user_id', 'is_active'),
        Index('idx_alert_criteria', 'make', 'model', 'min_price', 'max_price'),
        Index('idx_alert_location', 'city', 'region'),
        Index('idx_alert_frequency', 'notification_frequency', 'last_triggered'),
    )
