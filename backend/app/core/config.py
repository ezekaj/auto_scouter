from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Auto Scouter"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/auto_scouter"
    # Fallback to SQLite for development if PostgreSQL is not available
    SQLITE_FALLBACK: bool = True

    # Redis/Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    EMAIL_FROM: str = "noreply@autoscouter.com"
    EMAIL_FROM_NAME: str = "Auto Scouter"

    # Push Notification Configuration
    FIREBASE_CREDENTIALS_PATH: str = ""
    PUSH_NOTIFICATION_ENABLED: bool = False

    # CORS
    ALLOWED_HOSTS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
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

    class Config:
        env_file = ".env"


settings = Settings()
