"""
Health Check Service

Comprehensive health monitoring for all system components.
"""

import logging
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.base import engine, SessionLocal
from app.models.automotive import VehicleListing, ScrapingSession
from app.models.scout import Alert, User
from app.models.notifications import Notification
from app.core.config import settings

logger = logging.getLogger(__name__)


class HealthCheckService:
    """Service for monitoring system health"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
    
    def get_comprehensive_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        health_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "version": settings.VERSION,
            "environment": getattr(settings, 'ENVIRONMENT', 'development'),
            "components": {}
        }
        
        # Check all components
        components = [
            ("database", self._check_database),
            ("redis", self._check_redis),
            ("scraping", self._check_scraping_health),
            ("alerts", self._check_alert_system),
            ("notifications", self._check_notification_system),
            ("system_resources", self._check_system_resources),
            ("data_freshness", self._check_data_freshness)
        ]
        
        overall_healthy = True
        
        for component_name, check_func in components:
            try:
                component_health = check_func()
                health_data["components"][component_name] = component_health
                
                if component_health["status"] != "healthy":
                    overall_healthy = False
                    
            except Exception as e:
                logger.error(f"Health check failed for {component_name}: {e}")
                health_data["components"][component_name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                overall_healthy = False
        
        # Set overall status
        health_data["status"] = "healthy" if overall_healthy else "unhealthy"
        
        return health_data
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        start_time = time.time()
        
        try:
            db = SessionLocal()
            
            # Test basic connectivity
            db.execute(text("SELECT 1"))
            
            # Get database stats
            user_count = db.query(User).count()
            alert_count = db.query(Alert).filter(Alert.is_active == True).count()
            vehicle_count = db.query(VehicleListing).filter(VehicleListing.is_active == True).count()
            
            response_time = (time.time() - start_time) * 1000  # ms
            
            db.close()
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "stats": {
                    "users": user_count,
                    "active_alerts": alert_count,
                    "active_vehicles": vehicle_count
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            import redis
            r = redis.Redis.from_url(settings.REDIS_URL)
            
            start_time = time.time()
            r.ping()
            response_time = (time.time() - start_time) * 1000
            
            # Get Redis info
            info = r.info()
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "stats": {
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "unknown"),
                    "uptime_in_seconds": info.get("uptime_in_seconds", 0)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _check_scraping_health(self) -> Dict[str, Any]:
        """Check scraping system health"""
        try:
            db = SessionLocal()
            
            # Check recent scraping activity
            recent_sessions = db.query(ScrapingSession).filter(
                ScrapingSession.started_at >= datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            # Check last successful session
            last_session = db.query(ScrapingSession).filter(
                ScrapingSession.status == 'completed'
            ).order_by(ScrapingSession.completed_at.desc()).first()
            
            # Check recent vehicle additions
            recent_vehicles = db.query(VehicleListing).filter(
                VehicleListing.scraped_at >= datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            db.close()
            
            status = "healthy"
            if recent_sessions == 0 and recent_vehicles == 0:
                status = "warning"
            
            return {
                "status": status,
                "stats": {
                    "recent_sessions_1h": recent_sessions,
                    "recent_vehicles_1h": recent_vehicles,
                    "last_successful_session": last_session.completed_at.isoformat() if last_session else None
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _check_alert_system(self) -> Dict[str, Any]:
        """Check alert system health"""
        try:
            db = SessionLocal()
            
            active_alerts = db.query(Alert).filter(Alert.is_active == True).count()
            total_users = db.query(User).filter(User.is_active == True).count()
            
            # Check recent alert activity
            recent_notifications = db.query(Notification).filter(
                Notification.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            db.close()
            
            return {
                "status": "healthy",
                "stats": {
                    "active_alerts": active_alerts,
                    "active_users": total_users,
                    "notifications_24h": recent_notifications
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _check_notification_system(self) -> Dict[str, Any]:
        """Check notification system health"""
        try:
            db = SessionLocal()
            
            # Check notification queue
            pending_notifications = db.query(Notification).filter(
                Notification.status == 'pending'
            ).count()
            
            failed_notifications = db.query(Notification).filter(
                Notification.status == 'failed',
                Notification.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            db.close()
            
            status = "healthy"
            if failed_notifications > 10:  # More than 10 failures in 24h
                status = "warning"
            
            return {
                "status": status,
                "stats": {
                    "pending_notifications": pending_notifications,
                    "failed_notifications_24h": failed_notifications
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Determine status based on resource usage
            status = "healthy"
            if cpu_percent > 80 or memory.percent > 85 or disk.percent > 90:
                status = "warning"
            if cpu_percent > 95 or memory.percent > 95 or disk.percent > 95:
                status = "critical"
            
            return {
                "status": status,
                "stats": {
                    "cpu_percent": round(cpu_percent, 1),
                    "memory_percent": round(memory.percent, 1),
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_percent": round(disk.percent, 1),
                    "disk_free_gb": round(disk.free / (1024**3), 2)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _check_data_freshness(self) -> Dict[str, Any]:
        """Check data freshness"""
        try:
            db = SessionLocal()
            
            # Check latest vehicle data
            latest_vehicle = db.query(VehicleListing).order_by(
                VehicleListing.scraped_at.desc()
            ).first()
            
            # Check data age
            if latest_vehicle:
                data_age_hours = (datetime.utcnow() - latest_vehicle.scraped_at).total_seconds() / 3600
                status = "healthy" if data_age_hours < 2 else "warning"
            else:
                data_age_hours = None
                status = "warning"
            
            db.close()
            
            return {
                "status": status,
                "stats": {
                    "latest_vehicle_age_hours": round(data_age_hours, 2) if data_age_hours else None,
                    "latest_vehicle_scraped": latest_vehicle.scraped_at.isoformat() if latest_vehicle else None
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global health check service instance
health_service = HealthCheckService()
