# 🔧 Auto Scouter Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the Auto Scouter application across development, deployment, and production environments.

## 🚨 Quick Diagnostics

### Health Check Commands

```bash
# Backend health check
curl https://auto-scouter-backend-production.up.railway.app/health

# Local backend health check
curl http://localhost:8000/health

# Check Railway deployment status
railway status

# View Railway logs
railway logs
```

### Common Status Responses

**✅ Healthy Response:**
```json
{
  "status": "healthy",
  "environment": "production",
  "database_url": "configured"
}
```

**❌ Unhealthy Indicators:**
- HTTP 500/503 errors
- Connection timeouts
- Database connection failures
- Missing environment variables

## 🖥️ Backend Issues

### 1. Database Connection Problems

#### Symptoms
- `sqlalchemy.exc.OperationalError`
- "Connection refused" errors
- "Database does not exist" errors
- Slow query responses

#### Solutions

**Local SQLite Issues:**
```bash
# Check if database file exists
ls -la auto_scouter.db

# Recreate database
rm auto_scouter.db
python -c "from app.models.database import init_db; init_db()"

# Check database permissions
chmod 664 auto_scouter.db
```

**PostgreSQL Connection Issues:**
```bash
# Test connection manually
psql $DATABASE_URL

# Check environment variable
echo $DATABASE_URL

# Verify Railway PostgreSQL service
railway connect postgresql
```

**Connection Pool Issues:**
```python
# Add to database configuration
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300
)
```

### 2. Authentication Problems

#### Symptoms
- "Invalid token" errors
- "Token expired" messages
- 401 Unauthorized responses
- Login failures

#### Solutions

**JWT Token Issues:**
```bash
# Check secret key is set
echo $SECRET_KEY

# Generate new secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Verify token expiration settings
echo $ACCESS_TOKEN_EXPIRE_MINUTES
```

**Password Hashing Issues:**
```python
# Test password hashing
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash("test_password")
print(pwd_context.verify("test_password", hashed))
```

### 3. Import and Module Errors

#### Symptoms
- `ModuleNotFoundError`
- `ImportError`
- "No module named 'app'" errors

#### Solutions

**Python Path Issues:**
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Add current directory to path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Install in development mode
pip install -e .
```

**Virtual Environment Issues:**
```bash
# Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. API Endpoint Errors

#### Symptoms
- 404 Not Found for valid endpoints
- 422 Unprocessable Entity
- CORS errors
- Slow response times

#### Solutions

**Router Configuration:**
```python
# Check router inclusion in main.py
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

# Verify endpoint definitions
@router.get("/vehicles")
async def get_vehicles():
    pass
```

**CORS Configuration:**
```python
# Update CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5. Background Task Issues

#### Symptoms
- Scraping not working
- Tasks not executing
- Redis connection errors
- Celery worker failures

#### Solutions

**Redis Connection:**
```bash
# Test Redis connection
redis-cli ping

# Check Redis URL
echo $REDIS_URL

# Start Redis locally
redis-server
```

**Celery Configuration:**
```bash
# Start Celery worker
celery -A app.tasks.celery worker --loglevel=info

# Check Celery status
celery -A app.tasks.celery status

# Purge failed tasks
celery -A app.tasks.celery purge
```

## 🌐 Frontend Issues

### 1. Build and Compilation Errors

#### Symptoms
- TypeScript compilation errors
- Vite build failures
- Missing dependencies
- Import resolution errors

#### Solutions

**TypeScript Errors:**
```bash
# Check TypeScript configuration
npx tsc --noEmit

# Fix common issues
# Remove unused imports
# Add proper type definitions
# Fix component references
```

**Dependency Issues:**
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for version conflicts
npm ls

# Update dependencies
npm update
```

**Build Configuration:**
```javascript
// vite.config.ts
export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    target: 'es2020',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
        },
      },
    },
  },
});
```

### 2. API Connection Issues

#### Symptoms
- Network errors
- CORS blocked requests
- Timeout errors
- 404 errors for API calls

#### Solutions

**Environment Variables:**
```bash
# Check API URL configuration
echo $VITE_API_URL

# Verify environment file is loaded
cat .env
```

**Network Configuration:**
```javascript
// Check API client configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

**CORS Issues:**
```javascript
// Add credentials to requests
const response = await fetch(url, {
  method: 'POST',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(data),
});
```

### 3. Mobile App Issues

#### Symptoms
- APK build failures
- Capacitor sync errors
- Android build errors
- App crashes on device

#### Solutions

**Capacitor Configuration:**
```bash
# Reinstall Capacitor
npm uninstall @capacitor/core @capacitor/cli @capacitor/android
npm install @capacitor/core @capacitor/cli @capacitor/android

# Clean and sync
npx cap clean android
npx cap sync android
```

**Android Build Issues:**
```bash
# Clean Android build
cd android
./gradlew clean
cd ..

