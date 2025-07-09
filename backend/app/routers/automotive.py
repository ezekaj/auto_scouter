"""
Automotive API Endpoints

This module provides REST API endpoints for accessing scraped automotive data.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional, Dict, Any
import math
import logging

from app.models.base import get_db
from app.services.automotive_service import AutomotiveService
from app.schemas.automotive import (
    VehicleListing, VehicleListingCreate, VehicleListingUpdate,
    VehicleSearchFilters, VehicleSearchResponse, VehicleAnalytics,
    ScrapingSession, ScrapingLog
)
# Scraper imports removed for simplified single-user deployment

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/vehicles/simple")
def get_vehicles_simple(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get vehicles without enum validation for frontend testing"""
    try:
        from app.models.automotive import VehicleListing as VehicleModel

        vehicles = db.query(VehicleModel).filter(
            VehicleModel.is_active == True
        ).limit(limit).all()

        # Convert to simple dict format
        result = []
        for vehicle in vehicles:
            result.append({
                "id": vehicle.id,
                "make": vehicle.make,
                "model": vehicle.model,
                "year": vehicle.year,
                "price": vehicle.price,
                "currency": vehicle.currency,
                "mileage": vehicle.mileage,
                "fuel_type": vehicle.fuel_type,
                "city": vehicle.city,
                "country": vehicle.country,
                "source_website": vehicle.source_website,
                "listing_url": vehicle.listing_url,
                "primary_image_url": vehicle.primary_image_url,
                "scraped_at": vehicle.scraped_at.isoformat() if vehicle.scraped_at else None
            })

        return {
            "vehicles": result,
            "total": len(result),
            "message": "Vehicles retrieved successfully"
        }

    except Exception as e:
        logger.error(f"Error getting vehicles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving vehicles: {str(e)}"
        )

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


@router.get("/new-cars", response_model=List[Dict[str, Any]])
def get_new_cars(
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    hours: int = Query(48, ge=1, le=168, description="Hours to look back for new cars"),
    db: Session = Depends(get_db)
):
    """Get recently added vehicles (alias for /cars/new endpoint)"""
    try:
        from datetime import datetime, timedelta
        from app.models.automotive import VehicleListing

        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # Get recent vehicles
        vehicles = db.query(VehicleListing).filter(
            and_(
                VehicleListing.is_active == True,
                VehicleListing.scraped_at >= cutoff_time
            )
        ).order_by(desc(VehicleListing.scraped_at)).limit(limit).all()

        # Convert SQLAlchemy objects to dictionaries, excluding internal attributes
        result = []
        for vehicle in vehicles:
            vehicle_dict = {key: value for key, value in vehicle.__dict__.items()
                          if not key.startswith('_')}
            result.append(vehicle_dict)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting new cars: {str(e)}"
        )


@router.get("/makes", response_model=List[str])
def get_makes(db: Session = Depends(get_db)):
    """Get list of available car makes"""
    try:
        from app.models.automotive import VehicleListing

        makes = db.query(VehicleListing.make).filter(
            and_(
                VehicleListing.is_active == True,
                VehicleListing.make.isnot(None),
                VehicleListing.make != ""
            )
        ).distinct().order_by(VehicleListing.make).all()

        return [make[0] for make in makes if make[0]]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting makes: {str(e)}"
        )


@router.get("/models", response_model=List[str])
def get_models(
    make: Optional[str] = Query(None, description="Filter models by make"),
    db: Session = Depends(get_db)
):
    """Get list of available car models, optionally filtered by make"""
    try:
        from app.models.automotive import VehicleListing

        query = db.query(VehicleListing.model).filter(
            and_(
                VehicleListing.is_active == True,
                VehicleListing.model.isnot(None),
                VehicleListing.model != ""
            )
        )

        if make:
            query = query.filter(VehicleListing.make.ilike(f"%{make}%"))

        models = query.distinct().order_by(VehicleListing.model).all()

        return [model[0] for model in models if model[0]]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting models: {str(e)}"
        )


