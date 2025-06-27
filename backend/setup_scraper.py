#!/usr/bin/env python3
"""
Automotive Scraper Setup Script

This script sets up the complete automotive scraper system including:
- Database initialization
- Configuration validation
- Dependency checks
- Scheduler setup
- Health checks
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"🚗 {title}")
    print("=" * 60)

def print_step(step, description):
    """Print a formatted step"""
    print(f"\n📋 Step {step}: {description}")
    print("-" * 40)

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"✅ Python version OK: {sys.version}")
    return True

def install_dependencies():
    """Install required Python dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        # Install requirements
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ Failed to install dependencies")
            print(result.stderr)
            return False
        
        print("✅ Dependencies installed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def setup_database():
    """Initialize the database"""
    print("🗄️ Setting up database...")
    
    try:
        # Import after dependencies are installed
        from app.models.base import engine, Base
        from app.models.scout import Scout, Team, Match, ScoutReport, User, Alert
        from app.models.automotive import (
            VehicleListing, VehicleImage, PriceHistory,
            ScrapingLog, ScrapingSession, DataQualityMetric
        )
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False

def validate_configuration():
    """Validate scraper configuration"""
    print("⚙️ Validating configuration...")
    
    try:
        from app.scraper.config import scraper_settings
        
        # Check required settings
        required_settings = [
            'BASE_URL',
            'USATO_URL',
            'REQUEST_DELAY',
            'MAX_RETRIES'
        ]
        
        for setting in required_settings:
            value = getattr(scraper_settings, setting, None)
            if value is None:
                print(f"❌ Missing required setting: {setting}")
                return False
            print(f"✅ {setting}: {value}")
        
        # Validate URLs
        if not scraper_settings.BASE_URL.startswith('http'):
            print("❌ BASE_URL must be a valid HTTP URL")
            return False
        
        # Validate delays
        if scraper_settings.REQUEST_DELAY < 1.0:
            print("⚠️ Warning: REQUEST_DELAY is less than 1 second")
        
        print("✅ Configuration validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error validating configuration: {e}")
        return False

def test_network_connectivity():
    """Test connectivity to target website"""
    print("🌐 Testing network connectivity...")
    
    try:
        import requests
        from app.scraper.config import scraper_settings
        
        response = requests.get(
            scraper_settings.BASE_URL,
            timeout=10,
            headers={'User-Agent': 'Setup Script Health Check'}
        )
        
        if response.status_code == 200:
            print(f"✅ Successfully connected to {scraper_settings.BASE_URL}")
            return True
        else:
            print(f"⚠️ Received status code {response.status_code} from {scraper_settings.BASE_URL}")
            return True  # Still consider it working
        
    except Exception as e:
        print(f"❌ Network connectivity test failed: {e}")
        return False

def check_robots_txt():
    """Check robots.txt compliance"""
    print("🤖 Checking robots.txt compliance...")
    
    try:
        from app.scraper.compliance import ComplianceManager
        
        compliance = ComplianceManager()
        robots_info = compliance.robots_checker.get_robots_info()
        
        print(f"✅ Robots.txt URL: {robots_info.get('robots_url', 'N/A')}")
        print(f"✅ Respect robots.txt: {robots_info.get('respect_robots', 'N/A')}")
        
        # Test a sample URL
        test_url = "https://gruppoautouno.it/usato/"
        compliance_result = compliance.check_url_compliance(test_url)
        
        if compliance_result['allowed']:
            print(f"✅ Sample URL allowed: {test_url}")
        else:
            print(f"⚠️ Sample URL blocked: {test_url}")
            print(f"Reasons: {compliance_result['reasons']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking robots.txt: {e}")
        return False

def setup_scheduler():
    """Initialize the scheduler"""
    print("⏰ Setting up scheduler...")
    
    try:
        from app.scraper.scheduler import scraper_scheduler
        
        # Get scheduler status
        status = scraper_scheduler.get_job_status()
        
        print(f"✅ Scheduler initialized")
        print(f"✅ Scheduler running: {status['scheduler_running']}")
        print(f"✅ Jobs configured: {len(status['jobs'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up scheduler: {e}")
        return False

def run_health_checks():
    """Run comprehensive health checks"""
    print("🏥 Running health checks...")
    
    try:
        from app.scraper.monitoring import scraper_monitor
        from app.models.base import SessionLocal
        
        # System health
        health = scraper_monitor.get_system_health()
        print(f"✅ Overall system status: {health.get('overall_status', 'unknown')}")
        
        # Database connectivity
        db_status = health.get('services', {}).get('database', {})
        if db_status.get('status') == 'ok':
            print("✅ Database connectivity: OK")
        else:
            print("❌ Database connectivity: Failed")
            return False
        
        # Network connectivity
        network_status = health.get('services', {}).get('network', {})
        if network_status.get('status') == 'ok':
            print("✅ Network connectivity: OK")
        else:
            print("⚠️ Network connectivity: Issues detected")
        
        return True
        
    except Exception as e:
        print(f"❌ Error running health checks: {e}")
        return False

def create_sample_data():
    """Create sample data for testing"""
    print("📊 Creating sample data...")
    
    try:
        from app.models.base import SessionLocal
        from app.services.automotive_service import AutomotiveService
        
        db = SessionLocal()
        service = AutomotiveService(db)
        
        # Sample vehicle data
        sample_vehicles = [
            {
                "external_id": "sample-vw-golf-1",
                "listing_url": "https://gruppoautouno.it/usato/sample-vw-golf-1/",
                "make": "Volkswagen",
                "model": "Golf",
                "variant": "Golf 1.6 TDI Comfortline",
                "year": 2020,
                "price": 18500.0,
                "currency": "EUR",
                "mileage": 45000,
                "fuel_type": "diesel",
                "transmission": "manual",
                "doors": 5,
                "seats": 5,
                "city": "Napoli",
                "region": "Campania",
                "country": "IT",
                "dealer_name": "Autouno Group",
                "source_website": "gruppoautouno.it"
            },
            {
                "external_id": "sample-peugeot-208-1",
                "listing_url": "https://gruppoautouno.it/usato/sample-peugeot-208-1/",
                "make": "Peugeot",
                "model": "208",
                "variant": "208 1.2 PureTech Active",
                "year": 2019,
                "price": 14500.0,
                "currency": "EUR",
                "mileage": 32000,
                "fuel_type": "gasoline",
                "transmission": "manual",
                "doors": 5,
                "seats": 5,
                "city": "Napoli",
                "region": "Campania",
                "country": "IT",
                "dealer_name": "Autouno Group",
                "source_website": "gruppoautouno.it"
            }
        ]
        
        for vehicle_data in sample_vehicles:
            vehicle = service.create_vehicle_listing(vehicle_data)
            if vehicle:
                print(f"✅ Created sample vehicle: {vehicle.make} {vehicle.model}")
        
        db.close()
        print("✅ Sample data created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print_header("Setup Complete! 🎉")
    
    print("""
🚀 Your Automotive Scraper is ready to use!

Next Steps:
1. Start the FastAPI server:
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

2. Access the API documentation:
   http://localhost:8000/docs

3. View the automotive endpoints:
   http://localhost:8000/api/v1/automotive/vehicles

4. Monitor scraper health:
   http://localhost:8000/api/v1/automotive/scraper/health

5. Run tests:
   python run_tests.py

6. Start the scheduler (optional):
   python -c "from app.scraper.scheduler import scraper_scheduler; scraper_scheduler.start(); input('Press Enter to stop...')"

📚 Documentation:
- API Documentation: docs/AUTOMOTIVE_API.md
- Website Analysis: docs/WEBSITE_ANALYSIS.md
- Development Guide: docs/DEVELOPMENT.md

🔧 Configuration:
- Edit backend/app/scraper/config.py for scraper settings
- Set environment variables in backend/.env

⚠️ Important Notes:
- Respect the target website's robots.txt and terms of service
- Use reasonable delays between requests (current: 2 seconds)
- Monitor compliance score regularly
- Review data quality metrics periodically

Happy scraping! 🕷️
""")

def main():
    """Main setup function"""
    print_header("Automotive Scraper Setup")
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    setup_steps = [
        ("Python Version Check", check_python_version),
        ("Install Dependencies", install_dependencies),
        ("Database Setup", setup_database),
        ("Configuration Validation", validate_configuration),
        ("Network Connectivity Test", test_network_connectivity),
        ("Robots.txt Compliance Check", check_robots_txt),
        ("Scheduler Setup", setup_scheduler),
        ("Health Checks", run_health_checks),
        ("Sample Data Creation", create_sample_data)
    ]
    
    failed_steps = []
    
    for i, (step_name, step_function) in enumerate(setup_steps, 1):
        print_step(i, step_name)
        
        try:
            success = step_function()
            if not success:
                failed_steps.append(step_name)
                print(f"❌ Step {i} failed: {step_name}")
            else:
                print(f"✅ Step {i} completed: {step_name}")
        except Exception as e:
            failed_steps.append(step_name)
            print(f"❌ Step {i} failed with exception: {e}")
    
    # Summary
    print_header("Setup Summary")
    
    if failed_steps:
        print(f"❌ Setup completed with {len(failed_steps)} failed steps:")
        for step in failed_steps:
            print(f"  - {step}")
        print("\nPlease review the errors above and run the setup again.")
        sys.exit(1)
    else:
        print("✅ All setup steps completed successfully!")
        print_next_steps()
        sys.exit(0)

if __name__ == "__main__":
    main()
