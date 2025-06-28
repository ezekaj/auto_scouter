#!/usr/bin/env python3
"""
Simple API connectivity test for Auto Scouter backend
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Root endpoint: {response.status_code} - {response.json()}")
        
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health endpoint: {response.status_code} - {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_scouts_endpoint():
    """Test the scouts endpoint"""
    try:
        # Test GET scouts
        response = requests.get(f"{BASE_URL}/api/v1/scouts")
        print(f"✅ GET scouts: {response.status_code} - Found {len(response.json())} scouts")
        
        # Test POST scout
        scout_data = {
            "name": "Test Scout",
            "email": "test@example.com"
        }
        response = requests.post(f"{BASE_URL}/api/v1/scouts", json=scout_data)
        if response.status_code == 200:
            scout = response.json()
            print(f"✅ POST scout: {response.status_code} - Created scout ID {scout['id']}")
            return scout['id']
        else:
            print(f"⚠️ POST scout: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Scouts test failed: {e}")
        return None

def test_teams_endpoint():
    """Test the teams endpoint"""
    try:
        # Test GET teams
        response = requests.get(f"{BASE_URL}/api/v1/teams")
        print(f"✅ GET teams: {response.status_code} - Found {len(response.json())} teams")
        
        # Test POST team
        team_data = {
            "team_number": 1234,
            "team_name": "Test Team",
            "school": "Test School",
            "city": "Test City",
            "state": "TS",
            "country": "USA"
        }
        response = requests.post(f"{BASE_URL}/api/v1/teams", json=team_data)
        if response.status_code == 200:
            team = response.json()
            print(f"✅ POST team: {response.status_code} - Created team ID {team['id']}")
            return team['id']
        else:
            print(f"⚠️ POST team: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Teams test failed: {e}")
        return None

def main():
    """Run all API tests"""
    print("🧪 Auto Scouter API Connectivity Test")
    print("=" * 40)
    
    # Test health endpoints
    if not test_health_endpoint():
        print("❌ Backend is not responding. Make sure it's running on port 8000.")
        sys.exit(1)
    
    print("\n📊 Testing API endpoints...")
    
    # Test scouts
    scout_id = test_scouts_endpoint()
    
    # Test teams
    team_id = test_teams_endpoint()
    
    print("\n🎉 API connectivity test completed!")
    print(f"Backend is running at: {BASE_URL}")
    print(f"API docs available at: {BASE_URL}/docs")

if __name__ == "__main__":
    main()
