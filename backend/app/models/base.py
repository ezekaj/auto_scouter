from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def create_database_engine():
    """Create database engine with fallback to SQLite"""
    try:
        # Try PostgreSQL first
        engine = create_engine(
            settings.DATABASE_URL,
            echo=False,  # Set to True for SQL debugging
        )
        # Test connection
        engine.connect()
        logger.info("✅ Connected to PostgreSQL database")
        return engine
    except Exception as e:
        logger.warning(f"⚠️  PostgreSQL connection failed: {e}")
        if getattr(settings, 'SQLITE_FALLBACK', True):
            logger.info("🔄 Falling back to SQLite database")
            sqlite_url = "sqlite:///./auto_scouter.db"
            engine = create_engine(
                sqlite_url,
                echo=False,
                connect_args={"check_same_thread": False}  # SQLite specific
            )
            return engine
        else:
            raise e

engine = create_database_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
