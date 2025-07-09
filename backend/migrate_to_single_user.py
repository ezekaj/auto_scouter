#!/usr/bin/env python3
"""
Database Migration Script: Multi-User to Single-User Mode
=========================================================

This script migrates the Auto Scouter database from multi-user mode to single-user mode by:
1. Removing user_id foreign key constraints
2. Dropping user-related tables
3. Updating existing data to work without user associations

⚠️  WARNING: This migration is IRREVERSIBLE. Make sure to backup your database first!
"""

import sys
import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.models.base import get_db, engine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def backup_database():
    """Create a backup of the current database"""
    logger.info("🔄 Creating database backup...")
    
    try:
        if settings.DATABASE_URL.startswith("sqlite"):
            # For SQLite, copy the file
            import shutil
            db_file = settings.DATABASE_URL.replace("sqlite:///", "")
            backup_file = f"{db_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_file, backup_file)
            logger.info(f"✅ SQLite backup created: {backup_file}")
        else:
            # For PostgreSQL, suggest pg_dump
            logger.warning("⚠️  For PostgreSQL, please create a backup using pg_dump before proceeding")
            logger.info("Example: pg_dump your_database > backup.sql")
            
        return True
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")
        return False

def check_existing_data():
    """Check what data exists in user-related tables"""
    logger.info("🔍 Checking existing data...")
    
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            # Check if user-related tables exist
            user_tables = ['users', 'oauth_accounts', 'notification_preferences']
            existing_user_tables = [table for table in user_tables if table in tables]
            
            if existing_user_tables:
                logger.info(f"📊 Found user-related tables: {existing_user_tables}")
                
                # Count users
                if 'users' in tables:
                    result = conn.execute(text("SELECT COUNT(*) FROM users"))
                    user_count = result.scalar()
                    logger.info(f"👥 Total users: {user_count}")
                
                # Count alerts
                if 'alerts' in tables:
                    result = conn.execute(text("SELECT COUNT(*) FROM alerts"))
                    alert_count = result.scalar()
                    logger.info(f"🚨 Total alerts: {alert_count}")
                
                # Count notifications
                if 'notifications' in tables:
                    result = conn.execute(text("SELECT COUNT(*) FROM notifications"))
                    notification_count = result.scalar()
                    logger.info(f"📬 Total notifications: {notification_count}")
            else:
                logger.info("✅ No user-related tables found - database may already be in single-user mode")
                
        return True
    except Exception as e:
        logger.error(f"❌ Data check failed: {e}")
        return False

def migrate_alerts_table():
    """Remove user_id from alerts table"""
    logger.info("🔄 Migrating alerts table...")
    
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            
            if 'alerts' not in inspector.get_table_names():
                logger.info("ℹ️  Alerts table doesn't exist, skipping...")
                return True
            
            # Check if user_id column exists
            columns = [col['name'] for col in inspector.get_columns('alerts')]
            
            if 'user_id' in columns:
                logger.info("🗑️  Removing user_id column from alerts table...")
                
                if settings.DATABASE_URL.startswith("sqlite"):
                    # SQLite doesn't support DROP COLUMN, need to recreate table
                    conn.execute(text("""
                        CREATE TABLE alerts_new AS 
                        SELECT id, name, description, make, model, min_price, max_price, 
                               min_year, max_year, max_mileage, fuel_type, transmission, 
                               body_type, city, region, location_radius, min_engine_power, 
                               max_engine_power, condition, is_active, notification_frequency, 
                               last_triggered, trigger_count, max_notifications_per_day, 
                               created_at, updated_at
                        FROM alerts
                    """))
                    
                    conn.execute(text("DROP TABLE alerts"))
                    conn.execute(text("ALTER TABLE alerts_new RENAME TO alerts"))
                    
                else:
                    # PostgreSQL supports DROP COLUMN
                    conn.execute(text("ALTER TABLE alerts DROP COLUMN IF EXISTS user_id"))
                
                conn.commit()
                logger.info("✅ Alerts table migrated successfully")
            else:
                logger.info("ℹ️  user_id column not found in alerts table")
                
        return True
    except Exception as e:
        logger.error(f"❌ Alerts migration failed: {e}")
        return False

