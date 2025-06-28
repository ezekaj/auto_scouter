"""
Real-time API Endpoints

This module provides Server-Sent Events (SSE) and WebSocket endpoints
for real-time vehicle alerts and notifications.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.base import get_db
from app.models.scout import User, Alert
from app.models.automotive import VehicleListing
from app.models.notifications import Notification
from app.core.auth import get_current_active_user
from app.services.alert_matcher import AlertMatchingEngine

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/sse/notifications")
async def stream_notifications(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Server-Sent Events endpoint for real-time notifications
    
    Streams new notifications to the client as they are created.
    """
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for notifications"""
        last_check = datetime.utcnow()
        
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
        
        while True:
            try:
                # Check for new notifications since last check
                new_notifications = db.query(Notification).filter(
                    Notification.user_id == current_user.id,
                    Notification.created_at > last_check
                ).order_by(desc(Notification.created_at)).all()
                
                # Send new notifications
                for notification in new_notifications:
                    event_data = {
                        'type': 'notification',
                        'data': {
                            'id': notification.id,
                            'title': notification.title,
                            'message': notification.message,
                            'notification_type': notification.notification_type.value,
                            'priority': notification.priority,
                            'created_at': notification.created_at.isoformat(),
                            'is_read': notification.is_read
                        }
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
                
                # Update last check time
                if new_notifications:
                    last_check = new_notifications[0].created_at
                else:
                    last_check = datetime.utcnow()
                
                # Send heartbeat every 30 seconds
                heartbeat_data = {
                    'type': 'heartbeat',
                    'timestamp': datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(heartbeat_data)}\n\n"
                
                # Wait before next check
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in SSE stream: {e}")
                error_data = {
                    'type': 'error',
                    'message': 'Stream error occurred'
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                break
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.get("/sse/vehicle-matches")
async def stream_vehicle_matches(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Server-Sent Events endpoint for real-time vehicle matches
    
    Streams new vehicle matches for user's alerts as they are found.
    """
    
    async def match_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for vehicle matches"""
        last_check = datetime.utcnow()
        alert_matcher = AlertMatchingEngine(db)
        
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'user_id': current_user.id, 'timestamp': datetime.utcnow().isoformat()})}\n\n"
        
        # Get user's active alerts
        user_alerts = db.query(Alert).filter(
            Alert.user_id == current_user.id,
            Alert.is_active == True
        ).all()
        
        if not user_alerts:
            yield f"data: {json.dumps({'type': 'no_alerts', 'message': 'No active alerts found'})}\n\n"
            return
        
        while True:
            try:
                # Check for new vehicles since last check
                new_vehicles = db.query(VehicleListing).filter(
                    VehicleListing.scraped_at > last_check,
                    VehicleListing.is_active == True
                ).order_by(desc(VehicleListing.scraped_at)).limit(50).all()
                
                if new_vehicles:
                    # Check each alert against new vehicles
                    for alert in user_alerts:
                        matches = alert_matcher._match_alert_against_listings(alert, new_vehicles)
                        
                        for match in matches:
                            # Get the vehicle details
                            vehicle = next(v for v in new_vehicles if v.id == match.vehicle_id)
                            
                            match_data = {
                                'type': 'vehicle_match',
                                'data': {
                                    'alert_id': match.alert_id,
                                    'alert_name': alert.name,
                                    'vehicle_id': match.vehicle_id,
                                    'match_score': match.match_score,
                                    'matched_criteria': match.matched_criteria,
                                    'vehicle': {
                                        'make': vehicle.make,
                                        'model': vehicle.model,
                                        'year': vehicle.year,
                                        'price': vehicle.price,
                                        'mileage': vehicle.mileage,
                                        'fuel_type': vehicle.fuel_type,
                                        'transmission': vehicle.transmission,
                                        'city': vehicle.city,
                                        'listing_url': vehicle.listing_url,
                                        'scraped_at': vehicle.scraped_at.isoformat()
                                    }
                                }
                            }
                            yield f"data: {json.dumps(match_data)}\n\n"
                
                # Update last check time
                if new_vehicles:
                    last_check = new_vehicles[0].scraped_at
                else:
                    last_check = datetime.utcnow()
                
                # Send heartbeat every 30 seconds
                heartbeat_data = {
                    'type': 'heartbeat',
                    'active_alerts': len(user_alerts),
                    'timestamp': datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(heartbeat_data)}\n\n"
                
                # Wait before next check
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in vehicle match stream: {e}")
                error_data = {
                    'type': 'error',
                    'message': 'Match stream error occurred'
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                break
    
    return StreamingResponse(
        match_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.get("/sse/system-status")
async def stream_system_status(
    db: Session = Depends(get_db)
):
    """
    Server-Sent Events endpoint for system status updates
    
    Streams system health and activity information.
    """
    
    async def status_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for system status"""
        
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
        
        while True:
            try:
                # Get system statistics
                now = datetime.utcnow()
                
                # Recent activity stats
                recent_vehicles = db.query(VehicleListing).filter(
                    VehicleListing.scraped_at >= now - timedelta(hours=1)
                ).count()
                
                active_alerts = db.query(Alert).filter(
                    Alert.is_active == True
                ).count()
                
                recent_notifications = db.query(Notification).filter(
                    Notification.created_at >= now - timedelta(hours=1)
                ).count()
                
                total_vehicles = db.query(VehicleListing).filter(
                    VehicleListing.is_active == True
                ).count()
                
                status_data = {
                    'type': 'system_status',
                    'data': {
                        'timestamp': now.isoformat(),
                        'vehicles_last_hour': recent_vehicles,
                        'active_alerts': active_alerts,
                        'notifications_last_hour': recent_notifications,
                        'total_active_vehicles': total_vehicles,
                        'system_health': 'healthy' if recent_vehicles > 0 else 'warning'
                    }
                }
                yield f"data: {json.dumps(status_data)}\n\n"
                
                # Wait before next update
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in system status stream: {e}")
                error_data = {
                    'type': 'error',
                    'message': 'System status error occurred'
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                break
    
    return StreamingResponse(
        status_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )
