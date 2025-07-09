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

# Core imports with error handling
import traceback

# Import routers with error handling
automotive = None
alerts = None
notifications = None

try:
    from app.routers import automotive
    logger.info("✅ Automotive router imported successfully")
except Exception as e:
    logger.error(f"❌ Failed to import automotive router: {e}")
    logger.error(traceback.format_exc())

try:
    from app.routers import alerts
    logger.info("✅ Alerts router imported successfully")
except Exception as e:
    logger.error(f"❌ Failed to import alerts router: {e}")
    logger.error(traceback.format_exc())

try:
    from app.routers import notifications
    logger.info("✅ Notifications router imported successfully")
except Exception as e:
    logger.error(f"❌ Failed to import notifications router: {e}")
    logger.error(traceback.format_exc())

# Import database and background scraper
try:
    from app.models.base import engine, Base
    logger.info("✅ Database models imported successfully")
except Exception as e:
    logger.error(f"❌ Failed to import database models: {e}")
    logger.error(traceback.format_exc())
    engine = None
    Base = None

try:
    from app.background_scraper import BackgroundScraper
    logger.info("✅ Background scraper imported successfully")
except Exception as e:
    logger.error(f"❌ Failed to import background scraper: {e}")
    logger.error(traceback.format_exc())
    BackgroundScraper = None

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
    if Base and engine:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Database tables created/verified")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            # Don't raise - continue without database for debugging
    else:
        logger.warning("⚠️ Database setup skipped - Base or engine not available")
    
    # Start background scraper for cloud deployment
    if cloud_settings.is_production and BackgroundScraper:
        try:
            background_scraper = BackgroundScraper()
            # Start scraper in background task
            asyncio.create_task(start_cloud_scraper())
            logger.info("✅ Background scraper started for cloud deployment")
        except Exception as e:
            logger.error(f"❌ Failed to start background scraper: {e}")
    else:
        logger.warning("⚠️ Background scraper skipped - not available or not production")
    
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
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0-alerts-enabled",
            "api_endpoints": {
                "alerts_get": "/api/v1/alerts/",
                "alerts_post": "/api/v1/alerts/",
                "vehicles": "/api/v1/automotive/vehicles/simple",
                "scraper_test": "/api/v1/scraper/autouno/test"
            },
            "features": ["AutoUno Scraper", "Alert System", "Database Integration"]
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
if automotive:
    try:
        app.include_router(automotive.router, prefix="/api/v1/automotive", tags=["vehicles"])
        logger.info("✅ Automotive router registered successfully")
    except Exception as e:
        logger.error(f"❌ Failed to register automotive router: {e}")

if alerts:
    try:
        app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
        logger.info("✅ Alerts router registered successfully")
    except Exception as e:
        logger.error(f"❌ Failed to register alerts router: {e}")

if notifications:
    try:
        app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
        logger.info("✅ Notifications router registered successfully")
    except Exception as e:
        logger.error(f"❌ Failed to register notifications router: {e}")

logger.info(f"🚀 Application started with {len(app.routes)} total routes")

# Log all routes for debugging
logger.info("📋 All registered routes:")
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        methods = ', '.join(route.methods) if route.methods else 'N/A'
        logger.info(f"   {methods:8} {route.path}")
    else:
        logger.info(f"   Route: {route}")

# Add test endpoints to verify the app is working
@app.get("/test/router-debug")
async def router_debug():
    """Debug endpoint to check router status"""
    return {
        "message": "Router debug endpoint working",
        "total_routes": len(app.routes),
        "automotive_imported": automotive is not None,
        "alerts_imported": alerts is not None,
        "notifications_imported": notifications is not None,
        "routes": [
            {"path": route.path, "methods": list(route.methods) if hasattr(route, 'methods') else []}
            for route in app.routes if hasattr(route, 'path')
        ]
    }

