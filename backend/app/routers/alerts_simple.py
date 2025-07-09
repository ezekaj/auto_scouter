"""
Simplified Alert Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory storage for testing (will replace with database later)
alerts_storage = []

@router.get("/", response_model=List[Dict[str, Any]])
def get_alerts():
    """Get all alerts (simplified version)"""
    return alerts_storage

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_alert(alert_data: Dict[str, Any]):
    """Create a new alert (simplified version)"""
    # Add a simple ID
    alert_data["id"] = len(alerts_storage) + 1
    alert_data["active"] = True
    
    alerts_storage.append(alert_data)
    
    return {
        "message": "Alert created successfully",
        "alert": alert_data
    }

@router.get("/{alert_id}")
def get_alert(alert_id: int):
    """Get a specific alert"""
    for alert in alerts_storage:
        if alert.get("id") == alert_id:
            return alert
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Alert not found"
    )

@router.delete("/{alert_id}")
def delete_alert(alert_id: int):
    """Delete an alert"""
    global alerts_storage
    
    for i, alert in enumerate(alerts_storage):
        if alert.get("id") == alert_id:
            deleted_alert = alerts_storage.pop(i)
            return {
                "message": "Alert deleted successfully",
                "alert": deleted_alert
            }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Alert not found"
    )

@router.get("/test/ping")
def test_ping():
    """Test endpoint to verify router is working"""
    return {
        "message": "Alerts router is working!",
        "total_alerts": len(alerts_storage)
    }
