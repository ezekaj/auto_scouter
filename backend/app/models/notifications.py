"""
Notification System Models

This module contains SQLAlchemy models for the notification and alert system.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Float, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
from enum import Enum


class NotificationType(str, Enum):
    EMAIL = "email"
    IN_APP = "in_app"
    PUSH = "push"
    SMS = "sms"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    OPENED = "opened"
    CLICKED = "clicked"


class NotificationFrequency(str, Enum):
    IMMEDIATE = "immediate"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class Notification(Base):
    """Notification model for storing sent notifications (single-user mode)"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    # Relationships (keeping user_id for database compatibility)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=True, index=True)
    listing_id = Column(Integer, ForeignKey("vehicle_listings.id"), nullable=True, index=True)
    
    # Notification details
    notification_type = Column(String(20), nullable=False, index=True)  # email, in_app, push, sms
    status = Column(String(20), default=NotificationStatus.PENDING, index=True)
    
    # Content
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    content_data = Column(JSON)  # Additional structured data (car details, etc.)
    
    # Delivery tracking
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional fields
    external_id = Column(String(100), nullable=True)  # For tracking with external services
    priority = Column(Integer, default=1)  # 1=low, 2=medium, 3=high
    is_read = Column(Boolean, default=False, index=True)
    
    # Relationships (keeping for database compatibility)
    user = relationship("User")
    alert = relationship("Alert", back_populates="notifications")
    listing = relationship("VehicleListing")

    # Indexes for performance (removed user-based indexes)
    __table_args__ = (
        Index('idx_notifications_created', 'created_at'),
        Index('idx_alert_notifications', 'alert_id', 'sent_at'),
        Index('idx_notification_status', 'status', 'created_at'),
        Index('idx_notification_type_status', 'notification_type', 'status'),
    )


# Minimal NotificationPreferences model for single-user mode
class NotificationPreferences(Base):
    """Minimal notification preferences for single-user mode"""
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    email_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    max_notifications_per_day = Column(Integer, default=10)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes for performance
    __table_args__ = (
        Index('idx_notification_prefs_user', 'user_id'),
    )


class NotificationTemplate(Base):
    """Notification templates for different types of notifications"""
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    
    # Template identification
    name = Column(String(100), nullable=False, unique=True, index=True)
    notification_type = Column(String(20), nullable=False, index=True)
    language = Column(String(5), default="en")
    
    # Template content
    subject_template = Column(String(200), nullable=True)  # For email/SMS
    title_template = Column(String(200), nullable=False)
    message_template = Column(Text, nullable=False)
    html_template = Column(Text, nullable=True)  # For email HTML content
    
    # Template variables (JSON array of variable names)
    variables = Column(JSON, default=list)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_template_type_lang', 'notification_type', 'language'),
    )


class NotificationQueue(Base):
    """Queue for processing notifications"""
    __tablename__ = "notification_queue"

    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False, index=True)
    
    # Queue management
    priority = Column(Integer, default=1, index=True)  # Higher number = higher priority
    scheduled_for = Column(DateTime(timezone=True), nullable=True, index=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status tracking
    status = Column(String(20), default="queued", index=True)  # queued, processing, completed, failed
    worker_id = Column(String(50), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    notification = relationship("Notification")
    
    # Indexes
    __table_args__ = (
        Index('idx_queue_status_priority', 'status', 'priority'),
        Index('idx_queue_scheduled', 'scheduled_for', 'status'),
    )


class AlertMatchLog(Base):
    """Log of alert matching runs for tracking and debugging"""
    __tablename__ = "alert_match_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Run identification
    run_id = Column(String(36), nullable=False, index=True)  # UUID for each matching run
    
    # Run details
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="running")  # running, completed, failed
    
    # Statistics
    alerts_processed = Column(Integer, default=0)
    listings_checked = Column(Integer, default=0)
    matches_found = Column(Integer, default=0)
    notifications_created = Column(Integer, default=0)
    
    # Performance metrics
    processing_time_seconds = Column(Float, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Configuration used
    config_snapshot = Column(JSON, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_match_log_run', 'run_id', 'started_at'),
        Index('idx_match_log_status', 'status', 'started_at'),
    )
