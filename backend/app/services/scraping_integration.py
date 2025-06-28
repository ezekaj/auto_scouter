"""
Scraping System Integration

This module integrates the alert matching system with the vehicle scraping system
to automatically trigger alert checks when new listings are added.
"""

import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.automotive import VehicleListing, ScrapingSession
from app.models.scout import Alert
from app.models.notifications import AlertMatchLog
from app.services.enhanced_alert_matcher import EnhancedAlertMatchingEngine
from app.tasks.alert_matching import run_alert_matching_task, match_single_alert_task

logger = logging.getLogger(__name__)


class ScrapingIntegrationService:
    """Service to integrate alert matching with vehicle scraping"""

    def __init__(self, db: Session):
        self.db = db
        self.alert_matcher = EnhancedAlertMatchingEngine(db)

    def process_new_listings(self, listing_ids: List[int], trigger_immediate_matching: bool = True) -> dict:
        """
        Process newly scraped listings and trigger alert matching
        
        Args:
            listing_ids: List of new listing IDs to process
            trigger_immediate_matching: Whether to trigger immediate alert matching
            
        Returns:
            dict: Processing results
        """
        try:
            logger.info(f"Processing {len(listing_ids)} new listings for alert matching")
            
            # Get the listings
            listings = self.db.query(VehicleListing).filter(
                VehicleListing.id.in_(listing_ids)
            ).all()
            
            if not listings:
                logger.warning("No valid listings found for processing")
                return {"status": "no_listings", "processed": 0}
            
            processed_count = 0
            total_matches = 0
            
            if trigger_immediate_matching:
                # Process each listing against all active alerts
                for listing in listings:
                    matches = self._process_single_listing(listing)
                    total_matches += matches
                    processed_count += 1
            else:
                # Just mark for batch processing
                processed_count = len(listings)
                logger.info(f"Marked {processed_count} listings for batch processing")
            
            return {
                "status": "completed",
                "processed_listings": processed_count,
                "total_matches": total_matches,
                "trigger_immediate": trigger_immediate_matching
            }
            
        except Exception as e:
            logger.error(f"Error processing new listings: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _process_single_listing(self, listing: VehicleListing) -> int:
        """
        Process a single listing against all active alerts
        
        Args:
            listing: The vehicle listing to process
            
        Returns:
            int: Number of matches found
        """
        try:
            # Get all active alerts
            active_alerts = self.db.query(Alert).filter(Alert.is_active == True).all()
            
            matches_found = 0
            
            for alert in active_alerts:
                try:
                    # Check if listing matches alert
                    match_result = self.alert_matcher.check_alert_match(alert, listing)
                    
                    if match_result:
                        # Create notification
                        notification = self.alert_matcher.create_notification(
                            alert, listing, match_result
                        )
                        
                        if notification:
                            matches_found += 1
                            logger.info(
                                f"Created notification {notification.id} for alert {alert.id} "
                                f"and listing {listing.id}"
                            )
                
                except Exception as e:
                    logger.error(f"Error processing alert {alert.id} against listing {listing.id}: {str(e)}")
                    continue
            
            return matches_found
            
        except Exception as e:
            logger.error(f"Error processing listing {listing.id}: {str(e)}")
            return 0

    def trigger_batch_alert_matching(self, check_since_minutes: int = 5) -> dict:
        """
        Trigger batch alert matching for recent listings
        
        Args:
            check_since_minutes: Check listings added in the last N minutes
            
        Returns:
            dict: Task result
        """
        try:
            # Trigger Celery task for batch processing
            task = run_alert_matching_task.delay(check_since_minutes=check_since_minutes)
            
            logger.info(f"Triggered batch alert matching task {task.id}")
            
            return {
                "status": "triggered",
                "task_id": task.id,
                "check_since_minutes": check_since_minutes
            }
            
        except Exception as e:
            logger.error(f"Error triggering batch alert matching: {str(e)}")
            return {"status": "error", "error": str(e)}

    def on_scraping_session_complete(self, session_id: int) -> dict:
        """
        Handle completion of a scraping session
        
        Args:
            session_id: ID of the completed scraping session
            
        Returns:
            dict: Processing results
        """
        try:
            # Get the scraping session
            session = self.db.query(ScrapingSession).filter(
                ScrapingSession.id == session_id
            ).first()
            
            if not session:
                logger.warning(f"Scraping session {session_id} not found")
                return {"status": "session_not_found"}
            
            # Get new listings from this session
            new_listings = self.db.query(VehicleListing).filter(
                VehicleListing.scraping_session_id == session_id,
                VehicleListing.is_active == True
            ).all()
            
            if not new_listings:
                logger.info(f"No new listings found in session {session_id}")
                return {"status": "no_new_listings", "session_id": session_id}
            
            # Process the new listings
            listing_ids = [listing.id for listing in new_listings]
            result = self.process_new_listings(listing_ids, trigger_immediate_matching=False)
            
            # Trigger batch processing
            batch_result = self.trigger_batch_alert_matching(check_since_minutes=30)
            
            logger.info(
                f"Completed processing for scraping session {session_id}: "
                f"{len(new_listings)} new listings"
            )
            
            return {
                "status": "completed",
                "session_id": session_id,
                "new_listings_count": len(new_listings),
                "processing_result": result,
                "batch_task": batch_result
            }
            
        except Exception as e:
            logger.error(f"Error handling scraping session completion: {str(e)}")
            return {"status": "error", "error": str(e)}

    def get_alert_matching_stats(self, days: int = 7) -> dict:
        """
        Get alert matching statistics
        
        Args:
            days: Number of days to analyze
            
        Returns:
            dict: Statistics
        """
        try:
            from datetime import timedelta
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Get recent match logs
            recent_logs = self.db.query(AlertMatchLog).filter(
                AlertMatchLog.started_at >= since_date
            ).all()
            
            if not recent_logs:
                return {
                    "period_days": days,
                    "total_runs": 0,
                    "total_matches": 0,
                    "total_notifications": 0
                }
            
            # Calculate statistics
            total_runs = len(recent_logs)
            total_matches = sum(log.matches_found for log in recent_logs)
            total_notifications = sum(log.notifications_created for log in recent_logs)
            total_alerts_processed = sum(log.alerts_processed for log in recent_logs)
            total_listings_checked = sum(log.listings_checked for log in recent_logs)
            
            avg_processing_time = sum(
                log.processing_time_seconds for log in recent_logs if log.processing_time_seconds
            ) / len([log for log in recent_logs if log.processing_time_seconds])
            
            return {
                "period_days": days,
                "total_runs": total_runs,
                "total_matches": total_matches,
                "total_notifications": total_notifications,
                "total_alerts_processed": total_alerts_processed,
                "total_listings_checked": total_listings_checked,
                "average_processing_time_seconds": round(avg_processing_time, 2),
                "match_rate": round(total_matches / max(total_listings_checked, 1) * 100, 2),
                "notification_rate": round(total_notifications / max(total_matches, 1) * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting alert matching stats: {str(e)}")
            return {"error": str(e)}

    def optimize_alert_matching_schedule(self) -> dict:
        """
        Analyze scraping patterns and optimize alert matching schedule
        
        Returns:
            dict: Optimization recommendations
        """
        try:
            from datetime import timedelta
            from sqlalchemy import func
            
            # Analyze scraping patterns over the last 30 days
            since_date = datetime.utcnow() - timedelta(days=30)
            
            # Get hourly distribution of new listings
            hourly_stats = self.db.query(
                func.extract('hour', VehicleListing.scraped_at).label('hour'),
                func.count(VehicleListing.id).label('count')
            ).filter(
                VehicleListing.scraped_at >= since_date
            ).group_by(
                func.extract('hour', VehicleListing.scraped_at)
            ).all()
            
            # Get daily distribution
            daily_stats = self.db.query(
                func.extract('dow', VehicleListing.scraped_at).label('day_of_week'),
                func.count(VehicleListing.id).label('count')
            ).filter(
                VehicleListing.scraped_at >= since_date
            ).group_by(
                func.extract('dow', VehicleListing.scraped_at)
            ).all()
            
            # Calculate peak hours and days
            hourly_distribution = {int(stat.hour): stat.count for stat in hourly_stats}
            daily_distribution = {int(stat.day_of_week): stat.count for stat in daily_stats}
            
            peak_hours = sorted(hourly_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
            peak_days = sorted(daily_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Generate recommendations
            recommendations = []
            
            if peak_hours:
                peak_hour_list = [str(hour) for hour, _ in peak_hours]
                recommendations.append(
                    f"Peak scraping hours: {', '.join(peak_hour_list)}. "
                    f"Consider increasing alert matching frequency during these hours."
                )
            
            if peak_days:
                day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
                peak_day_list = [day_names[day] for day, _ in peak_days]
                recommendations.append(
                    f"Peak scraping days: {', '.join(peak_day_list)}. "
                    f"Consider more frequent matching on these days."
                )
            
            return {
                "analysis_period_days": 30,
                "hourly_distribution": hourly_distribution,
                "daily_distribution": daily_distribution,
                "peak_hours": peak_hours,
                "peak_days": peak_days,
                "recommendations": recommendations,
                "suggested_schedule": {
                    "peak_hours_frequency": "every_2_minutes",
                    "normal_hours_frequency": "every_5_minutes",
                    "low_activity_frequency": "every_10_minutes"
                }
            }
            
        except Exception as e:
            logger.error(f"Error optimizing alert matching schedule: {str(e)}")
            return {"error": str(e)}


# Webhook handlers for scraping system integration
def handle_new_listing_webhook(listing_data: dict, db: Session) -> dict:
    """
    Handle webhook for new listing creation
    
    Args:
        listing_data: New listing data
        db: Database session
        
    Returns:
        dict: Processing result
    """
    try:
        integration_service = ScrapingIntegrationService(db)
        
        # Extract listing ID
        listing_id = listing_data.get('id')
        if not listing_id:
            return {"status": "error", "error": "No listing ID provided"}
        
        # Process the single listing
        result = integration_service.process_new_listings([listing_id])
        
        return result
        
    except Exception as e:
        logger.error(f"Error handling new listing webhook: {str(e)}")
        return {"status": "error", "error": str(e)}


def handle_scraping_session_webhook(session_data: dict, db: Session) -> dict:
    """
    Handle webhook for scraping session completion
    
    Args:
        session_data: Scraping session data
        db: Database session
        
    Returns:
        dict: Processing result
    """
    try:
        integration_service = ScrapingIntegrationService(db)
        
        # Extract session ID
        session_id = session_data.get('id')
        if not session_id:
            return {"status": "error", "error": "No session ID provided"}
        
        # Handle session completion
        result = integration_service.on_scraping_session_complete(session_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error handling scraping session webhook: {str(e)}")
        return {"status": "error", "error": str(e)}
