"""
Dashboard API Endpoints

This module provides comprehensive dashboard data endpoints for analytics,
statistics, and real-time monitoring of the vehicle scraping system.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.models.base import get_db
from app.models.automotive import VehicleListing, ScrapingSession, MultiSourceSession
from app.models.scout import Alert, User
from app.models.notifications import Notification
from app.core.auth import get_current_active_user
from app.scraper.monitoring import scraper_monitor

router = APIRouter()


@router.get("/overview", response_model=Dict[str, Any])
def get_dashboard_overview(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard overview with key metrics"""
    try:
        # Vehicle statistics
        total_vehicles = db.query(VehicleListing).filter(VehicleListing.is_active == True).count()
        
        # Recent vehicles (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_vehicles = db.query(VehicleListing).filter(
            and_(
                VehicleListing.is_active == True,
                VehicleListing.scraped_at >= recent_cutoff
            )
        ).count()
        
        # Price statistics
        price_stats = db.query(
            func.min(VehicleListing.price).label('min_price'),
            func.max(VehicleListing.price).label('max_price'),
            func.avg(VehicleListing.price).label('avg_price')
        ).filter(VehicleListing.is_active == True).first()
        
        # Source distribution
        source_stats = db.query(
            VehicleListing.source_website,
            func.count(VehicleListing.id).label('count')
        ).filter(VehicleListing.is_active == True).group_by(
            VehicleListing.source_website
        ).all()
        
        # User's alerts
        user_alerts = db.query(Alert).filter(
            and_(Alert.user_id == current_user.id, Alert.is_active == True)
        ).count()
        
        # Recent notifications for user
        recent_notifications = db.query(Notification).filter(
            and_(
                Notification.user_id == current_user.id,
                Notification.created_at >= recent_cutoff
            )
        ).count()
        
        # Scraping activity (last 7 days)
        week_cutoff = datetime.utcnow() - timedelta(days=7)
        scraping_sessions = db.query(ScrapingSession).filter(
            ScrapingSession.started_at >= week_cutoff
        ).count()
        
        # Multi-source sessions (last 7 days)
        multi_source_sessions = db.query(MultiSourceSession).filter(
            MultiSourceSession.started_at >= week_cutoff
        ).count()
        
        return {
            "vehicles": {
                "total_active": total_vehicles,
                "added_last_24h": recent_vehicles,
                "price_range": {
                    "min": float(price_stats.min_price) if price_stats.min_price else 0,
                    "max": float(price_stats.max_price) if price_stats.max_price else 0,
                    "average": float(price_stats.avg_price) if price_stats.avg_price else 0
                }
            },
            "sources": {
                "distribution": [
                    {"source": source, "count": count} 
                    for source, count in source_stats
                ]
            },
            "user_activity": {
                "active_alerts": user_alerts,
                "recent_notifications": recent_notifications
            },
            "scraping_activity": {
                "sessions_last_7_days": scraping_sessions,
                "multi_source_sessions_last_7_days": multi_source_sessions
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting dashboard overview: {str(e)}"
        )


@router.get("/analytics", response_model=Dict[str, Any])
def get_dashboard_analytics(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed analytics for the dashboard"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Daily vehicle additions
        daily_additions = db.query(
            func.date(VehicleListing.scraped_at).label('date'),
            func.count(VehicleListing.id).label('count')
        ).filter(
            and_(
                VehicleListing.scraped_at >= cutoff_date,
                VehicleListing.is_active == True
            )
        ).group_by(func.date(VehicleListing.scraped_at)).order_by('date').all()
        
        # Top makes and models
        top_makes = db.query(
            VehicleListing.make,
            func.count(VehicleListing.id).label('count')
        ).filter(
            and_(
                VehicleListing.scraped_at >= cutoff_date,
                VehicleListing.is_active == True,
                VehicleListing.make.isnot(None)
            )
        ).group_by(VehicleListing.make).order_by(
            func.count(VehicleListing.id).desc()
        ).limit(10).all()
        
        # Price distribution by ranges
        price_ranges = [
            (0, 10000, "Under €10k"),
            (10000, 20000, "€10k-€20k"),
            (20000, 30000, "€20k-€30k"),
            (30000, 50000, "€30k-€50k"),
            (50000, float('inf'), "Over €50k")
        ]
        
        price_distribution = []
        for min_price, max_price, label in price_ranges:
            if max_price == float('inf'):
                count = db.query(VehicleListing).filter(
                    and_(
                        VehicleListing.price >= min_price,
                        VehicleListing.is_active == True,
                        VehicleListing.scraped_at >= cutoff_date
                    )
                ).count()
            else:
                count = db.query(VehicleListing).filter(
                    and_(
                        VehicleListing.price >= min_price,
                        VehicleListing.price < max_price,
                        VehicleListing.is_active == True,
                        VehicleListing.scraped_at >= cutoff_date
                    )
                ).count()
            
            price_distribution.append({
                "range": label,
                "count": count,
                "min_price": min_price,
                "max_price": max_price if max_price != float('inf') else None
            })
        
        # Scraping performance metrics
        scraping_performance = db.query(
            func.avg(ScrapingSession.total_vehicles_found).label('avg_vehicles_per_session'),
            func.avg(ScrapingSession.duration_seconds).label('avg_duration_seconds'),
            func.sum(ScrapingSession.total_errors).label('total_errors')
        ).filter(ScrapingSession.started_at >= cutoff_date).first()
        
        return {
            "period": {
                "days": days,
                "start_date": cutoff_date.isoformat(),
                "end_date": datetime.utcnow().isoformat()
            },
            "daily_additions": [
                {"date": str(date), "count": count} 
                for date, count in daily_additions
            ],
            "top_makes": [
                {"make": make, "count": count} 
                for make, count in top_makes
            ],
            "price_distribution": price_distribution,
            "scraping_performance": {
                "avg_vehicles_per_session": float(scraping_performance.avg_vehicles_per_session) if scraping_performance.avg_vehicles_per_session else 0,
                "avg_duration_minutes": float(scraping_performance.avg_duration_seconds / 60) if scraping_performance.avg_duration_seconds else 0,
                "total_errors": int(scraping_performance.total_errors) if scraping_performance.total_errors else 0
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting dashboard analytics: {str(e)}"
        )


@router.get("/system-health", response_model=Dict[str, Any])
def get_system_health(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get system health and monitoring information"""
    try:
        # Get scraper monitoring data
        system_health = scraper_monitor.get_system_health()
        
        # Recent scraping sessions status
        recent_sessions = db.query(ScrapingSession).filter(
            ScrapingSession.started_at >= datetime.utcnow() - timedelta(hours=24)
        ).order_by(desc(ScrapingSession.started_at)).limit(10).all()
        
        # Multi-source session status
        recent_multi_sessions = db.query(MultiSourceSession).filter(
            MultiSourceSession.started_at >= datetime.utcnow() - timedelta(hours=24)
        ).order_by(desc(MultiSourceSession.started_at)).limit(5).all()
        
        # Database health
        db_health = {
            "total_vehicles": db.query(VehicleListing).count(),
            "active_vehicles": db.query(VehicleListing).filter(VehicleListing.is_active == True).count(),
            "total_users": db.query(User).count(),
            "active_alerts": db.query(Alert).filter(Alert.is_active == True).count()
        }
        
        return {
            "system": system_health,
            "database": db_health,
            "recent_scraping_sessions": [
                {
                    "id": session.id,
                    "source": session.source_website,
                    "status": session.status,
                    "vehicles_found": session.total_vehicles_found,
                    "duration_seconds": session.duration_seconds,
                    "started_at": session.started_at.isoformat()
                }
                for session in recent_sessions
            ],
            "recent_multi_source_sessions": [
                {
                    "id": session.id,
                    "session_id": session.session_id,
                    "status": session.status,
                    "completed_sources": session.completed_sources,
                    "total_vehicles": session.total_vehicles_found,
                    "started_at": session.started_at.isoformat()
                }
                for session in recent_multi_sessions
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting system health: {str(e)}"
        )
