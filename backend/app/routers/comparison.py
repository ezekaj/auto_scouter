"""
Vehicle Comparison API Router

This module provides API endpoints for vehicle comparison functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.scout import User
from app.models.comparison import VehicleComparison
from app.services.comparison_service import ComparisonService
from app.schemas.comparison import (
    VehicleComparisonCreate, VehicleComparisonUpdate, VehicleComparisonResponse,
    VehicleComparisonListResponse, VehicleComparisonItemCreate,
    DetailedComparisonResponse, QuickComparisonRequest, ComparisonAnalysis
)

router = APIRouter()


@router.post("/", response_model=VehicleComparisonResponse)
async def create_comparison(
    comparison_data: VehicleComparisonCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new vehicle comparison"""
    try:
        comparison_service = ComparisonService(db)
        comparison = comparison_service.create_comparison(current_user.id, comparison_data)
        
        return VehicleComparisonResponse.from_orm(comparison)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create comparison: {str(e)}"
        )


@router.get("/", response_model=VehicleComparisonListResponse)
async def get_user_comparisons(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's vehicle comparisons"""
    comparison_service = ComparisonService(db)
    comparisons, total = comparison_service.get_user_comparisons(
        current_user.id, page, limit
    )
    
    return VehicleComparisonListResponse(
        comparisons=[VehicleComparisonResponse.from_orm(c) for c in comparisons],
        total=total,
        page=page,
        limit=limit,
        has_more=total > page * limit
    )


@router.get("/{comparison_id}", response_model=VehicleComparisonResponse)
async def get_comparison(
    comparison_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific comparison"""
    comparison_service = ComparisonService(db)
    comparison = comparison_service.get_comparison_by_id(comparison_id, current_user.id)
    
    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparison not found"
        )
    
    return VehicleComparisonResponse.from_orm(comparison)


@router.put("/{comparison_id}", response_model=VehicleComparisonResponse)
async def update_comparison(
    comparison_id: int,
    update_data: VehicleComparisonUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a comparison"""
    # Check if user owns the comparison
    comparison = db.query(VehicleComparison).filter(
        VehicleComparison.id == comparison_id,
        VehicleComparison.user_id == current_user.id
    ).first()
    
    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparison not found"
        )
    
    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(comparison, field, value)
    
    db.commit()
    db.refresh(comparison)
    
    return VehicleComparisonResponse.from_orm(comparison)


@router.delete("/{comparison_id}")
async def delete_comparison(
    comparison_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a comparison"""
    comparison = db.query(VehicleComparison).filter(
        VehicleComparison.id == comparison_id,
        VehicleComparison.user_id == current_user.id
    ).first()
    
    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparison not found"
        )
    
    db.delete(comparison)
    db.commit()
    
    return {"message": "Comparison deleted successfully"}


@router.post("/{comparison_id}/vehicles/{vehicle_id}")
async def add_vehicle_to_comparison(
    comparison_id: int,
    vehicle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a vehicle to comparison"""
    try:
        comparison_service = ComparisonService(db)
        item = comparison_service.add_vehicle_to_comparison(
            comparison_id, vehicle_id, current_user.id
        )
        
        return {
            "message": "Vehicle added to comparison successfully",
            "item_id": item.id
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{comparison_id}/vehicles/{vehicle_id}")
async def remove_vehicle_from_comparison(
    comparison_id: int,
    vehicle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a vehicle from comparison"""
    comparison_service = ComparisonService(db)
    success = comparison_service.remove_vehicle_from_comparison(
        comparison_id, vehicle_id, current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found in comparison"
        )
    
    return {"message": "Vehicle removed from comparison successfully"}


@router.get("/{comparison_id}/analysis", response_model=ComparisonAnalysis)
async def get_comparison_analysis(
    comparison_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed analysis of a comparison"""
    comparison_service = ComparisonService(db)
    
    # Check if user has access to comparison
    comparison = comparison_service.get_comparison_by_id(comparison_id, current_user.id)
    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparison not found"
        )
    
    try:
        analysis = comparison_service.analyze_comparison(comparison_id)
        return analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze comparison: {str(e)}"
        )


@router.get("/{comparison_id}/detailed", response_model=DetailedComparisonResponse)
async def get_detailed_comparison(
    comparison_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed comparison with analysis"""
    comparison_service = ComparisonService(db)
    
    # Get comparison
    comparison = comparison_service.get_comparison_by_id(comparison_id, current_user.id)
    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparison not found"
        )
    
    # Get analysis
    analysis = comparison_service.analyze_comparison(comparison_id)
    
    # Build comparison matrix
    comparison_matrix = []
    for item in comparison.comparison_items:
        vehicle = item.vehicle
        matrix_item = {
            'vehicle_id': vehicle.id,
            'make': vehicle.make,
            'model': vehicle.model,
            'year': vehicle.year,
            'price': vehicle.price,
            'mileage': vehicle.mileage,
            'fuel_type': vehicle.fuel_type,
            'transmission': vehicle.transmission,
            'engine_power_hp': vehicle.engine_power_hp,
            'body_type': vehicle.body_type,
            'city': vehicle.city,
            'overall_score': item.overall_score,
            'price_score': item.price_score,
            'feature_score': item.feature_score,
            'condition_score': item.condition_score
        }
        comparison_matrix.append(matrix_item)
    
    # Build scoring breakdown
    scoring_breakdown = {}
    for item in comparison.comparison_items:
        vehicle_key = f"{item.vehicle.make}_{item.vehicle.model}_{item.vehicle.id}"
        scoring_breakdown[vehicle_key] = {
            'overall_score': item.overall_score or 0.0,
            'price_score': item.price_score or 0.0,
            'feature_score': item.feature_score or 0.0,
            'condition_score': item.condition_score or 0.0
        }
    
    return DetailedComparisonResponse(
        comparison=VehicleComparisonResponse.from_orm(comparison),
        analysis=analysis,
        comparison_matrix=comparison_matrix,
        scoring_breakdown=scoring_breakdown
    )


@router.post("/quick", response_model=ComparisonAnalysis)
async def quick_comparison(
    request: QuickComparisonRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform a quick comparison without saving"""
    if len(request.vehicle_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 vehicles are required for comparison"
        )
    
    # Create temporary comparison
    temp_comparison_data = VehicleComparisonCreate(
        name="Quick Comparison",
        vehicle_ids=request.vehicle_ids,
        comparison_criteria=request.criteria
    )
    
    try:
        comparison_service = ComparisonService(db)
        
        # Create temporary comparison
        comparison = comparison_service.create_comparison(current_user.id, temp_comparison_data)
        
        # Get analysis
        analysis = comparison_service.analyze_comparison(comparison.id)
        
        # Clean up temporary comparison
        db.delete(comparison)
        db.commit()
        
        return analysis
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick comparison failed: {str(e)}"
        )


@router.post("/{comparison_id}/favorite")
async def toggle_favorite_comparison(
    comparison_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle favorite status of a comparison"""
    comparison = db.query(VehicleComparison).filter(
        VehicleComparison.id == comparison_id,
        VehicleComparison.user_id == current_user.id
    ).first()
    
    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparison not found"
        )
    
    comparison.is_favorite = not comparison.is_favorite
    db.commit()
    
    return {
        "message": f"Comparison {'added to' if comparison.is_favorite else 'removed from'} favorites",
        "is_favorite": comparison.is_favorite
    }
