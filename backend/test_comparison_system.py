#!/usr/bin/env python3
"""
Vehicle Comparison System Test Script

This script tests the vehicle comparison functionality including:
- Creating and managing comparisons
- Adding/removing vehicles from comparisons
- Comparison analysis and scoring
- Quick comparison features
"""

import os
import sys
from datetime import datetime
from sqlalchemy.orm import Session

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.base import SessionLocal, engine, Base
from app.models.scout import User
from app.models.automotive import VehicleListing
from app.models.comparison import VehicleComparison, VehicleComparisonItem
from app.services.comparison_service import ComparisonService
from app.schemas.comparison import VehicleComparisonCreate, QuickComparisonRequest, ComparisonCriteria


def setup_test_environment():
    """Setup test environment and sample data"""
    print("\n⚙️ Setting up Test Environment")
    print("=" * 50)
    
    try:
        # Import all models to ensure they're registered
        from app.models import automotive, scout, notifications, comparison
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")
        
        return True
        
    except Exception as e:
        print(f"❌ Test environment setup failed: {str(e)}")
        return False


def create_sample_data():
    """Create sample users and vehicles for testing"""
    print("\n📊 Creating Sample Data")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Create test user
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            test_user = User(
                username="testuser",
                email="test@example.com",
                password_hash="dummy_hash",
                is_active=True
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print(f"✅ Created test user: {test_user.username}")
        else:
            print(f"ℹ️ Test user already exists: {test_user.username}")
        
        # Create sample vehicles
        sample_vehicles = [
            {
                "external_id": "test_bmw_1",
                "listing_url": "https://example.com/bmw-320i",
                "make": "BMW",
                "model": "320i",
                "year": 2020,
                "price": 25000.0,
                "mileage": 45000,
                "fuel_type": "gasoline",
                "transmission": "automatic",
                "engine_power_hp": 184,
                "engine_displacement": 2000,
                "body_type": "sedan",
                "doors": 4,
                "seats": 5,
                "city": "Munich",
                "dealer_name": "BMW Munich"
            },
            {
                "external_id": "test_audi_1",
                "listing_url": "https://example.com/audi-a4",
                "make": "Audi",
                "model": "A4",
                "year": 2019,
                "price": 28000.0,
                "mileage": 38000,
                "fuel_type": "gasoline",
                "transmission": "automatic",
                "engine_power_hp": 190,
                "engine_displacement": 2000,
                "body_type": "sedan",
                "doors": 4,
                "seats": 5,
                "city": "Stuttgart",
                "dealer_name": "Audi Stuttgart"
            },
            {
                "external_id": "test_mercedes_1",
                "listing_url": "https://example.com/mercedes-c200",
                "make": "Mercedes-Benz",
                "model": "C200",
                "year": 2021,
                "price": 32000.0,
                "mileage": 25000,
                "fuel_type": "gasoline",
                "transmission": "automatic",
                "engine_power_hp": 204,
                "engine_displacement": 2000,
                "body_type": "sedan",
                "doors": 4,
                "seats": 5,
                "city": "Frankfurt",
                "dealer_name": "Mercedes Frankfurt"
            }
        ]
        
        vehicle_ids = []
        for vehicle_data in sample_vehicles:
            existing_vehicle = db.query(VehicleListing).filter(
                VehicleListing.external_id == vehicle_data["external_id"]
            ).first()
            
            if not existing_vehicle:
                vehicle = VehicleListing(**vehicle_data)
                db.add(vehicle)
                db.commit()
                db.refresh(vehicle)
                vehicle_ids.append(vehicle.id)
                print(f"✅ Created vehicle: {vehicle.make} {vehicle.model}")
            else:
                vehicle_ids.append(existing_vehicle.id)
                print(f"ℹ️ Vehicle already exists: {existing_vehicle.make} {existing_vehicle.model}")
        
        return test_user.id, vehicle_ids
        
    except Exception as e:
        print(f"❌ Sample data creation failed: {str(e)}")
        return None, []
    finally:
        db.close()


def test_create_comparison():
    """Test creating a vehicle comparison"""
    print("\n🔄 Testing Comparison Creation")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        user_id, vehicle_ids = create_sample_data()
        if not user_id or len(vehicle_ids) < 2:
            print("❌ Insufficient sample data")
            return False
        
        comparison_service = ComparisonService(db)
        
        # Create comparison
        comparison_data = VehicleComparisonCreate(
            name="German Luxury Sedans",
            description="Comparison of BMW, Audi, and Mercedes sedans",
            comparison_criteria=[
                ComparisonCriteria.PRICE,
                ComparisonCriteria.YEAR,
                ComparisonCriteria.MILEAGE,
                ComparisonCriteria.ENGINE_POWER
            ],
            vehicle_ids=vehicle_ids[:3]  # Use first 3 vehicles
        )
        
        comparison = comparison_service.create_comparison(user_id, comparison_data)
        
        print(f"✅ Created comparison: {comparison.name}")
        print(f"   ID: {comparison.id}")
        print(f"   Vehicles: {len(comparison.comparison_items)}")
        print(f"   Criteria: {len(comparison.comparison_criteria)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Comparison creation test failed: {str(e)}")
        return False
    finally:
        db.close()


def test_comparison_analysis():
    """Test comparison analysis functionality"""
    print("\n📊 Testing Comparison Analysis")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Get existing comparison
        comparison = db.query(VehicleComparison).first()
        if not comparison:
            print("❌ No comparison found for analysis")
            return False
        
        comparison_service = ComparisonService(db)
        analysis = comparison_service.analyze_comparison(comparison.id)
        
        print(f"✅ Analysis completed for comparison: {comparison.name}")
        
        if analysis.best_value:
            print(f"   Best Value: {analysis.best_value['make']} {analysis.best_value['model']} - €{analysis.best_value['price']:,.0f}")
        
        if analysis.best_performance:
            print(f"   Best Performance: {analysis.best_performance['make']} {analysis.best_performance['model']} - {analysis.best_performance['engine_power_hp']}hp")
        
        if analysis.best_condition:
            print(f"   Best Condition: {analysis.best_condition['make']} {analysis.best_condition['model']} ({analysis.best_condition['year']})")
        
        if analysis.price_range:
            print(f"   Price Range: €{analysis.price_range['min']:,.0f} - €{analysis.price_range['max']:,.0f}")
            print(f"   Average Price: €{analysis.price_range['average']:,.0f}")
        
        print(f"   Recommendations: {len(analysis.recommendations)}")
        for i, rec in enumerate(analysis.recommendations, 1):
            print(f"     {i}. {rec}")
        
        return True
        
    except Exception as e:
        print(f"❌ Comparison analysis test failed: {str(e)}")
        return False
    finally:
        db.close()


def test_quick_comparison():
    """Test quick comparison functionality"""
    print("\n⚡ Testing Quick Comparison")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        user_id, vehicle_ids = create_sample_data()
        if not user_id or len(vehicle_ids) < 2:
            print("❌ Insufficient sample data")
            return False
        
        comparison_service = ComparisonService(db)
        
        # Create quick comparison request
        quick_request = QuickComparisonRequest(
            vehicle_ids=vehicle_ids[:2],  # Compare first 2 vehicles
            criteria=[
                ComparisonCriteria.PRICE,
                ComparisonCriteria.ENGINE_POWER,
                ComparisonCriteria.MILEAGE
            ]
        )
        
        # Create temporary comparison for analysis
        temp_comparison_data = VehicleComparisonCreate(
            name="Quick Comparison",
            vehicle_ids=quick_request.vehicle_ids,
            comparison_criteria=quick_request.criteria
        )
        
        comparison = comparison_service.create_comparison(user_id, temp_comparison_data)
        analysis = comparison_service.analyze_comparison(comparison.id)
        
        # Clean up
        db.delete(comparison)
        db.commit()
        
        print("✅ Quick comparison completed")
        print(f"   Compared {len(quick_request.vehicle_ids)} vehicles")
        print(f"   Used {len(quick_request.criteria)} criteria")
        
        if analysis.best_value:
            print(f"   Winner: {analysis.best_value['make']} {analysis.best_value['model']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Quick comparison test failed: {str(e)}")
        return False
    finally:
        db.close()


def test_comparison_scoring():
    """Test comparison scoring system"""
    print("\n🎯 Testing Comparison Scoring")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        comparison = db.query(VehicleComparison).first()
        if not comparison:
            print("❌ No comparison found for scoring test")
            return False
        
        print(f"✅ Testing scores for comparison: {comparison.name}")
        
        for item in comparison.comparison_items:
            vehicle = item.vehicle
            print(f"\n   {vehicle.make} {vehicle.model}:")
            print(f"     Overall Score: {item.overall_score:.2f}" if item.overall_score else "     Overall Score: Not calculated")
            print(f"     Price Score: {item.price_score:.2f}" if item.price_score else "     Price Score: Not calculated")
            print(f"     Feature Score: {item.feature_score:.2f}" if item.feature_score else "     Feature Score: Not calculated")
            print(f"     Condition Score: {item.condition_score:.2f}" if item.condition_score else "     Condition Score: Not calculated")
        
        return True
        
    except Exception as e:
        print(f"❌ Comparison scoring test failed: {str(e)}")
        return False
    finally:
        db.close()


def main():
    """Main test function"""
    print("🚀 Vehicle Comparison System Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Setup test environment
    if not setup_test_environment():
        print("❌ Test environment setup failed")
        return False
    
    # Run tests
    tests = [
        ("Comparison Creation", test_create_comparison),
        ("Comparison Analysis", test_comparison_analysis),
        ("Quick Comparison", test_quick_comparison),
        ("Comparison Scoring", test_comparison_scoring)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print("\n📊 Test Summary")
    print("=" * 50)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Vehicle comparison system is working correctly.")
    else:
        print("⚠️ Some tests failed. Check implementation and logs.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
