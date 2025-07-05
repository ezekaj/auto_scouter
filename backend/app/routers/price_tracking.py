"""
Price Tracking API Router

This module provides API endpoints for vehicle price tracking functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.models.base import get_db
from app.models.scout import User
from app.models.automotive import VehicleListing, PriceHistory
from app.services.price_tracking_service import PriceTrackingService

router = APIRouter()


class PriceHistoryResponse(BaseModel):
    """Response model for price history"""
    id: int
    vehicle_id: int
    price: float
    currency: str
    price_change: Optional[float] = None
    change_percentage: Optional[float] = None
    market_position: Optional[str] = None
    days_on_market: int
    recorded_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class PriceTrendResponse(BaseModel):
    """Response model for price trend analysis"""
    trend: str
    total_change: float
    total_change_percentage: float
    average_price: float
    median_price: float
    min_price: float
    max_price: float
    price_volatility: float
    data_points: int
    first_recorded: Optional[datetime] = None
    last_recorded: Optional[datetime] = None


class PricePredictionResponse(BaseModel):
    """Response model for price predictions"""
    prediction: str
    confidence: float
    predicted_price: Optional[float] = None
    current_price: float
    predicted_change: Optional[float] = None
    predicted_change_percentage: Optional[float] = None
    prediction_range: Optional[Dict[str, float]] = None
    data_points_used: int
    prediction_horizon_days: int


class MarketComparisonResponse(BaseModel):
    """Response model for market comparison"""
    comparison: str
    market_position: Optional[str] = None
    vehicle_price: Optional[float] = None
    market_average: Optional[float] = None
    market_median: Optional[float] = None
    market_range: Optional[Dict[str, float]] = None
    price_difference_from_average: Optional[float] = None
    price_difference_percentage: Optional[float] = None
    percentile: Optional[float] = None
    similar_vehicles_count: Optional[int] = None


class PriceChangeRequest(BaseModel):
    """Request model for recording price changes"""
    new_price: float = Field(..., gt=0)
    source_website: Optional[str] = None
    source_url: Optional[str] = None


@router.get("/vehicles/{vehicle_id}/history", response_model=List[PriceHistoryResponse])
async def get_vehicle_price_history(
    vehicle_id: int,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get price history for a specific vehicle"""
    # Check if vehicle exists
    vehicle = db.query(VehicleListing).filter(VehicleListing.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    price_service = PriceTrackingService(db)
    price_history = price_service.get_price_history(vehicle_id, days)
    
    return [PriceHistoryResponse.from_orm(ph) for ph in price_history]


@router.get("/vehicles/{vehicle_id}/trend", response_model=PriceTrendResponse)
async def get_vehicle_price_trend(
    vehicle_id: int,
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get price trend analysis for a vehicle"""
    vehicle = db.query(VehicleListing).filter(VehicleListing.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    price_service = PriceTrackingService(db)
    trend_analysis = price_service.analyze_price_trend(vehicle_id, days)
    
    return PriceTrendResponse(**trend_analysis)


@router.get("/vehicles/{vehicle_id}/prediction", response_model=PricePredictionResponse)
async def get_price_prediction(
    vehicle_id: int,
    days_ahead: int = Query(30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get price prediction for a vehicle"""
    vehicle = db.query(VehicleListing).filter(VehicleListing.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    price_service = PriceTrackingService(db)
    prediction = price_service.predict_price_trend(vehicle_id, days_ahead)
    
    return PricePredictionResponse(**prediction)


@router.get("/vehicles/{vehicle_id}/market-comparison", response_model=MarketComparisonResponse)
async def get_market_comparison(
    vehicle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get market comparison for a vehicle"""
    vehicle = db.query(VehicleListing).filter(VehicleListing.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    price_service = PriceTrackingService(db)
    comparison = price_service.get_market_comparison(vehicle_id)
    
    return MarketComparisonResponse(**comparison)


@router.post("/vehicles/{vehicle_id}/record-price", response_model=PriceHistoryResponse)
async def record_price_change(
    vehicle_id: int,
    price_data: PriceChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record a new price for a vehicle (admin/scraper use)"""
    # Note: In production, this might be restricted to admin users or scraper services
    
    vehicle = db.query(VehicleListing).filter(VehicleListing.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    try:
        price_service = PriceTrackingService(db)
        price_history = price_service.record_price_change(
            vehicle_id=vehicle_id,
            new_price=price_data.new_price,
            source_website=price_data.source_website,
            source_url=price_data.source_url
        )
        
        return PriceHistoryResponse.from_orm(price_history)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record price change: {str(e)}"
        )


@router.get("/vehicles/{vehicle_id}/alerts-summary")
async def get_price_alerts_summary(
    vehicle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary of price alerts for a vehicle"""
    vehicle = db.query(VehicleListing).filter(VehicleListing.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    price_service = PriceTrackingService(db)
    alerts_summary = price_service.get_price_alerts_summary(vehicle_id)
    
    return alerts_summary


@router.get("/statistics")
async def get_price_statistics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall price statistics for the system"""
    price_service = PriceTrackingService(db)
    statistics = price_service.get_price_statistics(days)
    
    return statistics


@router.get("/trending-vehicles")
async def get_trending_vehicles(
    limit: int = Query(10, ge=1, le=50),
    trend_type: str = Query("price_drops", regex="^(price_drops|price_increases|most_volatile)$"),
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trending vehicles based on price changes"""
    from sqlalchemy import desc, asc
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Base query for recent price changes
    base_query = db.query(PriceHistory).filter(
        and_(
            PriceHistory.recorded_at >= cutoff_date,
            PriceHistory.change_percentage.isnot(None)
        )
    )
    
    if trend_type == "price_drops":
        # Vehicles with the largest price drops
        trending = base_query.filter(
            PriceHistory.change_percentage < 0
        ).order_by(asc(PriceHistory.change_percentage)).limit(limit).all()
        
    elif trend_type == "price_increases":
        # Vehicles with the largest price increases
        trending = base_query.filter(
            PriceHistory.change_percentage > 0
        ).order_by(desc(PriceHistory.change_percentage)).limit(limit).all()
        
    else:  # most_volatile
        # Vehicles with the most price changes
        from sqlalchemy import func, abs
        trending = base_query.order_by(
            desc(func.abs(PriceHistory.change_percentage))
        ).limit(limit).all()
    
    # Format response
    result = []
    for price_history in trending:
        vehicle = price_history.vehicle
        result.append({
            "vehicle_id": vehicle.id,
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year,
            "current_price": price_history.price,
            "price_change": price_history.price_change,
            "change_percentage": price_history.change_percentage,
            "recorded_at": price_history.recorded_at,
            "days_on_market": price_history.days_on_market,
            "market_position": price_history.market_position
        })
    
    return {
        "trend_type": trend_type,
        "period_days": days,
        "vehicles": result,
        "total_found": len(result)
    }


@router.get("/vehicles/{vehicle_id}/detailed-analysis")
async def get_detailed_price_analysis(
    vehicle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive price analysis for a vehicle"""
    vehicle = db.query(VehicleListing).filter(VehicleListing.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    price_service = PriceTrackingService(db)
    
    # Gather all analysis data
    price_history = price_service.get_price_history(vehicle_id, 90)
    trend_analysis = price_service.analyze_price_trend(vehicle_id, 30)
    prediction = price_service.predict_price_trend(vehicle_id, 30)
    market_comparison = price_service.get_market_comparison(vehicle_id)
    alerts_summary = price_service.get_price_alerts_summary(vehicle_id)
    
    return {
        "vehicle": {
            "id": vehicle.id,
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year,
            "current_price": vehicle.price,
            "currency": vehicle.currency
        },
        "price_history": [PriceHistoryResponse.from_orm(ph) for ph in price_history[-10:]],  # Last 10 entries
        "trend_analysis": trend_analysis,
        "price_prediction": prediction,
        "market_comparison": market_comparison,
        "alerts_summary": alerts_summary,
        "analysis_date": datetime.utcnow()
    }
