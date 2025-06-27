#!/usr/bin/env python3
"""
Test Runner for Automotive Scraper

This script runs all tests for the automotive scraper system.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """Run all tests with coverage reporting"""
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    print("🧪 Running Automotive Scraper Tests")
    print("=" * 50)
    
    # Test commands
    commands = [
        # Run tests with coverage
        [
            "python", "-m", "pytest", 
            "tests/", 
            "-v", 
            "--cov=app", 
            "--cov-report=html", 
            "--cov-report=term-missing",
            "--tb=short"
        ],
        
        # Run specific test categories
        ["python", "-m", "pytest", "tests/test_automotive_service.py", "-v"],
        ["python", "-m", "pytest", "tests/test_scraper.py", "-v"],
        ["python", "-m", "pytest", "tests/test_api.py", "-v"],
    ]
    
    for i, cmd in enumerate(commands):
        print(f"\n📋 Running test command {i+1}/{len(commands)}")
        print(f"Command: {' '.join(cmd)}")
        print("-" * 30)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.stdout:
                print(result.stdout)
            
            if result.stderr:
                print("STDERR:", result.stderr)
            
            if result.returncode != 0:
                print(f"❌ Test command failed with return code {result.returncode}")
                if i == 0:  # If main test command fails, stop
                    return False
            else:
                print(f"✅ Test command completed successfully")
                
        except Exception as e:
            print(f"❌ Error running test command: {e}")
            return False
    
    print("\n🎉 All tests completed!")
    print("\n📊 Coverage report generated in htmlcov/index.html")
    return True

def check_dependencies():
    """Check if required test dependencies are installed"""
    required_packages = [
        "pytest",
        "pytest-cov",
        "httpx",
        "fastapi",
        "sqlalchemy"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall missing packages with:")
        print("pip install " + " ".join(missing_packages))
        return False
    
    return True

def main():
    """Main test runner function"""
    print("🔍 Checking dependencies...")
    
    if not check_dependencies():
        print("❌ Dependency check failed")
        sys.exit(1)
    
    print("✅ Dependencies OK")
    
    # Run tests
    success = run_tests()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