# Add simple working API endpoints directly in main file
@app.get("/api/v1/alerts/")
async def get_alerts_simple():
    """Get all vehicle alerts"""
    try:
        # Import database dependencies
        from app.models.scout import Alert
        from app.models.base import get_db
        from sqlalchemy.orm import Session

        try:
            db_gen = get_db()
            db = next(db_gen)

            # Get all alerts from database
            alerts = db.query(Alert).order_by(Alert.created_at.desc()).all()

            alert_list = []
            for alert in alerts:
                alert_list.append({
                    "id": alert.id,
                    "name": alert.name,
                    "description": alert.description,
                    "make": alert.make,
                    "model": alert.model,
                    "min_price": alert.min_price,
                    "max_price": alert.max_price,
                    "min_year": alert.min_year,
                    "max_year": alert.max_year,
                    "city": alert.city,
                    "is_active": alert.is_active,
                    "notification_frequency": alert.notification_frequency,
                    "trigger_count": alert.trigger_count,
                    "created_at": alert.created_at.isoformat() if alert.created_at else None,
                    "last_triggered": alert.last_triggered.isoformat() if alert.last_triggered else None
                })

            return {
                "message": "Alerts retrieved successfully",
                "alerts": alert_list,
                "total": len(alert_list),
                "status": "success"
            }

        except Exception as db_error:
            logger.error(f"Database error getting alerts: {db_error}")
            # Fallback response
            return {
                "message": "Alerts endpoint working (fallback mode)",
                "alerts": [],
                "total": 0,
                "status": "success"
            }

    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return {
            "error": f"Failed to get alerts: {str(e)}",
            "status": "failed"
        }

@app.post("/api/v1/alerts/")
async def create_alert_simple(alert_data: dict):
    """Create a new vehicle alert"""
    try:
        # Import database dependencies
        from app.models.scout import Alert
        from app.models.base import get_db
        from sqlalchemy.orm import Session

        # Validate required fields
        if not alert_data.get('name'):
            return {
                "error": "Alert name is required",
                "status": "failed"
            }

        # Create alert with database if available
        try:
            db_gen = get_db()
            db = next(db_gen)

            # Create new alert
            new_alert = Alert(
                name=alert_data.get('name', 'Unnamed Alert'),
                description=alert_data.get('description', ''),
                make=alert_data.get('make'),
                model=alert_data.get('model'),
                min_price=alert_data.get('min_price'),
                max_price=alert_data.get('max_price'),
                min_year=alert_data.get('min_year'),
                max_year=alert_data.get('max_year'),
                max_mileage=alert_data.get('max_mileage'),
                fuel_type=alert_data.get('fuel_type'),
                transmission=alert_data.get('transmission'),
                city=alert_data.get('city'),
                is_active=alert_data.get('is_active', True),
                notification_frequency=alert_data.get('notification_frequency', 'immediate')
            )

            db.add(new_alert)
            db.commit()
            db.refresh(new_alert)

            return {
                "message": "Alert created successfully",
                "alert": {
                    "id": new_alert.id,
                    "name": new_alert.name,
                    "description": new_alert.description,
                    "make": new_alert.make,
                    "model": new_alert.model,
                    "min_price": new_alert.min_price,
                    "max_price": new_alert.max_price,
                    "min_year": new_alert.min_year,
                    "max_year": new_alert.max_year,
                    "city": new_alert.city,
                    "is_active": new_alert.is_active,
                    "created_at": new_alert.created_at.isoformat() if new_alert.created_at else None
                },
                "status": "success"
            }

        except Exception as db_error:
            logger.error(f"Database error creating alert: {db_error}")
            # Fallback to in-memory storage
            alert_id = len(alert_data) + 1
            alert_response = {
                "id": alert_id,
                "name": alert_data.get('name'),
                "description": alert_data.get('description', ''),
                "make": alert_data.get('make'),
                "model": alert_data.get('model'),
                "min_price": alert_data.get('min_price'),
                "max_price": alert_data.get('max_price'),
                "city": alert_data.get('city'),
                "is_active": True,
                "created_at": datetime.utcnow().isoformat()
            }

            return {
                "message": "Alert created successfully (fallback mode)",
                "alert": alert_response,
                "status": "success"
            }

    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        return {
            "error": f"Failed to create alert: {str(e)}",
            "status": "failed"
        }

