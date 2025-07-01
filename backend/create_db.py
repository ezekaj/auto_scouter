import os
from app.models.base import engine, Base
from app.models.scout import Scout, Team, Match, ScoutReport, User, Alert
from app.models.automotive import (
    VehicleListing, VehicleImage, PriceHistory,
    ScrapingLog, ScrapingSession, DataQualityMetric, MultiSourceSession
)
from app.models.notifications import (
    Notification, NotificationPreferences, NotificationTemplate,
    NotificationQueue, AlertMatchLog
)

def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")

        # Test the connection by trying to connect
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1"))
            print(f"Database connection test successful: {result.fetchone()}")

    except Exception as e:
        print(f"Error creating tables: {e}")
        raise

if __name__ == "__main__":
    print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'Not set')}")
    print(f"REDIS_URL: {os.getenv('REDIS_URL', 'Not set')}")
    create_tables()
