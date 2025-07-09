# 🔧 Environment Configuration Guide

This guide provides detailed information about configuring environment variables for the Auto Scouter application in different environments (development, staging, production).

## 📋 Overview

Auto Scouter uses environment variables to configure different aspects of the application:
- **Backend**: Database connections, security settings, API configurations
- **Frontend**: API endpoints, feature flags, build configurations
- **Deployment**: Cloud platform settings, service configurations

## 🏗️ Environment Structure

```
auto_scouter/
├── backend/
│   ├── .env                    # Local development
│   ├── .env.example           # Template file
│   ├── .env.production        # Production overrides
│   └── .env.migration         # Migration-specific settings
└── frontend/
    ├── .env                   # Local development
    ├── .env.example          # Template file
    ├── .env.production       # Production build
    └── .env.local            # Local overrides (git-ignored)
```

## 🖥️ Backend Environment Variables

### Core Configuration

#### Database Settings
```bash
# Development (SQLite)
DATABASE_URL=sqlite:///./auto_scouter.db

# Production (PostgreSQL on Railway)
DATABASE_URL=postgresql://postgres:password@host:port/database

# Test Environment
TEST_DATABASE_URL=sqlite:///./test.db
```

#### Security Configuration
```bash
# JWT Secret Key (REQUIRED)
SECRET_KEY=your-super-secret-key-here-change-in-production

# JWT Algorithm
ALGORITHM=HS256

# Token Expiration (in minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Password Hashing
BCRYPT_ROUNDS=12
```

#### Application Settings
```bash
# Environment Type
ENVIRONMENT=development  # development, staging, production

# Debug Mode
DEBUG=true  # false in production

# Logging Level
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# API Configuration
API_V1_PREFIX=/api/v1
DOCS_URL=/docs
REDOC_URL=/redoc
```

### Web Scraping Configuration

```bash
# Scraping Intervals
SCRAPING_INTERVAL_MINUTES=5
SCRAPING_TIMEOUT_SECONDS=30

# Scraping Limits
MAX_VEHICLES_PER_SCRAPE=50
MAX_CONCURRENT_SCRAPERS=3

# User Agent for Scraping
USER_AGENT=Mozilla/5.0 (compatible; AutoScouterBot/1.0)

# Scraping Sources
ENABLE_AUTOSCOUT24=true
ENABLE_MOBILE_DE=false
```

### Background Tasks Configuration

```bash
# Redis Configuration (for Celery)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Task Settings
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=["json"]
CELERY_TIMEZONE=UTC
```

### Email Configuration (Optional)

```bash
# SMTP Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TLS=true

# Email Templates
FROM_EMAIL=noreply@autoscouter.com
FROM_NAME=Auto Scouter
```

### CORS Configuration

```bash
# Allowed Origins (comma-separated)
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://yourdomain.com

# CORS Settings
ALLOW_CREDENTIALS=true
ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
ALLOW_HEADERS=*
```

### Rate Limiting

```bash
# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600  # seconds

# API Key Rate Limits
API_KEY_RATE_LIMIT=1000
API_KEY_RATE_WINDOW=3600
```

## 🌐 Frontend Environment Variables

### API Configuration

```bash
# Backend API URL
VITE_API_URL=http://localhost:8000/api/v1
VITE_API_BASE_URL=http://localhost:8000/api/v1  # Alternative name

# WebSocket URL
VITE_WS_BASE_URL=ws://localhost:8000/ws

# API Timeouts (milliseconds)
VITE_API_TIMEOUT=10000
VITE_WS_TIMEOUT=5000
```

### Application Configuration

```bash
# App Information
VITE_APP_NAME=Auto Scouter
VITE_APP_VERSION=1.0.0
VITE_APP_DESCRIPTION=Vehicle listing and search platform

# Environment
VITE_APP_ENVIRONMENT=development  # development, staging, production

# Build Information
VITE_BUILD_TIMESTAMP=2024-01-15T10:00:00Z
VITE_GIT_COMMIT=abc123def
```

### Feature Flags

```bash
# Core Features
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_ERROR_REPORTING=false
VITE_ENABLE_PERFORMANCE_MONITORING=false

# UI Features
VITE_ENABLE_DARK_MODE=true
VITE_ENABLE_NOTIFICATIONS=true
VITE_ENABLE_OFFLINE_MODE=true

# Development Features
VITE_ENABLE_DEBUG_PANEL=false
VITE_ENABLE_MOCK_DATA=false
```

### Security Configuration

```bash
# Security Headers
VITE_ENABLE_HTTPS_ONLY=false  # true in production
VITE_ENABLE_STRICT_CSP=false  # true in production

# Content Security Policy
VITE_CSP_SCRIPT_SRC=self
VITE_CSP_STYLE_SRC=self unsafe-inline
VITE_CSP_IMG_SRC=self data: https:
```

### External Services

```bash
# Google Analytics
VITE_GOOGLE_ANALYTICS_ID=GA-XXXXXXXXX

# Sentry Error Reporting
VITE_SENTRY_DSN=https://your-sentry-dsn

# Firebase Configuration
VITE_FIREBASE_API_KEY=your-firebase-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123456789:web:abcdef123456
```

### Build Configuration

