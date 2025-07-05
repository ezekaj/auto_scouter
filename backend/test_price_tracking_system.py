#!/usr/bin/env python3
"""
Price Tracking System Test Script

This script tests the price tracking functionality including:
- Recording price changes
- Analyzing price trends
- Price predictions
- Market comparisons
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.base import SessionLocal, engine, Base
from app.models.scout import User
from app.models.automotive import VehicleListing, PriceHistory
from app.services.price_tracking_service import PriceTrackingService


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
    """Create sample vehicle for price tracking"""
    print("\n📊 Creating Sample Data")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Create test vehicle
        test_vehicle = db.query(VehicleListing).filter(
            VehicleListing.external_id == "test_price_tracking_bmw"
        ).first()
        
        if not test_vehicle:
            test_vehicle = VehicleListing(
                external_id="test_price_tracking_bmw",
                listing_url="https://example.com/bmw-price-test",
                make="BMW",
                model="320i",
                year=2020,
                price=25000.0,
                mileage=45000,
                fuel_type="gasoline",
                transmission="automatic",
                engine_power_hp=184,
                city="Munich",
                dealer_name="BMW Munich",
                source_website="test_site"
            )
            db.add(test_vehicle)
            db.commit()
            db.refresh(test_vehicle)
            print(f"✅ Created test vehicle: {test_vehicle.make} {test_vehicle.model}")
        else:
            print(f"ℹ️ Test vehicle already exists: {test_vehicle.make} {test_vehicle.model}")
        
        return test_vehicle.id
        
    except Exception as e:
        print(f"❌ Sample data creation failed: {str(e)}")
        return None
    finally:
        db.close()


def test_record_price_changes():
    """Test recording price changes"""
    print("\n💰 Testing Price Change Recording")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        vehicle_id = create_sample_data()
        if not vehicle_id:
            print("❌ No test vehicle available")
            return False
        
        price_service = PriceTrackingService(db)
        
        # Record initial price
        initial_price = price_service.record_price_change(
            vehicle_id=vehicle_id,
            new_price=25000.0,
            source_website="test_site"
        )
        print(f"✅ Recorded initial price: €{initial_price.price}")
        
        # Record price drop
        price_drop = price_service.record_price_change(
            vehicle_id=vehicle_id,
            new_price=23500.0,
            source_website="test_site"
        )
        print(f"✅ Recorded price drop: €{price_drop.price} ({price_drop.change_percentage:+.1f}%)")
        
        # Record price increase
        price_increase = price_service.record_price_change(
            vehicle_id=vehicle_id,
            new_price=24200.0,
            source_website="test_site"
        )
        print(f"✅ Recorded price increase: €{price_increase.price} ({price_increase.change_percentage:+.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Price change recording test failed: {str(e)}")
        return False
    finally:
        db.close()


def test_price_trend_analysis():
    """Test price trend analysis"""
    print("\n📈 Testing Price Trend Analysis")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        vehicle_id = create_sample_data()
        if not vehicle_id:
            print("❌ No test vehicle available")
            return False
        
        price_service = PriceTrackingService(db)
        
        # Get price history
        price_history = price_service.get_price_history(vehicle_id, 30)
        print(f"✅ Retrieved price history: {len(price_history)} entries")
        
        if len(price_history) >= 2:
            # Analyze trend
            trend_analysis = price_service.analyze_price_trend(vehicle_id, 30)
            
            print(f"   Trend: {trend_analysis['trend']}")
            print(f"   Total Change: €{trend_analysis['total_change']:+.0f} ({trend_analysis['total_change_percentage']:+.1f}%)")
            print(f"   Average Price: €{trend_analysis['average_price']:,.0f}")
            print(f"   Price Range: €{trend_analysis['min_price']:,.0f} - €{trend_analysis['max_price']:,.0f}")
            print(f"   Volatility: {trend_analysis['price_volatility']:.2f}")
            print(f"   Data Points: {trend_analysis['data_points']}")
        else:
            print("ℹ️ Insufficient data for trend analysis")
        
        return True
        
    except Exception as e:
        print(f"❌ Price trend analysis test failed: {str(e)}")
        return False
    finally:
        db.close()


def test_price_prediction():
    """Test price prediction functionality"""
    print("\n🔮 Testing Price Prediction")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        vehicle_id = create_sample_data()
        if not vehicle_id:
            print("❌ No test vehicle available")
            return False
        
        price_service = PriceTrackingService(db)
        
        # Get price prediction
        prediction = price_service.predict_price_trend(vehicle_id, 30)
        
        print(f"✅ Price prediction generated")
        print(f"   Prediction: {prediction['prediction']}")
        print(f"   Confidence: {prediction['confidence']:.2f}")
        
        if prediction['predicted_price']:
            print(f"   Current Price: €{prediction['current_price']:,.0f}")
            print(f"   Predicted Price: €{prediction['predicted_price']:,.0f}")
            print(f"   Expected Change: €{prediction['predicted_change']:+.0f} ({prediction['predicted_change_percentage']:+.1f}%)")
            
            if prediction['prediction_range']:
                print(f"   Prediction Range: €{prediction['prediction_range']['min']:,.0f} - €{prediction['prediction_range']['max']:,.0f}")
        else:
            print("   Insufficient data for price prediction")
        
        print(f"   Data Points Used: {prediction['data_points_used']}")
        print(f"   Prediction Horizon: {prediction['prediction_horizon_days']} days")
        
        return True
        
    except Exception as e:
        print(f"❌ Price prediction test failed: {str(e)}")
        return False
    finally:
        db.close()


def test_market_comparison():
    """Test market comparison functionality"""
    print("\n🏪 Testing Market Comparison")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        vehicle_id = create_sample_data()
        if not vehicle_id:
            print("❌ No test vehicle available")
            return False
        
        # Create some similar vehicles for comparison
        similar_vehicles = [
            {
                "external_id": "similar_bmw_1",
                "listing_url": "https://example.com/similar-bmw-1",
                "make": "BMW",
                "model": "320i",
                "year": 2019,
                "price": 23000.0,
                "mileage": 55000,
                "fuel_type": "gasoline",
                "city": "Berlin",
                "source_website": "test_site"
            },
            {
                "external_id": "similar_bmw_2",
                "listing_url": "https://example.com/similar-bmw-2",
                "make": "BMW",
                "model": "320i",
                "year": 2021,
                "price": 27000.0,
                "mileage": 35000,
                "fuel_type": "gasoline",
                "city": "Hamburg",
                "source_website": "test_site"
            }
        ]
        
        for vehicle_data in similar_vehicles:
            existing = db.query(VehicleListing).filter(
                VehicleListing.external_id == vehicle_data["external_id"]
            ).first()
            
            if not existing:
                vehicle = VehicleListing(**vehicle_data)
                db.add(vehicle)
        
        db.commit()
        
        price_service = PriceTrackingService(db)
        comparison = price_service.get_market_comparison(vehicle_id)
        
        print(f"✅ Market comparison completed")
        print(f"   Comparison Status: {comparison.get('comparison', 'unknown')}")
        
        if comparison.get('comparison') == 'available':
            print(f"   Market Position: {comparison.get('market_position', 'unknown')}")
            print(f"   Vehicle Price: €{comparison.get('vehicle_price', 0):,.0f}")
            print(f"   Market Average: €{comparison.get('market_average', 0):,.0f}")
            print(f"   Market Median: €{comparison.get('market_median', 0):,.0f}")
            
            if comparison.get('market_range'):
                print(f"   Market Range: €{comparison['market_range']['min']:,.0f} - €{comparison['market_range']['max']:,.0f}")
            
            print(f"   Price vs Average: €{comparison.get('price_difference_from_average', 0):+.0f} ({comparison.get('price_difference_percentage', 0):+.1f}%)")
            print(f"   Market Percentile: {comparison.get('percentile', 0):.1f}%")
            print(f"   Similar Vehicles: {comparison.get('similar_vehicles_count', 0)}")
        else:
            print("   No similar vehicles found for comparison")
        
        return True
        
    except Exception as e:
        print(f"❌ Market comparison test failed: {str(e)}")
        return False
    finally:
        db.close()


def test_price_statistics():
    """Test price statistics functionality"""
    print("\n📊 Testing Price Statistics")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        price_service = PriceTrackingService(db)
        statistics = price_service.get_price_statistics(30)
        
        print(f"✅ Price statistics generated")
        print(f"   Period: {statistics['period_days']} days")
        print(f"   Total Changes: {statistics.get('total_changes', 0)}")
        print(f"   Price Drops: {statistics.get('price_drops', 0)}")
        print(f"   Price Increases: {statistics.get('price_increases', 0)}")
        print(f"   Average Change: €{statistics.get('average_change', 0):+.0f}")
        print(f"   Average Change %: {statistics.get('average_change_percentage', 0):+.1f}%")
        print(f"   Largest Drop: {statistics.get('largest_drop_percentage', 0):.1f}%")
        print(f"   Largest Increase: {statistics.get('largest_increase_percentage', 0):.1f}%")
        print(f"   Vehicles with Changes: {statistics.get('vehicles_with_changes', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Price statistics test failed: {str(e)}")
        return False
    finally:
        db.close()


def main():
    """Main test function"""
    print("🚀 Price Tracking System Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Setup test environment
    if not setup_test_environment():
        print("❌ Test environment setup failed")
        return False
    
    # Run tests
    tests = [
        ("Price Change Recording", test_record_price_changes),
        ("Price Trend Analysis", test_price_trend_analysis),
        ("Price Prediction", test_price_prediction),
        ("Market Comparison", test_market_comparison),
        ("Price Statistics", test_price_statistics)
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
        print("🎉 All tests passed! Price tracking system is working correctly.")
    else:
        print("⚠️ Some tests failed. Check implementation and logs.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
