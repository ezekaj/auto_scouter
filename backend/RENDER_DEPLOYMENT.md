# Auto Scouter Backend - Render Deployment Guide

## Automated Deployment (Recommended)

### Option 1: Deploy with render.yaml (Easiest)

1. **Go to [Render.com](https://render.com)** and sign up/login
2. **Click "New +" → "Blueprint"**
3. **Connect your GitHub repository** containing this code
4. **Select the repository** and branch (main)
5. **Render will automatically**:
   - Create the web service with correct configuration
   - Create PostgreSQL database
   - Set up environment variables
   - Deploy the application

The `render.yaml` file contains all necessary configuration.

## Manual Deployment (Alternative)

### 1. Create PostgreSQL Database First

1. **Go to Render Dashboard**
2. **Click "New +" → "PostgreSQL"**
3. **Configure database**:
   - **Name**: `auto-scouter-db`
   - **Database**: `auto_scouter`
   - **User**: `auto_scouter_user`
   - **Plan**: Free
4. **Create database** and note the connection string

### 2. Create Web Service

1. **Click "New +" → "Web Service"**
2. **Connect GitHub repository**
3. **Configure service**:
   - **Name**: `auto-scouter-backend`
   - **Runtime**: Python 3.11
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m uvicorn app.main_cloud:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
   - **Plan**: Free

### 3. Set Environment Variables

Add these in the Environment section:

```
ENVIRONMENT=production
SECRET_KEY=<generate-secure-key>
SCRAPING_INTERVAL_MINUTES=30
DATABASE_URL=<your-postgresql-connection-string>
```

### 4. Deploy and Test

1. **Deploy the service**
2. **Test the health endpoint**: `https://your-app.onrender.com/health`
3. **Verify API endpoints**:
   - `GET /api/v1/alerts/`
   - `POST /api/v1/alerts/`
   - `GET /api/v1/automotive/vehicles/simple`

## Expected Health Response

The health endpoint should return:

```json
{
    "status": "healthy",
    "environment": "production",
    "database": "healthy",
    "scraper": "running",
    "timestamp": "2025-07-09T...",
    "version": "2.0.0-alerts-enabled",
    "api_endpoints": {
        "alerts_get": "/api/v1/alerts/",
        "alerts_post": "/api/v1/alerts/",
        "vehicles": "/api/v1/automotive/vehicles/simple",
        "scraper_test": "/api/v1/scraper/autouno/test"
    },
    "features": ["AutoUno Scraper", "Alert System", "Database Integration"]
}
```

## Alternative Platforms

If Render doesn't work, try:

1. **Heroku**: Similar setup with Procfile
2. **DigitalOcean App Platform**: Good PostgreSQL integration
3. **Google Cloud Run**: Container-based deployment
4. **AWS ECS**: Enterprise-grade hosting

## Mobile App Configuration

Once deployed, update the mobile app's `.env` file:

```
VITE_API_URL=https://your-app.onrender.com/api/v1
VITE_WS_BASE_URL=wss://your-app.onrender.com/ws
```

## Testing Commands

```bash
# Test health endpoint
curl https://your-app.onrender.com/health

# Test alert creation
curl -X POST https://your-app.onrender.com/api/v1/alerts/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Alert", "make": "BMW", "max_price": 25000}'

# Test vehicle listings
curl https://your-app.onrender.com/api/v1/automotive/vehicles/simple?limit=5
```