@router.get("/analytics", response_model=Dict[str, Any])
def get_analytics(db: Session = Depends(get_db)):
    """Get analytics and statistics about the vehicle data"""
    try:
        automotive_service = AutomotiveService(db)

        # Get data quality metrics
        quality_metrics = automotive_service.get_data_quality_metrics()

        # Get monitoring data overview (disabled for single-user mode)
        data_overview = {"status": "disabled"}

        # Multi-source analytics
        from app.models.automotive import MultiSourceSession
        multi_source_stats = db.query(
            func.count(MultiSourceSession.id).label('total_sessions'),
            func.avg(MultiSourceSession.total_vehicles_found).label('avg_vehicles_per_session'),
            func.sum(MultiSourceSession.total_vehicles_found).label('total_vehicles_scraped')
        ).first()

        # Source distribution
        source_distribution = db.query(
            VehicleListing.source_website,
            VehicleListing.source_country,
            func.count(VehicleListing.id).label('count'),
            func.avg(VehicleListing.data_quality_score).label('avg_quality')
        ).filter(VehicleListing.is_active == True).group_by(
            VehicleListing.source_website, VehicleListing.source_country
        ).all()

        return {
            "data_quality": quality_metrics,
            "overview": data_overview,
            "multi_source": {
                "total_sessions": int(multi_source_stats.total_sessions) if multi_source_stats.total_sessions else 0,
                "avg_vehicles_per_session": float(multi_source_stats.avg_vehicles_per_session) if multi_source_stats.avg_vehicles_per_session else 0,
                "total_vehicles_scraped": int(multi_source_stats.total_vehicles_scraped) if multi_source_stats.total_vehicles_scraped else 0
            },
            "source_distribution": [
                {
                    "website": website,
                    "country": country,
                    "vehicle_count": count,
                    "avg_data_quality": float(avg_quality) if avg_quality else 0
                }
                for website, country, count, avg_quality in source_distribution
            ],
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


@router.post("/scraper/multi-source", response_model=Dict[str, Any])
def trigger_multi_source_scrape(
    max_vehicles_per_source: int = Query(50, ge=1, le=200, description="Maximum vehicles per source"),
    background_tasks: BackgroundTasks = None
):
    """Trigger multi-source scraping from all enabled sources"""
    try:
        # Start the multi-source scraping task
        task = scrape_all_sources_task.delay(max_vehicles_per_source=max_vehicles_per_source)

        return {
            "message": "Multi-source scraping started successfully",
            "task_id": task.id,
            "max_vehicles_per_source": max_vehicles_per_source,
            "status": "started"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting multi-source scraping: {str(e)}"
        )


@router.get("/scraper/sources", response_model=Dict[str, Any])
def get_scraper_sources():
    """Get status of all scraping sources"""
    try:
        return multi_source_scraper.get_source_status()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting source status: {str(e)}"
        )


@router.post("/scraper/sources/{source}/enable", response_model=Dict[str, str])
def enable_scraper_source(source: str):
    """Enable a specific scraping source"""
    try:
        success = multi_source_scraper.enable_source(source)
        if success:
            return {
                "message": f"Source '{source}' enabled successfully",
                "source": source,
                "status": "enabled"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to enable source '{source}'"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enabling source: {str(e)}"
        )


@router.post("/scraper/sources/{source}/disable", response_model=Dict[str, str])
def disable_scraper_source(source: str):
    """Disable a specific scraping source"""
    try:
        success = multi_source_scraper.disable_source(source)
        if success:
            return {
                "message": f"Source '{source}' disabled successfully",
                "source": source,
                "status": "disabled"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to disable source '{source}'"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error disabling source: {str(e)}"
        )


