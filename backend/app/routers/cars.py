"""
Car Listings API Endpoints

This module provides simplified REST API endpoints for accessing car listings
with the specific interface requested for the auto scouter application.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional
from datetime import datetime, timedelta
import math

from app.models.base import get_db
from app.models.automotive import VehicleListing
from app.schemas.automotive import VehicleListing as VehicleListingSchema

router = APIRouter()


@router.get("/", response_model=dict)
def get_cars(
    make: Optional[str] = Query(None, description="Filter by car manufacturer"),
    model: Optional[str] = Query(None, description="Filter by car model"),
    min_price: Optional[int] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[int] = Query(None, ge=0, description="Maximum price filter"),
    year: Optional[int] = Query(None, ge=1900, le=2030, description="Filter by year"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db)
):
    """
    Retrieve cars with query parameters for filtering
    
    Returns paginated results of car listings matching the search criteria.
    """
    try:
        # Build query with filters
        query = db.query(VehicleListing).filter(VehicleListing.is_active == True)
        
        # Apply filters
        if make:
            query = query.filter(VehicleListing.make.ilike(f"%{make}%"))
        
        if model:
            query = query.filter(VehicleListing.model.ilike(f"%{model}%"))
        
        if min_price is not None:
            query = query.filter(VehicleListing.price >= min_price)
        
        if max_price is not None:
            query = query.filter(VehicleListing.price <= max_price)
        
        if year is not None:
            query = query.filter(VehicleListing.year == year)
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination and ordering
        cars = query.order_by(desc(VehicleListing.scraped_at)).offset(offset).limit(limit).all()
        
        # Calculate pagination info
        total_pages = math.ceil(total_count / limit) if total_count > 0 else 0
        current_page = (offset // limit) + 1
        
        return {
            "cars": cars,
            "pagination": {
                "total_count": total_count,
                "total_pages": total_pages,
                "current_page": current_page,
                "limit": limit,
                "offset": offset,
                "has_next": offset + limit < total_count,
                "has_previous": offset > 0
            },
            "filters_applied": {
                "make": make,
                "model": model,
                "min_price": min_price,
                "max_price": max_price,
                "year": year
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving cars: {str(e)}"
        )


@router.get("/new", response_model=dict)
def get_new_cars(
    make: Optional[str] = Query(None, description="Filter by car manufacturer"),
    model: Optional[str] = Query(None, description="Filter by car model"),
    min_price: Optional[int] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[int] = Query(None, ge=0, description="Maximum price filter"),
    year: Optional[int] = Query(None, ge=1900, le=2030, description="Filter by year"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    hours: int = Query(48, ge=1, le=168, description="Hours to look back for new cars"),
    db: Session = Depends(get_db)
):
    """
    Retrieve recently added cars (last 24-48 hours)
    
    Returns cars sorted by date_added (newest first) with same filtering options.
    """
    try:
        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Build query with filters including time filter
        query = db.query(VehicleListing).filter(
            and_(
                VehicleListing.is_active == True,
                VehicleListing.scraped_at >= cutoff_time
            )
        )
        
        # Apply additional filters
        if make:
            query = query.filter(VehicleListing.make.ilike(f"%{make}%"))
        
        if model:
            query = query.filter(VehicleListing.model.ilike(f"%{model}%"))
        
        if min_price is not None:
            query = query.filter(VehicleListing.price >= min_price)
        
        if max_price is not None:
            query = query.filter(VehicleListing.price <= max_price)
        
        if year is not None:
            query = query.filter(VehicleListing.year == year)
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination and ordering (newest first)
        cars = query.order_by(desc(VehicleListing.scraped_at)).offset(offset).limit(limit).all()
        
        # Calculate pagination info
        total_pages = math.ceil(total_count / limit) if total_count > 0 else 0
        current_page = (offset // limit) + 1
        
        return {
            "cars": cars,
            "pagination": {
                "total_count": total_count,
                "total_pages": total_pages,
                "current_page": current_page,
                "limit": limit,
                "offset": offset,
                "has_next": offset + limit < total_count,
                "has_previous": offset > 0
            },
            "filters_applied": {
                "make": make,
                "model": model,
                "min_price": min_price,
                "max_price": max_price,
                "year": year,
                "hours_back": hours,
                "cutoff_time": cutoff_time.isoformat()
            },
            "metadata": {
                "endpoint": "new_cars",
                "description": f"Cars added in the last {hours} hours"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving new cars: {str(e)}"
        )


@router.get("/{car_id}", response_model=VehicleListingSchema)
def get_car_details(car_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific car"""
    car = db.query(VehicleListing).filter(
        VehicleListing.id == car_id,
        VehicleListing.is_active == True
    ).first()
    
    if not car:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Car not found"
        )
    
    return car


@router.get("/stats/summary", response_model=dict)
def get_cars_stats(db: Session = Depends(get_db)):
    """Get summary statistics about available cars"""
    try:
        from sqlalchemy import func
        
        # Basic counts
        total_cars = db.query(VehicleListing).filter(VehicleListing.is_active == True).count()
        
        # Price statistics
        price_stats = db.query(
            func.min(VehicleListing.price).label('min_price'),
            func.max(VehicleListing.price).label('max_price'),
            func.avg(VehicleListing.price).label('avg_price')
        ).filter(VehicleListing.is_active == True).first()
        
        # Most common makes (top 5)
        top_makes = db.query(
            VehicleListing.make,
            func.count(VehicleListing.id).label('count')
        ).filter(
            VehicleListing.is_active == True,
            VehicleListing.make.isnot(None)
        ).group_by(VehicleListing.make).order_by(
            func.count(VehicleListing.id).desc()
        ).limit(5).all()
        
        # Recent additions (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_count = db.query(VehicleListing).filter(
            VehicleListing.is_active == True,
            VehicleListing.scraped_at >= recent_cutoff
        ).count()
        
        return {
            "total_active_cars": total_cars,
            "price_statistics": {
                "min_price": float(price_stats.min_price) if price_stats.min_price else 0,
                "max_price": float(price_stats.max_price) if price_stats.max_price else 0,
                "average_price": float(price_stats.avg_price) if price_stats.avg_price else 0
            },
            "top_makes": [{"make": make, "count": count} for make, count in top_makes],
            "recent_additions_24h": recent_count,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting car statistics: {str(e)}"
        )
