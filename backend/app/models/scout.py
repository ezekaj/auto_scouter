from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


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
