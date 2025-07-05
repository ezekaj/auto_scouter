"""
Advanced Analytics Service

This module provides comprehensive analytics functionality including:
- Market trend analysis
- User behavior analytics
- Vehicle performance metrics
- Price analytics and forecasting
- Alert effectiveness analysis
- System usage statistics
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, asc, text
from collections import defaultdict, Counter

from app.models.automotive import VehicleListing, PriceHistory
from app.models.scout import User, Alert
from app.models.notifications import Notification, NotificationStatus
from app.models.comparison import VehicleComparison, VehicleComparisonItem

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for advanced analytics and insights"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_market_overview(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive market overview"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total active listings
        total_listings = self.db.query(VehicleListing).filter(
            VehicleListing.is_active == True
        ).count()
        
        # New listings in period
        new_listings = self.db.query(VehicleListing).filter(
            and_(
                VehicleListing.scraped_at >= cutoff_date,
                VehicleListing.is_active == True
            )
        ).count()
        
        # Price statistics
        price_stats = self.db.query(
            func.avg(VehicleListing.price).label('avg_price'),
            func.min(VehicleListing.price).label('min_price'),
            func.max(VehicleListing.price).label('max_price'),
            func.count(VehicleListing.price).label('price_count')
        ).filter(
            and_(
                VehicleListing.is_active == True,
                VehicleListing.price.isnot(None)
            )
        ).first()
        
        # Most popular makes
        popular_makes = self.db.query(
            VehicleListing.make,
            func.count(VehicleListing.id).label('count')
        ).filter(
            VehicleListing.is_active == True
        ).group_by(VehicleListing.make).order_by(desc('count')).limit(10).all()
        
        # Price changes in period
        price_changes = self.db.query(PriceHistory).filter(
            and_(
                PriceHistory.recorded_at >= cutoff_date,
                PriceHistory.price_change.isnot(None)
            )
        ).count()
        
        return {
            "period_days": days,
            "total_listings": total_listings,
            "new_listings": new_listings,
            "price_statistics": {
                "average_price": float(price_stats.avg_price) if price_stats.avg_price else 0,
                "min_price": float(price_stats.min_price) if price_stats.min_price else 0,
                "max_price": float(price_stats.max_price) if price_stats.max_price else 0,
                "listings_with_price": price_stats.price_count or 0
            },
            "popular_makes": [
                {"make": make, "count": count} for make, count in popular_makes
            ],
            "price_changes": price_changes,
            "market_activity": {
                "new_listings_per_day": new_listings / days if days > 0 else 0,
                "price_changes_per_day": price_changes / days if days > 0 else 0
            }
        }
    
    def get_user_analytics(self, user_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """Get user behavior analytics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        if user_id:
            # Single user analytics
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found"}
            
            # User's alerts
            alerts = self.db.query(Alert).filter(Alert.user_id == user_id).all()
            active_alerts = [a for a in alerts if a.is_active]
            
            # User's notifications
            notifications = self.db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.created_at >= cutoff_date
                )
            ).all()
            
            # User's comparisons
            comparisons = self.db.query(VehicleComparison).filter(
                and_(
                    VehicleComparison.user_id == user_id,
                    VehicleComparison.created_at >= cutoff_date
                )
            ).count()
            
            return {
                "user_id": user_id,
                "username": user.username,
                "period_days": days,
                "alerts": {
                    "total": len(alerts),
                    "active": len(active_alerts),
                    "inactive": len(alerts) - len(active_alerts)
                },
                "notifications": {
                    "total": len(notifications),
                    "sent": len([n for n in notifications if n.status == NotificationStatus.SENT]),
                    "pending": len([n for n in notifications if n.status == NotificationStatus.PENDING]),
                    "failed": len([n for n in notifications if n.status == NotificationStatus.FAILED])
                },
                "comparisons_created": comparisons,
                "account_age_days": (datetime.utcnow() - user.created_at).days if user.created_at else 0
            }
        else:
            # System-wide user analytics
            total_users = self.db.query(User).count()
            active_users = self.db.query(User).filter(User.is_active == True).count()
            
            # New users in period
            new_users = self.db.query(User).filter(
                User.created_at >= cutoff_date
            ).count()
            
            # Users with alerts
            users_with_alerts = self.db.query(Alert.user_id).distinct().count()
            
            # Users with comparisons
            users_with_comparisons = self.db.query(VehicleComparison.user_id).distinct().count()
            
            return {
                "period_days": days,
                "total_users": total_users,
                "active_users": active_users,
                "new_users": new_users,
                "users_with_alerts": users_with_alerts,
                "users_with_comparisons": users_with_comparisons,
                "user_engagement": {
                    "alert_adoption_rate": (users_with_alerts / total_users * 100) if total_users > 0 else 0,
                    "comparison_adoption_rate": (users_with_comparisons / total_users * 100) if total_users > 0 else 0
                }
            }
    
    def get_alert_effectiveness(self, days: int = 30) -> Dict[str, Any]:
        """Analyze alert effectiveness and performance"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total alerts
        total_alerts = self.db.query(Alert).count()
        active_alerts = self.db.query(Alert).filter(Alert.is_active == True).count()
        
        # Notifications generated by alerts
        notifications = self.db.query(Notification).filter(
            Notification.created_at >= cutoff_date
        ).all()
        
        # Alert trigger frequency
        alert_triggers = defaultdict(int)
        for notification in notifications:
            if notification.content_data and 'alert' in notification.content_data:
                alert_name = notification.content_data['alert'].get('name', 'Unknown')
                alert_triggers[alert_name] += 1
        
        # Most active alerts
        most_active_alerts = sorted(alert_triggers.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Notification delivery success rate
        sent_notifications = len([n for n in notifications if n.status == NotificationStatus.SENT])
        failed_notifications = len([n for n in notifications if n.status == NotificationStatus.FAILED])
        
        success_rate = (sent_notifications / len(notifications) * 100) if notifications else 0
        
        return {
            "period_days": days,
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "notifications_generated": len(notifications),
            "delivery_success_rate": success_rate,
            "most_active_alerts": [
                {"alert_name": name, "triggers": count} for name, count in most_active_alerts
            ],
            "notification_status_breakdown": {
                "sent": sent_notifications,
                "failed": failed_notifications,
                "pending": len([n for n in notifications if n.status == NotificationStatus.PENDING])
            }
        }
    
    def get_price_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive price analytics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Price changes in period
        price_changes = self.db.query(PriceHistory).filter(
            and_(
                PriceHistory.recorded_at >= cutoff_date,
                PriceHistory.price_change.isnot(None)
            )
        ).all()
        
        if not price_changes:
            return {
                "period_days": days,
                "total_price_changes": 0,
                "message": "No price changes in the specified period"
            }
        
        # Analyze price movements
        price_drops = [p for p in price_changes if p.price_change < 0]
        price_increases = [p for p in price_changes if p.price_change > 0]
        
        # Average changes
        avg_price_change = sum(p.price_change for p in price_changes) / len(price_changes)
        avg_percentage_change = sum(p.change_percentage or 0 for p in price_changes) / len(price_changes)
        
        # Largest changes
        largest_drop = min(price_changes, key=lambda p: p.price_change or 0)
        largest_increase = max(price_changes, key=lambda p: p.price_change or 0)
        
        # Price volatility by make
        make_volatility = defaultdict(list)
        for change in price_changes:
            if change.vehicle and change.vehicle.make:
                make_volatility[change.vehicle.make].append(abs(change.change_percentage or 0))
        
        make_volatility_avg = {
            make: sum(changes) / len(changes) for make, changes in make_volatility.items()
        }
        most_volatile_makes = sorted(make_volatility_avg.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "period_days": days,
            "total_price_changes": len(price_changes),
            "price_drops": len(price_drops),
            "price_increases": len(price_increases),
            "average_change": {
                "amount": avg_price_change,
                "percentage": avg_percentage_change
            },
            "largest_changes": {
                "drop": {
                    "amount": largest_drop.price_change,
                    "percentage": largest_drop.change_percentage,
                    "vehicle": f"{largest_drop.vehicle.make} {largest_drop.vehicle.model}" if largest_drop.vehicle else "Unknown"
                },
                "increase": {
                    "amount": largest_increase.price_change,
                    "percentage": largest_increase.change_percentage,
                    "vehicle": f"{largest_increase.vehicle.make} {largest_increase.vehicle.model}" if largest_increase.vehicle else "Unknown"
                }
            },
            "most_volatile_makes": [
                {"make": make, "avg_volatility": volatility} for make, volatility in most_volatile_makes
            ]
        }
    
    def get_comparison_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get vehicle comparison analytics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Comparisons in period
        comparisons = self.db.query(VehicleComparison).filter(
            VehicleComparison.created_at >= cutoff_date
        ).all()
        
        # Most compared vehicles
        vehicle_comparison_count = defaultdict(int)
        for comparison in comparisons:
            for item in comparison.comparison_items:
                if item.vehicle:
                    key = f"{item.vehicle.make} {item.vehicle.model}"
                    vehicle_comparison_count[key] += 1
        
        most_compared = sorted(vehicle_comparison_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Popular comparison criteria
        criteria_usage = defaultdict(int)
        for comparison in comparisons:
            for criterion in comparison.comparison_criteria or []:
                criteria_usage[criterion] += 1
        
        popular_criteria = sorted(criteria_usage.items(), key=lambda x: x[1], reverse=True)
        
        # Average vehicles per comparison
        total_vehicles_compared = sum(len(c.comparison_items) for c in comparisons)
        avg_vehicles_per_comparison = total_vehicles_compared / len(comparisons) if comparisons else 0
        
        return {
            "period_days": days,
            "total_comparisons": len(comparisons),
            "total_vehicles_compared": total_vehicles_compared,
            "average_vehicles_per_comparison": avg_vehicles_per_comparison,
            "most_compared_vehicles": [
                {"vehicle": vehicle, "comparison_count": count} for vehicle, count in most_compared
            ],
            "popular_criteria": [
                {"criterion": criterion, "usage_count": count} for criterion, count in popular_criteria
            ],
            "public_comparisons": len([c for c in comparisons if c.is_public]),
            "favorite_comparisons": len([c for c in comparisons if c.is_favorite])
        }
    
    def get_system_performance(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        # Database statistics
        total_vehicles = self.db.query(VehicleListing).count()
        active_vehicles = self.db.query(VehicleListing).filter(VehicleListing.is_active == True).count()
        
        # Data quality metrics
        vehicles_with_price = self.db.query(VehicleListing).filter(
            VehicleListing.price.isnot(None)
        ).count()
        
        vehicles_with_images = self.db.query(VehicleListing).filter(
            VehicleListing.primary_image_url.isnot(None)
        ).count()
        
        # Recent activity
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_listings = self.db.query(VehicleListing).filter(
            VehicleListing.scraped_at >= last_24h
        ).count()
        
        recent_price_changes = self.db.query(PriceHistory).filter(
            PriceHistory.recorded_at >= last_24h
        ).count()
        
        return {
            "database_stats": {
                "total_vehicles": total_vehicles,
                "active_vehicles": active_vehicles,
                "inactive_vehicles": total_vehicles - active_vehicles
            },
            "data_quality": {
                "price_coverage": (vehicles_with_price / total_vehicles * 100) if total_vehicles > 0 else 0,
                "image_coverage": (vehicles_with_images / total_vehicles * 100) if total_vehicles > 0 else 0
            },
            "recent_activity_24h": {
                "new_listings": recent_listings,
                "price_changes": recent_price_changes
            },
            "system_health": "healthy" if active_vehicles > 0 and recent_listings > 0 else "needs_attention"
        }
    
    def generate_insights(self, days: int = 30) -> List[Dict[str, Any]]:
        """Generate actionable insights based on analytics"""
        insights = []
        
        # Get analytics data
        market_overview = self.get_market_overview(days)
        price_analytics = self.get_price_analytics(days)
        alert_effectiveness = self.get_alert_effectiveness(days)
        
        # Market insights
        if market_overview["new_listings"] > 0:
            daily_new_listings = market_overview["new_listings"] / days
            if daily_new_listings > 10:
                insights.append({
                    "type": "market_activity",
                    "level": "positive",
                    "title": "High Market Activity",
                    "description": f"Market is very active with {daily_new_listings:.1f} new listings per day",
                    "recommendation": "Good time for buyers to find deals"
                })
        
        # Price insights
        if price_analytics.get("total_price_changes", 0) > 0:
            drops_ratio = price_analytics["price_drops"] / price_analytics["total_price_changes"]
            if drops_ratio > 0.6:
                insights.append({
                    "type": "price_trend",
                    "level": "positive",
                    "title": "Favorable Price Trends",
                    "description": f"{drops_ratio*100:.1f}% of price changes were decreases",
                    "recommendation": "Consider setting up price drop alerts for vehicles of interest"
                })
        
        # Alert insights
        if alert_effectiveness.get("delivery_success_rate", 0) < 90:
            insights.append({
                "type": "system_performance",
                "level": "warning",
                "title": "Alert Delivery Issues",
                "description": f"Only {alert_effectiveness['delivery_success_rate']:.1f}% of notifications delivered successfully",
                "recommendation": "Check email configuration and notification settings"
            })
        
        return insights
