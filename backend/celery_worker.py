#!/usr/bin/env python3
"""
Celery Worker Startup Script

This script starts a Celery worker for processing background tasks.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.celery_app import celery_app

if __name__ == "__main__":
    # Start the Celery worker
    celery_app.start()
