"""
Cloud-Optimized FastAPI Application
Designed for 24/7 cloud deployment with automated scraping
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager
import os
import asyncio

# Cloud configuration
from app.core.cloud_config import (
    get_cloud_settings, 
    setup_logging, 
    validate_cloud_environment,
    get_cors_origins
)

# Core imports
from app.routers import automotive, alerts, notifications
from app.models.base import engine, Base
from app.background_scraper import BackgroundScraper

# Initialize cloud settings and logging
cloud_settings = get_cloud_settings()
setup_logging()
logger = logging.getLogger(__name__)

# Global scraper instance for cloud deployment
background_scraper = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management for cloud deployment"""
    global background_scraper
    
    logger.info("🚀 Starting Vehicle Scout Cloud Application")
    logger.info(f"Environment: {cloud_settings.environment}")
    logger.info(f"Database: {'PostgreSQL (cloud)' if cloud_settings.is_cloud_deployed else 'SQLite (local)'}")
    
    # Validate cloud environment
    validate_cloud_environment()
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    # Start background scraper for cloud deployment
    if cloud_settings.is_production:
        try:
            background_scraper = BackgroundScraper()
            # Start scraper in background task
            asyncio.create_task(start_cloud_scraper())
            logger.info("✅ Background scraper started for cloud deployment")
        except Exception as e:
            logger.error(f"❌ Failed to start background scraper: {e}")
    
    logger.info("🎯 Application startup completed")
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down application")
    if background_scraper:
        background_scraper.stop()
        logger.info("✅ Background scraper stopped")

async def start_cloud_scraper():
    """Start the background scraper for continuous cloud operation"""
    global background_scraper
    
    if not background_scraper:
        return
    
    logger.info("🔄 Starting continuous cloud scraping...")
    
    while True:
        try:
            await background_scraper.run_scraping_cycle()
            logger.info(f"✅ Scraping cycle completed, sleeping for {cloud_settings.scraping_interval_minutes} minutes")
            
            # Sleep for configured interval (default 5 minutes)
            await asyncio.sleep(cloud_settings.scraping_interval_minutes * 60)
            
        except Exception as e:
            logger.error(f"❌ Scraping cycle failed: {e}")
            # Wait 1 minute before retrying on error
            await asyncio.sleep(60)

# Create FastAPI application with cloud configuration
app = FastAPI(
    title="Vehicle Scout - Cloud API",
    description="Automated car scouting system with 24/7 cloud operation",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not cloud_settings.is_production else None,
    redoc_url="/redoc" if not cloud_settings.is_production else None
)

# Configure CORS for cloud deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Health check endpoint for cloud platforms
@app.get("/health")
async def health_check():
    """Health check endpoint for cloud deployment monitoring"""
    try:
        # Check database connectivity
        from app.models.base import SessionLocal
        db = SessionLocal()
        try:
            db.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        finally:
            db.close()
        
        # Check scraper status
        scraper_status = "running" if background_scraper and background_scraper.running else "stopped"
        
        return {
            "status": "healthy",
            "environment": cloud_settings.environment,
            "database": db_status,
            "scraper": scraper_status,
            "timestamp": "2025-07-06T20:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2025-07-06T20:00:00Z"
            }
        )

# Cloud-specific endpoints
@app.get("/cloud/status")
async def cloud_status():
    """Get cloud deployment status"""
    return {
        "cloud_deployed": cloud_settings.is_cloud_deployed,
        "environment": cloud_settings.environment,
        "database_type": "PostgreSQL" if cloud_settings.is_cloud_deployed else "SQLite",
        "scraping_interval": f"{cloud_settings.scraping_interval_minutes} minutes",
        "max_vehicles_per_scrape": cloud_settings.max_vehicles_per_scrape
    }

@app.get("/cloud/scraper/status")
async def scraper_status():
    """Get background scraper status"""
    if not background_scraper:
        return {"status": "not_initialized"}
    
    return {
        "running": background_scraper.running,
        "last_run": background_scraper.last_run.isoformat() if background_scraper.last_run else None,
        "interval_minutes": cloud_settings.scraping_interval_minutes
    }

@app.post("/cloud/scraper/trigger")
async def trigger_scraping():
    """Manually trigger a scraping cycle (for testing)"""
    if not background_scraper:
        raise HTTPException(status_code=503, detail="Background scraper not initialized")
    
    try:
        await background_scraper.run_scraping_cycle()
        return {"message": "Scraping cycle triggered successfully"}
    except Exception as e:
        logger.error(f"Manual scraping trigger failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

# Include API routers (simplified for single-user mode)
app.include_router(automotive.router, prefix="/api/v1/automotive", tags=["vehicles"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with cloud deployment information"""
    return {
        "message": "Vehicle Scout Cloud API",
        "version": "1.0.0",
        "environment": cloud_settings.environment,
        "cloud_deployed": cloud_settings.is_cloud_deployed,
        "docs_url": "/docs" if not cloud_settings.is_production else "disabled",
        "health_check": "/health"
    }

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for cloud deployment"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": "2025-07-06T20:00:00Z"
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    # Run with cloud configuration
    uvicorn.run(
        "app.main_cloud:app",
        host=cloud_settings.api_host,
        port=cloud_settings.api_port,
        reload=not cloud_settings.is_production,
        log_level=cloud_settings.log_level.lower()
    )
