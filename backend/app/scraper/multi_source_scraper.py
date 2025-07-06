"""
Multi-Source Scraper Manager

This module coordinates scraping from multiple automotive data sources
and provides a unified interface for data collection.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Type
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from app.scraper.autoscout24_scraper import AutoScout24Scraper
from app.scraper.base import BaseScraper
from app.scraper.config import scraper_settings
from app.scraper.monitoring import scraper_monitor
from app.scraper.compliance import compliance_manager

logger = logging.getLogger(__name__)


@dataclass
class ScrapingResult:
    """Result of a scraping operation"""
    source: str
    success: bool
    vehicles_count: int
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
    scraped_at: datetime = None


class MultiSourceScraper:
    """
    Manages scraping from multiple automotive data sources
    """
    
    def __init__(self):
        self.scrapers = {
            'autoscout24': AutoScout24Scraper
        }
        
        self.enabled_sources = self._get_enabled_sources()
        self.max_workers = scraper_settings.CONCURRENT_REQUESTS
        
    def _get_enabled_sources(self) -> List[str]:
        """Get list of enabled scraping sources from configuration"""
        # For now, enable all sources. This could be made configurable
        enabled = ['gruppoautouno']  # Start with the most stable one
        
        # Add other sources if they're enabled in settings
        if getattr(scraper_settings, 'ENABLE_AUTOSCOUT24', True):
            enabled.append('autoscout24')
        
        if getattr(scraper_settings, 'ENABLE_MOBILE_DE', True):
            enabled.append('mobile_de')
        
        logger.info(f"Enabled scraping sources: {enabled}")
        return enabled
    
    def scrape_all_sources(self, max_vehicles_per_source: int = None) -> List[ScrapingResult]:
        """
        Scrape data from all enabled sources
        
        Args:
            max_vehicles_per_source: Maximum vehicles to scrape per source
        
        Returns:
            List of scraping results for each source
        """
        logger.info("Starting multi-source scraping operation")
        
        if max_vehicles_per_source is None:
            max_vehicles_per_source = scraper_settings.MAX_PAGES_TO_SCRAPE
        
        results = []
        
        # Use ThreadPoolExecutor for concurrent scraping
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit scraping tasks for each enabled source
            future_to_source = {
                executor.submit(
                    self._scrape_single_source, 
                    source, 
                    max_vehicles_per_source
                ): source 
                for source in self.enabled_sources
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Completed scraping {source}: {result.vehicles_count} vehicles")
                except Exception as e:
                    logger.error(f"Error scraping {source}: {e}")
                    results.append(ScrapingResult(
                        source=source,
                        success=False,
                        vehicles_count=0,
                        error_message=str(e),
                        scraped_at=datetime.utcnow()
                    ))
        
        # Log summary
        total_vehicles = sum(r.vehicles_count for r in results)
        successful_sources = sum(1 for r in results if r.success)
        
        logger.info(f"Multi-source scraping completed: {total_vehicles} total vehicles from {successful_sources}/{len(results)} sources")
        
        return results
    
    def _scrape_single_source(self, source: str, max_vehicles: int) -> ScrapingResult:
        """
        Scrape data from a single source
        
        Args:
            source: Source identifier
            max_vehicles: Maximum vehicles to scrape
        
        Returns:
            ScrapingResult object
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting scraping for source: {source}")
            
            # Check compliance before scraping
            if not self._check_source_compliance(source):
                return ScrapingResult(
                    source=source,
                    success=False,
                    vehicles_count=0,
                    error_message="Source blocked by compliance rules",
                    scraped_at=start_time
                )
            
            # Get scraper class and instantiate
            scraper_class = self.scrapers.get(source)
            if not scraper_class:
                raise ValueError(f"Unknown scraper source: {source}")
            
            scraper = scraper_class()
            
            # Perform scraping
            vehicles = scraper.scrape_all_listings(max_vehicles=max_vehicles)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Update monitoring metrics
            scraper_monitor.record_scraping_session(
                source=source,
                vehicles_count=len(vehicles),
                duration_seconds=duration,
                success=True
            )
            
            return ScrapingResult(
                source=source,
                success=True,
                vehicles_count=len(vehicles),
                duration_seconds=duration,
                scraped_at=start_time
            )
            
        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.error(f"Error scraping source {source}: {e}")
            
            # Update monitoring metrics for failed scraping
            scraper_monitor.record_scraping_session(
                source=source,
                vehicles_count=0,
                duration_seconds=duration,
                success=False,
                error_message=str(e)
            )
            
            return ScrapingResult(
                source=source,
                success=False,
                vehicles_count=0,
                error_message=str(e),
                duration_seconds=duration,
                scraped_at=start_time
            )
    
    def _check_source_compliance(self, source: str) -> bool:
        """
        Check if scraping from a source is compliant with robots.txt and rate limits
        
        Args:
            source: Source identifier
        
        Returns:
            True if scraping is allowed, False otherwise
        """
        try:
            scraper_class = self.scrapers.get(source)
            if not scraper_class:
                return False
            
            # Create temporary scraper instance to get base URL
            temp_scraper = scraper_class()
            base_url = getattr(temp_scraper, 'base_url', None)
            
            if not base_url:
                logger.warning(f"No base URL found for source {source}")
                return True  # Allow if we can't check
            
            # Check compliance
            compliance_result = compliance_manager.check_url_compliance(base_url)
            
            if not compliance_result['allowed']:
                logger.warning(f"Source {source} blocked: {compliance_result['reasons']}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking compliance for {source}: {e}")
            return True  # Allow if we can't check
    
    def get_source_status(self) -> Dict[str, Any]:
        """
        Get status information for all scraping sources
        
        Returns:
            Dictionary with status information for each source
        """
        status = {}
        
        for source in self.scrapers.keys():
            try:
                # Get recent scraping metrics
                recent_sessions = scraper_monitor.get_recent_sessions(
                    source=source,
                    hours=24
                )
                
                last_session = None
                if recent_sessions:
                    last_session = max(recent_sessions, key=lambda x: x.get('timestamp', datetime.min))
                
                status[source] = {
                    'enabled': source in self.enabled_sources,
                    'last_scrape': last_session.get('timestamp') if last_session else None,
                    'last_vehicles_count': last_session.get('vehicles_count', 0) if last_session else 0,
                    'last_success': last_session.get('success', False) if last_session else False,
                    'sessions_24h': len(recent_sessions),
                    'compliance_score': compliance_manager.calculate_compliance_score()
                }
                
            except Exception as e:
                logger.error(f"Error getting status for {source}: {e}")
                status[source] = {
                    'enabled': source in self.enabled_sources,
                    'error': str(e)
                }
        
        return status
    
    def scrape_source(self, source: str, max_vehicles: int = None) -> ScrapingResult:
        """
        Scrape data from a specific source
        
        Args:
            source: Source identifier
            max_vehicles: Maximum vehicles to scrape
        
        Returns:
            ScrapingResult object
        """
        if source not in self.scrapers:
            raise ValueError(f"Unknown scraper source: {source}")
        
        if max_vehicles is None:
            max_vehicles = scraper_settings.MAX_PAGES_TO_SCRAPE
        
        return self._scrape_single_source(source, max_vehicles)
    
    def enable_source(self, source: str) -> bool:
        """
        Enable a scraping source
        
        Args:
            source: Source identifier
        
        Returns:
            True if successfully enabled, False otherwise
        """
        if source not in self.scrapers:
            logger.error(f"Cannot enable unknown source: {source}")
            return False
        
        if source not in self.enabled_sources:
            self.enabled_sources.append(source)
            logger.info(f"Enabled scraping source: {source}")
        
        return True
    
    def disable_source(self, source: str) -> bool:
        """
        Disable a scraping source
        
        Args:
            source: Source identifier
        
        Returns:
            True if successfully disabled, False otherwise
        """
        if source in self.enabled_sources:
            self.enabled_sources.remove(source)
            logger.info(f"Disabled scraping source: {source}")
        
        return True


# Global instance
multi_source_scraper = MultiSourceScraper()
