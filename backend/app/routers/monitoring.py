"""
Monitoring and Analytics API Endpoints

This module provides comprehensive monitoring, analytics, and system insights.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from app.models.base import get_db
from app.models.scout import User, Alert
from app.models.automotive import VehicleListing, ScrapingSession
from app.models.notifications import Notification
from app.services.health_check import health_service
from app.core.auth import get_current_active_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dashboard")
async def get_dashboard_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard data for the current user
    """
    now = datetime.utcnow()
    
    # User's alerts
    user_alerts = db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.is_active == True
    ).count()
    
    # User's notifications (last 30 days)
    user_notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.created_at >= now - timedelta(days=30)
    ).count()
    
    # Recent matches for user
    recent_matches = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.notification_type == 'vehicle_match',
        Notification.created_at >= now - timedelta(days=7)
    ).count()
    
    # Available vehicles matching user's criteria
    available_vehicles = db.query(VehicleListing).filter(
        VehicleListing.is_active == True
    ).count()
    
    return {
        "user_stats": {
            "active_alerts": user_alerts,
            "notifications_30d": user_notifications,
            "recent_matches_7d": recent_matches,
            "available_vehicles": available_vehicles
        },
        "timestamp": now.isoformat()
    }


@router.get("/analytics/vehicles")
async def get_vehicle_analytics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get vehicle analytics and trends
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Vehicle count by make
    vehicles_by_make = db.query(
        VehicleListing.make,
        func.count(VehicleListing.id).label('count')
    ).filter(
        VehicleListing.is_active == True,
        VehicleListing.scraped_at >= cutoff_date
    ).group_by(VehicleListing.make).order_by(desc('count')).limit(10).all()
    
    # Price distribution
    price_stats = db.query(
        func.min(VehicleListing.price).label('min_price'),
        func.max(VehicleListing.price).label('max_price'),
        func.avg(VehicleListing.price).label('avg_price'),
        func.count(VehicleListing.id).label('total_vehicles')
    ).filter(
        VehicleListing.is_active == True,
        VehicleListing.price.isnot(None),
        VehicleListing.scraped_at >= cutoff_date
    ).first()
    
    # Vehicles by fuel type
    vehicles_by_fuel = db.query(
        VehicleListing.fuel_type,
        func.count(VehicleListing.id).label('count')
    ).filter(
        VehicleListing.is_active == True,
        VehicleListing.scraped_at >= cutoff_date
    ).group_by(VehicleListing.fuel_type).all()
    
    # Daily vehicle additions
    daily_additions = db.query(
        func.date(VehicleListing.scraped_at).label('date'),
        func.count(VehicleListing.id).label('count')
    ).filter(
        VehicleListing.scraped_at >= cutoff_date
    ).group_by(func.date(VehicleListing.scraped_at)).order_by('date').all()
    
    return {
        "period_days": days,
        "vehicles_by_make": [{"make": row.make, "count": row.count} for row in vehicles_by_make],
        "price_statistics": {
            "min_price": float(price_stats.min_price) if price_stats.min_price else 0,
            "max_price": float(price_stats.max_price) if price_stats.max_price else 0,
            "avg_price": float(price_stats.avg_price) if price_stats.avg_price else 0,
            "total_vehicles": price_stats.total_vehicles
        },
        "vehicles_by_fuel_type": [{"fuel_type": row.fuel_type, "count": row.count} for row in vehicles_by_fuel],
        "daily_additions": [{"date": row.date.isoformat(), "count": row.count} for row in daily_additions],
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/analytics/alerts")
async def get_alert_analytics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get alert performance analytics
    """
    # User's alert performance
    alert_performance = db.query(
        Alert.id,
        Alert.name,
        Alert.created_at,
        func.count(Notification.id).label('notification_count')
    ).outerjoin(
        Notification,
        and_(
            Notification.alert_id == Alert.id,
            Notification.notification_type == 'vehicle_match'
        )
    ).filter(
        Alert.user_id == current_user.id
    ).group_by(Alert.id, Alert.name, Alert.created_at).all()
    
    # Most active alerts
    most_active = db.query(
        Alert.name,
        func.count(Notification.id).label('matches')
    ).join(
        Notification,
        Notification.alert_id == Alert.id
    ).filter(
        Alert.user_id == current_user.id,
        Notification.notification_type == 'vehicle_match',
        Notification.created_at >= datetime.utcnow() - timedelta(days=30)
    ).group_by(Alert.id, Alert.name).order_by(desc('matches')).limit(5).all()
    
    return {
        "alert_performance": [
            {
                "alert_id": row.id,
                "alert_name": row.name,
                "created_at": row.created_at.isoformat(),
                "total_matches": row.notification_count
            }
            for row in alert_performance
        ],
        "most_active_alerts_30d": [
            {"alert_name": row.name, "matches": row.matches}
            for row in most_active
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/analytics/scraping")
async def get_scraping_analytics(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    Get scraping performance analytics
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Scraping sessions
    sessions = db.query(ScrapingSession).filter(
        ScrapingSession.started_at >= cutoff_date
    ).order_by(desc(ScrapingSession.started_at)).all()
    
    # Success rate
    total_sessions = len(sessions)
    successful_sessions = len([s for s in sessions if s.status == 'completed'])
    success_rate = (successful_sessions / total_sessions * 100) if total_sessions > 0 else 0
    
    # Performance metrics
    completed_sessions = [s for s in sessions if s.status == 'completed' and s.duration_seconds]
    avg_duration = sum(s.duration_seconds for s in completed_sessions) / len(completed_sessions) if completed_sessions else 0
    
    total_vehicles_found = sum(s.total_vehicles_found or 0 for s in completed_sessions)
    total_vehicles_new = sum(s.total_vehicles_new or 0 for s in completed_sessions)
    
    # Daily scraping stats
    daily_stats = {}
    for session in sessions:
        date_key = session.started_at.date().isoformat()
        if date_key not in daily_stats:
            daily_stats[date_key] = {
                'sessions': 0,
                'vehicles_found': 0,
                'vehicles_new': 0,
                'successful_sessions': 0
            }
        
        daily_stats[date_key]['sessions'] += 1
        daily_stats[date_key]['vehicles_found'] += session.total_vehicles_found or 0
        daily_stats[date_key]['vehicles_new'] += session.total_vehicles_new or 0
        
        if session.status == 'completed':
            daily_stats[date_key]['successful_sessions'] += 1
    
    return {
        "period_days": days,
        "summary": {
            "total_sessions": total_sessions,
            "successful_sessions": successful_sessions,
            "success_rate_percent": round(success_rate, 1),
            "avg_duration_seconds": round(avg_duration, 1),
            "total_vehicles_found": total_vehicles_found,
            "total_vehicles_new": total_vehicles_new
        },
        "daily_stats": [
            {
                "date": date,
                **stats
            }
            for date, stats in sorted(daily_stats.items())
        ],
        "recent_sessions": [
            {
                "session_id": session.session_id,
                "started_at": session.started_at.isoformat(),
                "status": session.status,
                "duration_seconds": session.duration_seconds,
                "vehicles_found": session.total_vehicles_found,
                "vehicles_new": session.total_vehicles_new,
                "errors": session.total_errors
            }
            for session in sessions[:10]  # Last 10 sessions
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/system/health")
async def get_system_health():
    """
    Get comprehensive system health information
    """
    return health_service.get_comprehensive_health()


@router.get("/system/metrics")
async def get_system_metrics(
    db: Session = Depends(get_db)
):
    """
    Get system-wide metrics and statistics
    """
    now = datetime.utcnow()
    
    # Database statistics
    total_users = db.query(User).filter(User.is_active == True).count()
    total_alerts = db.query(Alert).filter(Alert.is_active == True).count()
    total_vehicles = db.query(VehicleListing).filter(VehicleListing.is_active == True).count()
    total_notifications = db.query(Notification).count()
    
    # Recent activity (24 hours)
    recent_users = db.query(User).filter(
        User.last_login >= now - timedelta(hours=24)
    ).count() if hasattr(User, 'last_login') else 0
    
    recent_vehicles = db.query(VehicleListing).filter(
        VehicleListing.scraped_at >= now - timedelta(hours=24)
    ).count()
    
    recent_notifications = db.query(Notification).filter(
        Notification.created_at >= now - timedelta(hours=24)
    ).count()
    
    # Performance metrics
    avg_response_time = 0  # Would be calculated from request logs
    error_rate = 0  # Would be calculated from error logs
    
    return {
        "database_stats": {
            "total_users": total_users,
            "total_alerts": total_alerts,
            "total_vehicles": total_vehicles,
            "total_notifications": total_notifications
        },
        "activity_24h": {
            "active_users": recent_users,
            "new_vehicles": recent_vehicles,
            "new_notifications": recent_notifications
        },
        "performance": {
            "avg_response_time_ms": avg_response_time,
            "error_rate_percent": error_rate,
            "uptime_seconds": (now - datetime(2024, 1, 1)).total_seconds()  # Placeholder
        },
        "timestamp": now.isoformat()
    }


@router.get("/export/data")
async def export_user_data(
    current_user: User = Depends(get_current_active_user),
    format: str = Query("json", regex="^(json|csv)$"),
    db: Session = Depends(get_db)
):
    """
    Export user's data (alerts, notifications, etc.)
    """
    # Get user's alerts
    alerts = db.query(Alert).filter(Alert.user_id == current_user.id).all()
    
    # Get user's notifications
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(desc(Notification.created_at)).all()
    
    export_data = {
        "user_info": {
            "username": current_user.username,
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat(),
            "export_date": datetime.utcnow().isoformat()
        },
        "alerts": [
            {
                "id": alert.id,
                "name": alert.name,
                "description": alert.description,
                "make": alert.make,
                "model": alert.model,
                "min_price": alert.min_price,
                "max_price": alert.max_price,
                "min_year": alert.min_year,
                "max_year": alert.max_year,
                "fuel_type": alert.fuel_type,
                "transmission": alert.transmission,
                "is_active": alert.is_active,
                "created_at": alert.created_at.isoformat()
            }
            for alert in alerts
        ],
        "notifications": [
            {
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "notification_type": notification.notification_type.value,
                "priority": notification.priority,
                "is_read": notification.is_read,
                "created_at": notification.created_at.isoformat()
            }
            for notification in notifications
        ]
    }
    
    if format == "json":
        return export_data
    else:
        # CSV format would require additional processing
        raise HTTPException(status_code=501, detail="CSV export not yet implemented")
