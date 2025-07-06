#!/usr/bin/env python3
"""
Cloud Database Migration Script
Migrates data from SQLite to PostgreSQL for cloud deployment
"""

import logging
import sys
from datetime import datetime
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CloudDatabaseMigrator:
    """Handles migration from SQLite to PostgreSQL"""
    
    def __init__(self):
        self.sqlite_url = "sqlite:///./app.db"
        self.migration_stats = {
            "users": 0,
            "vehicles": 0,
            "alerts": 0,
            "notifications": 0,
            "errors": []
        }
    
    def setup_cloud_database(self):
        """Setup cloud PostgreSQL database"""
        logger.info("🔧 Setting up cloud PostgreSQL database...")
        
        try:
            from app.models.cloud_base import init_cloud_database, test_cloud_database_connection
            
            # Test connection first
            if not test_cloud_database_connection():
                logger.error("❌ Cannot connect to cloud database")
                return False
            
            # Initialize database schema
            if not init_cloud_database():
                logger.error("❌ Failed to initialize cloud database")
                return False
            
            logger.info("✅ Cloud database setup completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Cloud database setup failed: {e}")
            return False
    
    def get_sqlite_data(self):
        """Extract data from SQLite database"""
        logger.info("📤 Extracting data from SQLite database...")
        
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from app.models.scout import User, Alert
            from app.models.automotive import VehicleListing
            from app.models.notifications import Notification
            
            # Connect to SQLite
            sqlite_engine = create_engine(self.sqlite_url, connect_args={"check_same_thread": False})
            SqliteSession = sessionmaker(bind=sqlite_engine)
            sqlite_db = SqliteSession()
            
            data = {}
            
            try:
                # Extract users
                users = sqlite_db.query(User).all()
                data['users'] = [self._serialize_model(user) for user in users]
                logger.info(f"📊 Found {len(data['users'])} users")
                
                # Extract vehicles
                vehicles = sqlite_db.query(VehicleListing).all()
                data['vehicles'] = [self._serialize_model(vehicle) for vehicle in vehicles]
                logger.info(f"📊 Found {len(data['vehicles'])} vehicles")
                
                # Extract alerts
                alerts = sqlite_db.query(Alert).all()
                data['alerts'] = [self._serialize_model(alert) for alert in alerts]
                logger.info(f"📊 Found {len(data['alerts'])} alerts")
                
                # Extract notifications
                notifications = sqlite_db.query(Notification).all()
                data['notifications'] = [self._serialize_model(notification) for notification in notifications]
                logger.info(f"📊 Found {len(data['notifications'])} notifications")
                
                logger.info("✅ SQLite data extraction completed")
                return data
                
            finally:
                sqlite_db.close()
                
        except Exception as e:
            logger.error(f"❌ SQLite data extraction failed: {e}")
            return None
    
    def _serialize_model(self, model) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dictionary"""
        data = {}
        for column in model.__table__.columns:
            value = getattr(model, column.name)
            # Handle datetime objects
            if isinstance(value, datetime):
                data[column.name] = value
            else:
                data[column.name] = value
        return data
    
    def migrate_data_to_cloud(self, data: Dict[str, List[Dict]]):
        """Migrate data to cloud PostgreSQL database"""
        logger.info("📥 Migrating data to cloud PostgreSQL...")
        
        try:
            from app.models.cloud_base import SessionLocal
            from app.models.scout import User, Alert
            from app.models.automotive import VehicleListing
            from app.models.notifications import Notification
            
            cloud_db = SessionLocal()
            
            try:
                # Migrate users
                logger.info("👥 Migrating users...")
                for user_data in data.get('users', []):
                    try:
                        # Check if user already exists
                        existing = cloud_db.query(User).filter(User.email == user_data['email']).first()
                        if not existing:
                            user = User(**user_data)
                            cloud_db.add(user)
                            self.migration_stats['users'] += 1
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to migrate user {user_data.get('email', 'unknown')}: {e}")
                        self.migration_stats['errors'].append(f"User migration: {e}")
                
                cloud_db.commit()
                logger.info(f"✅ Migrated {self.migration_stats['users']} users")
                
                # Migrate vehicles
                logger.info("🚗 Migrating vehicles...")
                for vehicle_data in data.get('vehicles', []):
                    try:
                        # Check if vehicle already exists
                        existing = cloud_db.query(VehicleListing).filter(
                            VehicleListing.external_id == vehicle_data['external_id']
                        ).first()
                        if not existing:
                            vehicle = VehicleListing(**vehicle_data)
                            cloud_db.add(vehicle)
                            self.migration_stats['vehicles'] += 1
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to migrate vehicle {vehicle_data.get('external_id', 'unknown')}: {e}")
                        self.migration_stats['errors'].append(f"Vehicle migration: {e}")
                
                cloud_db.commit()
                logger.info(f"✅ Migrated {self.migration_stats['vehicles']} vehicles")
                
                # Migrate alerts
                logger.info("🔔 Migrating alerts...")
                for alert_data in data.get('alerts', []):
                    try:
                        # Skip if user doesn't exist in cloud
                        user_exists = cloud_db.query(User).filter(User.id == alert_data['user_id']).first()
                        if user_exists:
                            alert = Alert(**alert_data)
                            cloud_db.add(alert)
                            self.migration_stats['alerts'] += 1
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to migrate alert {alert_data.get('id', 'unknown')}: {e}")
                        self.migration_stats['errors'].append(f"Alert migration: {e}")
                
                cloud_db.commit()
                logger.info(f"✅ Migrated {self.migration_stats['alerts']} alerts")
                
                # Migrate notifications
                logger.info("📧 Migrating notifications...")
                for notification_data in data.get('notifications', []):
                    try:
                        # Skip if user doesn't exist in cloud
                        user_exists = cloud_db.query(User).filter(User.id == notification_data['user_id']).first()
                        if user_exists:
                            notification = Notification(**notification_data)
                            cloud_db.add(notification)
                            self.migration_stats['notifications'] += 1
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to migrate notification {notification_data.get('id', 'unknown')}: {e}")
                        self.migration_stats['errors'].append(f"Notification migration: {e}")
                
                cloud_db.commit()
                logger.info(f"✅ Migrated {self.migration_stats['notifications']} notifications")
                
                logger.info("✅ Data migration to cloud completed")
                return True
                
            finally:
                cloud_db.close()
                
        except Exception as e:
            logger.error(f"❌ Cloud data migration failed: {e}")
            return False
    
    def verify_migration(self):
        """Verify migration was successful"""
        logger.info("🔍 Verifying migration...")
        
        try:
            from app.models.cloud_base import SessionLocal
            from app.models.scout import User, Alert
            from app.models.automotive import VehicleListing
            from app.models.notifications import Notification
            
            cloud_db = SessionLocal()
            
            try:
                # Count records in cloud database
                user_count = cloud_db.query(User).count()
                vehicle_count = cloud_db.query(VehicleListing).count()
                alert_count = cloud_db.query(Alert).count()
                notification_count = cloud_db.query(Notification).count()
                
                logger.info("📊 Cloud database verification:")
                logger.info(f"   Users: {user_count}")
                logger.info(f"   Vehicles: {vehicle_count}")
                logger.info(f"   Alerts: {alert_count}")
                logger.info(f"   Notifications: {notification_count}")
                
                # Check if we have data
                if vehicle_count > 0:
                    logger.info("✅ Migration verification successful")
                    return True
                else:
                    logger.warning("⚠️  No vehicles found in cloud database")
                    return False
                    
            finally:
                cloud_db.close()
                
        except Exception as e:
            logger.error(f"❌ Migration verification failed: {e}")
            return False
    
    def run_migration(self):
        """Run the complete migration process"""
        logger.info("🚀 Starting cloud database migration...")
        
        steps = [
            ("Setup Cloud Database", self.setup_cloud_database),
            ("Extract SQLite Data", lambda: self.get_sqlite_data() is not None),
            ("Migrate to Cloud", lambda: self.migrate_data_to_cloud(self.get_sqlite_data() or {})),
            ("Verify Migration", self.verify_migration)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n{'='*20} {step_name} {'='*20}")
            
            if not step_func():
                logger.error(f"❌ Step '{step_name}' failed")
                return False
        
        # Print migration summary
        logger.info(f"\n{'='*50}")
        logger.info("📊 MIGRATION SUMMARY")
        logger.info(f"{'='*50}")
        logger.info(f"✅ Users migrated: {self.migration_stats['users']}")
        logger.info(f"✅ Vehicles migrated: {self.migration_stats['vehicles']}")
        logger.info(f"✅ Alerts migrated: {self.migration_stats['alerts']}")
        logger.info(f"✅ Notifications migrated: {self.migration_stats['notifications']}")
        
        if self.migration_stats['errors']:
            logger.info(f"⚠️  Errors encountered: {len(self.migration_stats['errors'])}")
            for error in self.migration_stats['errors'][:5]:  # Show first 5 errors
                logger.info(f"   - {error}")
        
        logger.info("\n🎉 CLOUD DATABASE MIGRATION COMPLETED!")
        logger.info("🌐 Your data is now ready for 24/7 cloud operation!")
        
        return True

def main():
    """Main migration function"""
    print("🌐 Vehicle Scout - Cloud Database Migration")
    print("=" * 50)
    
    migrator = CloudDatabaseMigrator()
    
    if migrator.run_migration():
        print("\n✅ SUCCESS: Data migrated to cloud database!")
        print("🚀 Ready for Railway deployment!")
        sys.exit(0)
    else:
        print("\n❌ FAILED: Migration encountered errors")
        print("🔧 Check the logs above and fix any issues")
        sys.exit(1)

if __name__ == "__main__":
    main()
