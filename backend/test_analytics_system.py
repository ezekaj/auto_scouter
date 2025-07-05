#!/usr/bin/env python3
"""
Analytics System Test Script

This script tests the analytics functionality including:
- Market overview analytics
- User behavior analytics
- Price analytics
- Alert effectiveness analysis
- System performance metrics
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.base import SessionLocal, engine, Base
from app.models.scout import User, Alert
from app.models.automotive import VehicleListing, PriceHistory
from app.models.notifications import Notification, NotificationStatus, NotificationType
from app.models.comparison import VehicleComparison
from app.services.analytics_service import AnalyticsService


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
    """Create comprehensive sample data for analytics testing"""
    print("\n📊 Creating Sample Data")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Create test user
        test_user = db.query(User).filter(User.email == "analytics_test@example.com").first()
        if not test_user:
            test_user = User(
                username="analytics_user",
                email="analytics_test@example.com",
                password_hash="dummy_hash",
                is_active=True
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print(f"✅ Created test user: {test_user.username}")
        
        # Create sample vehicles
        sample_vehicles = []
        vehicle_data = [
            {"make": "BMW", "model": "320i", "year": 2020, "price": 25000.0, "mileage": 45000},
            {"make": "Audi", "model": "A4", "year": 2019, "price": 28000.0, "mileage": 38000},
            {"make": "Mercedes-Benz", "model": "C200", "year": 2021, "price": 32000.0, "mileage": 25000},
            {"make": "BMW", "model": "X3", "year": 2020, "price": 35000.0, "mileage": 40000},
            {"make": "Audi", "model": "Q5", "year": 2019, "price": 38000.0, "mileage": 42000}
        ]
        
        for i, data in enumerate(vehicle_data):
            external_id = f"analytics_test_vehicle_{i+1}"
            existing = db.query(VehicleListing).filter(
                VehicleListing.external_id == external_id
            ).first()
            
            if not existing:
                vehicle = VehicleListing(
                    external_id=external_id,
                    listing_url=f"https://example.com/vehicle-{i+1}",
                    source_website="test_site",
                    **data
                )
                db.add(vehicle)
                sample_vehicles.append(vehicle)
        
        db.commit()
        
        # Refresh vehicles to get IDs
        for vehicle in sample_vehicles:
            db.refresh(vehicle)
        
        # Create price history
        for vehicle in sample_vehicles:
            # Create some price changes
            base_price = vehicle.price
            for days_ago in [10, 5, 1]:
                change_date = datetime.utcnow() - timedelta(days=days_ago)
                price_change = base_price * (0.95 + (days_ago * 0.02))  # Simulate price changes
                
                price_history = PriceHistory(
                    vehicle_id=vehicle.id,
                    price=price_change,
                    price_change=price_change - base_price,
                    change_percentage=((price_change - base_price) / base_price) * 100,
                    recorded_at=change_date
                )
                db.add(price_history)
        
        # Create sample alerts
        alert = Alert(
            user_id=test_user.id,
            name="Test Alert",
            make="BMW",
            max_price=30000,
            is_active=True
        )
        db.add(alert)
        
        # Create sample notifications
        for i in range(5):
            notification = Notification(
                user_id=test_user.id,
                notification_type=NotificationType.EMAIL,
                title=f"Test Notification {i+1}",
                message=f"This is test notification {i+1}",
                status=NotificationStatus.SENT if i < 4 else NotificationStatus.FAILED
            )
            db.add(notification)
        
        # Create sample comparison
        comparison = VehicleComparison(
            user_id=test_user.id,
            name="Test Comparison",
            description="Analytics test comparison"
        )
        db.add(comparison)
        
        db.commit()
        print("✅ Created comprehensive sample data")
        return test_user.id
        
    except Exception as e:
        print(f"❌ Sample data creation failed: {str(e)}")
        return None
    finally:
        db.close()


def test_market_overview():
    """Test market overview analytics"""
    print("\n🏪 Testing Market Overview Analytics")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        analytics_service = AnalyticsService(db)
        overview = analytics_service.get_market_overview(30)
        
        print("✅ Market overview generated")
        print(f"   Total Listings: {overview['total_listings']}")
        print(f"   New Listings (30d): {overview['new_listings']}")
        print(f"   Price Changes: {overview['price_changes']}")
        
        if overview['price_statistics']:
            stats = overview['price_statistics']
            print(f"   Average Price: €{stats['average_price']:,.0f}")
            print(f"   Price Range: €{stats['min_price']:,.0f} - €{stats['max_price']:,.0f}")
            print(f"   Listings with Price: {stats['listings_with_price']}")
        
        print(f"   Popular Makes: {len(overview['popular_makes'])}")
        for make_data in overview['popular_makes'][:3]:
            print(f"     - {make_data['make']}: {make_data['count']} listings")
        
        return True
        
    except Exception as e:
        print(f"❌ Market overview test failed: {str(e)}")
        return False
    finally:
        db.close()


def test_user_analytics():
    """Test user analytics"""
    print("\n👤 Testing User Analytics")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        user_id = create_sample_data()
        if not user_id:
            print("❌ No test user available")
            return False
        
        analytics_service = AnalyticsService(db)
        
        # Test individual user analytics
        user_analytics = analytics_service.get_user_analytics(user_id, 30)
        
        print("✅ User analytics generated")
        print(f"   User: {user_analytics['username']}")
        print(f"   Account Age: {user_analytics['account_age_days']} days")
        
        alerts = user_analytics['alerts']
        print(f"   Alerts - Total: {alerts['total']}, Active: {alerts['active']}")
        
        notifications = user_analytics['notifications']
        print(f"   Notifications - Total: {notifications['total']}, Sent: {notifications['sent']}, Failed: {notifications['failed']}")
        
        print(f"   Comparisons Created: {user_analytics['comparisons_created']}")
        
        # Test system-wide analytics
        system_analytics = analytics_service.get_user_analytics(None, 30)
        print(f"\n   System Analytics:")
        print(f"   Total Users: {system_analytics['total_users']}")
        print(f"   Active Users: {system_analytics['active_users']}")
        print(f"   New Users (30d): {system_analytics['new_users']}")
        
        engagement = system_analytics['user_engagement']
        print(f"   Alert Adoption: {engagement['alert_adoption_rate']:.1f}%")
        print(f"   Comparison Adoption: {engagement['comparison_adoption_rate']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ User analytics test failed: {str(e)}")
        return False
    finally:
        db.close()


def test_price_analytics():
    """Test price analytics"""
    print("\n💰 Testing Price Analytics")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        analytics_service = AnalyticsService(db)
        price_analytics = analytics_service.get_price_analytics(30)
        
        print("✅ Price analytics generated")
        print(f"   Total Price Changes: {price_analytics.get('total_price_changes', 0)}")
        
        if price_analytics.get('total_price_changes', 0) > 0:
            print(f"   Price Drops: {price_analytics['price_drops']}")
            print(f"   Price Increases: {price_analytics['price_increases']}")
            
            avg_change = price_analytics['average_change']
            print(f"   Average Change: €{avg_change['amount']:+.0f} ({avg_change['percentage']:+.1f}%)")
            
            largest = price_analytics['largest_changes']
            print(f"   Largest Drop: {largest['drop']['percentage']:.1f}% ({largest['drop']['vehicle']})")
            print(f"   Largest Increase: {largest['increase']['percentage']:.1f}% ({largest['increase']['vehicle']})")
            
            print(f"   Most Volatile Makes: {len(price_analytics['most_volatile_makes'])}")
            for make_data in price_analytics['most_volatile_makes'][:3]:
                print(f"     - {make_data['make']}: {make_data['avg_volatility']:.1f}% avg volatility")
        else:
            print("   No price changes in the period")
        
        return True
        
    except Exception as e:
        print(f"❌ Price analytics test failed: {str(e)}")
        return False
    finally:
        db.close()


def test_alert_effectiveness():
    """Test alert effectiveness analytics"""
    print("\n🔔 Testing Alert Effectiveness")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        analytics_service = AnalyticsService(db)
        effectiveness = analytics_service.get_alert_effectiveness(30)
        
        print("✅ Alert effectiveness analyzed")
        print(f"   Total Alerts: {effectiveness['total_alerts']}")
        print(f"   Active Alerts: {effectiveness['active_alerts']}")
        print(f"   Notifications Generated: {effectiveness['notifications_generated']}")
        print(f"   Delivery Success Rate: {effectiveness['delivery_success_rate']:.1f}%")
        
        status_breakdown = effectiveness['notification_status_breakdown']
        print(f"   Status Breakdown - Sent: {status_breakdown['sent']}, Failed: {status_breakdown['failed']}, Pending: {status_breakdown['pending']}")
        
        print(f"   Most Active Alerts: {len(effectiveness['most_active_alerts'])}")
        for alert_data in effectiveness['most_active_alerts'][:3]:
            print(f"     - {alert_data['alert_name']}: {alert_data['triggers']} triggers")
        
        return True
        
    except Exception as e:
        print(f"❌ Alert effectiveness test failed: {str(e)}")
        return False
    finally:
        db.close()


def test_system_performance():
    """Test system performance metrics"""
    print("\n⚡ Testing System Performance")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        analytics_service = AnalyticsService(db)
        performance = analytics_service.get_system_performance()
        
        print("✅ System performance analyzed")
        
        db_stats = performance['database_stats']
        print(f"   Database - Total: {db_stats['total_vehicles']}, Active: {db_stats['active_vehicles']}, Inactive: {db_stats['inactive_vehicles']}")
        
        quality = performance['data_quality']
        print(f"   Data Quality - Price Coverage: {quality['price_coverage']:.1f}%, Image Coverage: {quality['image_coverage']:.1f}%")
        
        activity = performance['recent_activity_24h']
        print(f"   Recent Activity (24h) - New Listings: {activity['new_listings']}, Price Changes: {activity['price_changes']}")
        
        print(f"   System Health: {performance['system_health']}")
        
        return True
        
    except Exception as e:
        print(f"❌ System performance test failed: {str(e)}")
        return False
    finally:
        db.close()


def test_insights_generation():
    """Test insights generation"""
    print("\n💡 Testing Insights Generation")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        analytics_service = AnalyticsService(db)
        insights = analytics_service.generate_insights(30)
        
        print("✅ Insights generated")
        print(f"   Total Insights: {len(insights)}")
        
        for i, insight in enumerate(insights, 1):
            print(f"   {i}. [{insight['level'].upper()}] {insight['title']}")
            print(f"      {insight['description']}")
            print(f"      Recommendation: {insight['recommendation']}")
        
        if not insights:
            print("   No specific insights generated (normal for test data)")
        
        return True
        
    except Exception as e:
        print(f"❌ Insights generation test failed: {str(e)}")
        return False
    finally:
        db.close()


def main():
    """Main test function"""
    print("🚀 Analytics System Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Setup test environment
    if not setup_test_environment():
        print("❌ Test environment setup failed")
        return False
    
    # Run tests
    tests = [
        ("Market Overview", test_market_overview),
        ("User Analytics", test_user_analytics),
        ("Price Analytics", test_price_analytics),
        ("Alert Effectiveness", test_alert_effectiveness),
        ("System Performance", test_system_performance),
        ("Insights Generation", test_insights_generation)
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
        print("🎉 All tests passed! Analytics system is working correctly.")
    else:
        print("⚠️ Some tests failed. Check implementation and logs.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
