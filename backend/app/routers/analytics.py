"""
Advanced Analytics API Router

This module provides API endpoints for comprehensive analytics and insights.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.core.auth import get_current_user
from app.models.base import get_db
from app.models.scout import User
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/market-overview")
async def get_market_overview(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive market overview and statistics"""
    analytics_service = AnalyticsService(db)
    overview = analytics_service.get_market_overview(days)
    
    return {
        "market_overview": overview,
        "generated_at": "2025-07-06T01:15:00Z"  # Current timestamp
    }


@router.get("/user-analytics")
async def get_user_analytics(
    days: int = Query(30, ge=1, le=365),
    user_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user behavior analytics (own data or system-wide if admin)"""
    analytics_service = AnalyticsService(db)
    
    # If user_id is specified, only allow access to own data (unless admin)
    if user_id and user_id != current_user.id:
        # TODO: Add admin check here
        # For now, only allow users to see their own analytics
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only view your own analytics."
        )
    
    # If no user_id specified, show current user's analytics
    target_user_id = user_id or current_user.id
    
    analytics = analytics_service.get_user_analytics(target_user_id, days)
    
    return {
        "user_analytics": analytics,
        "generated_at": "2025-07-06T01:15:00Z"
    }


@router.get("/system-analytics")
async def get_system_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system-wide analytics (admin only)"""
    # TODO: Add admin check
    # For now, allow all authenticated users
    
    analytics_service = AnalyticsService(db)
    
    # Get system-wide user analytics
    user_analytics = analytics_service.get_user_analytics(None, days)
    
    return {
        "system_analytics": user_analytics,
        "generated_at": "2025-07-06T01:15:00Z"
    }


@router.get("/alert-effectiveness")
async def get_alert_effectiveness(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get alert effectiveness and performance analytics"""
    analytics_service = AnalyticsService(db)
    effectiveness = analytics_service.get_alert_effectiveness(days)
    
    return {
        "alert_effectiveness": effectiveness,
        "generated_at": "2025-07-06T01:15:00Z"
    }


@router.get("/price-analytics")
async def get_price_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive price analytics and trends"""
    analytics_service = AnalyticsService(db)
    price_analytics = analytics_service.get_price_analytics(days)
    
    return {
        "price_analytics": price_analytics,
        "generated_at": "2025-07-06T01:15:00Z"
    }


@router.get("/comparison-analytics")
async def get_comparison_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get vehicle comparison analytics"""
    analytics_service = AnalyticsService(db)
    comparison_analytics = analytics_service.get_comparison_analytics(days)
    
    return {
        "comparison_analytics": comparison_analytics,
        "generated_at": "2025-07-06T01:15:00Z"
    }


@router.get("/system-performance")
async def get_system_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system performance metrics"""
    analytics_service = AnalyticsService(db)
    performance = analytics_service.get_system_performance()
    
    return {
        "system_performance": performance,
        "generated_at": "2025-07-06T01:15:00Z"
    }


@router.get("/insights")
async def get_insights(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get actionable insights based on analytics"""
    analytics_service = AnalyticsService(db)
    insights = analytics_service.generate_insights(days)
    
    return {
        "insights": insights,
        "period_days": days,
        "total_insights": len(insights),
        "generated_at": "2025-07-06T01:15:00Z"
    }


@router.get("/dashboard")
async def get_dashboard_data(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard data combining all analytics"""
    analytics_service = AnalyticsService(db)
    
    # Gather all analytics data
    market_overview = analytics_service.get_market_overview(days)
    user_analytics = analytics_service.get_user_analytics(current_user.id, days)
    alert_effectiveness = analytics_service.get_alert_effectiveness(days)
    price_analytics = analytics_service.get_price_analytics(days)
    comparison_analytics = analytics_service.get_comparison_analytics(days)
    system_performance = analytics_service.get_system_performance()
    insights = analytics_service.generate_insights(days)
    
    return {
        "dashboard": {
            "market_overview": market_overview,
            "user_analytics": user_analytics,
            "alert_effectiveness": alert_effectiveness,
            "price_analytics": price_analytics,
            "comparison_analytics": comparison_analytics,
            "system_performance": system_performance,
            "insights": insights
        },
        "period_days": days,
        "generated_at": "2025-07-06T01:15:00Z",
        "user": {
            "id": current_user.id,
            "username": current_user.username
        }
    }


@router.get("/charts/price-trends")
async def get_price_trend_chart_data(
    days: int = Query(30, ge=7, le=365),
    make: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get price trend data formatted for charts"""
    from datetime import datetime, timedelta
    from sqlalchemy import and_, func
    from app.models.automotive import VehicleListing, PriceHistory
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Build query
    query = db.query(
        func.date(PriceHistory.recorded_at).label('date'),
        func.avg(PriceHistory.price).label('avg_price'),
        func.count(PriceHistory.id).label('price_count')
    ).join(VehicleListing).filter(
        PriceHistory.recorded_at >= cutoff_date
    )
    
    # Add filters if specified
    if make:
        query = query.filter(VehicleListing.make == make)
    if model:
        query = query.filter(VehicleListing.model == model)
    
    # Group by date and order
    results = query.group_by(func.date(PriceHistory.recorded_at)).order_by('date').all()
    
    # Format for chart
    chart_data = [
        {
            "date": str(result.date),
            "average_price": float(result.avg_price),
            "data_points": result.price_count
        }
        for result in results
    ]
    
    return {
        "chart_data": chart_data,
        "period_days": days,
        "filters": {
            "make": make,
            "model": model
        },
        "total_data_points": len(chart_data)
    }


@router.get("/charts/market-activity")
async def get_market_activity_chart_data(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get market activity data formatted for charts"""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from app.models.automotive import VehicleListing
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # New listings per day
    new_listings = db.query(
        func.date(VehicleListing.scraped_at).label('date'),
        func.count(VehicleListing.id).label('new_listings')
    ).filter(
        VehicleListing.scraped_at >= cutoff_date
    ).group_by(func.date(VehicleListing.scraped_at)).order_by('date').all()
    
    # Format for chart
    chart_data = [
        {
            "date": str(result.date),
            "new_listings": result.new_listings
        }
        for result in new_listings
    ]
    
    return {
        "chart_data": chart_data,
        "period_days": days,
        "total_data_points": len(chart_data)
    }


@router.get("/export")
async def export_analytics(
    format: str = Query("json", pattern="^(json|csv)$"),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export analytics data in various formats"""
    analytics_service = AnalyticsService(db)
    
    # Get comprehensive analytics
    data = {
        "market_overview": analytics_service.get_market_overview(days),
        "user_analytics": analytics_service.get_user_analytics(current_user.id, days),
        "price_analytics": analytics_service.get_price_analytics(days),
        "comparison_analytics": analytics_service.get_comparison_analytics(days),
        "system_performance": analytics_service.get_system_performance(),
        "export_metadata": {
            "exported_by": current_user.username,
            "export_date": "2025-07-06T01:15:00Z",
            "period_days": days,
            "format": format
        }
    }
    
    if format == "json":
        return data
    elif format == "csv":
        # For CSV, we'll return a simplified flat structure
        # In a real implementation, you'd use pandas or csv module
        return {
            "message": "CSV export not implemented yet",
            "data": data
        }
    
    return data
