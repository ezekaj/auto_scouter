#!/usr/bin/env python3
"""
Auto Scouter Notification System Setup Script

This script sets up the complete notification system including:
- Database migrations
- Default templates
- Celery workers
- Redis configuration
- Initial data
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        "fastapi",
        "sqlalchemy",
        "alembic",
        "celery",
        "redis",
        "psycopg2-binary",
        "python-multipart",
        "python-jose",
        "passlib",
        "bcrypt",
        "jinja2",
        "aiofiles"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing_packages)
    
    return len(missing_packages) == 0

def check_redis():
    """Check if Redis is running"""
    print("\n🔍 Checking Redis connection...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is running")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("Please start Redis server:")
        print("  - Windows: Download and run Redis from https://redis.io/download")
        print("  - macOS: brew install redis && brew services start redis")
        print("  - Linux: sudo systemctl start redis")
        return False

def check_database():
    """Check database connection and create if needed"""
    print("\n🔍 Checking database connection...")
    try:
        from app.core.database import engine
        from app.models.base import Base
        
        # Test connection
        with engine.connect() as conn:
            print("✅ Database connection successful")
        
        # Create tables
        print("🏗️ Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/updated")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        print("Please check your database configuration in app/core/config.py")
        return False

def setup_notification_templates():
    """Create default notification templates"""
    print("\n📧 Setting up notification templates...")
    
    try:
        from app.services.notification_service import NotificationService
        from app.core.database import get_db
        
        # Get database session
        db = next(get_db())
        notification_service = NotificationService(db)
        
        # Create default templates
        templates = [
            {
                "name": "new_car_alert",
                "subject": "🚗 New Car Alert: {{car.make}} {{car.model}}",
                "body": """
                Hi {{user.username}},
                
                A new car matching your alert "{{alert.name}}" has been found!
                
                🚗 **{{car.make}} {{car.model}}** ({{car.year}})
                💰 **Price:** €{{car.price}}
                📍 **Location:** {{car.city}}
                🔗 **View Details:** {{car.url}}
                
                Best regards,
                Auto Scouter Team
                """,
                "template_type": "email"
            },
            {
                "name": "price_drop_alert",
                "subject": "💰 Price Drop Alert: {{car.make}} {{car.model}}",
                "body": """
                Hi {{user.username}},
                
                Great news! The price for a car you're watching has dropped!
                
                🚗 **{{car.make}} {{car.model}}** ({{car.year}})
                💰 **New Price:** €{{car.price}} (was €{{car.old_price}})
                💸 **You save:** €{{car.price_difference}}
                📍 **Location:** {{car.city}}
                🔗 **View Details:** {{car.url}}
                
                Don't miss this opportunity!
                
                Best regards,
                Auto Scouter Team
                """,
                "template_type": "email"
            },
            {
                "name": "weekly_summary",
                "subject": "📊 Weekly Car Alert Summary",
                "body": """
                Hi {{user.username}},
                
                Here's your weekly summary of car alerts:
                
                📈 **This Week:**
                - {{stats.new_cars}} new cars found
                - {{stats.price_drops}} price drops
                - {{stats.active_alerts}} active alerts
                
                🔥 **Top Matches:**
                {% for car in top_matches %}
                - {{car.make}} {{car.model}} ({{car.year}}) - €{{car.price}}
                {% endfor %}
                
                🔗 **Manage your alerts:** {{dashboard_url}}
                
                Best regards,
                Auto Scouter Team
                """,
                "template_type": "email"
            }
        ]
        
        for template_data in templates:
            notification_service.create_template(template_data)
            print(f"✅ Created template: {template_data['name']}")
        
        print("✅ Notification templates setup complete")
        return True
        
    except Exception as e:
        print(f"❌ Template setup failed: {e}")
        return False

def setup_celery_workers():
    """Setup and start Celery workers"""
    print("\n⚙️ Setting up Celery workers...")
    
    try:
        # Create celery configuration if it doesn't exist
        celery_config = """
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "auto_scouter",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.notification_tasks", "app.tasks.scraper_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "process-notifications": {
            "task": "app.tasks.notification_tasks.process_pending_notifications",
            "schedule": 60.0,  # Every minute
        },
        "scrape-cars": {
            "task": "app.tasks.scraper_tasks.scrape_all_sources",
            "schedule": 300.0,  # Every 5 minutes
        },
        "cleanup-old-notifications": {
            "task": "app.tasks.notification_tasks.cleanup_old_notifications",
            "schedule": 3600.0,  # Every hour
        },
    },
)
"""
        
        with open("celery_app.py", "w") as f:
            f.write(celery_config)
        
        print("✅ Celery configuration created")
        
        # Note: In production, you would start workers as separate processes
        print("ℹ️ To start Celery workers, run:")
        print("  celery -A celery_app worker --loglevel=info")
        print("  celery -A celery_app beat --loglevel=info")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery setup failed: {e}")
        return False

def create_sample_data():
    """Create sample data for testing"""
    print("\n🎯 Creating sample data...")
    
    try:
        from app.services.auth_service import AuthService
        from app.services.alert_service import AlertService
        from app.core.database import get_db
        
        db = next(get_db())
        auth_service = AuthService(db)
        alert_service = AlertService(db)
        
        # Create sample user
        sample_user = {
            "username": "demo_user",
            "email": "demo@autoscouter.com",
            "password": "demo123"
        }
        
        try:
            user = auth_service.create_user(sample_user)
            print(f"✅ Created sample user: {user.username}")
            
            # Create sample alert
            sample_alert = {
                "name": "BMW 3 Series Alert",
                "description": "Looking for a BMW 3 Series under €25,000",
                "make": "BMW",
                "model": "3 Series",
                "max_price": 25000,
                "min_year": 2015,
                "city": "Munich",
                "is_active": True
            }
            
            alert = alert_service.create_alert(user.id, sample_alert)
            print(f"✅ Created sample alert: {alert.name}")
            
        except Exception as e:
            if "already exists" in str(e).lower():
                print("ℹ️ Sample data already exists")
            else:
                raise e
        
        return True
        
    except Exception as e:
        print(f"❌ Sample data creation failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Auto Scouter Notification System Setup")
    print("=" * 50)
    
    # Check all dependencies
    if not check_dependencies():
        print("❌ Dependency check failed")
        return False
    
    # Check Redis
    if not check_redis():
        print("❌ Redis check failed")
        return False
    
    # Setup database
    if not check_database():
        print("❌ Database setup failed")
        return False
    
    # Setup notification templates
    if not setup_notification_templates():
        print("❌ Template setup failed")
        return False
    
    # Setup Celery
    if not setup_celery_workers():
        print("❌ Celery setup failed")
        return False
    
    # Create sample data
    if not create_sample_data():
        print("❌ Sample data creation failed")
        return False
    
    print("\n🎉 Notification system setup completed successfully!")
    print("=" * 50)
    print("\n📋 Next steps:")
    print("1. Start the FastAPI server: uvicorn app.main:app --reload")
    print("2. Start Celery worker: celery -A celery_app worker --loglevel=info")
    print("3. Start Celery beat: celery -A celery_app beat --loglevel=info")
    print("4. Visit http://localhost:8000/docs for API documentation")
    print("5. Test notifications with the sample user (demo@autoscouter.com)")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
