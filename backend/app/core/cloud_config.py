"""
Cloud Configuration for Production Deployment
Handles environment variables and cloud-specific settings
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import validator
import logging

logger = logging.getLogger(__name__)

class CloudSettings(BaseSettings):
    """Cloud deployment settings"""
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "production")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Database Configuration
    database_url: Optional[str] = os.getenv("DATABASE_URL")
    postgres_host: Optional[str] = os.getenv("PGHOST")
    postgres_port: Optional[str] = os.getenv("PGPORT", "5432")
    postgres_user: Optional[str] = os.getenv("PGUSER")
    postgres_password: Optional[str] = os.getenv("PGPASSWORD")
    postgres_database: Optional[str] = os.getenv("PGDATABASE")
    
    # Redis Configuration (for Celery)
    redis_url: Optional[str] = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("PORT", "8000"))
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    allowed_hosts: list = os.getenv("ALLOWED_HOSTS", "*").split(",")
    
    # Scraping Configuration
    scraping_interval_minutes: int = int(os.getenv("SCRAPING_INTERVAL_MINUTES", "5"))
    max_vehicles_per_scrape: int = int(os.getenv("MAX_VEHICLES_PER_SCRAPE", "50"))
    
    # Notification Configuration
    firebase_credentials_path: Optional[str] = os.getenv("FIREBASE_CREDENTIALS_PATH")
    firebase_project_id: Optional[str] = os.getenv("FIREBASE_PROJECT_ID")
    
    # Email Configuration (backup notifications)
    smtp_host: Optional[str] = os.getenv("SMTP_HOST")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: Optional[str] = os.getenv("SMTP_USER")
    smtp_password: Optional[str] = os.getenv("SMTP_PASSWORD")
    
    # Monitoring
    sentry_dsn: Optional[str] = os.getenv("SENTRY_DSN")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    @validator("database_url", pre=True)
    def build_database_url(cls, v, values):
        """Build database URL from individual components if not provided"""
        if v:
            return v
        
        # Build from individual components
        host = values.get("postgres_host")
        port = values.get("postgres_port", "5432")
        user = values.get("postgres_user")
        password = values.get("postgres_password")
        database = values.get("postgres_database")
        
        if all([host, user, password, database]):
            return f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        # Fallback to SQLite for development
        return "sqlite:///./app.db"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"
    
    @property
    def is_cloud_deployed(self) -> bool:
        """Check if deployed to cloud platform"""
        return bool(self.database_url and "postgresql" in self.database_url)
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }

# Global settings instance
cloud_settings = CloudSettings()

def get_cloud_settings() -> CloudSettings:
    """Get cloud settings instance"""
    return cloud_settings

def setup_logging():
    """Setup logging for cloud deployment"""
    log_level = getattr(logging, cloud_settings.log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    logger.info(f"Logging configured for {cloud_settings.environment} environment")

def get_database_url() -> str:
    """Get database URL for cloud deployment"""
    db_url = cloud_settings.database_url
    
    # Handle Railway's DATABASE_URL format
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    logger.info(f"Using database: {'PostgreSQL (cloud)' if 'postgresql' in db_url else 'SQLite (local)'}")
    return db_url

def get_cors_origins() -> list:
    """Get CORS origins for cloud deployment"""
    if cloud_settings.is_production:
        # Production CORS origins
        return [
            "https://your-frontend-domain.com",
            "capacitor://localhost",
            "ionic://localhost",
            "http://localhost",
            "http://localhost:3000",
            "http://localhost:8100"
        ]
    else:
        # Development CORS origins
        return ["*"]

def get_celery_broker_url() -> str:
    """Get Celery broker URL"""
    return cloud_settings.redis_url

def get_celery_result_backend() -> str:
    """Get Celery result backend URL"""
    return cloud_settings.redis_url

# Environment validation
def validate_cloud_environment():
    """Validate cloud environment configuration"""
    issues = []
    
    if cloud_settings.is_production:
        if not cloud_settings.database_url or "sqlite" in cloud_settings.database_url:
            issues.append("Production environment requires PostgreSQL database")
        
        if cloud_settings.secret_key == "your-secret-key-change-in-production":
            issues.append("SECRET_KEY must be changed for production")
        
        if not cloud_settings.redis_url or "localhost" in cloud_settings.redis_url:
            issues.append("Production environment requires cloud Redis instance")
    
    if issues:
        logger.warning("Cloud environment validation issues:")
        for issue in issues:
            logger.warning(f"  - {issue}")
    else:
        logger.info("Cloud environment validation passed")
    
    return len(issues) == 0
