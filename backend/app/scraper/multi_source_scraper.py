"""
Multi-Source Scraper Module
Manages scraping from multiple vehicle listing sources
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ScrapingResult:
    """Result of a scraping operation"""
    success: bool
    vehicles_scraped: int = 0
    errors: List[str] = None
    duration_seconds: float = 0.0
    source: str = ""
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class MultiSourceScraper:
    """Manages scraping from multiple vehicle sources"""
    
    def __init__(self):
        self.sources = {
            "ayvens": {
                "name": "Ayvens Carmarket",
                "enabled": True,
                "url": "https://carmarket.ayvens.com",
                "country": "EU",
                "status": "active",
                "last_scrape": None,
                "total_scraped": 0
            },

        }

    def get_sources(self) -> Dict[str, Dict[str, Any]]:
        """Get all available sources"""
        return self.sources

    def get_source_status(self) -> Dict[str, Any]:
        """Get status of all scraping sources"""
        return {
            "sources": self.sources,
            "total_sources": len(self.sources),
            "enabled_sources": len([s for s in self.sources.values() if s["enabled"]]),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def enable_source(self, source: str) -> bool:
        """Enable a scraping source"""
        if source in self.sources:
            self.sources[source]["enabled"] = True
            self.sources[source]["status"] = "active"
            logger.info(f"Source {source} enabled")
            return True
        return False
    
    def disable_source(self, source: str) -> bool:
        """Disable a scraping source"""
        if source in self.sources:
            self.sources[source]["enabled"] = False
            self.sources[source]["status"] = "disabled"
            logger.info(f"Source {source} disabled")
            return True
        return False
    
    def scrape_source(self, source: str, max_vehicles: int = 50) -> ScrapingResult:
        """Scrape from a specific source"""
        if source not in self.sources:
            return ScrapingResult(
                success=False,
                errors=[f"Unknown source: {source}"],
                source=source
            )
            
        if not self.sources[source]["enabled"]:
            return ScrapingResult(
                success=False,
                errors=[f"Source {source} is disabled"],
                source=source
            )
        
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting scraping from {source} (max: {max_vehicles})")

            # Call the appropriate scraper based on source
            vehicles_found = 0

            if source == "ayvens":
                from app.scraper.ayvens_scraper import AyvensCarmarketScraper
                scraper = AyvensCarmarketScraper()
                vehicles = scraper.scrape_all_listings(max_vehicles)
                vehicles_found = len(vehicles)
            else:
                logger.error(f"Unknown or unsupported source: {source}")
                vehicles_found = 0

            # Update source statistics
            self.sources[source]["last_scrape"] = datetime.utcnow().isoformat()
            self.sources[source]["total_scraped"] += vehicles_found

            duration = (datetime.utcnow() - start_time).total_seconds()

            logger.info(f"Scraping from {source} completed: {vehicles_found} vehicles")

            return ScrapingResult(
                success=True,
                vehicles_scraped=vehicles_found,
                duration_seconds=duration,
                source=source
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Scraping from {source} failed: {e}")
            
            return ScrapingResult(
                success=False,
                errors=[str(e)],
                duration_seconds=duration,
                source=source
            )
    
    def scrape_all_enabled(self, max_vehicles_per_source: int = 50) -> Dict[str, ScrapingResult]:
        """Scrape from all enabled sources"""
        results = {}
        
        for source_id, source_info in self.sources.items():
            if source_info["enabled"]:
                results[source_id] = self.scrape_source(source_id, max_vehicles_per_source)
            else:
                results[source_id] = ScrapingResult(
                    success=False,
                    errors=["Source is disabled"],
                    source=source_id
                )
                
        return results
    
    def get_scraping_statistics(self) -> Dict[str, Any]:
        """Get overall scraping statistics"""
        total_scraped = sum(source["total_scraped"] for source in self.sources.values())
        enabled_count = len([s for s in self.sources.values() if s["enabled"]])
        
        return {
            "total_vehicles_scraped": total_scraped,
            "total_sources": len(self.sources),
            "enabled_sources": enabled_count,
            "sources_breakdown": {
                source_id: {
                    "total_scraped": info["total_scraped"],
                    "last_scrape": info["last_scrape"],
                    "enabled": info["enabled"]
                }
                for source_id, info in self.sources.items()
            },
            "last_updated": datetime.utcnow().isoformat()
        }

# Global multi-source scraper instance
multi_source_scraper = MultiSourceScraper()