@router.post("/scraper/sources/{source}/scrape", response_model=Dict[str, Any])
def scrape_single_source(
    source: str,
    max_vehicles: int = Query(50, ge=1, le=200, description="Maximum vehicles to scrape")
):
    """Scrape from a single specific source"""
    try:
        result = multi_source_scraper.scrape_source(source, max_vehicles)

        return {
            "message": f"Scraping from '{source}' completed",
            "source": source,
            "success": result.success,
            "vehicles_count": result.vehicles_count,
            "duration_seconds": result.duration_seconds,
            "error": result.error_message
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scraping from source '{source}': {str(e)}"
        )


@router.get("/multi-source-sessions", response_model=Dict[str, Any])
def get_multi_source_sessions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, description="Filter by session status"),
    db: Session = Depends(get_db)
):
    """Get multi-source scraping sessions with pagination"""
    try:
        from app.models.automotive import MultiSourceSession

        query = db.query(MultiSourceSession)

        if status:
            query = query.filter(MultiSourceSession.status == status)

        total_count = query.count()
        sessions = query.order_by(desc(MultiSourceSession.started_at)).offset(offset).limit(limit).all()

        return {
            "sessions": [
                {
                    "id": session.id,
                    "session_id": session.session_id,
                    "status": session.status,
                    "trigger_type": session.trigger_type,
                    "total_sources": session.total_sources,
                    "completed_sources": session.completed_sources,
                    "failed_sources": session.failed_sources,
                    "total_vehicles_found": session.total_vehicles_found,
                    "total_duplicates_found": session.total_duplicates_found,
                    "total_errors": session.total_errors,
                    "started_at": session.started_at.isoformat() if session.started_at else None,
                    "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                    "duration_seconds": session.duration_seconds
                }
                for session in sessions
            ],
            "pagination": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_next": offset + limit < total_count,
                "has_previous": offset > 0
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting multi-source sessions: {str(e)}"
        )


@router.get("/multi-source-sessions/{session_id}", response_model=Dict[str, Any])
def get_multi_source_session_details(session_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific multi-source session"""
    try:
        from app.models.automotive import MultiSourceSession, ScrapingSession

        # Get the multi-source session
        multi_session = db.query(MultiSourceSession).filter(
            MultiSourceSession.session_id == session_id
        ).first()

        if not multi_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Multi-source session not found"
            )

        # Get individual scraping sessions for this multi-source session
        individual_sessions = db.query(ScrapingSession).filter(
            ScrapingSession.multi_source_session_id == session_id
        ).order_by(ScrapingSession.started_at).all()

        return {
            "multi_source_session": {
                "id": multi_session.id,
                "session_id": multi_session.session_id,
                "status": multi_session.status,
                "trigger_type": multi_session.trigger_type,
                "total_sources": multi_session.total_sources,
                "completed_sources": multi_session.completed_sources,
                "failed_sources": multi_session.failed_sources,
                "total_vehicles_found": multi_session.total_vehicles_found,
                "total_duplicates_found": multi_session.total_duplicates_found,
                "total_errors": multi_session.total_errors,
                "started_at": multi_session.started_at.isoformat() if multi_session.started_at else None,
                "completed_at": multi_session.completed_at.isoformat() if multi_session.completed_at else None,
                "duration_seconds": multi_session.duration_seconds,
                "performance_metrics": multi_session.performance_metrics
            },
            "individual_sessions": [
                {
                    "id": session.id,
                    "source_website": session.source_website,
                    "status": session.status,
                    "total_vehicles_found": session.total_vehicles_found,
                    "total_vehicles_processed": session.total_vehicles_processed,
                    "total_errors": session.total_errors,
                    "started_at": session.started_at.isoformat() if session.started_at else None,
                    "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                    "duration_seconds": session.duration_seconds,
                    "error_details": session.error_details
                }
                for session in individual_sessions
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting multi-source session details: {str(e)}"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scraping source: {str(e)}"
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
