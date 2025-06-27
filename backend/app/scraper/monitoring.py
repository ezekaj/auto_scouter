"""
Scraper Monitoring and Health Checks

This module provides monitoring capabilities for the scraper system,
including health checks, metrics collection, and alerting.
"""

import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.automotive import VehicleListing, ScrapingSession, ScrapingLog
from app.services.automotive_service import AutomotiveService
from app.scraper.config import scraper_settings
import logging

logger = logging.getLogger(__name__)


class ScraperMonitor:
    """Monitor scraper performance and health"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.metrics_history = []
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network connectivity test
            network_status = self.check_network_connectivity()
            
            # Database connectivity test
            db_status = self.check_database_connectivity()
            
            health_status = {
                'timestamp': datetime.utcnow().isoformat(),
                'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_percent': disk.percent,
                    'disk_free_gb': disk.free / (1024**3)
                },
                'services': {
                    'network': network_status,
                    'database': db_status
                },
                'overall_status': 'healthy' if all([
                    cpu_percent < 80,
                    memory.percent < 80,
                    disk.percent < 90,
                    network_status['status'] == 'ok',
                    db_status['status'] == 'ok'
                ]) else 'warning'
            }
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_status': 'error',
                'error': str(e)
            }
    
    def check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity to target website"""
        try:
            import requests
            
            start_time = time.time()
            response = requests.get(
                scraper_settings.BASE_URL,
                timeout=10,
                headers={'User-Agent': 'Health Check Bot'}
            )
            response_time = time.time() - start_time
            
            return {
                'status': 'ok' if response.status_code == 200 else 'warning',
                'response_code': response.status_code,
                'response_time_ms': round(response_time * 1000, 2),
                'target_url': scraper_settings.BASE_URL
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'target_url': scraper_settings.BASE_URL
            }
    
    def check_database_connectivity(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            from app.models.base import SessionLocal
            
            start_time = time.time()
            db = SessionLocal()
            
            # Simple query to test connectivity
            count = db.query(VehicleListing).count()
            query_time = time.time() - start_time
            
            db.close()
            
            return {
                'status': 'ok',
                'query_time_ms': round(query_time * 1000, 2),
                'total_vehicles': count
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_scraping_metrics(self, db: Session, hours: int = 24) -> Dict[str, Any]:
        """Get scraping performance metrics for the last N hours"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Get recent sessions
            recent_sessions = db.query(ScrapingSession).filter(
                ScrapingSession.started_at >= cutoff_time
            ).order_by(desc(ScrapingSession.started_at)).all()
            
            # Calculate session statistics
            total_sessions = len(recent_sessions)
            successful_sessions = len([s for s in recent_sessions if s.status == 'completed'])
            failed_sessions = len([s for s in recent_sessions if s.status == 'failed'])
            
            # Calculate vehicle statistics
            total_vehicles_found = sum(s.total_vehicles_found or 0 for s in recent_sessions)
            total_vehicles_new = sum(s.total_vehicles_new or 0 for s in recent_sessions)
            total_vehicles_updated = sum(s.total_vehicles_updated or 0 for s in recent_sessions)
            total_errors = sum(s.total_errors or 0 for s in recent_sessions)
            
            # Calculate average response time
            response_times = []
            for session in recent_sessions:
                logs = db.query(ScrapingLog).filter(
                    ScrapingLog.session_id == session.session_id,
                    ScrapingLog.response_time.isnot(None)
                ).all()
                response_times.extend([log.response_time for log in logs])
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Get error rate
            total_requests = db.query(ScrapingLog).filter(
                ScrapingLog.started_at >= cutoff_time
            ).count()
            
            error_requests = db.query(ScrapingLog).filter(
                ScrapingLog.started_at >= cutoff_time,
                ScrapingLog.status == 'error'
            ).count()
            
            error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'period_hours': hours,
                'sessions': {
                    'total': total_sessions,
                    'successful': successful_sessions,
                    'failed': failed_sessions,
                    'success_rate': (successful_sessions / total_sessions * 100) if total_sessions > 0 else 0
                },
                'vehicles': {
                    'total_found': total_vehicles_found,
                    'new': total_vehicles_new,
                    'updated': total_vehicles_updated,
                    'errors': total_errors
                },
                'performance': {
                    'average_response_time_ms': round(avg_response_time * 1000, 2) if avg_response_time else 0,
                    'total_requests': total_requests,
                    'error_rate_percent': round(error_rate, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting scraping metrics: {e}")
            return {'error': str(e)}
    
    def get_data_overview(self, db: Session) -> Dict[str, Any]:
        """Get overview of scraped data"""
        try:
            # Total counts
            total_vehicles = db.query(VehicleListing).count()
            active_vehicles = db.query(VehicleListing).filter(VehicleListing.is_active == True).count()
            
            # Recent additions (last 24 hours)
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_vehicles = db.query(VehicleListing).filter(
                VehicleListing.scraped_at >= recent_cutoff
            ).count()
            
            # Price statistics
            price_stats = db.query(
                func.avg(VehicleListing.price),
                func.min(VehicleListing.price),
                func.max(VehicleListing.price)
            ).filter(
                VehicleListing.price.isnot(None),
                VehicleListing.is_active == True
            ).first()
            
            # Top makes
            top_makes = db.query(
                VehicleListing.make,
                func.count(VehicleListing.id).label('count')
            ).filter(
                VehicleListing.is_active == True
            ).group_by(VehicleListing.make).order_by(desc('count')).limit(10).all()
            
            # Fuel type distribution
            fuel_distribution = db.query(
                VehicleListing.fuel_type,
                func.count(VehicleListing.id).label('count')
            ).filter(
                VehicleListing.is_active == True,
                VehicleListing.fuel_type.isnot(None)
            ).group_by(VehicleListing.fuel_type).order_by(desc('count')).all()
            
            return {
                'totals': {
                    'total_vehicles': total_vehicles,
                    'active_vehicles': active_vehicles,
                    'recent_additions_24h': recent_vehicles
                },
                'pricing': {
                    'average_price': round(float(price_stats[0]), 2) if price_stats[0] else 0,
                    'min_price': float(price_stats[1]) if price_stats[1] else 0,
                    'max_price': float(price_stats[2]) if price_stats[2] else 0
                },
                'top_makes': [{'make': make, 'count': count} for make, count in top_makes],
                'fuel_distribution': [{'fuel_type': fuel, 'count': count} for fuel, count in fuel_distribution]
            }
            
        except Exception as e:
            logger.error(f"Error getting data overview: {e}")
            return {'error': str(e)}
    
    def get_recent_errors(self, db: Session, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent scraping errors"""
        try:
            recent_errors = db.query(ScrapingLog).filter(
                ScrapingLog.status == 'error'
            ).order_by(desc(ScrapingLog.started_at)).limit(limit).all()
            
            errors = []
            for error in recent_errors:
                errors.append({
                    'timestamp': error.started_at.isoformat(),
                    'session_id': error.session_id,
                    'source_url': error.source_url,
                    'action': error.action,
                    'error_message': error.error_message,
                    'response_code': error.response_code
                })
            
            return errors
            
        except Exception as e:
            logger.error(f"Error getting recent errors: {e}")
            return []
    
    def check_data_quality_alerts(self, db: Session) -> List[Dict[str, Any]]:
        """Check for data quality issues that need attention"""
        alerts = []
        
        try:
            automotive_service = AutomotiveService(db)
            metrics = automotive_service.get_data_quality_metrics()
            
            # Check overall completeness
            overall_completeness = metrics.get('overall_completeness', 0)
            if overall_completeness < 80:
                alerts.append({
                    'type': 'data_quality',
                    'severity': 'warning',
                    'message': f'Data completeness below threshold: {overall_completeness:.1f}%',
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Check for missing critical fields
            completeness_scores = metrics.get('completeness_scores', {})
            critical_fields = ['make', 'model', 'price']
            
            for field in critical_fields:
                score = completeness_scores.get(field, 0)
                if score < 90:
                    alerts.append({
                        'type': 'missing_data',
                        'severity': 'warning',
                        'message': f'Critical field "{field}" missing in {100-score:.1f}% of records',
                        'timestamp': datetime.utcnow().isoformat()
                    })
            
            # Check for stale data
            cutoff_time = datetime.utcnow() - timedelta(hours=scraper_settings.SCRAPING_INTERVAL_HOURS * 2)
            recent_vehicles = db.query(VehicleListing).filter(
                VehicleListing.scraped_at >= cutoff_time
            ).count()
            
            if recent_vehicles == 0:
                alerts.append({
                    'type': 'stale_data',
                    'severity': 'error',
                    'message': 'No vehicles scraped in the last 2 scraping intervals',
                    'timestamp': datetime.utcnow().isoformat()
                })
            
        except Exception as e:
            logger.error(f"Error checking data quality alerts: {e}")
            alerts.append({
                'type': 'system_error',
                'severity': 'error',
                'message': f'Error checking data quality: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            })
        
        return alerts
    
    def generate_monitoring_report(self, db: Session) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'system_health': self.get_system_health(),
            'scraping_metrics_24h': self.get_scraping_metrics(db, 24),
            'data_overview': self.get_data_overview(db),
            'recent_errors': self.get_recent_errors(db, 20),
            'alerts': self.check_data_quality_alerts(db)
        }


# Global monitor instance
scraper_monitor = ScraperMonitor()
