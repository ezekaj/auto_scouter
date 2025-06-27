from app.models.base import engine, Base
from app.models.scout import Scout, Team, Match, ScoutReport, User, Alert
from app.models.automotive import (
    VehicleListing, VehicleImage, PriceHistory,
    ScrapingLog, ScrapingSession, DataQualityMetric
)
from app.models.notifications import (
    Notification, NotificationPreferences, NotificationTemplate,
    NotificationQueue, AlertMatchLog
)

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    create_tables()
