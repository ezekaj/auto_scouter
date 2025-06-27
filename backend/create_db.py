from app.models.base import engine, Base
from app.models.scout import Scout, Team, Match, ScoutReport

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    create_tables()
