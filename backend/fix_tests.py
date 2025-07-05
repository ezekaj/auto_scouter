#!/usr/bin/env python3
"""
Quick test fixes for Auto Scouter
This script fixes the most critical test issues to get the test suite running.
"""

import os
import sys
import re
from pathlib import Path

def fix_vehicle_listing_fixtures():
    """Fix VehicleListing fixtures to include required source_website field"""
    test_files = [
        "tests/test_alert_matching.py",
        "tests/test_cars.py", 
        "tests/test_automotive_service.py",
        "tests/test_integration.py"
    ]
    
    for test_file in test_files:
        if not os.path.exists(test_file):
            continue
            
        print(f"Fixing {test_file}...")
        
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Fix VehicleListing constructor calls missing source_website
        pattern = r'VehicleListing\(\s*([^)]*?)\s*\)'
        
        def fix_constructor(match):
            args = match.group(1)
            if 'source_website' not in args:
                # Add source_website before the last argument or is_active
                if 'is_active' in args:
                    args = args.replace('is_active=', 'source_website="test_source",\n            is_active=')
                else:
                    args += ',\n            source_website="test_source"'
            return f'VehicleListing(\n            {args}\n        )'
        
        content = re.sub(pattern, fix_constructor, content, flags=re.DOTALL)
        
        with open(test_file, 'w') as f:
            f.write(content)

def fix_alert_fixtures():
    """Fix Alert fixtures to use correct field names"""
    test_files = [
        "tests/test_alert_matching.py",
        "tests/test_alerts.py",
        "tests/test_notification_system.py"
    ]
    
    for test_file in test_files:
        if not os.path.exists(test_file):
            continue
            
        print(f"Fixing Alert fixtures in {test_file}...")
        
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Fix Alert constructor calls
        # Replace year= with min_year= and max_year=
        content = re.sub(r'year=(\d+)', r'min_year=\1,\n            max_year=\1', content)
        
        # Ensure Alert has name field
        pattern = r'Alert\(\s*([^)]*?user_id[^)]*?)\s*\)'
        
        def fix_alert_constructor(match):
            args = match.group(1)
            if 'name=' not in args:
                # Add name after user_id
                args = args.replace('user_id=', 'user_id=').replace(',', ',\n            name="Test Alert",', 1)
            return f'Alert(\n            {args}\n        )'
        
        content = re.sub(pattern, fix_alert_constructor, content, flags=re.DOTALL)
        
        with open(test_file, 'w') as f:
            f.write(content)

def fix_user_fixtures():
    """Fix User fixtures to use correct field names"""
    test_files = [
        "tests/test_auth.py",
        "tests/test_alert_matching.py",
        "tests/test_alerts.py",
        "tests/test_notification_system.py"
    ]
    
    for test_file in test_files:
        if not os.path.exists(test_file):
            continue
            
        print(f"Fixing User fixtures in {test_file}...")
        
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Replace hashed_password with password_hash
        content = content.replace('hashed_password=', 'password_hash=')
        
        with open(test_file, 'w') as f:
            f.write(content)

def main():
    """Run all fixes"""
    print("🔧 Fixing test files...")

    fix_vehicle_listing_fixtures()
    fix_alert_fixtures()
    fix_user_fixtures()

    print("✅ Test fixes completed!")

if __name__ == "__main__":
    main()
