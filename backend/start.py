#!/usr/bin/env python3
"""
Auto Scouter Backend Startup Script

This script initializes the database and starts the FastAPI server.
"""

import subprocess
import sys
import os
from pathlib import Path

def create_database():
    """Create database tables if they don't exist."""
    try:
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
        
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def start_server():
    """Start the FastAPI server."""
    try:
        print("🚀 Starting Auto Scouter backend server...")
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    """Main startup function."""
    print("🔧 Auto Scouter Backend Setup")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("app").exists():
        print("❌ Please run this script from the backend directory")
        sys.exit(1)
    
    # Create database
    if create_database():
        print("📊 Database ready!")
    else:
        print("❌ Database setup failed")
        sys.exit(1)
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
