"""
Automotive Data Service

This module provides database operations for automotive data,
including deduplication, validation, and historical tracking.
"""

import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text
from sqlalchemy.exc import IntegrityError

from app.models.automotive import (
    VehicleListing, VehicleImage, PriceHistory, 
    ScrapingLog, ScrapingSession, DataQualityMetric
)
from app.schemas.automotive import (
    VehicleListingCreate, VehicleListingUpdate, VehicleImageCreate,
    VehicleSearchFilters, ScrapingLogCreate, ScrapingSessionCreate
)
import logging

logger = logging.getLogger(__name__)


class AutomotiveService:
    """Service class for automotive data operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_vehicle_listing(self, vehicle_data: Dict[str, Any]) -> Optional[VehicleListing]:
        """
        Create a new vehicle listing with deduplication
        
        Args:
            vehicle_data: Dictionary containing vehicle information
        
        Returns:
            VehicleListing object or None if creation failed
        """
        try:
            # Check for existing listing
            existing = self.find_duplicate_listing(vehicle_data)
            if existing:
                logger.info(f"Duplicate listing found for {vehicle_data.get('external_id')}, updating instead")
                return self.update_vehicle_listing(existing.id, vehicle_data)
            
            # Extract images data
            images_data = vehicle_data.pop('images', [])
            
            # Create vehicle listing
            vehicle = VehicleListing(**vehicle_data)
            self.db.add(vehicle)
            self.db.flush()  # Get the ID without committing
            
            # Add images
            for image_data in images_data:
                image = VehicleImage(vehicle_id=vehicle.id, **image_data)
                self.db.add(image)
            
            # Create initial price history entry
            if vehicle.price:
                price_history = PriceHistory(
                    vehicle_id=vehicle.id,
                    price=vehicle.price,
                    currency=vehicle.currency
                )
                self.db.add(price_history)
            
            self.db.commit()
            logger.info(f"Created new vehicle listing: {vehicle.make} {vehicle.model} (ID: {vehicle.id})")
            return vehicle
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating vehicle listing: {e}")
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating vehicle listing: {e}")
            return None
    
    def update_vehicle_listing(self, vehicle_id: int, update_data: Dict[str, Any]) -> Optional[VehicleListing]:
        """
        Update an existing vehicle listing
        
        Args:
            vehicle_id: ID of the vehicle to update
            update_data: Dictionary containing updated information
        
        Returns:
            Updated VehicleListing object or None if update failed
        """
        try:
            vehicle = self.db.query(VehicleListing).filter(VehicleListing.id == vehicle_id).first()
            if not vehicle:
                logger.warning(f"Vehicle with ID {vehicle_id} not found")
                return None
            
            # Track price changes
            old_price = vehicle.price
            new_price = update_data.get('price')
            
            # Extract images data
            images_data = update_data.pop('images', [])
            
            # Update vehicle fields
            for field, value in update_data.items():
                if hasattr(vehicle, field) and value is not None:
                    setattr(vehicle, field, value)
            
            vehicle.last_updated = datetime.utcnow()
            
            # Update images if provided
            if images_data:
                # Remove old images
                self.db.query(VehicleImage).filter(VehicleImage.vehicle_id == vehicle_id).delete()
                
                # Add new images
                for image_data in images_data:
                    image = VehicleImage(vehicle_id=vehicle_id, **image_data)
                    self.db.add(image)
            
            # Track price change
            if new_price and new_price != old_price:
                price_change = new_price - old_price if old_price else 0
                change_percentage = (price_change / old_price * 100) if old_price else 0
                
                price_history = PriceHistory(
                    vehicle_id=vehicle_id,
                    price=new_price,
                    currency=update_data.get('currency', 'EUR'),
                    price_change=price_change,
                    change_percentage=change_percentage
                )
                self.db.add(price_history)
                
                logger.info(f"Price change tracked for vehicle {vehicle_id}: {old_price} -> {new_price}")
            
            self.db.commit()
            logger.info(f"Updated vehicle listing: {vehicle.make} {vehicle.model} (ID: {vehicle.id})")
            return vehicle
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating vehicle listing {vehicle_id}: {e}")
            return None
    
    def find_duplicate_listing(self, vehicle_data: Dict[str, Any]) -> Optional[VehicleListing]:
        """
        Find potential duplicate listings based on various criteria
        
        Args:
            vehicle_data: Vehicle data to check for duplicates
        
        Returns:
            Existing VehicleListing if duplicate found, None otherwise
        """
        # Check by external_id first (most reliable)
        if vehicle_data.get('external_id'):
            existing = self.db.query(VehicleListing).filter(
                VehicleListing.external_id == vehicle_data['external_id']
            ).first()
            if existing:
                return existing
        
        # Check by listing_url
        if vehicle_data.get('listing_url'):
            existing = self.db.query(VehicleListing).filter(
                VehicleListing.listing_url == vehicle_data['listing_url']
            ).first()
            if existing:
                return existing
        
        # Check by VIN if available
        if vehicle_data.get('vin'):
            existing = self.db.query(VehicleListing).filter(
                VehicleListing.vin == vehicle_data['vin']
            ).first()
            if existing:
                return existing
        
        # Check by combination of make, model, year, mileage (fuzzy match)
        if all(key in vehicle_data for key in ['make', 'model', 'year', 'mileage']):
            mileage_tolerance = 1000  # Allow 1000km difference
            
            existing = self.db.query(VehicleListing).filter(
                and_(
                    VehicleListing.make == vehicle_data['make'],
                    VehicleListing.model == vehicle_data['model'],
                    VehicleListing.year == vehicle_data['year'],
                    VehicleListing.mileage.between(
                        vehicle_data['mileage'] - mileage_tolerance,
                        vehicle_data['mileage'] + mileage_tolerance
                    ),
                    VehicleListing.is_active == True
                )
            ).first()
            if existing:
                return existing
        
        return None
    
    def search_vehicles(self, filters: VehicleSearchFilters, page: int = 1, page_size: int = 20) -> Tuple[List[VehicleListing], int]:
        """
        Search vehicles with filters and pagination
        
        Args:
            filters: Search filters
            page: Page number (1-based)
            page_size: Number of results per page
        
        Returns:
            Tuple of (vehicles list, total count)
        """
        query = self.db.query(VehicleListing)
        
        # Apply filters
        if filters.make:
            query = query.filter(VehicleListing.make.ilike(f"%{filters.make}%"))
        
        if filters.model:
            query = query.filter(VehicleListing.model.ilike(f"%{filters.model}%"))
        
        if filters.year_min:
            query = query.filter(VehicleListing.year >= filters.year_min)
        
        if filters.year_max:
            query = query.filter(VehicleListing.year <= filters.year_max)
        
        if filters.price_min:
            query = query.filter(VehicleListing.price >= filters.price_min)
        
        if filters.price_max:
            query = query.filter(VehicleListing.price <= filters.price_max)
        
        if filters.mileage_max:
            query = query.filter(VehicleListing.mileage <= filters.mileage_max)
        
        if filters.fuel_type:
            query = query.filter(VehicleListing.fuel_type == filters.fuel_type)
        
        if filters.transmission:
            query = query.filter(VehicleListing.transmission == filters.transmission)
        
        if filters.body_type:
            query = query.filter(VehicleListing.body_type == filters.body_type)
        
        if filters.condition:
            query = query.filter(VehicleListing.condition == filters.condition)
        
        if filters.city:
            query = query.filter(VehicleListing.city.ilike(f"%{filters.city}%"))
        
        if filters.region:
            query = query.filter(VehicleListing.region.ilike(f"%{filters.region}%"))
        
        query = query.filter(VehicleListing.is_active == filters.is_active)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        vehicles = query.order_by(desc(VehicleListing.scraped_at))\
                       .offset((page - 1) * page_size)\
                       .limit(page_size)\
                       .all()
        
        return vehicles, total_count
    
    def get_vehicle_by_id(self, vehicle_id: int) -> Optional[VehicleListing]:
        """Get vehicle by ID"""
        return self.db.query(VehicleListing).filter(VehicleListing.id == vehicle_id).first()
    
    def deactivate_old_listings(self, days_old: int = 30) -> int:
        """
        Deactivate listings that haven't been updated in specified days
        
        Args:
            days_old: Number of days after which to deactivate listings
        
        Returns:
            Number of listings deactivated
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        updated_count = self.db.query(VehicleListing).filter(
            and_(
                VehicleListing.last_updated < cutoff_date,
                VehicleListing.is_active == True
            )
        ).update({'is_active': False})
        
        self.db.commit()
        logger.info(f"Deactivated {updated_count} old listings")
        return updated_count
    
    def create_scraping_log(self, log_data: Dict[str, Any]) -> ScrapingLog:
        """Create a scraping log entry"""
        try:
            log_entry = ScrapingLog(**log_data)
            self.db.add(log_entry)
            self.db.commit()
            return log_entry
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating scraping log: {e}")
            raise
    
    def create_scraping_session(self, session_data: Dict[str, Any]) -> ScrapingSession:
        """Create a scraping session"""
        try:
            session = ScrapingSession(**session_data)
            self.db.add(session)
            self.db.commit()
            return session
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating scraping session: {e}")
            raise
    
    def update_scraping_session(self, session_id: str, update_data: Dict[str, Any]) -> Optional[ScrapingSession]:
        """Update a scraping session"""
        try:
            session = self.db.query(ScrapingSession).filter(
                ScrapingSession.session_id == session_id
            ).first()
            
            if session:
                for field, value in update_data.items():
                    if hasattr(session, field):
                        setattr(session, field, value)
                
                self.db.commit()
                return session
            
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating scraping session {session_id}: {e}")
            return None
    
    def get_data_quality_metrics(self) -> Dict[str, Any]:
        """Calculate and return data quality metrics"""
        try:
            total_vehicles = self.db.query(VehicleListing).count()
            active_vehicles = self.db.query(VehicleListing).filter(VehicleListing.is_active == True).count()
            
            # Calculate completeness scores for key fields
            required_fields = ['make', 'model', 'price', 'year', 'mileage', 'fuel_type']
            completeness_scores = {}
            
            for field in required_fields:
                non_null_count = self.db.query(VehicleListing).filter(
                    getattr(VehicleListing, field).isnot(None)
                ).count()
                completeness_scores[field] = (non_null_count / total_vehicles * 100) if total_vehicles > 0 else 0
            
            # Calculate average price and other stats
            price_stats = self.db.query(
                func.avg(VehicleListing.price),
                func.min(VehicleListing.price),
                func.max(VehicleListing.price)
            ).filter(VehicleListing.price.isnot(None)).first()
            
            return {
                'total_vehicles': total_vehicles,
                'active_vehicles': active_vehicles,
                'completeness_scores': completeness_scores,
                'average_price': float(price_stats[0]) if price_stats[0] else 0,
                'min_price': float(price_stats[1]) if price_stats[1] else 0,
                'max_price': float(price_stats[2]) if price_stats[2] else 0,
                'overall_completeness': sum(completeness_scores.values()) / len(completeness_scores)
            }
            
        except Exception as e:
            logger.error(f"Error calculating data quality metrics: {e}")
            return {}
    
    def cleanup_old_data(self, retention_days: int = 365) -> Dict[str, int]:
        """
        Clean up old data based on retention policy
        
        Args:
            retention_days: Number of days to retain data
        
        Returns:
            Dictionary with cleanup statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Delete old scraping logs
        old_logs_deleted = self.db.query(ScrapingLog).filter(
            ScrapingLog.started_at < cutoff_date
        ).delete()
        
        # Delete old price history (keep recent ones)
        old_price_history_deleted = self.db.query(PriceHistory).filter(
            PriceHistory.recorded_at < cutoff_date
        ).delete()
        
        # Delete inactive old vehicle listings
        old_vehicles_deleted = self.db.query(VehicleListing).filter(
            and_(
                VehicleListing.scraped_at < cutoff_date,
                VehicleListing.is_active == False
            )
        ).delete()
        
        self.db.commit()
        
        cleanup_stats = {
            'old_logs_deleted': old_logs_deleted,
            'old_price_history_deleted': old_price_history_deleted,
            'old_vehicles_deleted': old_vehicles_deleted
        }
        
        logger.info(f"Cleanup completed: {cleanup_stats}")
        return cleanup_stats
