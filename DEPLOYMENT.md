# 🚀 Auto Scouter Deployment Guide

This comprehensive guide walks you through the complete deployment process for the Auto Scouter application to Railway cloud platform, including backend deployment, database setup, and mobile app configuration.

## 📋 Prerequisites

Before starting the deployment process, ensure you have:

- **Railway Account**: Sign up at [railway.app](https://railway.app)
- **Railway CLI**: Install via `npm install -g @railway/cli`
- **Git Repository**: Code pushed to GitHub
- **Node.js 18+**: For frontend build process
- **Python 3.11+**: For backend development
- **Android Studio**: For mobile app development (optional)

## 🏗️ Deployment Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub Repo   │    │   Railway       │    │   PostgreSQL    │
│   (Source)      │───►│   Backend       │◄──►│   Database      │
└─────────────────┘    │   (FastAPI)     │    │   (Managed)     │
                       └─────────────────┘    └─────────────────┘
                               │
                               ▼
                       ┌─────────────────┐
                       │   Mobile APK    │
                       │   (Generated)   │
                       └─────────────────┘
```

## 🎯 Phase 1: Backend Deployment to Railway

### Step 1: Prepare Railway Configuration

Create the necessary configuration files in your backend directory:

**1. Create `railway.json`:**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main_cloud:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**2. Create `Procfile`:**
```
web: uvicorn app.main_cloud:app --host 0.0.0.0 --port $PORT
```

**3. Ensure `requirements.txt` includes all dependencies:**
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
```

### Step 2: Create Cloud-Specific Application Entry Point

Create `app/main_cloud.py` for production deployment:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.cloud_config import get_cloud_settings
from app.models.cloud_base import init_cloud_db
from app.routers import auth, vehicles, alerts, system

# Initialize cloud settings
settings = get_cloud_settings()

# Create FastAPI app
app = FastAPI(
    title="Auto Scouter API",
    description="Vehicle listing and search platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
@app.on_event("startup")
async def startup_event():
    init_cloud_db()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.environment,
        "database_url": "configured"
    }

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(vehicles.router, prefix="/api/v1/vehicles", tags=["vehicles"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Auto Scouter API",
        "version": "1.0.0",
        "environment": settings.environment,
        "docs": "/docs"
    }
```

### Step 3: Configure Cloud Settings

Create `app/core/cloud_config.py`:

```python
from pydantic_settings import BaseSettings
from typing import Optional

class CloudSettings(BaseSettings):
    database_url: str
    secret_key: str
    environment: str = "production"
    
    class Config:
        env_file = ".env"
        extra = "forbid"

def get_cloud_settings() -> CloudSettings:
    return CloudSettings()
```

### Step 4: Set Up Database Models for Cloud

Create `app/models/cloud_base.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.cloud_config import get_cloud_settings

settings = get_cloud_settings()

# Create engine for PostgreSQL
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_cloud_db():
    """Initialize cloud database tables"""
    Base.metadata.create_all(bind=engine)

def get_cloud_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Step 5: Deploy to Railway

**1. Login to Railway:**
```bash
railway login
```

**2. Initialize Railway project:**
```bash
cd backend
railway init
# Select "Create new project"
# Choose a project name (e.g., "auto-scouter-backend")
```

**3. Add PostgreSQL database:**
```bash
railway add postgresql
```

**4. Deploy the backend:**
```bash
railway up --detach
```

**5. Set environment variables in Railway dashboard:**
- `DATABASE_URL`: Automatically set by Railway PostgreSQL service
- `SECRET_KEY`: Generate a secure secret key
- `ENVIRONMENT`: Set to "production"

### Step 6: Verify Backend Deployment

**1. Check deployment status:**
```bash
railway status
```

**2. View logs:**
```bash
railway logs
```

**3. Test health endpoint:**
```bash
curl https://your-app-name.up.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "production",
  "database_url": "configured"
}
```

## 🗄️ Phase 2: Database Migration

### Step 1: Create Migration Script

Create `migrate_to_cloud_db.py` in the backend directory:

```python
import os
import sys
from sqlalchemy import create_engine, text
from app.core.cloud_config import get_cloud_settings
from app.models.cloud_base import Base, init_cloud_db

def migrate_to_cloud():
    """Migrate local SQLite data to cloud PostgreSQL"""
    try:
        # Initialize cloud database
        print("Initializing cloud database...")
        init_cloud_db()
        print("✅ Cloud database initialized successfully")
        
        # Note: For production, you would implement actual data migration here
        # This is a placeholder for the migration logic
        
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_to_cloud()
    sys.exit(0 if success else 1)
```

### Step 2: Run Migration

**1. Set up local environment:**
```bash
cd backend
python -m venv migration_env
source migration_env/bin/activate
pip install -r requirements.txt
```

**2. Configure environment variables:**
Create `.env.migration`:
```bash
DATABASE_URL=postgresql://user:pass@host:port/db
SECRET_KEY=your-production-secret-key
```

**3. Run migration:**
```bash
python migrate_to_cloud_db.py
```

**Note**: The database schema will be automatically created when the application starts due to the `init_cloud_db()` call in the startup event.

## 📱 Phase 3: Mobile App Cloud Configuration

### Step 1: Update Frontend Environment

**1. Create `.env.production`:**
```bash
# API Configuration
VITE_API_URL=https://your-app-name.up.railway.app/api/v1
VITE_WS_BASE_URL=wss://your-app-name.up.railway.app/ws
VITE_API_TIMEOUT=10000

# Application Configuration
VITE_APP_NAME=Auto Scouter
VITE_APP_VERSION=1.0.0
VITE_APP_ENVIRONMENT=production

# Feature Flags
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_ERROR_REPORTING=true
VITE_ENABLE_PERFORMANCE_MONITORING=true

# Security Configuration
VITE_ENABLE_HTTPS_ONLY=true
VITE_ENABLE_STRICT_CSP=true
```

**2. Update regular `.env` file:**
```bash
VITE_API_URL=https://your-app-name.up.railway.app/api/v1
VITE_WS_BASE_URL=wss://your-app-name.up.railway.app/ws
VITE_APP_ENVIRONMENT=production
VITE_ENABLE_HTTPS_ONLY=true
```

### Step 2: Fix TypeScript Compilation Issues

**1. Remove unused imports and variables:**
- Remove references to non-existent components (e.g., `ApiTest`)
- Comment out or remove unused variables to avoid compilation errors
- Ensure all imports are valid and components exist

**2. Common fixes needed:**
```typescript
// Instead of unused variables, use underscore prefix or comment out
const _duration = endTime.getTime() - startTime.getTime();
// or
// const duration = endTime.getTime() - startTime.getTime();
```

### Step 3: Build Production APK

**1. Create build script `build_cloud_apk.sh`:**
```bash
#!/bin/bash
set -e

echo "🚀 Building Auto Scouter for Cloud Deployment"

# Load production environment
if [ -f .env.production ]; then
    export $(cat .env.production | xargs)
    echo "✅ Loaded production environment variables"
else
    echo "❌ .env.production file not found"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build the web app
echo "🔨 Building web application..."
npm run build

# Sync with Capacitor
echo "📱 Syncing with Capacitor..."
npx cap sync android

# Build Android APK
echo "🤖 Building Android APK..."
cd android
./gradlew assembleRelease
cd ..

# Copy APK to dist folder
mkdir -p dist/apk
cp android/app/build/outputs/apk/release/app-release.apk dist/apk/VehicleScout-cloud-release.apk

echo "✅ Build completed successfully!"
echo "📱 APK location: dist/apk/VehicleScout-cloud-release.apk"
```

**2. Make script executable and run:**
```bash
chmod +x build_cloud_apk.sh
./build_cloud_apk.sh
```

### Step 4: Test Mobile App

**1. Install APK on Android device:**
- Enable "Unknown Sources" in Android settings
- Transfer APK to device and install
- Launch the app and test connectivity

**2. Verify functionality:**
- User registration/login
- Vehicle search and filtering
- Alert creation and management
- Real-time updates

## ✅ Verification and Testing

### Backend Testing

**1. Health check:**
```bash
curl https://your-app-name.up.railway.app/health
```

**2. API documentation:**
Visit: `https://your-app-name.up.railway.app/docs`

**3. Test authentication:**
```bash
curl -X POST "https://your-app-name.up.railway.app/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","full_name":"Test User"}'
```

### Database Testing

**1. Check database connection:**
```bash
railway connect postgresql
```

**2. Verify tables were created:**
```sql
\dt
```

### Mobile App Testing

**1. Test API connectivity from mobile app**
**2. Verify user authentication flow**
**3. Test vehicle search functionality**
**4. Confirm alert creation and management**

## 🔧 Troubleshooting

### Common Backend Issues

**1. Build failures:**
- Check `requirements.txt` for missing dependencies
- Verify Python version compatibility
- Review Railway build logs

**2. Database connection issues:**
- Confirm `DATABASE_URL` environment variable
- Check PostgreSQL service status in Railway
- Verify database initialization

**3. Environment variable issues:**
- Set all required variables in Railway dashboard
- Use Railway CLI: `railway variables set KEY=value`

### Common Frontend Issues

**1. TypeScript compilation errors:**
- Remove unused imports and variables
- Fix component references
- Check type definitions

**2. API connection issues:**
- Verify backend URL in environment variables
- Check CORS configuration
- Test API endpoints manually

**3. APK build failures:**
- Ensure Android SDK is properly configured
- Check Capacitor configuration
- Review Gradle build logs

### Performance Optimization

**1. Backend optimization:**
- Enable database connection pooling
- Implement caching strategies
- Optimize database queries

**2. Frontend optimization:**
- Enable code splitting
- Implement lazy loading
- Optimize bundle size

## 📊 Monitoring and Maintenance

### Railway Dashboard

- Monitor deployment status
- View application logs
- Check resource usage
- Manage environment variables

### Health Monitoring

- Set up uptime monitoring
- Configure alerting for failures
- Monitor API response times
- Track error rates

### Database Maintenance

- Regular backups (Railway handles this automatically)
- Monitor database performance
- Optimize queries as needed
- Scale resources when necessary

## 🚀 Next Steps

After successful deployment:

1. **Configure custom domain** (optional)
2. **Set up Firebase for push notifications**
3. **Implement analytics and error reporting**
4. **Set up CI/CD pipeline for automated deployments**
5. **Configure monitoring and alerting**
6. **Plan for scaling and performance optimization**

---

**Congratulations! Your Auto Scouter application is now successfully deployed to the cloud! 🎉**

For additional support, refer to:
- [API Documentation](API_GUIDE.md)
- [Environment Configuration](ENVIRONMENT.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
