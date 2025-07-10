# Database models
# Import all models to ensure proper SQLAlchemy relationship resolution

from .base import Base, get_db, engine, SessionLocal
from .scout import User, Scout, Team, Match, ScoutReport, Alert
from .automotive import (
    VehicleListing, VehicleImage, PriceHistory,
    ScrapingLog, ScrapingSession, DataQualityMetric, MultiSourceSession
)
from .notifications import (
    Notification, NotificationTemplate,
    NotificationQueue, AlertMatchLog
)
from .comparison import (
    VehicleComparison, VehicleComparisonItem, ComparisonTemplate,
    ComparisonShare, ComparisonView
)

__all__ = [
    'Base', 'get_db', 'engine', 'SessionLocal',
    'User', 'Scout', 'Team', 'Match', 'ScoutReport', 'Alert',
    'VehicleListing', 'VehicleImage', 'PriceHistory',
    'ScrapingLog', 'ScrapingSession', 'DataQualityMetric', 'MultiSourceSession',
    'Notification', 'NotificationTemplate',
    'NotificationQueue', 'AlertMatchLog',
    'VehicleComparison', 'VehicleComparisonItem', 'ComparisonTemplate',
    'ComparisonShare', 'ComparisonView'
]