# Check Android SDK
echo $ANDROID_HOME

# Update Gradle wrapper
cd android
./gradlew wrapper --gradle-version=7.6
```

**APK Signing Issues:**
```bash
# Generate debug keystore
keytool -genkey -v -keystore debug.keystore -storepass android -alias androiddebugkey -keypass android -keyalg RSA -keysize 2048 -validity 10000
```

## 🚀 Deployment Issues

### 1. Railway Deployment Problems

#### Symptoms
- Build failures on Railway
- Deployment timeouts
- Service not starting
- Environment variable issues

#### Solutions

**Build Configuration:**
```json
// railway.json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main_cloud:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100
  }
}
```

**Environment Variables:**
```bash
# Set variables via CLI
railway variables set SECRET_KEY=your-secret-key
railway variables set DATABASE_URL=postgresql://...

# Check variables
railway variables
```

**Deployment Logs:**
```bash
# View build logs
railway logs --deployment

# View runtime logs
railway logs

# Follow logs in real-time
railway logs --follow
```

### 2. Database Migration Issues

#### Symptoms
- Migration script failures
- Schema creation errors
- Data loss during migration
- Connection timeouts

#### Solutions

**Migration Script Debugging:**
```python
# Add detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test connection before migration
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("Database connection successful")
except Exception as e:
    print(f"Database connection failed: {e}")
```

**Schema Issues:**
```python
# Force table creation
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Check existing tables
inspector = inspect(engine)
tables = inspector.get_table_names()
print("Existing tables:", tables)
```

### 3. Performance Issues

#### Symptoms
- Slow API responses
- High memory usage
- Database query timeouts
- Frontend loading delays

#### Solutions

**Database Optimization:**
```python
# Add database indexes
class VehicleListing(Base):
    __tablename__ = "vehicle_listings"
    
    id = Column(Integer, primary_key=True, index=True)
    make = Column(String, index=True)  # Add index
    price = Column(Integer, index=True)  # Add index
```

**API Optimization:**
```python
# Add response caching
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

@cache(expire=300)  # Cache for 5 minutes
async def get_vehicles():
    return vehicles
```

**Frontend Optimization:**
```javascript
// Implement lazy loading
const VehicleList = lazy(() => import('./components/VehicleList'));

// Add loading states
const { data, isLoading, error } = useQuery('vehicles', fetchVehicles);
```

## 🔍 Debugging Tools

### Backend Debugging

**Logging Configuration:**
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

**Database Query Debugging:**
```python
# Enable SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Log slow queries
engine = create_engine(DATABASE_URL, echo=True)
```

### Frontend Debugging

**Console Debugging:**
```javascript
// Add debug logs
console.log('API Response:', response);
console.error('Error:', error);

// Network debugging
fetch(url).then(response => {
  console.log('Status:', response.status);
  console.log('Headers:', response.headers);
  return response.json();
});
```

**React DevTools:**
```bash
# Install React DevTools browser extension
# Use React Query DevTools
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

function App() {
  return (
    <>
      <YourApp />
      <ReactQueryDevtools initialIsOpen={false} />
    </>
  );
}
```

## 📞 Getting Help

### Information to Gather

When reporting issues, include:

1. **Environment details:**
   - Operating system
   - Node.js/Python versions
   - Browser version (for frontend issues)

2. **Error messages:**
   - Full error stack traces
   - Console logs
   - Network request details

3. **Steps to reproduce:**
   - Exact commands run
   - Configuration used
   - Expected vs actual behavior

### Useful Commands

```bash
# System information
node --version
python --version
npm --version

# Environment variables
env | grep VITE_
env | grep DATABASE_URL

# Network debugging
curl -v https://your-api-url/health
ping your-domain.com

# Process information
ps aux | grep python
ps aux | grep node
```

### Log Collection

```bash
# Backend logs
tail -f app.log

# Railway logs
railway logs --follow

# Frontend build logs
npm run build 2>&1 | tee build.log

# System logs (Linux)
journalctl -u your-service -f
```

## 🔄 Recovery Procedures

### Database Recovery

```bash
# Backup current database
pg_dump $DATABASE_URL > backup.sql

# Restore from backup
psql $DATABASE_URL < backup.sql

# Reset database (destructive)
python -c "from app.models.database import Base, engine; Base.metadata.drop_all(engine); Base.metadata.create_all(engine)"
```

### Service Recovery

```bash
# Restart Railway service
railway restart

# Redeploy application
railway up --detach

# Rollback deployment
railway rollback
```

### Cache Clearing

```bash
# Clear Redis cache
redis-cli FLUSHALL

# Clear browser cache
# Use browser developer tools

# Clear npm cache
npm cache clean --force

# Clear pip cache
pip cache purge
```

---

**If you continue to experience issues, please check the [API documentation](API_GUIDE.md) or [deployment guide](DEPLOYMENT.md) for additional information.**