```bash
# Build Settings
VITE_BUILD_TARGET=es2020
VITE_BUILD_MINIFY=true
VITE_BUILD_SOURCEMAP=false  # true in development

# Bundle Analysis
VITE_ANALYZE_BUNDLE=false
VITE_BUNDLE_SIZE_LIMIT=500  # KB

# Cache Configuration
VITE_CACHE_VERSION=1.0.0
VITE_SW_CACHE_NAME=auto-scouter-v1
```

## 🌍 Environment-Specific Configurations

### Development Environment

**Backend (.env):**
```bash
DATABASE_URL=sqlite:///./auto_scouter.db
SECRET_KEY=dev-secret-key-not-for-production
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
SCRAPING_INTERVAL_MINUTES=10
RATE_LIMIT_ENABLED=false
```

**Frontend (.env):**
```bash
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_BASE_URL=ws://localhost:8000/ws
VITE_APP_ENVIRONMENT=development
VITE_ENABLE_DEBUG_PANEL=true
VITE_ENABLE_MOCK_DATA=false
VITE_ENABLE_HTTPS_ONLY=false
```

### Production Environment

**Backend (Railway Environment Variables):**
```bash
DATABASE_URL=postgresql://postgres:***@mainline.proxy.rlwy.net:37278/railway
SECRET_KEY=super-secure-production-key-256-bits
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://yourdomain.com
SCRAPING_INTERVAL_MINUTES=5
RATE_LIMIT_ENABLED=true
```

**Frontend (.env.production):**
```bash
VITE_API_URL=https://auto-scouter-backend-production.up.railway.app/api/v1
VITE_WS_BASE_URL=wss://auto-scouter-backend-production.up.railway.app/ws
VITE_APP_ENVIRONMENT=production
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_ERROR_REPORTING=true
VITE_ENABLE_HTTPS_ONLY=true
VITE_ENABLE_STRICT_CSP=true
```

### Staging Environment

**Backend (.env.staging):**
```bash
DATABASE_URL=postgresql://staging-db-url
SECRET_KEY=staging-secret-key
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://staging.yourdomain.com
SCRAPING_INTERVAL_MINUTES=15
RATE_LIMIT_ENABLED=true
```

**Frontend (.env.staging):**
```bash
VITE_API_URL=https://staging-api.yourdomain.com/api/v1
VITE_WS_BASE_URL=wss://staging-api.yourdomain.com/ws
VITE_APP_ENVIRONMENT=staging
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_ERROR_REPORTING=true
VITE_ENABLE_HTTPS_ONLY=true
```

## 🔐 Security Best Practices

### Secret Management

1. **Never commit secrets to version control**
2. **Use different secrets for each environment**
3. **Rotate secrets regularly**
4. **Use environment-specific secret management tools**

### Secret Generation

```bash
# Generate secure secret key (Python)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate secure secret key (OpenSSL)
openssl rand -base64 32

# Generate UUID for API keys
python -c "import uuid; print(str(uuid.uuid4()))"
```

### Environment Variable Validation

**Backend validation (Pydantic):**
```python
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    secret_key: str
    database_url: str
    
    @validator('secret_key')
    def secret_key_must_be_strong(cls, v):
        if len(v) < 32:
            raise ValueError('Secret key must be at least 32 characters')
        return v
```

## 🛠️ Setup Instructions

### 1. Backend Setup

```bash
cd backend

# Copy example file
cp .env.example .env

# Edit with your values
nano .env

# Validate configuration
python -c "from app.core.config import get_settings; print(get_settings())"
```

### 2. Frontend Setup

```bash
cd frontend

# Copy example file
cp .env.example .env

# Edit with your values
nano .env

# Validate configuration
npm run build
```

### 3. Railway Deployment

```bash
# Set environment variables
railway variables set SECRET_KEY=your-secret-key
railway variables set ENVIRONMENT=production

# Deploy
railway up
```

## 🔍 Troubleshooting

### Common Issues

**1. Missing environment variables:**
```bash
# Check if variable is set
echo $VARIABLE_NAME

# List all environment variables
env | grep VITE_
```

**2. Invalid database URL:**
```bash
# Test database connection
python -c "from sqlalchemy import create_engine; engine = create_engine('your-db-url'); print(engine.execute('SELECT 1').scalar())"
```

**3. CORS issues:**
- Check `ALLOWED_ORIGINS` includes your frontend URL
- Verify protocol (http vs https)
- Check port numbers

### Validation Scripts

**Backend validation:**
```python
# validate_env.py
import os
from app.core.config import get_settings

def validate_backend_env():
    try:
        settings = get_settings()
        print("✅ Backend environment valid")
        return True
    except Exception as e:
        print(f"❌ Backend environment invalid: {e}")
        return False

if __name__ == "__main__":
    validate_backend_env()
```

**Frontend validation:**
```javascript
// validate-env.js
const requiredVars = [
  'VITE_API_URL',
  'VITE_APP_ENVIRONMENT'
];

const missing = requiredVars.filter(var => !process.env[var]);

if (missing.length > 0) {
  console.error('❌ Missing environment variables:', missing);
  process.exit(1);
} else {
  console.log('✅ Frontend environment valid');
}
```

## 📚 Additional Resources

- [Railway Environment Variables](https://docs.railway.app/develop/variables)
- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)
- [FastAPI Settings Management](https://fastapi.tiangolo.com/advanced/settings/)
- [Pydantic Settings](https://pydantic-docs.helpmanual.io/usage/settings/)

---

**For more information, see the [deployment guide](DEPLOYMENT.md) or [troubleshooting guide](TROUBLESHOOTING.md).**
