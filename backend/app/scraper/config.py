"""
Scraper Configuration Module

This module contains all configuration settings for the automotive web scraper.
"""

from pydantic_settings import BaseSettings
from typing import List, Dict, Any
import os


class ScraperSettings(BaseSettings):
    """Configuration settings for the web scraper"""
    
    # Target Website Configuration
    BASE_URL: str = "https://gruppoautouno.it"
    USATO_URL: str = "https://gruppoautouno.it/usato"
    
    # Request Configuration
    REQUEST_DELAY: float = 2.0  # Seconds between requests
    REQUEST_TIMEOUT: int = 30   # Request timeout in seconds
    MAX_RETRIES: int = 3        # Maximum retry attempts
    CONCURRENT_REQUESTS: int = 1 # Maximum concurrent requests
    
    # User Agent Configuration
    USER_AGENTS: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    
    # Selenium Configuration
    SELENIUM_HEADLESS: bool = True
    SELENIUM_TIMEOUT: int = 30
    SELENIUM_PAGE_LOAD_TIMEOUT: int = 30
    
    # 24/7 Automated Scraping Schedule Configuration
    SCRAPING_ENABLED: bool = True
    SCRAPING_INTERVAL_HOURS: int = 8  # Legacy setting
    SCRAPING_START_HOUR: int = 2  # Start at 2 AM to avoid peak hours

    # Enhanced 24/7 Scheduling Configuration
    ENABLE_24_7_SCRAPING: bool = True
    COMPREHENSIVE_SCRAPING_INTERVAL_HOURS: int = 2  # Every 2 hours
    PEAK_HOURS_SCRAPING_INTERVAL_MINUTES: int = 30  # Every 30 minutes during peak hours
    OFF_PEAK_SCRAPING_INTERVAL_HOURS: int = 4  # Every 4 hours during off-peak
    REALTIME_MONITORING_INTERVAL_MINUTES: int = 10  # Every 10 minutes for new listings

    # Peak Hours Configuration (8 AM - 10 PM)
    PEAK_HOURS_START: int = 8  # 8 AM
    PEAK_HOURS_END: int = 22   # 10 PM

    # Scraping Load Configuration
    COMPREHENSIVE_MAX_VEHICLES: int = 200  # Max vehicles per comprehensive scraping
    PEAK_HOURS_MAX_VEHICLES: int = 100     # Max vehicles per source during peak hours
    OFF_PEAK_MAX_VEHICLES: int = 50        # Max vehicles per source during off-peak
    REALTIME_MAX_VEHICLES: int = 20        # Max vehicles per source for real-time monitoring

    # Performance Optimization
    ENABLE_ADAPTIVE_SCHEDULING: bool = True  # Adjust intervals based on activity
    ENABLE_LOAD_BALANCING: bool = True       # Balance load across sources
    ENABLE_SMART_RETRY: bool = True          # Smart retry logic for failed scraping

    # Multi-Source Configuration
    ENABLE_AUTOSCOUT24: bool = True
    ENABLE_MOBILE_DE: bool = True
    ENABLE_GRUPPOAUTOUNO: bool = True

    # Data Processing Configuration
    MAX_PAGES_TO_SCRAPE: int = 50
    ENABLE_IMAGE_DOWNLOAD: bool = False
    IMAGE_STORAGE_PATH: str = "/tmp/scraped_images"
    
    # Database Configuration
    ENABLE_DEDUPLICATION: bool = True
    KEEP_HISTORICAL_DATA: bool = True
    DATA_RETENTION_DAYS: int = 365
    
    # Monitoring Configuration
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 8001
    LOG_LEVEL: str = "INFO"
    
    # Error Handling Configuration
    MAX_CONSECUTIVE_FAILURES: int = 5
    FAILURE_COOLDOWN_MINUTES: int = 30
    ENABLE_EMAIL_ALERTS: bool = False
    ALERT_EMAIL: str = ""
    
    # Rate Limiting Configuration
    REQUESTS_PER_MINUTE: int = 30
    REQUESTS_PER_HOUR: int = 1000
    
    # Compliance Configuration
    RESPECT_ROBOTS_TXT: bool = True
    ENABLE_POLITENESS_DELAY: bool = True
    
    class Config:
        env_file = ".env"
        env_prefix = "SCRAPER_"


# Global scraper settings instance
scraper_settings = ScraperSettings()


# CSS Selectors for data extraction
CSS_SELECTORS = {
    "listing_page": {
        "vehicle_cards": "div[class*='vehicle-card'], article[class*='usato']",
        "vehicle_links": "a[href*='/usato/']",
        "load_more_button": "a[href*='page/'], button[class*='load-more']",
        "total_count": "span[class*='count'], div[class*='results-count']"
    },
    "detail_page": {
        "title": "h1, .vehicle-title, .car-title",
        "price": "[class*='price'], .prezzo, .costo",
        "make": "[class*='make'], .marca",
        "model": "[class*='model'], .modello",
        "year": "[class*='year'], .anno, [class*='immatricolazione']",
        "mileage": "[class*='km'], [class*='chilometr'], [class*='mileage']",
        "fuel_type": "[class*='fuel'], [class*='alimentazione']",
        "transmission": "[class*='transmission'], [class*='cambio']",
        "engine_power": "[class*='power'], [class*='potenza']",
        "displacement": "[class*='displacement'], [class*='cilindrata']",
        "doors": "[class*='doors'], [class*='porte']",
        "seats": "[class*='seats'], [class*='posti']",
        "features": "[class*='features'], [class*='dotazioni'] li, .equipment li",
        "images": "img[src*='usato'], .gallery img, .vehicle-images img",
        "listing_id": "[class*='id'], [data-id]",
        "dealer_info": "[class*='dealer'], [class*='concessionaria']"
    }
}


# Data field mappings for normalization
FIELD_MAPPINGS = {
    "fuel_types": {
        "benzina": "gasoline",
        "diesel": "diesel",
        "gpl": "lpg",
        "metano": "cng",
        "elettrica": "electric",
        "ibrida": "hybrid"
    },
    "transmission_types": {
        "manuale": "manual",
        "automatico": "automatic",
        "sequenziale": "sequential"
    },
    "condition_types": {
        "nuovo": "new",
        "usato": "used",
        "km 0": "demo"
    }
}


# Headers for HTTP requests
DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0"
}
