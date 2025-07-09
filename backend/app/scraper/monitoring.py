"""
Scraper Monitoring Module
Provides monitoring and health check functionality for scrapers
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func

logger = logging.getLogger(__name__)

class ScraperMonitor:
    """Monitors scraper performance and health"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        
    def get_system_health(self) -> Dict[str, Any]:
        """Get basic system health information"""
        uptime = datetime.utcnow() - self.start_time
        
        return {
            "status": "healthy",
            "uptime_seconds": int(uptime.total_seconds()),
            "timestamp": datetime.utcnow().isoformat(),
            "memory_usage": "N/A",  # Could implement actual memory monitoring
            "cpu_usage": "N/A"      # Could implement actual CPU monitoring
        }
    
    def get_data_overview(self, db: Session) -> Dict[str, Any]:
        """Get overview of scraped data"""
        try:
            from app.models.automotive import VehicleListing
            
            # Get basic vehicle counts
            total_vehicles = db.query(VehicleListing).count()
            recent_vehicles = db.query(VehicleListing).filter(
                VehicleListing.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            return {
                "total_vehicles": total_vehicles,
                "recent_vehicles": recent_vehicles,
                "last_updated": datetime.utcnow().isoformat(),
                "status": "active"
            }
        except Exception as e:
            logger.error(f"Error getting data overview: {e}")
            return {
                "total_vehicles": 0,
                "recent_vehicles": 0,
                "last_updated": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    def generate_monitoring_report(self, db: Session) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        try:
            from app.models.automotive import VehicleListing, ScrapingLog
            
            # System health
            health = self.get_system_health()
            
            # Data statistics
            total_vehicles = db.query(VehicleListing).count()
            
            # Recent scraping activity
            recent_logs = db.query(ScrapingLog).filter(
                ScrapingLog.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            return {
                "system_health": health,
                "data_stats": {
                    "total_vehicles": total_vehicles,
                    "recent_scraping_sessions": recent_logs
                },
                "alerts": [],  # Could implement actual alerting
                "recommendations": [
                    "System is operating normally",
                    "Consider implementing data quality checks"
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating monitoring report: {e}")
            return {
                "system_health": {"status": "error", "error": str(e)},
                "data_stats": {},
                "alerts": [f"Monitoring error: {str(e)}"],
                "recommendations": ["Check system logs for errors"],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def check_data_quality_alerts(self, db: Session) -> List[Dict[str, Any]]:
        """Check for data quality issues and return alerts"""
        alerts = []
        
        try:
            from app.models.automotive import VehicleListing
            
            # Check for duplicate entries
            duplicates = db.query(
                VehicleListing.title,
                func.count(VehicleListing.id).label('count')
            ).group_by(VehicleListing.title).having(
                func.count(VehicleListing.id) > 1
            ).limit(5).all()
            
            if duplicates:
                alerts.append({
                    "type": "data_quality",
                    "severity": "warning",
                    "message": f"Found {len(duplicates)} potential duplicate listings",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Check for very old data
            old_cutoff = datetime.utcnow() - timedelta(days=30)
            old_count = db.query(VehicleListing).filter(
                VehicleListing.created_at < old_cutoff
            ).count()
            
            if old_count > 1000:
                alerts.append({
                    "type": "data_retention",
                    "severity": "info",
                    "message": f"Found {old_count} listings older than 30 days",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error checking data quality: {e}")
            alerts.append({
                "type": "system_error",
                "severity": "error",
                "message": f"Data quality check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            })
            
        return alerts

# Global monitor instance
scraper_monitor = ScraperMonitor()
