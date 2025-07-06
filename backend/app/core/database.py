# Database configuration and utilities
# This module provides database connection and session management

from app.models.base import get_db, engine, Base, SessionLocal

# Re-export for compatibility
__all__ = ['get_db', 'engine', 'Base', 'SessionLocal']
