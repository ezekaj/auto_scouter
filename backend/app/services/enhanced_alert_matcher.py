"""
Enhanced Alert Matching Engine

This module implements comprehensive logic for matching vehicle listings against user alerts
with advanced scoring and rate limiting.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import math

from app.models.scout import Alert, User
from app.models.automotive import VehicleListing
from app.models.notifications import (
    Notification, AlertMatchLog, NotificationPreferences, 
    NotificationQueue, NotificationFrequency
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class EnhancedAlertMatchingEngine:
    """Enhanced engine for matching vehicle listings against user alerts"""

    def __init__(self, db: Session):
        self.db = db
        self.match_threshold = 0.6  # Minimum match score to trigger notification
        self.perfect_match_threshold = 0.9  # Score for high-priority notifications

    def check_alert_match(self, alert: Alert, listing: VehicleListing) -> Optional[Dict[str, Any]]:
        """
        Check if a listing matches an alert and return match details
        
        Args:
            alert: The alert to check against
            listing: The vehicle listing to check
            
        Returns:
            Dict with match details if match found, None otherwise
        """
        if not alert.is_active:
            return None
            
        match_score = 0.0
        matched_criteria = []
        total_criteria = 0
        
        # Check make (high weight)
        if alert.make:
            total_criteria += 1
            if listing.make and alert.make.lower() == listing.make.lower():
                match_score += 0.25
                matched_criteria.append("make")
        
        # Check model (high weight)
        if alert.model:
            total_criteria += 1
            if listing.model and alert.model.lower() in listing.model.lower():
                match_score += 0.25
                matched_criteria.append("model")
        
        # Check price range (high weight)
        price_match = self._check_price_match(alert, listing)
        if price_match["has_criteria"]:
            total_criteria += 1
            match_score += price_match["score"] * 0.2
            if price_match["matches"]:
                matched_criteria.append("price")
        
        # Check year range
        year_match = self._check_year_match(alert, listing)
        if year_match["has_criteria"]:
            total_criteria += 1
            match_score += year_match["score"] * 0.1
            if year_match["matches"]:
                matched_criteria.append("year")
        
        # Check mileage
        if alert.max_mileage and listing.mileage:
            total_criteria += 1
            if listing.mileage <= alert.max_mileage:
                match_score += 0.1
                matched_criteria.append("mileage")
        
        # Check fuel type
        if alert.fuel_type:
            total_criteria += 1
            if listing.fuel_type and alert.fuel_type.lower() == listing.fuel_type.lower():
                match_score += 0.05
                matched_criteria.append("fuel_type")
        
        # Check transmission
        if alert.transmission:
            total_criteria += 1
            if listing.transmission and alert.transmission.lower() == listing.transmission.lower():
                match_score += 0.05
                matched_criteria.append("transmission")
        
        # Check body type
        if alert.body_type:
            total_criteria += 1
            if listing.body_type and alert.body_type.lower() == listing.body_type.lower():
                match_score += 0.05
                matched_criteria.append("body_type")
        
        # Check location
        location_match = self._check_location_match(alert, listing)
        if location_match["has_criteria"]:
            total_criteria += 1
            match_score += location_match["score"] * 0.05
            if location_match["matches"]:
                matched_criteria.append("location")
        
        # Normalize score based on criteria count
        if total_criteria > 0:
            match_score = match_score / max(total_criteria * 0.1, 1.0)  # Normalize to 0-1 range
        
        # Check if match meets threshold
        if match_score >= self.match_threshold:
            return {
                "listing_id": listing.id,
                "match_score": match_score,
                "matched_criteria": matched_criteria,
                "total_criteria": total_criteria,
                "is_perfect_match": match_score >= self.perfect_match_threshold
            }
        
        return None

    def _check_price_match(self, alert: Alert, listing: VehicleListing) -> Dict[str, Any]:
        """Check price match with scoring"""
        if not (alert.min_price or alert.max_price) or not listing.price:
            return {"has_criteria": False, "matches": False, "score": 0.0}
        
        price = listing.price
        min_price = alert.min_price or 0
        max_price = alert.max_price or float('inf')
        
        if min_price <= price <= max_price:
            # Perfect match
            return {"has_criteria": True, "matches": True, "score": 1.0}
        
        # Partial match with tolerance
        tolerance = 0.1  # 10% tolerance
        
        if price < min_price:
            diff_ratio = (min_price - price) / min_price
            if diff_ratio <= tolerance:
                score = 1.0 - (diff_ratio / tolerance) * 0.5
                return {"has_criteria": True, "matches": False, "score": score}
        
        if price > max_price:
            diff_ratio = (price - max_price) / max_price
            if diff_ratio <= tolerance:
                score = 1.0 - (diff_ratio / tolerance) * 0.5
                return {"has_criteria": True, "matches": False, "score": score}
        
        return {"has_criteria": True, "matches": False, "score": 0.0}

    def _check_year_match(self, alert: Alert, listing: VehicleListing) -> Dict[str, Any]:
        """Check year match with range support"""
        if not (alert.min_year or alert.max_year) or not listing.year:
            return {"has_criteria": False, "matches": False, "score": 0.0}
        
        year = listing.year
        min_year = alert.min_year or 1900
        max_year = alert.max_year or 2030
        
        if min_year <= year <= max_year:
            return {"has_criteria": True, "matches": True, "score": 1.0}
        
        # Partial match with 2-year tolerance
        tolerance = 2
        
        if year < min_year and (min_year - year) <= tolerance:
            score = 1.0 - ((min_year - year) / tolerance) * 0.5
            return {"has_criteria": True, "matches": False, "score": score}
        
        if year > max_year and (year - max_year) <= tolerance:
            score = 1.0 - ((year - max_year) / tolerance) * 0.5
            return {"has_criteria": True, "matches": False, "score": score}
        
        return {"has_criteria": True, "matches": False, "score": 0.0}

    def _check_location_match(self, alert: Alert, listing: VehicleListing) -> Dict[str, Any]:
        """Check location match with radius support"""
        if not alert.city or not listing.city:
            return {"has_criteria": False, "matches": False, "score": 0.0}
        
        # Exact city match
        if alert.city.lower() == listing.city.lower():
            return {"has_criteria": True, "matches": True, "score": 1.0}
        
        # Region match
        if alert.region and listing.region:
            if alert.region.lower() == listing.region.lower():
                return {"has_criteria": True, "matches": True, "score": 0.8}
        
        # TODO: Implement radius-based matching using coordinates
        # For now, partial string matching
        if alert.city.lower() in listing.city.lower() or listing.city.lower() in alert.city.lower():
            return {"has_criteria": True, "matches": False, "score": 0.5}
        
        return {"has_criteria": True, "matches": False, "score": 0.0}

    def create_notification(self, alert: Alert, listing: VehicleListing, match_details: Dict[str, Any]) -> Optional[Notification]:
        """Create a notification for a matched alert"""
        try:
            # Check rate limiting
            if not self._check_rate_limits(alert.user_id, alert.id):
                logger.info(f"Rate limit exceeded for alert {alert.id}")
                return None
            
            # Determine notification type based on user preferences
            notification_type = self._determine_notification_type(alert.user_id, match_details)
            
            # Create notification content
            title = f"New {listing.make} {listing.model} matches your alert"
            message = self._generate_notification_message(listing, match_details)
            content_data = self._generate_notification_content_data(listing, alert, match_details)
            
            # Determine priority
            priority = 3 if match_details["is_perfect_match"] else 2
            
            # Create notification
            notification = Notification(
                user_id=alert.user_id,
                alert_id=alert.id,
                listing_id=listing.id,
                notification_type=notification_type,
                title=title,
                message=message,
                content_data=content_data,
                priority=priority
            )
            
            self.db.add(notification)
            self.db.flush()  # Get the ID
            
            # Queue for delivery
            self._queue_notification(notification, match_details)
            
            # Update alert statistics
            alert.last_triggered = datetime.utcnow()
            alert.trigger_count += 1
            
            self.db.commit()
            
            logger.info(f"Created notification {notification.id} for alert {alert.id}")
            return notification
            
        except Exception as e:
            logger.error(f"Failed to create notification for alert {alert.id}: {str(e)}")
            self.db.rollback()
            return None

    def _determine_notification_type(self, user_id: int, match_details: Dict[str, Any]) -> str:
        """Determine the best notification type for the user"""
        prefs = self.db.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == user_id
        ).first()
        
        if not prefs:
            return "in_app"  # Default
        
        # For perfect matches, prefer immediate email if enabled
        if match_details["is_perfect_match"] and prefs.email_enabled:
            if prefs.email_frequency == NotificationFrequency.IMMEDIATE:
                return "email"
        
        # Otherwise use in-app
        return "in_app"

    def _queue_notification(self, notification: Notification, match_details: Dict[str, Any]):
        """Queue notification for delivery"""
        priority = 3 if match_details["is_perfect_match"] else 2
        
        queue_item = NotificationQueue(
            notification_id=notification.id,
            priority=priority,
            scheduled_for=datetime.utcnow()  # Send immediately
        )
        
        self.db.add(queue_item)

    def _check_rate_limits(self, user_id: int, alert_id: int) -> bool:
        """Check if notification can be sent based on rate limits"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get user preferences for limits
        prefs = self.db.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == user_id
        ).first()
        
        max_per_day = prefs.max_notifications_per_day if prefs else 10
        max_per_alert_per_day = prefs.max_notifications_per_alert_per_day if prefs else 5
        
        # Check daily limit for user
        daily_count = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.created_at >= today_start
        ).count()
        
        if daily_count >= max_per_day:
            return False
        
        # Check daily limit per alert
        alert_daily_count = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.alert_id == alert_id,
            Notification.created_at >= today_start
        ).count()
        
        return alert_daily_count < max_per_alert_per_day

    def _generate_notification_message(self, listing: VehicleListing, match_details: Dict[str, Any]) -> str:
        """Generate notification message text"""
        price_str = f"€{listing.price:,.0f}" if listing.price else "Price on request"
        year_str = f" ({listing.year})" if listing.year else ""
        location_str = f" in {listing.city}" if listing.city else ""
        
        match_quality = "Perfect match!" if match_details["is_perfect_match"] else f"Match score: {match_details['match_score']:.0%}"
        
        return (f"{listing.make} {listing.model}{year_str} - {price_str}"
                f"{location_str}. {match_quality}")

    def _generate_notification_content_data(self, listing: VehicleListing, alert: Alert, match_details: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured content data for the notification"""
        return {
            "listing": {
                "id": listing.id,
                "make": listing.make,
                "model": listing.model,
                "year": listing.year,
                "price": listing.price,
                "mileage": listing.mileage,
                "fuel_type": listing.fuel_type,
                "transmission": listing.transmission,
                "body_type": listing.body_type,
                "city": listing.city,
                "region": listing.region,
                "listing_url": listing.listing_url,
                "primary_image_url": listing.primary_image_url
            },
            "alert": {
                "id": alert.id,
                "name": alert.name,
                "criteria": {
                    "make": alert.make,
                    "model": alert.model,
                    "min_price": alert.min_price,
                    "max_price": alert.max_price,
                    "min_year": alert.min_year,
                    "max_year": alert.max_year,
                    "max_mileage": alert.max_mileage,
                    "fuel_type": alert.fuel_type,
                    "transmission": alert.transmission,
                    "body_type": alert.body_type,
                    "city": alert.city,
                    "region": alert.region
                }
            },
            "match": {
                "score": match_details["match_score"],
                "matched_criteria": match_details["matched_criteria"],
                "is_perfect_match": match_details["is_perfect_match"]
            }
        }
