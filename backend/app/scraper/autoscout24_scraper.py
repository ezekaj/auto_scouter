"""
AutoScout24 Scraper

This module contains the scraper implementation for extracting
automotive data from AutoScout24.com
"""

import re
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup, Tag

from app.scraper.base import BaseScraper
from app.scraper.config import scraper_settings
from app.schemas.automotive import VehicleListingCreate, VehicleImageCreate
import logging

logger = logging.getLogger(__name__)


class AutoScout24Scraper(BaseScraper):
    """Scraper for AutoScout24.com automotive listings"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.autoscout24.com"
        self.search_url = "https://www.autoscout24.com/lst"
        self.session_id = str(uuid.uuid4())
        self.scraped_urls = set()
        
        # AutoScout24 specific headers
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def scrape_all_listings(self, max_vehicles: int = None) -> List[Dict[str, Any]]:
        """
        Scrape all vehicle listings from AutoScout24
        
        Args:
            max_vehicles: Maximum number of vehicles to scrape
        
        Returns:
            List of vehicle data dictionaries
        """
        logger.info(f"Starting AutoScout24 scrape session {self.session_id}")
        all_vehicles = []
        
        if max_vehicles is None:
            max_vehicles = scraper_settings.MAX_PAGES_TO_SCRAPE
        
        try:
            # Start with the main search page
            page = 1
            while len(all_vehicles) < max_vehicles:
                search_params = {
                    'sort': 'standard',
                    'desc': '0',
                    'ustate': 'U',  # Used cars
                    'size': '20',   # Results per page
                    'page': str(page)
                }
                
                search_url = f"{self.search_url}?" + "&".join([f"{k}={v}" for k, v in search_params.items()])
                
                response = self.get_page(search_url)
                if not response:
                    logger.error(f"Failed to fetch search page {page}")
                    break
                
                soup = self.parse_html(response.text)
                
                # Extract vehicle links from the search results
                vehicle_links = self.extract_vehicle_links(soup)
                if not vehicle_links:
                    logger.info(f"No more vehicles found on page {page}")
                    break
                
                logger.info(f"Found {len(vehicle_links)} vehicle links on page {page}")
                
                # Scrape each vehicle detail page
                for link in vehicle_links:
                    if len(all_vehicles) >= max_vehicles:
                        break
                        
                    vehicle_data = self.scrape_vehicle_detail(link)
                    if vehicle_data:
                        all_vehicles.append(vehicle_data)
                        logger.info(f"Scraped vehicle {len(all_vehicles)}/{max_vehicles}: {vehicle_data.get('make')} {vehicle_data.get('model')}")
                
                page += 1
                
                # Progress logging
                if len(all_vehicles) % 10 == 0:
                    logger.info(f"Progress: {len(all_vehicles)}/{max_vehicles} vehicles scraped")
            
            logger.info(f"AutoScout24 scraping session {self.session_id} completed. Total vehicles: {len(all_vehicles)}")
            
        except Exception as e:
            logger.error(f"Error during AutoScout24 scraping session: {e}")
        
        return all_vehicles
    
    def extract_vehicle_links(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract all vehicle detail page links from the search results page
        
        Args:
            soup: BeautifulSoup object of the search results page
        
        Returns:
            List of absolute URLs to vehicle detail pages
        """
        links = []
        
        # AutoScout24 specific selectors for vehicle links
        selectors = [
            'article[data-item-name="listing"] a[href*="/offers/"]',
            '.cldt-summary-full-item a[href*="/offers/"]',
            'a[data-item-name="detail-page-link"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href and '/offers/' in href and href not in self.scraped_urls:
                    absolute_url = urljoin(self.base_url, href)
                    if absolute_url not in links:
                        links.append(absolute_url)
                        self.scraped_urls.add(href)
        
        return links
    
    def scrape_vehicle_detail(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape detailed information from an AutoScout24 vehicle detail page
        
        Args:
            url: URL of the vehicle detail page
        
        Returns:
            Dictionary containing vehicle data or None if failed
        """
        try:
            response = self.get_page(url)
            if not response:
                logger.warning(f"Failed to fetch AutoScout24 vehicle page: {url}")
                return None
            
            soup = self.parse_html(response.text)
            
            # Extract vehicle data
            vehicle_data = {
                'listing_url': url,
                'external_id': self.extract_external_id(url, soup),
                'source_website': 'autoscout24.com'
            }
            
            # Extract basic information
            vehicle_data.update(self.extract_basic_info(soup))
            
            # Extract technical specifications
            vehicle_data.update(self.extract_technical_specs(soup))
            
            # Extract pricing information
            vehicle_data.update(self.extract_pricing_info(soup))
            
            # Extract images
            vehicle_data['images'] = self.extract_images(soup)
            
            # Extract features and description
            vehicle_data.update(self.extract_content_info(soup))
            
            # Extract dealer information
            vehicle_data.update(self.extract_dealer_info(soup))
            
            # Set metadata
            vehicle_data['scraped_at'] = datetime.utcnow()
            
            return vehicle_data
            
        except Exception as e:
            logger.error(f"Error scraping AutoScout24 vehicle detail {url}: {e}")
            return None
    
    def extract_external_id(self, url: str, soup: BeautifulSoup) -> str:
        """Extract external ID from URL or page content"""
        # Try to extract ID from URL
        match = re.search(r'/offers/([^/?]+)', url)
        if match:
            return f"as24_{match.group(1)}"
        
        # Fallback to generating ID from URL
        return f"as24_{hash(url) % 1000000}"
    
    def extract_basic_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract basic vehicle information"""
        data = {}
        
        try:
            # Extract title (usually contains make and model)
            title_elem = soup.select_one('h1[data-item-name="detail-title"]')
            if title_elem:
                title = title_elem.get_text(strip=True)
                # Parse make and model from title
                parts = title.split()
                if len(parts) >= 2:
                    data['make'] = parts[0]
                    data['model'] = ' '.join(parts[1:3])  # Take next 1-2 words as model
            
            # Extract year
            year_elem = soup.select_one('[data-item-name="first-registration"]')
            if year_elem:
                year_text = year_elem.get_text(strip=True)
                year_match = re.search(r'(\d{4})', year_text)
                if year_match:
                    data['year'] = int(year_match.group(1))
            
            # Extract mileage
            mileage_elem = soup.select_one('[data-item-name="mileage"]')
            if mileage_elem:
                mileage_text = mileage_elem.get_text(strip=True)
                mileage_match = re.search(r'([\d,]+)', mileage_text.replace('.', ','))
                if mileage_match:
                    data['mileage_km'] = int(mileage_match.group(1).replace(',', ''))
            
        except Exception as e:
            logger.warning(f"Error extracting basic info: {e}")
        
        return data
    
    def extract_technical_specs(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract technical specifications"""
        data = {}
        
        try:
            # Extract fuel type
            fuel_elem = soup.select_one('[data-item-name="fuel-type"]')
            if fuel_elem:
                fuel_text = fuel_elem.get_text(strip=True).lower()
                if 'petrol' in fuel_text or 'gasoline' in fuel_text:
                    data['fuel_type'] = 'petrol'
                elif 'diesel' in fuel_text:
                    data['fuel_type'] = 'diesel'
                elif 'electric' in fuel_text:
                    data['fuel_type'] = 'electric'
                elif 'hybrid' in fuel_text:
                    data['fuel_type'] = 'hybrid'
            
            # Extract transmission
            transmission_elem = soup.select_one('[data-item-name="transmission"]')
            if transmission_elem:
                transmission_text = transmission_elem.get_text(strip=True).lower()
                if 'manual' in transmission_text:
                    data['transmission'] = 'manual'
                elif 'automatic' in transmission_text:
                    data['transmission'] = 'automatic'
            
            # Extract power
            power_elem = soup.select_one('[data-item-name="power"]')
            if power_elem:
                power_text = power_elem.get_text(strip=True)
                power_match = re.search(r'(\d+)\s*(?:hp|kw|ps)', power_text.lower())
                if power_match:
                    data['power_hp'] = int(power_match.group(1))
            
        except Exception as e:
            logger.warning(f"Error extracting technical specs: {e}")
        
        return data
    
    def extract_pricing_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract pricing information"""
        data = {}
        
        try:
            # Extract price
            price_elem = soup.select_one('[data-item-name="price"]')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'([\d,]+)', price_text.replace('.', ','))
                if price_match:
                    data['price_eur'] = int(price_match.group(1).replace(',', ''))
            
        except Exception as e:
            logger.warning(f"Error extracting pricing info: {e}")
        
        return data
    
    def extract_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract vehicle images"""
        images = []
        
        try:
            # Look for image elements
            img_selectors = [
                '.gallery-picture img',
                '.image-gallery img',
                '[data-item-name="gallery"] img'
            ]
            
            for selector in img_selectors:
                img_elements = soup.select(selector)
                for img in img_elements:
                    src = img.get('src') or img.get('data-src')
                    if src and src.startswith('http'):
                        if src not in images:
                            images.append(src)
            
        except Exception as e:
            logger.warning(f"Error extracting images: {e}")
        
        return images
    
    def extract_content_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract description and features"""
        data = {}
        
        try:
            # Extract description
            desc_elem = soup.select_one('[data-item-name="description"]')
            if desc_elem:
                data['description'] = desc_elem.get_text(strip=True)
            
            # Extract features
            features = []
            feature_elems = soup.select('.equipment-block li, .features-list li')
            for elem in feature_elems:
                feature = elem.get_text(strip=True)
                if feature:
                    features.append(feature)
            
            if features:
                data['features'] = json.dumps(features)
            
        except Exception as e:
            logger.warning(f"Error extracting content info: {e}")
        
        return data
    
    def extract_dealer_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract dealer information"""
        data = {}
        
        try:
            # Extract dealer name
            dealer_elem = soup.select_one('[data-item-name="dealer-name"]')
            if dealer_elem:
                data['dealer_name'] = dealer_elem.get_text(strip=True)
            
            # Extract location
            location_elem = soup.select_one('[data-item-name="dealer-address"]')
            if location_elem:
                location_text = location_elem.get_text(strip=True)
                data['dealer_location'] = location_text
                
                # Try to extract city from location
                parts = location_text.split(',')
                if parts:
                    data['city'] = parts[-1].strip()
            
        except Exception as e:
            logger.warning(f"Error extracting dealer info: {e}")
        
        return data