def migrate_notifications_table():
    """Remove user_id from notifications table"""
    logger.info("🔄 Migrating notifications table...")
    
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            
            if 'notifications' not in inspector.get_table_names():
                logger.info("ℹ️  Notifications table doesn't exist, skipping...")
                return True
            
            # Check if user_id column exists
            columns = [col['name'] for col in inspector.get_columns('notifications')]
            
            if 'user_id' in columns:
                logger.info("🗑️  Removing user_id column from notifications table...")
                
                if settings.DATABASE_URL.startswith("sqlite"):
                    # SQLite doesn't support DROP COLUMN, need to recreate table
                    conn.execute(text("""
                        CREATE TABLE notifications_new AS 
                        SELECT id, alert_id, listing_id, notification_type, status, title, 
                               message, content_data, sent_at, delivered_at, opened_at, 
                               clicked_at, error_message, retry_count, max_retries, 
                               created_at, updated_at, expires_at, external_id, priority, is_read
                        FROM notifications
                    """))
                    
                    conn.execute(text("DROP TABLE notifications"))
                    conn.execute(text("ALTER TABLE notifications_new RENAME TO notifications"))
                    
                else:
                    # PostgreSQL supports DROP COLUMN
                    conn.execute(text("ALTER TABLE notifications DROP COLUMN IF EXISTS user_id"))
                
                conn.commit()
                logger.info("✅ Notifications table migrated successfully")
            else:
                logger.info("ℹ️  user_id column not found in notifications table")
                
        return True
    except Exception as e:
        logger.error(f"❌ Notifications migration failed: {e}")
        return False

def drop_user_tables():
    """Drop user-related tables"""
    logger.info("🗑️  Dropping user-related tables...")
    
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            tables_to_drop = ['oauth_accounts', 'notification_preferences', 'users']
            
            for table in tables_to_drop:
                if table in inspector.get_table_names():
                    logger.info(f"🗑️  Dropping table: {table}")
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                else:
                    logger.info(f"ℹ️  Table {table} doesn't exist, skipping...")
            
            conn.commit()
            logger.info("✅ User-related tables dropped successfully")
                
        return True
    except Exception as e:
        logger.error(f"❌ Failed to drop user tables: {e}")
        return False

def recreate_tables():
    """Recreate tables with new schema"""
    logger.info("🔄 Recreating tables with simplified schema...")
    
    try:
        # Import models to ensure they're registered
        from app.models import scout, automotive, notifications, comparison
        from app.models.base import Base
        
        # Create all tables with new schema
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Tables recreated with simplified schema")
        return True
    except Exception as e:
        logger.error(f"❌ Table recreation failed: {e}")
        return False

def main():
    """Main migration function"""
    logger.info("🚀 Starting migration to single-user mode...")
    logger.info("=" * 60)
    
    # Step 1: Backup database
    if not backup_database():
        logger.error("❌ Migration aborted due to backup failure")
        return False
    
    # Step 2: Check existing data
    if not check_existing_data():
        logger.error("❌ Migration aborted due to data check failure")
        return False
    
    # Step 3: Migrate alerts table
    if not migrate_alerts_table():
        logger.error("❌ Migration aborted due to alerts migration failure")
        return False
    
    # Step 4: Migrate notifications table
    if not migrate_notifications_table():
        logger.error("❌ Migration aborted due to notifications migration failure")
        return False
    
    # Step 5: Drop user-related tables
    if not drop_user_tables():
        logger.error("❌ Migration aborted due to table drop failure")
        return False
    
    # Step 6: Recreate tables with new schema
    if not recreate_tables():
        logger.error("❌ Migration aborted due to table recreation failure")
        return False
    
    logger.info("=" * 60)
    logger.info("🎉 Migration to single-user mode completed successfully!")
    logger.info("✅ Your Auto Scouter database is now in single-user mode")
    logger.info("🔄 Please restart your application to use the new schema")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
