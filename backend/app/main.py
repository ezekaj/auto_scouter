from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import scouts, teams, matches, automotive, auth, alerts, cars, notifications, admin
from app.core.config import settings
from app.services.background_tasks import start_background_tasks, stop_background_tasks

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

    ### Authentication
    Most endpoints require authentication using JWT tokens.
    1. Register a new account or login with existing credentials
    2. Use the returned JWT token in the Authorization header: `Bearer <token>`

    ### Rate Limiting
    API requests are rate-limited to ensure fair usage and system stability.
    """,
    version="1.0.0",
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

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(cars.router, prefix="/api/v1/cars", tags=["cars"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(scouts.router, prefix="/api/v1/scouts", tags=["scouts"])
app.include_router(teams.router, prefix="/api/v1/teams", tags=["teams"])
app.include_router(matches.router, prefix="/api/v1/matches", tags=["matches"])
app.include_router(automotive.router, prefix="/api/v1/automotive", tags=["automotive"])


# Event handlers for background tasks
@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
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
    return {"status": "healthy"}
