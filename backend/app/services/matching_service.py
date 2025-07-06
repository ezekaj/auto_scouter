"""
Vehicle Matching Service

Matches new vehicle listings against user alert criteria
Implements comprehensive filtering and scoring system
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.scout import User, Alert
from app.models.automotive import VehicleListing
from app.models.notifications import Notification, AlertMatchLog

logger = logging.getLogger(__name__)

class VehicleMatchingService:
    """Service for matching vehicles against user criteria"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_matches_for_vehicle(self, vehicle: VehicleListing) -> List[Tuple[Alert, float]]:
        """
        Find all alerts that match a given vehicle
        Returns list of (alert, match_score) tuples
        """
        matches = []
        
        # Get all active alerts
        active_alerts = self.db.query(Alert).filter(Alert.is_active == True).all()
        
        for alert in active_alerts:
            match_score = self._calculate_match_score(vehicle, alert)
            if match_score > 0:
                matches.append((alert, match_score))
        
        # Sort by match score (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Found {len(matches)} matching alerts for vehicle {vehicle.make} {vehicle.model}")
        return matches
    
    def find_vehicles_for_alert(self, alert: Alert, limit: int = 50) -> List[Tuple[VehicleListing, float]]:
        """
        Find vehicles that match a given alert
        Returns list of (vehicle, match_score) tuples
        """
        # Build query based on alert criteria
        query = self.db.query(VehicleListing).filter(VehicleListing.is_active == True)
        
        # Apply filters
        if alert.make:
            query = query.filter(VehicleListing.make.ilike(f"%{alert.make}%"))
        
        if alert.model:
            query = query.filter(VehicleListing.model.ilike(f"%{alert.model}%"))
        
        if alert.min_price:
            query = query.filter(VehicleListing.price >= alert.min_price)
        
        if alert.max_price:
            query = query.filter(VehicleListing.price <= alert.max_price)
        
        if alert.min_year:
            query = query.filter(VehicleListing.year >= alert.min_year)
        
        if alert.max_year:
            query = query.filter(VehicleListing.year <= alert.max_year)
        
        if alert.max_mileage:
            query = query.filter(VehicleListing.mileage <= alert.max_mileage)
        
        if alert.fuel_type:
            query = query.filter(VehicleListing.fuel_type.ilike(f"%{alert.fuel_type}%"))
        
        if alert.city:
            query = query.filter(VehicleListing.city.ilike(f"%{alert.city}%"))
        
        # Get vehicles and calculate match scores
        vehicles = query.limit(limit * 2).all()  # Get more than needed for scoring
        
        matches = []
        for vehicle in vehicles:
            match_score = self._calculate_match_score(vehicle, alert)
            if match_score > 0:
                matches.append((vehicle, match_score))
        
        # Sort by match score and limit results
        matches.sort(key=lambda x: x[1], reverse=True)
        matches = matches[:limit]
        
        logger.info(f"Found {len(matches)} matching vehicles for alert '{alert.name}'")
        return matches
    
    def _calculate_match_score(self, vehicle: VehicleListing, alert: Alert) -> float:
        """
        Calculate match score between vehicle and alert (0.0 to 1.0)
        Higher score means better match
        """
        score = 0.0
        total_criteria = 0
        
        # Make match (exact match gets full points, partial gets half)
        if alert.make:
            total_criteria += 1
            if vehicle.make and alert.make.lower() in vehicle.make.lower():
                if alert.make.lower() == vehicle.make.lower():
                    score += 1.0  # Exact match
                else:
                    score += 0.5  # Partial match
            else:
                return 0.0  # No make match = no match at all
        
        # Model match
        if alert.model:
            total_criteria += 1
            if vehicle.model and alert.model.lower() in vehicle.model.lower():
                if alert.model.lower() == vehicle.model.lower():
                    score += 1.0  # Exact match
                else:
                    score += 0.5  # Partial match
            else:
                return 0.0  # No model match = no match at all
        
        # Price range match
        if alert.min_price or alert.max_price:
            total_criteria += 1
            if vehicle.price:
                price_match = True
                if alert.min_price and vehicle.price < alert.min_price:
                    price_match = False
                if alert.max_price and vehicle.price > alert.max_price:
                    price_match = False
                
                if price_match:
                    # Calculate how well the price fits within the range
                    if alert.min_price and alert.max_price:
                        range_size = alert.max_price - alert.min_price
                        if range_size > 0:
                            # Score based on how close to the middle of the range
                            middle = (alert.min_price + alert.max_price) / 2
                            distance_from_middle = abs(vehicle.price - middle)
                            price_score = max(0.5, 1.0 - (distance_from_middle / (range_size / 2)))
                            score += price_score
                        else:
                            score += 1.0
                    else:
                        score += 1.0
                else:
                    return 0.0  # Price out of range = no match
        
        # Year range match
        if alert.min_year or alert.max_year:
            total_criteria += 1
            if vehicle.year:
                year_match = True
                if alert.min_year and vehicle.year < alert.min_year:
                    year_match = False
                if alert.max_year and vehicle.year > alert.max_year:
                    year_match = False
                
                if year_match:
                    score += 1.0
                else:
                    score += 0.3  # Slight penalty but not complete exclusion
        
        # Mileage match
        if alert.max_mileage:
            total_criteria += 1
            if vehicle.mileage:
                if vehicle.mileage <= alert.max_mileage:
                    # Score based on how low the mileage is
                    mileage_score = max(0.5, 1.0 - (vehicle.mileage / alert.max_mileage))
                    score += mileage_score
                else:
                    score += 0.2  # High mileage penalty but not complete exclusion
        
        # Fuel type match
        if alert.fuel_type:
            total_criteria += 1
            if vehicle.fuel_type and alert.fuel_type.lower() in vehicle.fuel_type.lower():
                score += 1.0
            else:
                score += 0.3  # Different fuel type penalty
        
        # Location match
        if alert.city:
            total_criteria += 1
            if vehicle.city and alert.city.lower() in vehicle.city.lower():
                score += 1.0
            else:
                score += 0.5  # Different city penalty but not complete exclusion
        
        # If no criteria specified, it's a match but with low score
        if total_criteria == 0:
            return 0.1
        
        # Calculate final score
        final_score = score / total_criteria
        
        # Bonus for newer vehicles
        if vehicle.year and vehicle.year >= 2020:
            final_score += 0.05
        
        # Bonus for lower mileage
        if vehicle.mileage and vehicle.mileage < 50000:
            final_score += 0.05
        
        # Ensure score is between 0 and 1
        final_score = min(1.0, max(0.0, final_score))
        
        return final_score
    
    def create_match_notification(self, alert: Alert, vehicle: VehicleListing, match_score: float) -> Optional[Notification]:
        """Create a notification for a vehicle match"""
        try:
            # Check if we already notified about this vehicle for this alert
            existing_log = self.db.query(AlertMatchLog).filter(
                AlertMatchLog.alert_id == alert.id,
                AlertMatchLog.vehicle_id == vehicle.id
            ).first()
            
            if existing_log:
                logger.debug(f"Already notified about vehicle {vehicle.id} for alert {alert.id}")
                return None
            
            # Check daily notification limit
            today = datetime.utcnow().date()
            today_notifications = self.db.query(Notification).filter(
                Notification.user_id == alert.user_id,
                Notification.alert_id == alert.id,
                Notification.created_at >= today
            ).count()
            
            if today_notifications >= alert.max_notifications_per_day:
                logger.info(f"Daily notification limit reached for alert {alert.id}")
                return None
            
            # Create notification
            notification = Notification(
                user_id=alert.user_id,
                alert_id=alert.id,
                title=f"New {vehicle.make} {vehicle.model} Match!",
                message=f"Found a {vehicle.year} {vehicle.make} {vehicle.model} for {vehicle.price} EUR in {vehicle.city}. Match score: {match_score:.0%}",
                notification_type="vehicle_match",
                priority="normal" if match_score < 0.8 else "high",
                data={
                    "vehicle_id": vehicle.id,
                    "match_score": match_score,
                    "vehicle_url": vehicle.listing_url
                }
            )
            
            self.db.add(notification)
            
            # Log the match
            match_log = AlertMatchLog(
                alert_id=alert.id,
                vehicle_id=vehicle.id,
                match_score=match_score,
                notification_sent=True
            )
            
            self.db.add(match_log)
            
            # Update alert statistics
            alert.last_triggered = datetime.utcnow()
            alert.trigger_count += 1
            
            self.db.commit()
            
            logger.info(f"Created notification for vehicle match: {vehicle.make} {vehicle.model} -> Alert '{alert.name}'")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating match notification: {e}")
            self.db.rollback()
            return None
    
    def process_new_vehicle_matches(self, vehicle: VehicleListing) -> int:
        """
        Process a new vehicle against all alerts and create notifications
        Returns number of notifications created
        """
        matches = self.find_matches_for_vehicle(vehicle)
        notifications_created = 0
        
        for alert, match_score in matches:
            # Only notify for good matches (score > 0.5)
            if match_score > 0.5:
                notification = self.create_match_notification(alert, vehicle, match_score)
                if notification:
                    notifications_created += 1
        
        logger.info(f"Created {notifications_created} notifications for vehicle {vehicle.make} {vehicle.model}")
        return notifications_created
    
    def get_user_matches(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get recent matches for a user"""
        user_alerts = self.db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.is_active == True
        ).all()
        
        all_matches = []
        
        for alert in user_alerts:
            vehicles = self.find_vehicles_for_alert(alert, limit=10)
            for vehicle, match_score in vehicles:
                all_matches.append({
                    "alert": alert,
                    "vehicle": vehicle,
                    "match_score": match_score,
                    "alert_name": alert.name
                })
        
        # Sort by match score and limit
        all_matches.sort(key=lambda x: x["match_score"], reverse=True)
        return all_matches[:limit]
