"""
Automotive API Endpoints

This module provides REST API endpoints for accessing scraped automotive data.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import math

from app.models.base import get_db
from app.services.automotive_service import AutomotiveService
from app.schemas.automotive import (
    VehicleListing, VehicleListingCreate, VehicleListingUpdate,
    VehicleSearchFilters, VehicleSearchResponse, VehicleAnalytics,
    ScrapingSession, ScrapingLog
)
from app.scraper.scheduler import scraper_scheduler
from app.scraper.monitoring import scraper_monitor
from app.scraper.compliance import compliance_manager

router = APIRouter()


@router.get("/vehicles", response_model=VehicleSearchResponse)
def search_vehicles(
    make: Optional[str] = Query(None, description="Vehicle make (e.g., Volkswagen, Peugeot)"),
    model: Optional[str] = Query(None, description="Vehicle model"),
    year_min: Optional[int] = Query(None, ge=1900, le=2030, description="Minimum year"),
    year_max: Optional[int] = Query(None, ge=1900, le=2030, description="Maximum year"),
    price_min: Optional[float] = Query(None, ge=0, description="Minimum price in EUR"),
    price_max: Optional[float] = Query(None, ge=0, description="Maximum price in EUR"),
    mileage_max: Optional[int] = Query(None, ge=0, description="Maximum mileage in km"),
    fuel_type: Optional[str] = Query(None, description="Fuel type (gasoline, diesel, electric, hybrid)"),
    transmission: Optional[str] = Query(None, description="Transmission type (manual, automatic)"),
    city: Optional[str] = Query(None, description="City location"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Search vehicles with various filters
    
    Returns paginated results of vehicle listings matching the search criteria.
    """
    try:
        # Create search filters
        filters = VehicleSearchFilters(
            make=make,
            model=model,
            year_min=year_min,
            year_max=year_max,
            price_min=price_min,
            price_max=price_max,
            mileage_max=mileage_max,
            fuel_type=fuel_type,
            transmission=transmission,
            city=city,
            is_active=True
        )
        
        # Search vehicles
        automotive_service = AutomotiveService(db)
        vehicles, total_count = automotive_service.search_vehicles(filters, page, page_size)
        
        # Calculate pagination info
        total_pages = math.ceil(total_count / page_size)
        
        return VehicleSearchResponse(
            vehicles=vehicles,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            filters_applied=filters
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching vehicles: {str(e)}"
        )


