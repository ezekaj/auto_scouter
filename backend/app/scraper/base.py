"""
Base Scraper Classes

This module contains the base classes and utilities for web scraping.
"""

import requests
import time
import random
import logging
from typing import Optional, Dict, List, Any
from urllib.parse import urljoin, urlparse
# Removed fake_useragent dependency - using static user agents
from bs4 import BeautifulSoup
# Selenium imports removed - not needed for basic scraping
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException, WebDriverException

from app.scraper.config import scraper_settings, DEFAULT_HEADERS

# Use standard logging instead of structlog
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiting utility to control request frequency"""
    
    def __init__(self, requests_per_minute: int = 30, requests_per_hour: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.minute_requests = []
        self.hour_requests = []
    
    def wait_if_needed(self):
        """Wait if rate limits would be exceeded"""
        current_time = time.time()
        
        # Clean old requests
        self.minute_requests = [t for t in self.minute_requests if current_time - t < 60]
        self.hour_requests = [t for t in self.hour_requests if current_time - t < 3600]
        
        # Check minute limit
        if len(self.minute_requests) >= self.requests_per_minute:
            sleep_time = 60 - (current_time - self.minute_requests[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        # Check hour limit
        if len(self.hour_requests) >= self.requests_per_hour:
            sleep_time = 3600 - (current_time - self.hour_requests[0])
            if sleep_time > 0:
                logger.info(f"Hourly rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        # Record this request
        self.minute_requests.append(current_time)
        self.hour_requests.append(current_time)


class BaseScraper:
    """Base scraper class with common functionality"""
    
    def __init__(self):
        self.session = requests.Session()
        self.rate_limiter = RateLimiter(
            scraper_settings.REQUESTS_PER_MINUTE,
            scraper_settings.REQUESTS_PER_HOUR
        )
        # Use static user agent instead of fake_useragent
        self.setup_session()
    
    def setup_session(self):
        """Configure the requests session"""
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.timeout = scraper_settings.REQUEST_TIMEOUT
        
        # Set a random user agent
        self.session.headers['User-Agent'] = random.choice(scraper_settings.USER_AGENTS)
    
    def get_page(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Fetch a web page with rate limiting and error handling
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments for requests.get()
        
        Returns:
            Response object or None if failed
        """
        self.rate_limiter.wait_if_needed()
        
        # Add politeness delay
        if scraper_settings.ENABLE_POLITENESS_DELAY:
            delay = scraper_settings.REQUEST_DELAY + random.uniform(0, 1)
            time.sleep(delay)
        
        for attempt in range(scraper_settings.MAX_RETRIES):
            try:
                logger.info(f"Fetching URL: {url} (attempt {attempt + 1})")
                
                response = self.session.get(url, **kwargs)
                response.raise_for_status()
                
                logger.info(f"Successfully fetched {url} - Status: {response.status_code}")
                return response
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed for {url}: {e}")
                if attempt < scraper_settings.MAX_RETRIES - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch {url} after {scraper_settings.MAX_RETRIES} attempts")
        
        return None
    
    def parse_html(self, html_content: str) -> BeautifulSoup:
        """Parse HTML content with BeautifulSoup"""
        return BeautifulSoup(html_content, 'lxml')
    
    def extract_text(self, element, default: str = "") -> str:
        """Safely extract text from a BeautifulSoup element"""
        if element:
            return element.get_text(strip=True)
        return default
    
    def extract_attribute(self, element, attribute: str, default: str = "") -> str:
        """Safely extract an attribute from a BeautifulSoup element"""
        if element:
            return element.get(attribute, default)
        return default
    
    def clean_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not price_text:
            return None
        
        # Remove currency symbols and spaces
        import re
        price_clean = re.sub(r'[€$£,\s]', '', price_text)
        price_clean = price_clean.replace('.', '')  # Remove thousands separator
        
        try:
            return float(price_clean)
        except ValueError:
            logger.warning(f"Could not parse price: {price_text}")
            return None
    
    def clean_number(self, text: str) -> Optional[int]:
        """Extract integer from text"""
        if not text:
            return None
        
        import re
        numbers = re.findall(r'\d+', text.replace('.', '').replace(',', ''))
        if numbers:
            try:
                return int(numbers[0])
            except ValueError:
                pass
        return None
    
    def normalize_fuel_type(self, fuel_text: str) -> Optional[str]:
        """Normalize fuel type to standard values"""
        if not fuel_text:
            return None
        
        fuel_lower = fuel_text.lower()
        fuel_mappings = {
            'benzina': 'gasoline',
            'diesel': 'diesel',
            'elettrica': 'electric',
            'ibrida': 'hybrid',
            'gpl': 'lpg',
            'metano': 'cng'
        }
        
        for italian, english in fuel_mappings.items():
            if italian in fuel_lower:
                return english
        
        return fuel_text.lower()
    
    def normalize_transmission(self, transmission_text: str) -> Optional[str]:
        """Normalize transmission type to standard values"""
        if not transmission_text:
            return None
        
        trans_lower = transmission_text.lower()
        if 'automatico' in trans_lower or 'automatic' in trans_lower:
            return 'automatic'
        elif 'manuale' in trans_lower or 'manual' in trans_lower:
            return 'manual'
        
        return transmission_text.lower()


# SeleniumScraper class commented out - not needed for basic scraping
"""
class SeleniumScraper(BaseScraper):
    # Selenium-based scraper for JavaScript-heavy sites

    def __init__(self):
        super().__init__()
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        # Setup Chrome WebDriver with appropriate options
        chrome_options = Options()

        if scraper_settings.SELENIUM_HEADLESS:
            chrome_options.add_argument('--headless')

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'--user-agent={random.choice(scraper_settings.USER_AGENTS)}')

        # Disable images and CSS for faster loading
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(scraper_settings.SELENIUM_PAGE_LOAD_TIMEOUT)
            self.driver.implicitly_wait(scraper_settings.SELENIUM_TIMEOUT)
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise
"""

# SeleniumScraper class and methods have been removed to eliminate selenium dependency
