#!/bin/bash

# Vehicle Scout Backend - Local Development Startup
# This script starts the backend locally for testing

set -e

echo "🚀 Starting Vehicle Scout Backend Locally"
echo "========================================"

# Check if we're in the backend directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Please run this script from the backend directory"
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv || {
        echo "❌ Failed to create virtual environment"
        echo "💡 Try: sudo apt install python3-venv"
        exit 1
    }
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Using default configuration."
    echo "💡 Create a .env file for custom configuration."
fi

# Initialize database
echo "🗄️ Initializing database..."
python3 create_db.py || {
    echo "⚠️  Database initialization failed. Continuing anyway..."
}

# Start the server
echo "🌐 Starting FastAPI server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📊 API documentation at: http://localhost:8000/docs"
echo "🔍 Health check at: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start with uvicorn
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