@router.get("/vehicles/{vehicle_id}", response_model=VehicleListing)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific vehicle"""
    automotive_service = AutomotiveService(db)
    vehicle = automotive_service.get_vehicle_by_id(vehicle_id)
    
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    return vehicle


@router.get("/analytics", response_model=Dict[str, Any])
def get_analytics(db: Session = Depends(get_db)):
    """Get analytics and statistics about the vehicle data"""
    try:
        automotive_service = AutomotiveService(db)
        
        # Get data quality metrics
        quality_metrics = automotive_service.get_data_quality_metrics()
        
        # Get monitoring data overview
        data_overview = scraper_monitor.get_data_overview(db)
        
        return {
            "data_quality": quality_metrics,
            "overview": data_overview,
            "timestamp": scraper_monitor.get_system_health()["timestamp"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting analytics: {str(e)}"
        )


@router.get("/makes", response_model=List[Dict[str, Any]])
def get_available_makes(db: Session = Depends(get_db)):
    """Get list of available vehicle makes with counts"""
    try:
        from sqlalchemy import func
        from app.models.automotive import VehicleListing
        
        makes = db.query(
            VehicleListing.make,
            func.count(VehicleListing.id).label('count')
        ).filter(
            VehicleListing.is_active == True,
            VehicleListing.make.isnot(None)
        ).group_by(VehicleListing.make).order_by(VehicleListing.make).all()
        
        return [{"make": make, "count": count} for make, count in makes]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting makes: {str(e)}"
        )


@router.get("/models", response_model=List[Dict[str, Any]])
def get_available_models(
    make: Optional[str] = Query(None, description="Filter models by make"),
    db: Session = Depends(get_db)
):
    """Get list of available vehicle models, optionally filtered by make"""
    try:
        from sqlalchemy import func
        from app.models.automotive import VehicleListing
        
        query = db.query(
            VehicleListing.make,
            VehicleListing.model,
            func.count(VehicleListing.id).label('count')
        ).filter(
            VehicleListing.is_active == True,
            VehicleListing.model.isnot(None)
        )
        
        if make:
            query = query.filter(VehicleListing.make.ilike(f"%{make}%"))
        
        models = query.group_by(
            VehicleListing.make, VehicleListing.model
        ).order_by(VehicleListing.make, VehicleListing.model).all()
        
        return [{"make": make, "model": model, "count": count} for make, model, count in models]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting models: {str(e)}"
        )


# Scraper Management Endpoints

@router.get("/scraper/status", response_model=Dict[str, Any])
def get_scraper_status():
    """Get current status of the scraper system"""
    try:
        scheduler_status = scraper_scheduler.get_job_status()
        compliance_status = compliance_manager.get_compliance_status()
        
        return {
            "scheduler": scheduler_status,
            "compliance": compliance_status,
            "timestamp": scraper_monitor.get_system_health()["timestamp"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting scraper status: {str(e)}"
        )


@router.post("/scraper/trigger", response_model=Dict[str, str])
def trigger_manual_scrape(background_tasks: BackgroundTasks):
    """Trigger a manual scraping run"""
    try:
        job_id = scraper_scheduler.trigger_manual_scrape()
        return {
            "message": "Manual scraping job triggered successfully",
            "job_id": job_id
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering scrape: {str(e)}"
        )


@router.get("/scraper/health", response_model=Dict[str, Any])
def get_scraper_health(db: Session = Depends(get_db)):
    """Get comprehensive health check of the scraper system"""
    try:
        return scraper_monitor.generate_monitoring_report(db)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting health status: {str(e)}"
        )


@router.get("/scraper/sessions", response_model=List[ScrapingSession])
def get_scraping_sessions(
    limit: int = Query(10, ge=1, le=100, description="Number of sessions to return"),
    db: Session = Depends(get_db)
):
    """Get recent scraping sessions"""
    try:
        from app.models.automotive import ScrapingSession
        from sqlalchemy import desc
        
        sessions = db.query(ScrapingSession).order_by(
            desc(ScrapingSession.started_at)
        ).limit(limit).all()
        
        return sessions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting sessions: {str(e)}"
        )


@router.get("/scraper/logs", response_model=List[ScrapingLog])
def get_scraping_logs(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    status: Optional[str] = Query(None, description="Filter by status (success, error)"),
    limit: int = Query(50, ge=1, le=200, description="Number of logs to return"),
    db: Session = Depends(get_db)
):
    """Get scraping logs with optional filters"""
    try:
        from app.models.automotive import ScrapingLog
        from sqlalchemy import desc
        
        query = db.query(ScrapingLog)
        
        if session_id:
            query = query.filter(ScrapingLog.session_id == session_id)
        
        if status:
            query = query.filter(ScrapingLog.status == status)
        
        logs = query.order_by(desc(ScrapingLog.started_at)).limit(limit).all()
        
        return logs
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting logs: {str(e)}"
        )


@router.get("/scraper/compliance", response_model=Dict[str, Any])
def get_compliance_info():
    """Get compliance and ethical guidelines information"""
    try:
        return compliance_manager.get_ethical_guidelines()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting compliance info: {str(e)}"
        )


# Data Management Endpoints

@router.post("/maintenance/cleanup", response_model=Dict[str, Any])
def run_data_cleanup(
    retention_days: int = Query(365, ge=30, le=1095, description="Data retention period in days"),
    db: Session = Depends(get_db)
):
    """Run data cleanup and maintenance tasks"""
    try:
        automotive_service = AutomotiveService(db)
        
        # Run cleanup
        cleanup_stats = automotive_service.cleanup_old_data(retention_days)
        
        # Deactivate old listings
        deactivated_count = automotive_service.deactivate_old_listings(days_old=30)
        cleanup_stats['deactivated_listings'] = deactivated_count
        
        return {
            "message": "Cleanup completed successfully",
            "statistics": cleanup_stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running cleanup: {str(e)}"
        )


@router.get("/maintenance/quality", response_model=Dict[str, Any])
def get_data_quality_report(db: Session = Depends(get_db)):
    """Get detailed data quality report"""
    try:
        automotive_service = AutomotiveService(db)
        quality_metrics = automotive_service.get_data_quality_metrics()
        
        # Get additional quality checks
        alerts = scraper_monitor.check_data_quality_alerts(db)
        
        return {
            "metrics": quality_metrics,
            "alerts": alerts,
            "timestamp": scraper_monitor.get_system_health()["timestamp"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting quality report: {str(e)}"
        )
