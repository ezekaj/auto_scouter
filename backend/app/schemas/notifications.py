"""
Notification System Schemas

This module contains Pydantic schemas for notification system validation and API serialization.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
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


# Notification Preferences Schemas
class NotificationPreferencesBase(BaseModel):
    email_enabled: bool = True
    in_app_enabled: bool = True
    push_enabled: bool = False
    sms_enabled: bool = False
    email_frequency: NotificationFrequency = NotificationFrequency.IMMEDIATE
    push_frequency: NotificationFrequency = NotificationFrequency.IMMEDIATE
    max_notifications_per_day: int = Field(10, ge=1, le=100)
    max_notifications_per_alert_per_day: int = Field(5, ge=1, le=20)
    quiet_hours_start: str = Field("22:00", regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: str = Field("08:00", regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_enabled: bool = False
    include_images: bool = True
    include_full_details: bool = True
    language: str = Field("en", max_length=5)


class NotificationPreferencesCreate(NotificationPreferencesBase):
    pass


class NotificationPreferencesUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    email_frequency: Optional[NotificationFrequency] = None
    push_frequency: Optional[NotificationFrequency] = None
    max_notifications_per_day: Optional[int] = Field(None, ge=1, le=100)
    max_notifications_per_alert_per_day: Optional[int] = Field(None, ge=1, le=20)
    quiet_hours_start: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_enabled: Optional[bool] = None
    include_images: Optional[bool] = None
    include_full_details: Optional[bool] = None
    language: Optional[str] = Field(None, max_length=5)


class NotificationPreferencesResponse(NotificationPreferencesBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Notification Schemas
class NotificationBase(BaseModel):
    notification_type: NotificationType
    title: str = Field(..., max_length=200)
    message: str
    content_data: Optional[Dict[str, Any]] = None
    priority: int = Field(1, ge=1, le=3)


class NotificationCreate(NotificationBase):
    user_id: int
    alert_id: Optional[int] = None
    listing_id: Optional[int] = None


class NotificationUpdate(BaseModel):
    status: Optional[NotificationStatus] = None
    is_read: Optional[bool] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None


class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    alert_id: Optional[int] = None
    listing_id: Optional[int] = None
    status: NotificationStatus
    is_read: bool
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int

    class Config:
        from_attributes = True


class NotificationWithDetails(NotificationResponse):
    """Notification with related alert and listing details"""
    alert: Optional[Dict[str, Any]] = None
    listing: Optional[Dict[str, Any]] = None


# Notification Template Schemas
class NotificationTemplateBase(BaseModel):
    name: str = Field(..., max_length=100)
    notification_type: NotificationType
    language: str = Field("en", max_length=5)
    subject_template: Optional[str] = Field(None, max_length=200)
    title_template: str = Field(..., max_length=200)
    message_template: str
    html_template: Optional[str] = None
    variables: List[str] = []
    is_active: bool = True


class NotificationTemplateCreate(NotificationTemplateBase):
    pass


class NotificationTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    subject_template: Optional[str] = Field(None, max_length=200)
    title_template: Optional[str] = Field(None, max_length=200)
    message_template: Optional[str] = None
    html_template: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None


class NotificationTemplateResponse(NotificationTemplateBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Alert Matching Schemas
class AlertMatchResult(BaseModel):
    alert_id: int
    listing_id: int
    match_score: float = Field(..., ge=0.0, le=1.0)
    matched_criteria: List[str]
    notification_created: bool = False


class AlertMatchRunSummary(BaseModel):
    run_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    alerts_processed: int
    listings_checked: int
    matches_found: int
    notifications_created: int
    processing_time_seconds: Optional[float] = None
    error_message: Optional[str] = None


# Notification Statistics Schemas
class NotificationStats(BaseModel):
    total_notifications: int
    notifications_by_type: Dict[str, int]
    notifications_by_status: Dict[str, int]
    recent_notifications_24h: int
    failed_notifications_24h: int
    average_delivery_time_minutes: Optional[float] = None


class UserNotificationStats(BaseModel):
    user_id: int
    total_notifications: int
    unread_notifications: int
    notifications_last_7_days: int
    most_common_alert_type: Optional[str] = None


# Bulk Operations Schemas
class BulkNotificationCreate(BaseModel):
    notifications: List[NotificationCreate]
    send_immediately: bool = False


class BulkNotificationResponse(BaseModel):
    created_count: int
    failed_count: int
    created_ids: List[int]
    errors: List[str]


# Notification History Schemas
class NotificationHistoryFilter(BaseModel):
    notification_type: Optional[NotificationType] = None
    status: Optional[NotificationStatus] = None
    alert_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    is_read: Optional[bool] = None


class NotificationHistoryResponse(BaseModel):
    notifications: List[NotificationResponse]
    total_count: int
    unread_count: int
    page: int
    page_size: int
    total_pages: int


# Admin Monitoring Schemas
class NotificationSystemHealth(BaseModel):
    status: str  # healthy, warning, critical
    queue_size: int
    failed_notifications_last_hour: int
    average_processing_time_seconds: float
    last_successful_alert_run: Optional[datetime] = None
    active_workers: int
    system_load: float
    issues: List[str] = []


class NotificationDeliveryReport(BaseModel):
    period_start: datetime
    period_end: datetime
    total_sent: int
    delivery_rate: float
    open_rate: float
    click_rate: float
    bounce_rate: float
    delivery_times_by_type: Dict[str, float]
