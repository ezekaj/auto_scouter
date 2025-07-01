#!/usr/bin/env python3
"""
Database Migration Script for Multi-Source Scraper Enhancement

This script migrates the existing database schema to support multi-source scraping
with enhanced data quality tracking and duplicate detection.
"""

import os
import sys
from sqlalchemy import text, inspect
from app.models.base import engine, Base
from app.models.automotive import (
    VehicleListing, VehicleImage, PriceHistory,
    ScrapingLog, ScrapingSession, DataQualityMetric, MultiSourceSession
)
from app.models.scout import Scout, Team, Match, ScoutReport, User, Alert
from app.models.notifications import (
    Notification, NotificationPreferences, NotificationTemplate,
    NotificationQueue, AlertMatchLog
)

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception:
        return False

def check_table_exists(table_name):
    """Check if a table exists"""
    try:
        inspector = inspect(engine)
        return table_name in inspector.get_table_names()
    except Exception:
        return False

def add_column_if_not_exists(table_name, column_name, column_definition):
    """Add a column to a table if it doesn't exist"""
    if not check_column_exists(table_name, column_name):
        try:
            with engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"))
                conn.commit()
            print(f"✅ Added column {column_name} to {table_name}")
            return True
        except Exception as e:
            print(f"❌ Error adding column {column_name} to {table_name}: {e}")
            return False
    else:
        print(f"ℹ️  Column {column_name} already exists in {table_name}")
        return True

def create_index_if_not_exists(index_name, table_name, columns):
    """Create an index if it doesn't exist"""
    try:
        with engine.connect() as conn:
            # Try to create the index, ignore if it already exists
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns})"))
            conn.commit()
        print(f"✅ Created index {index_name}")
        return True
    except Exception as e:
        print(f"❌ Error creating index {index_name}: {e}")
        return False

def migrate_vehicle_listings():
    """Migrate vehicle_listings table for multi-source support"""
    print("🔄 Migrating vehicle_listings table...")
    
    # Add new columns for multi-source support
    migrations = [
        ("source_country", "VARCHAR(3) DEFAULT 'IT'"),
        ("data_quality_score", "FLOAT DEFAULT 0.0"),
        ("duplicate_of", "INTEGER"),
        ("is_duplicate", "BOOLEAN DEFAULT FALSE"),
        ("confidence_score", "FLOAT DEFAULT 1.0"),
    ]
    
    success = True
    for column_name, column_def in migrations:
        if not add_column_if_not_exists("vehicle_listings", column_name, column_def):
            success = False
    
    # Update source_website column to remove default and make it indexed
    if check_column_exists("vehicle_listings", "source_website"):
        try:
            with engine.connect() as conn:
                # Update existing records that might have NULL source_website
                conn.execute(text("""
                    UPDATE vehicle_listings 
                    SET source_website = 'gruppoautouno' 
                    WHERE source_website IS NULL OR source_website = ''
                """))
                conn.commit()
            print("✅ Updated existing source_website values")
        except Exception as e:
            print(f"❌ Error updating source_website values: {e}")
            success = False
    
    # Create new indexes
    indexes = [
        ("idx_source_website_new", "vehicle_listings", "source_website, is_active"),
        ("idx_source_country_new", "vehicle_listings", "source_country, source_website"),
        ("idx_duplicates_new", "vehicle_listings", "is_duplicate, duplicate_of"),
        ("idx_data_quality_new", "vehicle_listings", "data_quality_score, confidence_score"),
        ("idx_external_source_new", "vehicle_listings", "external_id, source_website"),
    ]
    
    for index_name, table_name, columns in indexes:
        if not create_index_if_not_exists(index_name, table_name, columns):
            success = False
    
    return success

def migrate_scraping_sessions():
    """Migrate scraping_sessions table for multi-source support"""
    print("🔄 Migrating scraping_sessions table...")
    
    # Add new columns
    migrations = [
        ("source_country", "VARCHAR(3) DEFAULT 'IT'"),
        ("session_type", "VARCHAR(20) DEFAULT 'single'"),
        ("total_vehicles_skipped", "INTEGER DEFAULT 0"),
        ("total_duplicates_found", "INTEGER DEFAULT 0"),
    ]
    
    success = True
    for column_name, column_def in migrations:
        if not add_column_if_not_exists("scraping_sessions", column_name, column_def):
            success = False
    
    return success

def create_multi_source_sessions_table():
    """Create the new multi_source_sessions table"""
    print("🔄 Creating multi_source_sessions table...")
    
    if not check_table_exists("multi_source_sessions"):
        try:
            # Create all tables (this will create only missing tables)
            Base.metadata.create_all(bind=engine)
            print("✅ Created multi_source_sessions table")
            return True
        except Exception as e:
            print(f"❌ Error creating multi_source_sessions table: {e}")
            return False
    else:
        print("ℹ️  multi_source_sessions table already exists")
        return True

def run_migration():
    """Run the complete database migration"""
    print("🚀 Starting database migration for multi-source scraper support...")
    print("=" * 60)
    
    success = True
    
    # Step 1: Migrate vehicle_listings table
    if not migrate_vehicle_listings():
        success = False
    
    print()
    
    # Step 2: Migrate scraping_sessions table
    if not migrate_scraping_sessions():
        success = False
    
    print()
    
    # Step 3: Create new multi_source_sessions table
    if not create_multi_source_sessions_table():
        success = False
    
    print()
    print("=" * 60)
    
    if success:
        print("✅ Database migration completed successfully!")
        print("🎉 Multi-source scraper database schema is ready!")
    else:
        print("❌ Database migration completed with errors!")
        print("⚠️  Please check the error messages above and resolve any issues.")
    
    return success

if __name__ == "__main__":
    try:
        success = run_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"💥 Fatal error during migration: {e}")
        sys.exit(1)