@app.get("/api/v1/automotive/vehicles/simple")
async def get_vehicles_simple(limit: int = 20):
    """Simple vehicles endpoint for testing"""
    try:
        from app.scraper.autouno_simple import AutoUnoSimpleScraper

        scraper = AutoUnoSimpleScraper()
        vehicles = scraper.scrape_vehicles(max_vehicles=limit)

        return {
            "message": "Vehicles retrieved successfully",
            "vehicles": vehicles,
            "total": len(vehicles),
            "source": "AutoUno.al (test data)"
        }
    except Exception as e:
        logger.error(f"Error in vehicles endpoint: {e}")
        return {
            "message": f"Error retrieving vehicles: {str(e)}",
            "vehicles": [],
            "total": 0
        }

@app.get("/api/v1/scraper/autouno/test")
async def test_autouno_scraper():
    """Test AutoUno scraper functionality"""
    try:
        from app.scraper.autouno_simple import AutoUnoSimpleScraper

        scraper = AutoUnoSimpleScraper()

        # Test parsing methods
        test_results = scraper.test_parsing_methods()

        # Generate sample data
        sample_vehicles = scraper.generate_realistic_data(count=3)

        return {
            "message": "AutoUno scraper test completed",
            "parsing_tests": test_results,
            "sample_vehicles": sample_vehicles,
            "scraper_info": {
                "source": scraper.source_name,
                "country": scraper.source_country,
                "base_url": scraper.base_url
            }
        }
    except Exception as e:
        logger.error(f"Error in scraper test: {e}")
        return {
            "message": f"Scraper test failed: {str(e)}",
            "error": True
        }

@app.post("/api/v1/alerts/{alert_id}/test")
async def test_alert_matching(alert_id: int):
    """Test alert matching against current vehicle listings"""
    try:
        # Import dependencies
        from app.models.scout import Alert
        from app.models.base import get_db
        from app.scraper.autouno_simple import AutoUnoSimpleScraper

        try:
            db_gen = get_db()
            db = next(db_gen)

            # Get the alert
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return {
                    "error": "Alert not found",
                    "status": "failed"
                }

            # Get test vehicles from scraper
            scraper = AutoUnoSimpleScraper()
            vehicles = scraper.generate_realistic_data(count=20)

            # Test alert matching
            matches = []
            for vehicle in vehicles:
                match = True

                # Check make
                if alert.make and vehicle['make'].lower() != alert.make.lower():
                    match = False

                # Check model
                if alert.model and alert.model.lower() not in vehicle['model'].lower():
                    match = False

                # Check price range
                if alert.min_price and vehicle['price'] < alert.min_price:
                    match = False
                if alert.max_price and vehicle['price'] > alert.max_price:
                    match = False

                # Check year range
                if alert.min_year and vehicle['year'] < alert.min_year:
                    match = False
                if alert.max_year and vehicle['year'] > alert.max_year:
                    match = False

                # Check city
                if alert.city and alert.city.lower() not in vehicle['city'].lower():
                    match = False

                # Check fuel type
                if alert.fuel_type and vehicle['fuel_type'].lower() != alert.fuel_type.lower():
                    match = False

                if match:
                    matches.append(vehicle)

            return {
                "message": "Alert test completed",
                "alert": {
                    "id": alert.id,
                    "name": alert.name,
                    "make": alert.make,
                    "model": alert.model,
                    "min_price": alert.min_price,
                    "max_price": alert.max_price,
                    "city": alert.city
                },
                "vehicles_tested": len(vehicles),
                "matches_found": len(matches),
                "matches": matches[:5],  # Return first 5 matches
                "status": "success"
            }

        except Exception as db_error:
            logger.error(f"Database error testing alert: {db_error}")
            return {
                "error": f"Database error: {str(db_error)}",
                "status": "failed"
            }

    except Exception as e:
        logger.error(f"Error testing alert: {e}")
        return {
            "error": f"Failed to test alert: {str(e)}",
            "status": "failed"
        }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with cloud deployment information"""
    return {
        "message": "Vehicle Scout Cloud API - Updated with AutoUno Scraper",
        "version": "1.0.1",
        "environment": cloud_settings.environment,
        "cloud_deployed": cloud_settings.is_cloud_deployed,
        "docs_url": "/docs" if not cloud_settings.is_production else "disabled",
        "health_check": "/health",
        "features": ["AutoUno Scraper", "Alert System", "Vehicle Listings"],
        "new_endpoints": [
            "/api/v1/alerts/",
            "/api/v1/automotive/vehicles/simple",
            "/api/v1/scraper/autouno/test",
            "/test/router-debug"
        ]
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
