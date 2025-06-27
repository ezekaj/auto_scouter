"""
Alert Matching Engine

This module implements the core logic for matching car listings against user alerts.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.scout import Alert, User
from app.models.automotive import VehicleListing
from app.models.notifications import Notification, AlertMatchLog, NotificationPreferences
from app.schemas.notifications import AlertMatchResult, NotificationType
from app.core.config import settings

logger = logging.getLogger(__name__)


class AlertMatchingEngine:
    """Core engine for matching car listings against user alerts"""
    
    def __init__(self, db: Session):
        self.db = db
        self.match_threshold = 0.7  # Minimum match score to trigger notification
        
    def run_alert_matching(self, 
                          check_since: Optional[datetime] = None,
                          max_listings: Optional[int] = None) -> AlertMatchLog:
        """
        Run the alert matching process for new listings
        
        Args:
            check_since: Only check listings added since this time
            max_listings: Maximum number of listings to process
            
        Returns:
            AlertMatchLog: Summary of the matching run
        """
        run_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        
        logger.info(f"Starting alert matching run {run_id}")
        
        # Create match log entry
        match_log = AlertMatchLog(
            run_id=run_id,
            started_at=started_at,
            status="running"
        )
        self.db.add(match_log)
        self.db.commit()
        
        try:
            # Get active alerts
            active_alerts = self._get_active_alerts()
            match_log.alerts_processed = len(active_alerts)
            
            # Get new listings to check
            new_listings = self._get_new_listings(check_since, max_listings)
            match_log.listings_checked = len(new_listings)
            
            logger.info(f"Processing {len(active_alerts)} alerts against {len(new_listings)} listings")
            
            matches_found = 0
            notifications_created = 0
            
            # Process each alert against new listings
            for alert in active_alerts:
                alert_matches = self._match_alert_against_listings(alert, new_listings)
                matches_found += len(alert_matches)
                
                # Create notifications for matches
                for match in alert_matches:
                    if self._should_create_notification(alert, match):
                        notification = self._create_notification(alert, match)
                        if notification:
                            notifications_created += 1
            
            # Update match log
            match_log.matches_found = matches_found
            match_log.notifications_created = notifications_created
            match_log.completed_at = datetime.utcnow()
            match_log.processing_time_seconds = (match_log.completed_at - started_at).total_seconds()
            match_log.status = "completed"
            
            self.db.commit()
            
            logger.info(f"Alert matching run {run_id} completed: "
                       f"{matches_found} matches, {notifications_created} notifications")
            
            return match_log
            
        except Exception as e:
            logger.error(f"Alert matching run {run_id} failed: {str(e)}")
            match_log.status = "failed"
            match_log.error_message = str(e)
            match_log.completed_at = datetime.utcnow()
            self.db.commit()
            raise
    
    def _get_active_alerts(self) -> List[Alert]:
        """Get all active alerts that should be processed"""
        return self.db.query(Alert).filter(
            Alert.is_active == True
        ).join(User).filter(
            User.is_active == True
        ).all()
    
    def _get_new_listings(self, 
                         check_since: Optional[datetime] = None,
                         max_listings: Optional[int] = None) -> List[VehicleListing]:
        """Get new listings to check against alerts"""
        query = self.db.query(VehicleListing).filter(
            VehicleListing.is_active == True
        )
        
        # Only check listings added since last run or specified time
        if check_since:
            query = query.filter(VehicleListing.scraped_at >= check_since)
        else:
            # Default: check listings from last 2 hours
            default_since = datetime.utcnow() - timedelta(hours=2)
            query = query.filter(VehicleListing.scraped_at >= default_since)
        
        # Order by newest first
        query = query.order_by(VehicleListing.scraped_at.desc())
        
        if max_listings:
            query = query.limit(max_listings)
        
        return query.all()
    
    def _match_alert_against_listings(self, 
                                    alert: Alert, 
                                    listings: List[VehicleListing]) -> List[AlertMatchResult]:
        """Match a single alert against a list of listings"""
        matches = []
        
        for listing in listings:
            match_result = self._calculate_match_score(alert, listing)
            if match_result and match_result.match_score >= self.match_threshold:
                matches.append(match_result)
        
        return matches
    
    def _calculate_match_score(self, alert: Alert, listing: VehicleListing) -> Optional[AlertMatchResult]:
        """
        Calculate match score between an alert and a listing
        
        Returns:
            AlertMatchResult if there's a potential match, None otherwise
        """
        matched_criteria = []
        score_components = []
        
        # Make/Model matching (required if specified)
        if alert.make:
            if not self._match_make(alert.make, listing.make):
                return None  # Hard requirement
            matched_criteria.append("make")
            score_components.append(1.0)
        
        if alert.model:
            if not self._match_model(alert.model, listing.model):
                return None  # Hard requirement
            matched_criteria.append("model")
            score_components.append(1.0)
        
        # Price range matching (required if specified)
        if alert.min_price is not None or alert.max_price is not None:
            price_match = self._match_price_range(alert, listing)
            if not price_match:
                return None  # Hard requirement
            matched_criteria.append("price")
            score_components.append(1.0)
        
        # Year matching (required if specified)
        if alert.year is not None:
            if not self._match_year(alert.year, listing.year):
                return None  # Hard requirement
            matched_criteria.append("year")
            score_components.append(1.0)
        
        # Optional criteria (add to score but don't exclude)
        if alert.fuel_type and self._match_fuel_type(alert.fuel_type, listing.fuel_type):
            matched_criteria.append("fuel_type")
            score_components.append(0.8)
        
        if alert.transmission and self._match_transmission(alert.transmission, listing.transmission):
            matched_criteria.append("transmission")
            score_components.append(0.8)
        
        if alert.city and self._match_location(alert.city, listing.city):
            matched_criteria.append("location")
            score_components.append(0.6)
        
        # Calculate overall match score
        if not score_components:
            return None
        
        match_score = sum(score_components) / len(score_components)
        
        return AlertMatchResult(
            alert_id=alert.id,
            listing_id=listing.id,
            match_score=match_score,
            matched_criteria=matched_criteria
        )
    
    def _match_make(self, alert_make: str, listing_make: str) -> bool:
        """Match car make with fuzzy matching"""
        if not alert_make or not listing_make:
            return False
        
        alert_make = alert_make.lower().strip()
        listing_make = listing_make.lower().strip()
        
        # Exact match
        if alert_make == listing_make:
            return True
        
        # Partial match (alert make contained in listing make or vice versa)
        if alert_make in listing_make or listing_make in alert_make:
            return True
        
        return False
    
    def _match_model(self, alert_model: str, listing_model: str) -> bool:
        """Match car model with fuzzy matching"""
        if not alert_model or not listing_model:
            return False
        
        alert_model = alert_model.lower().strip()
        listing_model = listing_model.lower().strip()
        
        # Exact match
        if alert_model == listing_model:
            return True
        
        # Partial match
        if alert_model in listing_model or listing_model in alert_model:
            return True
        
        return False
    
    def _match_price_range(self, alert: Alert, listing: VehicleListing) -> bool:
        """Match price range"""
        if not listing.price:
            return False
        
        if alert.min_price is not None and listing.price < alert.min_price:
            return False
        
        if alert.max_price is not None and listing.price > alert.max_price:
            return False
        
        return True
    
    def _match_year(self, alert_year: int, listing_year: Optional[int]) -> bool:
        """Match car year"""
        if not listing_year:
            return False
        
        return alert_year == listing_year
    
    def _match_fuel_type(self, alert_fuel_type: str, listing_fuel_type: Optional[str]) -> bool:
        """Match fuel type"""
        if not alert_fuel_type or not listing_fuel_type:
            return False
        
        return alert_fuel_type.lower() == listing_fuel_type.lower()
    
    def _match_transmission(self, alert_transmission: str, listing_transmission: Optional[str]) -> bool:
        """Match transmission type"""
        if not alert_transmission or not listing_transmission:
            return False
        
        return alert_transmission.lower() == listing_transmission.lower()
    
    def _match_location(self, alert_city: str, listing_city: Optional[str]) -> bool:
        """Match location with proximity-based matching"""
        if not alert_city or not listing_city:
            return False
        
        alert_city = alert_city.lower().strip()
        listing_city = listing_city.lower().strip()
        
        # Exact match
        if alert_city == listing_city:
            return True
        
        # Partial match (useful for metropolitan areas)
        if alert_city in listing_city or listing_city in alert_city:
            return True
        
        # TODO: Implement geographic proximity matching using coordinates
        
        return False
    
    def _should_create_notification(self, alert: Alert, match: AlertMatchResult) -> bool:
        """Determine if a notification should be created for this match"""
        # Check if notification already exists for this alert/listing combination
        existing_notification = self.db.query(Notification).filter(
            Notification.alert_id == alert.id,
            Notification.listing_id == match.listing_id
        ).first()
        
        if existing_notification:
            return False
        
        # Check rate limiting
        if not self._check_rate_limits(alert.user_id, alert.id):
            return False
        
        return True
    
    def _check_rate_limits(self, user_id: int, alert_id: int) -> bool:
        """Check if rate limits allow sending a notification"""
        # Get user preferences
        prefs = self.db.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == user_id
        ).first()
        
        if not prefs:
            # Use default limits
            max_per_day = 10
            max_per_alert_per_day = 5
        else:
            max_per_day = prefs.max_notifications_per_day
            max_per_alert_per_day = prefs.max_notifications_per_alert_per_day
        
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        # Check daily limit for user
        daily_count = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.created_at >= today_start
        ).count()
        
        if daily_count >= max_per_day:
            logger.info(f"Daily notification limit reached for user {user_id}")
            return False
        
        # Check daily limit per alert
        alert_daily_count = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.alert_id == alert_id,
            Notification.created_at >= today_start
        ).count()
        
        if alert_daily_count >= max_per_alert_per_day:
            logger.info(f"Daily alert notification limit reached for alert {alert_id}")
            return False
        
        return True
    
    def _create_notification(self, alert: Alert, match: AlertMatchResult) -> Optional[Notification]:
        """Create a notification for a matched alert"""
        try:
            # Get the listing details
            listing = self.db.query(VehicleListing).filter(
                VehicleListing.id == match.listing_id
            ).first()
            
            if not listing:
                return None
            
            # Create notification content
            title = f"New {listing.make} {listing.model} matches your alert"
            message = self._generate_notification_message(listing, match)
            content_data = self._generate_notification_content_data(listing, alert, match)
            
            # Create notification
            notification = Notification(
                user_id=alert.user_id,
                alert_id=alert.id,
                listing_id=listing.id,
                notification_type=NotificationType.IN_APP,  # Default to in-app
                title=title,
                message=message,
                content_data=content_data,
                priority=2  # Medium priority for alert matches
            )
            
            self.db.add(notification)
            self.db.commit()
            
            logger.info(f"Created notification {notification.id} for alert {alert.id}")
            return notification
            
        except Exception as e:
            logger.error(f"Failed to create notification for alert {alert.id}: {str(e)}")
            return None
    
    def _generate_notification_message(self, listing: VehicleListing, match: AlertMatchResult) -> str:
        """Generate notification message text"""
        price_str = f"€{listing.price:,.0f}" if listing.price else "Price on request"
        year_str = f" ({listing.year})" if listing.year else ""
        location_str = f" in {listing.city}" if listing.city else ""
        
        return (f"{listing.make} {listing.model}{year_str} - {price_str}"
                f"{location_str}. Match score: {match.match_score:.0%}")
    
    def _generate_notification_content_data(self, 
                                          listing: VehicleListing, 
                                          alert: Alert, 
                                          match: AlertMatchResult) -> Dict[str, Any]:
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
                "city": listing.city,
                "listing_url": listing.listing_url,
                "primary_image_url": listing.primary_image_url
            },
            "alert": {
                "id": alert.id,
                "criteria": {
                    "make": alert.make,
                    "model": alert.model,
                    "min_price": alert.min_price,
                    "max_price": alert.max_price,
                    "year": alert.year,
                    "fuel_type": alert.fuel_type,
                    "transmission": alert.transmission,
                    "city": alert.city
                }
            },
            "match": {
                "score": match.match_score,
                "matched_criteria": match.matched_criteria
            }
        }
