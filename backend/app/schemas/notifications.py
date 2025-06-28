"""
Pydantic schemas for notification-related API endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from app.models.notifications import NotificationType, NotificationStatus, NotificationFrequency


class NotificationResponse(BaseModel):
    """Response schema for notification data"""
    id: int
    user_id: int
    alert_id: Optional[int] = None
    listing_id: Optional[int] = None
    notification_type: NotificationType
    title: str
    message: str
    content_data: Optional[Dict[str, Any]] = None
    priority: int
    status: NotificationStatus
    is_read: bool = False
    created_at: datetime
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    retry_count: int = 0
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class NotificationPreferencesResponse(BaseModel):
    """Response schema for notification preferences"""
    id: int
    user_id: int
    email_enabled: bool = True
    email_frequency: NotificationFrequency = NotificationFrequency.IMMEDIATE
    push_enabled: bool = True
    push_frequency: NotificationFrequency = NotificationFrequency.IMMEDIATE
    in_app_enabled: bool = True
    sms_enabled: bool = False
    sms_frequency: NotificationFrequency = NotificationFrequency.IMMEDIATE
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"
    max_notifications_per_day: int = 10
    max_notifications_per_alert_per_day: int = 5
    digest_enabled: bool = False
    digest_frequency: NotificationFrequency = NotificationFrequency.DAILY
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationWithDetails(NotificationResponse):
    """Notification with additional details"""
    alert_name: Optional[str] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_year: Optional[int] = None
    vehicle_price: Optional[float] = None

class NotificationHistoryResponse(BaseModel):
    """Response for notification history"""
    notifications: List[NotificationWithDetails]
    total: int
    page: int
    limit: int
    has_more: bool

class UserNotificationStats(BaseModel):
    """User notification statistics"""
    total_notifications: int
    unread_notifications: int
    notifications_today: int
    notifications_this_week: int
    notifications_this_month: int
    most_active_alert: Optional[str] = None

class NotificationUpdate(BaseModel):
    """Schema for updating notifications"""
    is_read: Optional[bool] = None
    action: str = Field(..., pattern="^(mark_read|mark_unread|delete)$")

class NotificationSystemHealth(BaseModel):
    """System health for notifications"""
    email_service_status: str
    push_service_status: str
    sms_service_status: str
    queue_size: int
    failed_notifications_24h: int
    average_delivery_time_seconds: float

class AlertMatchRunSummary(BaseModel):
    """Summary of alert matching run"""
    run_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_alerts_checked: int
    total_vehicles_processed: int
    total_matches_found: int
    notifications_sent: int
    errors_encountered: int
    status: str

class AlertMatchResult(BaseModel):
    """Result of alert matching"""
    alert_id: int
    vehicle_id: int
    match_score: float
    matched_criteria: List[str]
    notification_sent: bool = False

class NotificationType(str, Enum):
    """Types of notifications"""
    VEHICLE_MATCH = "vehicle_match"
    PRICE_DROP = "price_drop"
    ALERT_CREATED = "alert_created"
    ALERT_TRIGGERED = "alert_triggered"
    SYSTEM_NOTIFICATION = "system_notification"

class NotificationPreferencesUpdate(BaseModel):
    """Schema for updating notification preferences"""
    email_enabled: Optional[bool] = None
    email_frequency: Optional[NotificationFrequency] = None
    push_enabled: Optional[bool] = None
    push_frequency: Optional[NotificationFrequency] = None
    in_app_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    sms_frequency: Optional[NotificationFrequency] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    timezone: Optional[str] = None
    language: Optional[str] = None
    max_notifications_per_day: Optional[int] = Field(None, ge=1, le=100)
    max_notifications_per_alert_per_day: Optional[int] = Field(None, ge=1, le=20)
    digest_enabled: Optional[bool] = None
    digest_frequency: Optional[NotificationFrequency] = None


class NotificationStats(BaseModel):
    """Schema for notification statistics"""
    total_notifications: int
    unread_notifications: int
    notifications_by_type: Dict[str, int]
    notifications_by_status: Dict[str, int]
    period_days: int


class NotificationTemplateResponse(BaseModel):
    """Response schema for notification templates"""
    id: int
    name: str
    notification_type: NotificationType
    language: str
    subject_template: Optional[str] = None
    title_template: Optional[str] = None
    message_template: str
    html_template: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationQueueResponse(BaseModel):
    """Response schema for notification queue items"""
    id: int
    notification_id: int
    priority: int = 2
    status: str = "queued"
    scheduled_for: Optional[datetime] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    worker_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationCreate(BaseModel):
    """Schema for creating notifications"""
    alert_id: Optional[int] = None
    listing_id: Optional[int] = None
    notification_type: NotificationType
    title: str
    message: str
    content_data: Optional[Dict[str, Any]] = None
    priority: int = Field(2, ge=1, le=5)


class NotificationBulkAction(BaseModel):
    """Schema for bulk notification actions"""
    notification_ids: List[int]
    action: str = Field(..., pattern="^(mark_read|mark_unread|delete)$")


class NotificationFilter(BaseModel):
    """Schema for notification filtering"""
    notification_type: Optional[NotificationType] = None
    status: Optional[NotificationStatus] = None
    is_read: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    alert_id: Optional[int] = None
    priority_min: Optional[int] = Field(None, ge=1, le=5)
    priority_max: Optional[int] = Field(None, ge=1, le=5)


class NotificationExport(BaseModel):
    """Schema for notification export requests"""
    format: str = Field("json", pattern="^(json|csv|excel)$")
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    include_content_data: bool = False
    filters: Optional[NotificationFilter] = None


class NotificationDigestPreview(BaseModel):
    """Schema for digest preview"""
    user_id: int
    date_from: datetime
    date_to: datetime
    notification_count: int
    alert_groups: Dict[str, int]
    preview_content: str


class NotificationDeliveryReport(BaseModel):
    """Schema for delivery reports"""
    notification_id: int
    delivery_attempts: int
    last_attempt_at: Optional[datetime] = None
    delivery_status: str
    delivery_details: Optional[Dict[str, Any]] = None
    bounce_reason: Optional[str] = None
    opened: bool = False
    clicked: bool = False
    unsubscribed: bool = False
