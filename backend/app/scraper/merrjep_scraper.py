"""
MerrJep.com Car Scraper for Albanian/Kosovo Market

This module scrapes car listings from MerrJep.com, the largest classified ads
website in Kosovo/Albania for automotive listings.
"""

import re
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag

from app.scraper.base import BaseScraper
from app.scraper.config import scraper_settings
from app.schemas.automotive import VehicleListingCreate
import logging

logger = logging.getLogger(__name__)


class MerrJepScraper(BaseScraper):
    """Scraper for MerrJep.com Albanian/Kosovo car marketplace"""
    
    def __init__(self):
        super().__init__()
        self.base_url = scraper_settings.BASE_URL
        self.cars_url = scraper_settings.CARS_URL
        self.session_id = str(uuid.uuid4())
        self.scraped_urls = set()
        
    def scrape_all_listings(self, max_vehicles: int = 50) -> List[Dict[str, Any]]:
        """
        Scrape car listings from MerrJep.com

        Args:
            max_vehicles: Maximum number of vehicles to scrape

        Returns:
            List of vehicle data dictionaries
        """
        logger.info(f"Starting MerrJep scrape session {self.session_id}")
        all_vehicles = []

        try:
            page = 1
            while len(all_vehicles) < max_vehicles:
                # Build page URL
                page_url = f"{self.cars_url}?page={page}"

                response = self.get_page(page_url)
                if not response:
                    logger.error(f"Failed to fetch page {page}")
                    break

                soup = self.parse_html(response.text)

                # Extract vehicles directly from listing page
                vehicles_on_page = self.extract_vehicles_from_listing_page(soup)
                if not vehicles_on_page:
                    logger.info(f"No more vehicles found on page {page}")
                    break

                logger.info(f"Found {len(vehicles_on_page)} vehicles on page {page}")

                # Add vehicles to results
                for vehicle_data in vehicles_on_page:
                    if len(all_vehicles) >= max_vehicles:
                        break
                    all_vehicles.append(vehicle_data)
                    logger.info(f"Scraped vehicle {len(all_vehicles)}: {vehicle_data.get('make', 'Unknown')} {vehicle_data.get('model', 'Unknown')} - {vehicle_data.get('price', 'N/A')} EUR")

                page += 1

                # Safety limit to prevent infinite loops
                if page > 3:  # Limit to 3 pages for testing
                    logger.warning("Reached maximum page limit (3)")
                    break

        except Exception as e:
            logger.error(f"Error during scraping: {e}")

        logger.info(f"Scraping completed. Total vehicles: {len(all_vehicles)}")
        return all_vehicles
    
    def extract_vehicle_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract vehicle detail page links from listing page"""
        links = []

        try:
            # MerrJep vehicle listings are in anchor tags with specific href patterns
            # Look for all links that contain '/shpallja/makina/vetura/'
            all_links = soup.find_all('a', href=True)

            for link in all_links:
                href = link.get('href', '')
                if '/shpallja/makina/vetura/' in href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in self.scraped_urls:
                        links.append(full_url)
                        self.scraped_urls.add(full_url)

        except Exception as e:
            logger.error(f"Error extracting vehicle links: {e}")

        return links

    def extract_vehicles_from_listing_page(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract vehicle data directly from the listing page"""
        vehicles = []

        try:
            # Find all vehicle listing containers
            # MerrJep listings appear to be in anchor tags with specific patterns
            listing_links = soup.find_all('a', href=True)

            for link in listing_links:
                href = link.get('href', '')
                if '/shpallja/makina/vetura/' in href:
                    vehicle_data = self.extract_vehicle_from_listing_element(link, href)
                    if vehicle_data:
                        vehicles.append(vehicle_data)

        except Exception as e:
            logger.error(f"Error extracting vehicles from listing page: {e}")

        return vehicles

    def extract_vehicle_from_listing_element(self, link_element, href: str) -> Optional[Dict[str, Any]]:
        """Extract vehicle data from a single listing element"""
        try:
            # Get the full URL
            full_url = urljoin(self.base_url, href)

            # Extract external ID from URL
            external_id = self.extract_external_id(full_url)

            # Get the title from the link text or nearby elements
            title = link_element.get_text(strip=True)
            if not title:
                # Try to find title in parent elements
                parent = link_element.parent
                if parent:
                    title = parent.get_text(strip=True)

            if not title or len(title) < 5:
                return None

            # Parse make and model from title
            make_model = self.parse_make_model(title)

            # Try to find price, year, and mileage in the surrounding text
            price_info = self.extract_price_from_context(link_element)
            year_info = self.extract_year_from_context(link_element)
            mileage_info = self.extract_mileage_from_context(link_element)
            location_info = self.extract_location_from_context(link_element)

            vehicle_data = {
                'external_id': external_id,
                'listing_url': full_url,
                'source_website': 'merrjep.com',
                'source_country': 'AL',
                'scraped_at': datetime.utcnow(),
                'is_active': True,
                'confidence_score': 1.0,
                'title': title
            }

            # Add extracted data
            vehicle_data.update(make_model)
            vehicle_data.update(price_info)
            vehicle_data.update(year_info)
            vehicle_data.update(mileage_info)
            vehicle_data.update(location_info)

            return vehicle_data

        except Exception as e:
            logger.error(f"Error extracting vehicle from element: {e}")
            return None
    
    def scrape_vehicle_detail(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape detailed information from a vehicle listing page"""
        try:
            response = self.get_page(url)
            if not response:
                return None
                
            soup = self.parse_html(response.text)
            
            # Extract vehicle data
            vehicle_data = {
                'external_id': self.extract_external_id(url),
                'listing_url': url,
                'source_website': 'merrjep.com',
                'source_country': 'AL',  # Albania/Kosovo
                'scraped_at': datetime.utcnow(),
                'is_active': True,
                'confidence_score': 1.0
            }
            
            # Extract title and parse make/model
            title = self.extract_title(soup)
            if title:
                make_model = self.parse_make_model(title)
                vehicle_data.update(make_model)
            
            # Extract price
            price_info = self.extract_price(soup)
            vehicle_data.update(price_info)
            
            # Extract other details
            vehicle_data.update(self.extract_vehicle_details(soup))
            
            # Extract images
            images = self.extract_images(soup)
            vehicle_data['images'] = images
            
            return vehicle_data
            
        except Exception as e:
            logger.error(f"Error scraping vehicle detail from {url}: {e}")
            return None
    
    def extract_external_id(self, url: str) -> str:
        """Extract unique ID from URL"""
        # MerrJep URLs typically end with a numeric ID
        match = re.search(r'/(\d+)/?$', url)
        if match:
            return f"merrjep_{match.group(1)}"
        else:
            # Fallback to URL hash
            return f"merrjep_{hash(url)}"
    
    def extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract vehicle title from page"""
        # Try different possible title selectors
        selectors = [
            'h1.ad-title',
            'h1',
            '.ad-title',
            '.listing-title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None
    
    def parse_make_model(self, title: str) -> Dict[str, str]:
        """Parse make and model from title"""
        # Common car makes in Albanian market
        makes = [
            'BMW', 'Mercedes', 'Audi', 'Volkswagen', 'VW', 'Opel', 'Ford',
            'Peugeot', 'Renault', 'Fiat', 'Toyota', 'Honda', 'Nissan',
            'Hyundai', 'Kia', 'Skoda', 'Seat', 'Citroen', 'Mazda',
            'Mitsubishi', 'Subaru', 'Volvo', 'Alfa Romeo', 'Lancia'
        ]
        
        title_upper = title.upper()
        
        for make in makes:
            if make.upper() in title_upper:
                # Extract model (word after make)
                pattern = rf'\b{re.escape(make.upper())}\s+(\w+)'
                match = re.search(pattern, title_upper)
                model = match.group(1) if match else None
                
                return {
                    'make': make,
                    'model': model,
                    'title': title
                }
        
        return {'title': title}
    
    def extract_price(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract price information"""
        price_data = {'currency': 'EUR'}  # Default currency in Kosovo/Albania
        
        # Try different price selectors
        selectors = [
            '.price',
            '.ad-price',
            '.listing-price',
            '[class*="price"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                price = self.parse_price(price_text)
                if price:
                    price_data['price'] = price
                    break
        
        return price_data
    
    def parse_price(self, price_text: str) -> Optional[float]:
        """Parse price from text"""
        # Remove common currency symbols and text
        clean_text = re.sub(r'[€$£,\s]', '', price_text)
        clean_text = re.sub(r'(EUR|USD|euro|dollar)', '', clean_text, flags=re.IGNORECASE)
        
        # Extract numeric value
        match = re.search(r'(\d+(?:\.\d+)?)', clean_text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        
        return None
    
    def extract_vehicle_details(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract additional vehicle details"""
        details = {}
        
        # Try to find details table or list
        detail_elements = soup.find_all(['dt', 'dd', 'li', 'span'])
        
        for element in detail_elements:
            text = element.get_text(strip=True).lower()
            
            # Extract year
            year_match = re.search(r'\b(19|20)\d{2}\b', text)
            if year_match and 'year' not in details:
                details['year'] = int(year_match.group())
            
            # Extract mileage
            if 'km' in text:
                mileage_match = re.search(r'(\d+(?:,\d+)*)\s*km', text)
                if mileage_match:
                    mileage_str = mileage_match.group(1).replace(',', '')
                    try:
                        details['mileage'] = int(mileage_str)
                    except ValueError:
                        pass
            
            # Extract fuel type
            fuel_types = ['benzin', 'diesel', 'gas', 'elektrik', 'hibrid']
            for fuel in fuel_types:
                if fuel in text:
                    details['fuel_type'] = fuel
                    break
        
        return details
    
    def extract_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract image URLs"""
        images = []
        
        # Find image elements
        img_elements = soup.find_all('img')
        
        for img in img_elements:
            src = img.get('src') or img.get('data-src')
            if src and ('car' in src.lower() or 'vehicle' in src.lower() or 'auto' in src.lower()):
                full_url = urljoin(self.base_url, src)
                if full_url not in images:
                    images.append(full_url)
        
        return images[:5]  # Limit to 5 images
