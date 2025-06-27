from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import scouts, teams, matches
from app.core.config import settings

app = FastAPI(
    title="Auto Scouter API",
    description="API for automated scouting system",
    version="1.0.0",
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
app.include_router(scouts.router, prefix="/api/v1/scouts", tags=["scouts"])
app.include_router(teams.router, prefix="/api/v1/teams", tags=["teams"])
app.include_router(matches.router, prefix="/api/v1/matches", tags=["matches"])


@app.get("/")
async def root():
    return {"message": "Welcome to Auto Scouter API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
