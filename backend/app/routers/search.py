"""
Advanced Search API Endpoints

This module provides comprehensive search functionality with advanced filtering,
sorting, and aggregation capabilities for vehicle listings.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import math

from app.models.base import get_db
from app.models.automotive import VehicleListing
from app.schemas.automotive import VehicleListing as VehicleListingSchema

router = APIRouter()


@router.get("/advanced", response_model=Dict[str, Any])
def advanced_search(
    # Basic filters
    make: Optional[str] = Query(None, description="Vehicle make"),
    model: Optional[str] = Query(None, description="Vehicle model"),
    year_min: Optional[int] = Query(None, ge=1900, le=2030),
    year_max: Optional[int] = Query(None, ge=1900, le=2030),
    price_min: Optional[float] = Query(None, ge=0),
    price_max: Optional[float] = Query(None, ge=0),
    
    # Technical specifications
    mileage_max: Optional[int] = Query(None, ge=0),
    fuel_type: Optional[str] = Query(None),
    transmission: Optional[str] = Query(None),
    body_type: Optional[str] = Query(None),
    engine_power_min: Optional[int] = Query(None, ge=0),
    engine_power_max: Optional[int] = Query(None, ge=0),
    
    # Location filters
    city: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    
    # Source filters
    source_website: Optional[str] = Query(None),
    source_country: Optional[str] = Query(None),
    
    # Quality filters
    min_data_quality: Optional[float] = Query(None, ge=0.0, le=1.0),
    exclude_duplicates: bool = Query(True),
    
    # Condition filters
    condition: Optional[str] = Query(None),
    max_owners: Optional[int] = Query(None, ge=0),
    no_accidents: bool = Query(False),
    
    # Sorting and pagination
    sort_by: str = Query("scraped_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    
    # Additional options
    include_images: bool = Query(False),
    include_price_history: bool = Query(False),
    
    db: Session = Depends(get_db)
):
    """
    Advanced search with comprehensive filtering and sorting options
    """
    try:
        # Build base query
        query = db.query(VehicleListing).filter(VehicleListing.is_active == True)
        
        # Apply duplicate filter
        if exclude_duplicates:
            query = query.filter(VehicleListing.is_duplicate == False)
        
        # Apply basic filters
        if make:
            query = query.filter(VehicleListing.make.ilike(f"%{make}%"))
        if model:
            query = query.filter(VehicleListing.model.ilike(f"%{model}%"))
        if year_min:
            query = query.filter(VehicleListing.year >= year_min)
        if year_max:
            query = query.filter(VehicleListing.year <= year_max)
        if price_min:
            query = query.filter(VehicleListing.price >= price_min)
        if price_max:
            query = query.filter(VehicleListing.price <= price_max)
        
        # Apply technical filters
        if mileage_max:
            query = query.filter(VehicleListing.mileage <= mileage_max)
        if fuel_type:
            query = query.filter(VehicleListing.fuel_type.ilike(f"%{fuel_type}%"))
        if transmission:
            query = query.filter(VehicleListing.transmission.ilike(f"%{transmission}%"))
        if body_type:
            query = query.filter(VehicleListing.body_type.ilike(f"%{body_type}%"))
        if engine_power_min:
            query = query.filter(VehicleListing.engine_power_hp >= engine_power_min)
        if engine_power_max:
            query = query.filter(VehicleListing.engine_power_hp <= engine_power_max)
        
        # Apply location filters
        if city:
            query = query.filter(VehicleListing.city.ilike(f"%{city}%"))
        if region:
            query = query.filter(VehicleListing.region.ilike(f"%{region}%"))
        if country:
            query = query.filter(VehicleListing.country.ilike(f"%{country}%"))
        
        # Apply source filters
        if source_website:
            query = query.filter(VehicleListing.source_website == source_website)
        if source_country:
            query = query.filter(VehicleListing.source_country == source_country)
        
        # Apply quality filters
        if min_data_quality:
            query = query.filter(VehicleListing.data_quality_score >= min_data_quality)
        
        # Apply condition filters
        if condition:
            query = query.filter(VehicleListing.condition == condition)
        if max_owners:
            query = query.filter(VehicleListing.previous_owners <= max_owners)
        if no_accidents:
            query = query.filter(VehicleListing.accident_history == False)
        
        # Apply sorting
        sort_field = getattr(VehicleListing, sort_by, VehicleListing.scraped_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_field))
        else:
            query = query.order_by(desc(sort_field))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        vehicles = query.offset(offset).limit(page_size).all()
        
        # Calculate pagination info
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0
        
        # Prepare response
        result = {
            "vehicles": vehicles,
            "pagination": {
                "total_count": total_count,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
                "has_next": page < total_pages,
                "has_previous": page > 1
            },
            "filters_applied": {
                "make": make,
                "model": model,
                "year_range": [year_min, year_max],
                "price_range": [price_min, price_max],
                "mileage_max": mileage_max,
                "fuel_type": fuel_type,
                "transmission": transmission,
                "body_type": body_type,
                "engine_power_range": [engine_power_min, engine_power_max],
                "location": {"city": city, "region": region, "country": country},
                "source": {"website": source_website, "country": source_country},
                "quality": {"min_data_quality": min_data_quality, "exclude_duplicates": exclude_duplicates},
                "condition": {"type": condition, "max_owners": max_owners, "no_accidents": no_accidents}
            },
            "sorting": {
                "field": sort_by,
                "order": sort_order
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing advanced search: {str(e)}"
        )


@router.get("/suggestions", response_model=Dict[str, List[str]])
def get_search_suggestions(
    field: str = Query(..., description="Field to get suggestions for"),
    query: Optional[str] = Query(None, description="Partial query to filter suggestions"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get search suggestions for autocomplete functionality
    """
    try:
        suggestions = []
        
        if field == "make":
            query_obj = db.query(VehicleListing.make).filter(
                and_(
                    VehicleListing.is_active == True,
                    VehicleListing.make.isnot(None)
                )
            ).distinct()
            
            if query:
                query_obj = query_obj.filter(VehicleListing.make.ilike(f"%{query}%"))
            
            suggestions = [row[0] for row in query_obj.limit(limit).all()]
            
        elif field == "model":
            query_obj = db.query(VehicleListing.model).filter(
                and_(
                    VehicleListing.is_active == True,
                    VehicleListing.model.isnot(None)
                )
            ).distinct()
            
            if query:
                query_obj = query_obj.filter(VehicleListing.model.ilike(f"%{query}%"))
            
            suggestions = [row[0] for row in query_obj.limit(limit).all()]
            
        elif field == "city":
            query_obj = db.query(VehicleListing.city).filter(
                and_(
                    VehicleListing.is_active == True,
                    VehicleListing.city.isnot(None)
                )
            ).distinct()
            
            if query:
                query_obj = query_obj.filter(VehicleListing.city.ilike(f"%{query}%"))
            
            suggestions = [row[0] for row in query_obj.limit(limit).all()]
            
        elif field == "fuel_type":
            query_obj = db.query(VehicleListing.fuel_type).filter(
                and_(
                    VehicleListing.is_active == True,
                    VehicleListing.fuel_type.isnot(None)
                )
            ).distinct()
            
            suggestions = [row[0] for row in query_obj.limit(limit).all()]
            
        elif field == "transmission":
            query_obj = db.query(VehicleListing.transmission).filter(
                and_(
                    VehicleListing.is_active == True,
                    VehicleListing.transmission.isnot(None)
                )
            ).distinct()
            
            suggestions = [row[0] for row in query_obj.limit(limit).all()]
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Suggestions not available for field: {field}"
            )
        
        return {
            "field": field,
            "suggestions": suggestions,
            "query": query,
            "count": len(suggestions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting search suggestions: {str(e)}"
        )


@router.get("/filters", response_model=Dict[str, Any])
def get_available_filters(db: Session = Depends(get_db)):
    """
    Get available filter options for the search interface
    """
    try:
        # Get unique values for various filter fields
        makes = db.query(VehicleListing.make).filter(
            and_(VehicleListing.is_active == True, VehicleListing.make.isnot(None))
        ).distinct().order_by(VehicleListing.make).all()
        
        fuel_types = db.query(VehicleListing.fuel_type).filter(
            and_(VehicleListing.is_active == True, VehicleListing.fuel_type.isnot(None))
        ).distinct().order_by(VehicleListing.fuel_type).all()
        
        transmissions = db.query(VehicleListing.transmission).filter(
            and_(VehicleListing.is_active == True, VehicleListing.transmission.isnot(None))
        ).distinct().order_by(VehicleListing.transmission).all()
        
        body_types = db.query(VehicleListing.body_type).filter(
            and_(VehicleListing.is_active == True, VehicleListing.body_type.isnot(None))
        ).distinct().order_by(VehicleListing.body_type).all()
        
        cities = db.query(VehicleListing.city).filter(
            and_(VehicleListing.is_active == True, VehicleListing.city.isnot(None))
        ).distinct().order_by(VehicleListing.city).limit(50).all()
        
        sources = db.query(VehicleListing.source_website).filter(
            VehicleListing.is_active == True
        ).distinct().order_by(VehicleListing.source_website).all()
        
        # Get price and year ranges
        price_range = db.query(
            func.min(VehicleListing.price).label('min_price'),
            func.max(VehicleListing.price).label('max_price')
        ).filter(VehicleListing.is_active == True).first()
        
        year_range = db.query(
            func.min(VehicleListing.year).label('min_year'),
            func.max(VehicleListing.year).label('max_year')
        ).filter(
            and_(VehicleListing.is_active == True, VehicleListing.year.isnot(None))
        ).first()
        
        return {
            "makes": [row[0] for row in makes],
            "fuel_types": [row[0] for row in fuel_types],
            "transmissions": [row[0] for row in transmissions],
            "body_types": [row[0] for row in body_types],
            "cities": [row[0] for row in cities],
            "sources": [row[0] for row in sources],
            "price_range": {
                "min": float(price_range.min_price) if price_range.min_price else 0,
                "max": float(price_range.max_price) if price_range.max_price else 0
            },
            "year_range": {
                "min": int(year_range.min_year) if year_range.min_year else 1900,
                "max": int(year_range.max_year) if year_range.max_year else datetime.now().year
            },
            "conditions": ["new", "used", "demo"],
            "sort_options": [
                {"field": "scraped_at", "label": "Date Added"},
                {"field": "price", "label": "Price"},
                {"field": "year", "label": "Year"},
                {"field": "mileage", "label": "Mileage"},
                {"field": "make", "label": "Make"},
                {"field": "model", "label": "Model"}
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting available filters: {str(e)}"
        )
