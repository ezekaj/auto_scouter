"""
Alert Management API Endpoints

This module provides REST API endpoints for managing price/availability alerts.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.base import get_db
from app.models.scout import Alert
from app.schemas.alerts import AlertCreate, AlertUpdate, AlertResponse

router = APIRouter()


@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db)
):
    """Create a new price/availability alert"""
    # Validate that at least one filter criterion is provided
    filter_fields = [
        alert_data.make, alert_data.model, alert_data.min_price,
        alert_data.max_price, alert_data.min_year, alert_data.max_year,
        alert_data.fuel_type, alert_data.transmission, alert_data.city
    ]

    if not any(field is not None for field in filter_fields):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one filter criterion must be specified"
        )

    # Validate price range
    if alert_data.min_price is not None and alert_data.max_price is not None:
        if alert_data.min_price >= alert_data.max_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum price must be less than maximum price"
            )

    # Validate year range
    if alert_data.min_year is not None and alert_data.max_year is not None:
        if alert_data.min_year >= alert_data.max_year:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum year must be less than maximum year"
            )

    # Create alert (no user_id needed for single-user mode)
    db_alert = Alert(
        **alert_data.dict(exclude_unset=True)
    )

    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)

    return db_alert


@router.get("/", response_model=List[AlertResponse])
def get_alerts(
    db: Session = Depends(get_db),
    active_only: bool = Query(True, description="Return only active alerts")
):
    """Get all alerts (single-user mode)"""
    query = db.query(Alert)

    if active_only:
        query = query.filter(Alert.is_active == True)

    alerts = query.order_by(Alert.created_at.desc()).all()
    return alerts


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific alert by ID"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    return alert


@router.put("/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    update_data = alert_update.dict(exclude_unset=True)

    # Validate price range if both are being updated
    min_price = update_data.get("min_price", alert.min_price)
    max_price = update_data.get("max_price", alert.max_price)

    if min_price is not None and max_price is not None and min_price >= max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum price must be less than maximum price"
        )

    # Update alert
    for field, value in update_data.items():
        setattr(alert, field, value)

    db.commit()
    db.refresh(alert)

    return alert


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Delete a specific alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    db.delete(alert)
    db.commit()

    return None


@router.post("/{alert_id}/toggle", response_model=AlertResponse)
def toggle_alert_status(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Toggle alert active/inactive status"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    alert.is_active = not alert.is_active
    db.commit()
    db.refresh(alert)

    return alert


@router.get("/stats/summary", response_model=dict)
def get_alert_stats(
    db: Session = Depends(get_db)
):
    """Get alert statistics (single-user mode)"""
    total_alerts = db.query(Alert).count()
    active_alerts = db.query(Alert).filter(Alert.is_active == True).count()

    return {
        "total_alerts": total_alerts,
        "active_alerts": active_alerts,
        "inactive_alerts": total_alerts - active_alerts
    }
