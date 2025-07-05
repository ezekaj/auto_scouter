from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.routers import scouts, teams, matches, automotive, auth, cars, admin
from app.routers import enhanced_notifications, enhanced_alerts, webhooks, realtime, monitoring, dashboard, search, api_docs, email, comparison, price_tracking, analytics, rate_limiting, logging, i18n
from app.core.config import settings
from app.services.background_tasks import start_background_tasks, stop_background_tasks
from app.services.health_check import health_service
from app.middleware.rate_limiting import RateLimitMiddleware, RateLimitService
from app.core.logging_config import setup_logging
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.i18n_middleware import I18nMiddleware
from app.models.base import engine, Base

# Initialize logging first
setup_logging()

app = FastAPI(
    title="Auto Scouter API",
    description="""
    ## Auto Scouter REST API

    A comprehensive API for automotive data scouting and alert management.

    ### Features
    - **Car Listings**: Search and filter car listings with advanced criteria
    - **User Authentication**: JWT-based authentication system
    - **Price Alerts**: Create and manage price/availability alerts
    - **Real-time Data**: Access to recently scraped automotive data
    - **Notification System**: Comprehensive alert and notification management
    - **Background Processing**: Celery-based background task processing

    ### Authentication
    Most endpoints require authentication using JWT tokens.
    1. Register a new account or login with existing credentials
    2. Use the returned JWT token in the Authorization header: `Bearer <token>`

    ### Rate Limiting
    API requests are rate-limited to ensure fair usage and system stability.
    """,
    version="1.0.1",
    contact={
        "name": "Auto Scouter Team",
        "email": "support@autoscouter.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize rate limiting
try:
    import redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()  # Test connection
    rate_limit_middleware = RateLimitMiddleware(redis_client)
    print("Rate limiting initialized with Redis storage")
except Exception as e:
    print(f"Redis unavailable for rate limiting, using in-memory storage: {str(e)}")
    rate_limit_middleware = RateLimitMiddleware()

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# Add logging middleware
logging_middleware = LoggingMiddleware(app)
app.add_middleware(LoggingMiddleware)

# Add i18n middleware
app.add_middleware(I18nMiddleware)

# Initialize rate limiting service
rate_limit_service = RateLimitService(rate_limit_middleware)
rate_limiting.set_rate_limit_service(rate_limit_service)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(cars.router, prefix="/api/v1/cars", tags=["cars"])
# Enhanced notification system routes
app.include_router(enhanced_notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(enhanced_alerts.router, prefix="/api/v1/alerts", tags=["enhanced-alerts"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(realtime.router, prefix="/api/v1/realtime", tags=["realtime"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["monitoring"])

app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(api_docs.router, prefix="/api/v1/docs", tags=["api-documentation"])
app.include_router(scouts.router, prefix="/api/v1/scouts", tags=["scouts"])
app.include_router(teams.router, prefix="/api/v1/teams", tags=["teams"])
app.include_router(matches.router, prefix="/api/v1/matches", tags=["matches"])
app.include_router(automotive.router, prefix="/api/v1/automotive", tags=["automotive"])
app.include_router(email.router, prefix="/api/v1/email", tags=["email"])
app.include_router(comparison.router, prefix="/api/v1/comparisons", tags=["comparisons"])
app.include_router(price_tracking.router, prefix="/api/v1/price-tracking", tags=["price-tracking"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(rate_limiting.router, prefix="/api/v1/rate-limiting", tags=["rate-limiting"])
app.include_router(logging.router, prefix="/api/v1/logging", tags=["logging"])
app.include_router(i18n.router, prefix="/api/v1/i18n", tags=["i18n"])


# Event handlers for background tasks
@app.on_event("startup")
async def startup_event():
    """Initialize database and background tasks on startup"""
    # Create database tables
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Warning: Failed to create database tables: {e}")

    # Start background tasks
    try:
        start_background_tasks()
    except Exception as e:
        print(f"Warning: Failed to start background tasks: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up background tasks on shutdown"""
    try:
        stop_background_tasks()
    except Exception as e:
        print(f"Warning: Failed to stop background tasks: {e}")


@app.get("/")
async def root():
    return {"message": "Welcome to Auto Scouter API"}


@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Comprehensive health check endpoint"""
    return health_service.get_comprehensive_health()


@app.get("/api/v1/system/status")
async def system_status():
    """Get system status including notification system"""
    try:
        # Check Redis connection
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        redis_status = "connected" if r.ping() else "disconnected"
    except:
        redis_status = "disconnected"
    
    try:
        # Check Celery workers
        from app.core.celery_app import celery_app
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        celery_status = "running" if active_workers else "stopped"
    except:
        celery_status = "unknown"
    
    return {
        "status": "healthy",
        "components": {
            "api": "running",
            "database": "connected",
            "redis": redis_status,
            "celery": celery_status,
            "notification_system": "active" if redis_status == "connected" and celery_status == "running" else "inactive"
        },
        "version": "1.0.0"
    }
