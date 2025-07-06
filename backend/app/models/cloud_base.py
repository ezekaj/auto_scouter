"""
Cloud-Optimized Database Configuration
Handles PostgreSQL for cloud deployment and SQLite for local development
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
import os

from app.core.cloud_config import get_cloud_settings

logger = logging.getLogger(__name__)
cloud_settings = get_cloud_settings()

def get_cloud_database_url():
    """Get database URL optimized for cloud deployment"""
    db_url = cloud_settings.database_url
    
    # Handle Railway's DATABASE_URL format
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    return db_url

# Create cloud-optimized database engine
DATABASE_URL = get_cloud_database_url()

if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration for local development
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
        pool_pre_ping=True
    )
    logger.info("🔧 Using SQLite database (local development)")
else:
    # PostgreSQL configuration for cloud deployment
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False,
        connect_args={
            "sslmode": "require" if cloud_settings.is_production else "prefer"
        }
    )
    logger.info("🌐 Using PostgreSQL database (cloud deployment)")

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_cloud_database():
    """Initialize database for cloud deployment"""
    try:
        logger.info("🔄 Initializing cloud database...")
        
        # Import all models to ensure they're registered
        from app.models import scout, automotive, notifications, comparison
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Cloud database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize cloud database: {e}")
        return False

def test_cloud_database_connection():
    """Test database connection for cloud deployment"""
    try:
        db = SessionLocal()
        try:
            # Test basic query
            result = db.execute("SELECT 1").fetchone()
            logger.info("✅ Cloud database connection test successful")
            return True
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Cloud database connection test failed: {e}")
        return False

def get_database_info():
    """Get database information for monitoring"""
    db_type = "PostgreSQL" if "postgresql" in DATABASE_URL else "SQLite"
    is_cloud = "postgresql" in DATABASE_URL
    
    return {
        "type": db_type,
        "is_cloud": is_cloud,
        "url_masked": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "local",
        "connection_pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else "N/A"
    }
