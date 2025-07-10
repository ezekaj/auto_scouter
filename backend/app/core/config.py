from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "Auto Scouter"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database - Use environment variable if available, fallback to local
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/auto_scouter")
    # Fallback to SQLite for development if PostgreSQL is not available
    SQLITE_FALLBACK: bool = True

    # Redis/Celery - Use environment variables if available
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Email Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "true").lower() == "true"
    SMTP_SSL: bool = os.getenv("SMTP_SSL", "false").lower() == "true"
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@autoscouter.com")
    EMAIL_FROM_NAME: str = os.getenv("EMAIL_FROM_NAME", "Auto Scouter")
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
    EMAIL_TEST_MODE: bool = os.getenv("EMAIL_TEST_MODE", "true").lower() == "true"

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_TO_FILE: bool = os.getenv("LOG_TO_FILE", "true").lower() == "true"
    LOG_JSON_FORMAT: bool = os.getenv("LOG_JSON_FORMAT", "false").lower() == "true"
    LOG_MAX_SIZE: int = int(os.getenv("LOG_MAX_SIZE", "10485760"))  # 10MB
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # Push Notification Configuration
    FIREBASE_CREDENTIALS_PATH: str = ""
    PUSH_NOTIFICATION_ENABLED: bool = False

    # CORS - Allow development, production, and mobile app origins
    ALLOWED_HOSTS: List[str] = [
        # Development origins
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        # Mobile app origins (Capacitor)
        "capacitor://localhost",
        "ionic://localhost",
        "https://localhost",
        "http://localhost",
        # Production origins (add your production URLs here)
        "https://vehiclescout.app",
        "https://www.vehiclescout.app",
        "https://auto-scouter.herokuapp.com",
        "https://auto-scouter.railway.app",
        # Allow all origins for development (remove in production)
        "*"
    ]

    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Notification Settings
    MAX_NOTIFICATIONS_PER_USER_PER_DAY: int = 50
    NOTIFICATION_BATCH_SIZE: int = 100
    ALERT_MATCHING_INTERVAL_SECONDS: int = 300  # 5 minutes
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60

    # Webhook Security
    WEBHOOK_SECRET: str = ""

    # Scraper Configuration
    SCRAPER_SCRAPING_ENABLED: bool = True
    SCRAPER_SCRAPING_INTERVAL_HOURS: int = 8
    SCRAPER_MAX_PAGES_TO_SCRAPE: int = 50
    SCRAPER_REQUEST_DELAY: float = 2.0
    SCRAPER_ENABLE_DEDUPLICATION: bool = True
    SCRAPER_KEEP_HISTORICAL_DATA: bool = True
    SCRAPER_DATA_RETENTION_DAYS: int = 365
    SCRAPER_ENABLE_METRICS: bool = True
    SCRAPER_LOG_LEVEL: str = "INFO"

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }


settings = Settings()
