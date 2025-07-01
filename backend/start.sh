#!/bin/bash

# Set default port if not provided
export PORT=${PORT:-8000}

# Start the FastAPI application
python3 -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
