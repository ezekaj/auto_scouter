"""
Automotive Scraper for GruppoAutoUno.it

This module contains the main scraper implementation for extracting
automotive data from the GruppoAutoUno website.
"""

import re
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag

from app.scraper.base import BaseScraper, SeleniumScraper
from app.scraper.config import scraper_settings, CSS_SELECTORS, FIELD_MAPPINGS
from app.schemas.automotive import VehicleListingCreate, VehicleImageCreate
import logging

logger = logging.getLogger(__name__)


class GruppoAutoUnoScraper(BaseScraper):
    """Main scraper for GruppoAutoUno.it automotive listings"""
    
    def __init__(self):
        super().__init__()
        self.base_url = scraper_settings.BASE_URL
        self.usato_url = scraper_settings.USATO_URL
        self.session_id = str(uuid.uuid4())
        self.scraped_urls = set()
        
    def scrape_all_listings(self) -> List[Dict[str, Any]]:
        """
        Scrape all vehicle listings from the website
        
        Returns:
            List of vehicle data dictionaries
        """
        logger.info(f"Starting scrape session {self.session_id}")
        all_vehicles = []
        
        try:
            # Get the main listing page
            response = self.get_page(self.usato_url)
            if not response:
                logger.error("Failed to fetch main listing page")
                return []
            
            soup = self.parse_html(response.text)
            
            # Extract vehicle links from the main page
            vehicle_links = self.extract_vehicle_links(soup)
            logger.info(f"Found {len(vehicle_links)} vehicle links")
            
            # Scrape each vehicle detail page
            for i, link in enumerate(vehicle_links):
                if i >= scraper_settings.MAX_PAGES_TO_SCRAPE:
                    logger.info(f"Reached maximum pages limit ({scraper_settings.MAX_PAGES_TO_SCRAPE})")
                    break
                
                vehicle_data = self.scrape_vehicle_detail(link)
                if vehicle_data:
                    all_vehicles.append(vehicle_data)
                    logger.info(f"Scraped vehicle {i+1}/{len(vehicle_links)}: {vehicle_data.get('make')} {vehicle_data.get('model')}")
                
                # Progress logging
                if (i + 1) % 10 == 0:
                    logger.info(f"Progress: {i+1}/{len(vehicle_links)} vehicles scraped")
            
            logger.info(f"Scraping session {self.session_id} completed. Total vehicles: {len(all_vehicles)}")
            
        except Exception as e:
            logger.error(f"Error during scraping session: {e}")
        
        return all_vehicles
    
    def extract_vehicle_links(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract all vehicle detail page links from the listing page
        
        Args:
            soup: BeautifulSoup object of the listing page
        
        Returns:
            List of absolute URLs to vehicle detail pages
        """
        links = []
        
        # Find all vehicle links using multiple selectors
        selectors = [
            'a[href*="/usato/"]',
            '.vehicle-card a',
            'article a[href*="/usato/"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href and '/usato/' in href and href not in self.scraped_urls:
                    absolute_url = urljoin(self.base_url, href)
                    if absolute_url not in links:
                        links.append(absolute_url)
                        self.scraped_urls.add(href)
        
        return links
    
    def scrape_vehicle_detail(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape detailed information from a vehicle detail page
        
        Args:
            url: URL of the vehicle detail page
        
        Returns:
            Dictionary containing vehicle data or None if failed
        """
        try:
            response = self.get_page(url)
            if not response:
                logger.warning(f"Failed to fetch vehicle page: {url}")
                return None
            
            soup = self.parse_html(response.text)
            
            # Extract vehicle data
            vehicle_data = {
                'listing_url': url,
                'external_id': self.extract_external_id(url, soup),
                'source_website': 'gruppoautouno.it'
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
            
            # Validate and clean data
            vehicle_data = self.clean_vehicle_data(vehicle_data)
            
            return vehicle_data
            
        except Exception as e:
            logger.error(f"Error scraping vehicle detail {url}: {e}")
            return None
    
    def extract_external_id(self, url: str, soup: BeautifulSoup) -> Optional[str]:
        """Extract the external listing ID"""
        # Try to extract from URL
        url_parts = url.split('/')
        if len(url_parts) > 1:
            last_part = url_parts[-1] or url_parts[-2]
            if last_part and last_part != 'usato':
                return last_part
        
        # Try to extract from page content
        id_patterns = [
            r'ID[.\s]*(\d+)',
            r'id[.\s]*(\d+)',
            r'listing[.\s]*(\d+)'
        ]
        
        page_text = soup.get_text()
        for pattern in id_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def extract_basic_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract basic vehicle information"""
        data = {}
        
        # Extract title and parse make/model
        title_element = soup.find('h1') or soup.select_one('.vehicle-title, .car-title')
        if title_element:
            title = self.extract_text(title_element)
            make_model = self.parse_make_model_from_title(title)
            data.update(make_model)
            data['variant'] = title
        
        # Extract year/registration date
        year_patterns = [
            r'Immatricolazione[:\s]*(\d{2})/(\d{4})',
            r'(\d{2})/(\d{4})',
            r'Anno[:\s]*(\d{4})',
            r'(\d{4})'
        ]
        
        page_text = soup.get_text()
        for pattern in year_patterns:
            match = re.search(pattern, page_text)
            if match:
                if len(match.groups()) == 2 and len(match.group(1)) == 2:
                    # Month/Year format
                    month, year = match.groups()
                    data['year'] = int(year)
                    try:
                        data['registration_date'] = datetime(int(year), int(month), 1)
                    except ValueError:
                        pass
                else:
                    # Just year
                    data['year'] = int(match.group(1) if len(match.groups()) == 1 else match.group(2))
                break
        
        return data
    
    def extract_technical_specs(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract technical specifications"""
        data = {}
        
        # Extract mileage
        km_text = self.find_text_by_patterns(soup, [r'Km[:\s]*(\d+[\d.,]*)', r'(\d+[\d.,]*)\s*km'])
        if km_text:
            data['mileage'] = self.clean_number(km_text)
        
        # Extract fuel type
        fuel_text = self.find_text_by_patterns(soup, [r'Alimentazione[:\s]*(\w+)', r'(Benzina|Diesel|Elettrica|Ibrida|GPL|Metano)'])
        if fuel_text:
            data['fuel_type'] = self.normalize_fuel_type(fuel_text)
        
        # Extract transmission
        transmission_text = self.find_text_by_patterns(soup, [r'Cambio[:\s]*(\w+)', r'(Manuale|Automatico)'])
        if transmission_text:
            data['transmission'] = self.normalize_transmission(transmission_text)
        
        # Extract engine power
        power_text = self.find_text_by_patterns(soup, [r'Potenza[:\s]*(\d+)\s*kW', r'(\d+)\s*kW'])
        if power_text:
            data['engine_power_kw'] = self.clean_number(power_text)
        
        # Extract displacement
        displacement_text = self.find_text_by_patterns(soup, [r'Cilindrata[:\s]*(\d+)', r'(\d+[\d.,]*)\s*cc'])
        if displacement_text:
            data['engine_displacement'] = self.clean_number(displacement_text)
        
        # Extract doors and seats
        doors_text = self.find_text_by_patterns(soup, [r'(\d+)\s*Porte', r'Porte[:\s]*(\d+)'])
        if doors_text:
            data['doors'] = self.clean_number(doors_text)
        
        seats_text = self.find_text_by_patterns(soup, [r'(\d+)\s*Posti', r'Posti[:\s]*(\d+)'])
        if seats_text:
            data['seats'] = self.clean_number(seats_text)
        
        # Extract cylinders and gears
        cylinders_text = self.find_text_by_patterns(soup, [r'(\d+)\s*Cilindri', r'Cilindri[:\s]*(\d+)'])
        if cylinders_text:
            data['cylinders'] = self.clean_number(cylinders_text)
        
        gears_text = self.find_text_by_patterns(soup, [r'(\d+)\s*Marce', r'Marce[:\s]*(\d+)'])
        if gears_text:
            data['gears'] = self.clean_number(gears_text)
        
        return data
    
    def extract_pricing_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract pricing information"""
        data = {}
        
        # Find price elements
        price_selectors = [
            '.price', '.prezzo', '.costo',
            '[class*="price"]', '[class*="prezzo"]',
            'span:contains("€")', 'div:contains("€")'
        ]
        
        for selector in price_selectors:
            price_element = soup.select_one(selector)
            if price_element:
                price_text = self.extract_text(price_element)
                price = self.clean_price(price_text)
                if price and price > 1000:  # Reasonable minimum price
                    data['price'] = price
                    data['currency'] = 'EUR'
                    break
        
        return data
    
    def extract_images(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract vehicle images"""
        images = []
        
        # Find image elements
        img_elements = soup.find_all('img')
        
        for i, img in enumerate(img_elements):
            src = img.get('src') or img.get('data-src')
            if src and ('usato' in src or 'vehicle' in src or 'auto' in src):
                # Make absolute URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(self.base_url, src)
                
                image_data = {
                    'image_url': src,
                    'image_order': i,
                    'alt_text': img.get('alt', ''),
                    'image_type': 'exterior' if i == 0 else 'detail'
                }
                images.append(image_data)
        
        return images[:20]  # Limit to 20 images
    
    def extract_content_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract description and features"""
        data = {}
        
        # Extract features
        features = []
        feature_lists = soup.find_all(['ul', 'ol'])
        for feature_list in feature_lists:
            list_items = feature_list.find_all('li')
            for item in list_items:
                feature_text = self.extract_text(item)
                if feature_text and len(feature_text) > 2:
                    features.append(feature_text)
        
        if features:
            data['features'] = json.dumps(features[:50])  # Limit features
        
        # Extract description
        description_selectors = [
            '.description', '.descrizione', '.vehicle-description',
            'p:contains("Disclaimer")', '.content p'
        ]
        
        for selector in description_selectors:
            desc_element = soup.select_one(selector)
            if desc_element:
                description = self.extract_text(desc_element)
                if description and len(description) > 50:
                    data['description'] = description[:1000]  # Limit length
                    break
        
        return data
    
    def extract_dealer_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract dealer information"""
        data = {
            'dealer_name': 'Autouno Group',
            'city': 'Napoli',
            'region': 'Campania',
            'country': 'IT'
        }
        
        # Try to extract more specific location info
        location_text = soup.get_text()
        if 'Avellino' in location_text:
            data['city'] = 'Avellino'
        elif 'Nola' in location_text:
            data['city'] = 'Nola'
        
        return data
    
    def find_text_by_patterns(self, soup: BeautifulSoup, patterns: List[str]) -> Optional[str]:
        """Find text matching any of the given regex patterns"""
        page_text = soup.get_text()
        for pattern in patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        return None
    
    def parse_make_model_from_title(self, title: str) -> Dict[str, str]:
        """Parse make and model from vehicle title"""
        if not title:
            return {}
        
        # Common Italian car makes
        makes = [
            'Volkswagen', 'Peugeot', 'Citroën', 'Citroen', 'Opel', 'BMW', 'Mercedes', 'Audi',
            'Fiat', 'Ford', 'Renault', 'Toyota', 'Honda', 'Nissan', 'Hyundai', 'Kia',
            'Jeep', 'Mini', 'Skoda', 'Seat', 'Alfa Romeo', 'Lancia', 'Maserati', 'Ferrari',
            'Lamborghini', 'Porsche', 'Volvo', 'Jaguar', 'Land Rover', 'MG', 'Ssangyong'
        ]
        
        title_words = title.split()
        make = None
        model = None
        
        # Find make
        for word in title_words:
            for car_make in makes:
                if word.lower() == car_make.lower():
                    make = car_make
                    break
            if make:
                break
        
        # Find model (usually the word after make)
        if make:
            try:
                make_index = next(i for i, word in enumerate(title_words) 
                                if word.lower() == make.lower())
                if make_index + 1 < len(title_words):
                    model = title_words[make_index + 1]
            except StopIteration:
                pass
        
        result = {}
        if make:
            result['make'] = make
        if model:
            result['model'] = model
        
        return result
    
    def clean_vehicle_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate vehicle data"""
        # Remove None values
        cleaned = {k: v for k, v in data.items() if v is not None}
        
        # Ensure required fields have defaults
        if 'make' not in cleaned:
            cleaned['make'] = 'Unknown'
        if 'model' not in cleaned:
            cleaned['model'] = 'Unknown'
        if 'condition' not in cleaned:
            cleaned['condition'] = 'used'
        
        # Validate numeric fields
        numeric_fields = ['price', 'year', 'mileage', 'engine_power_kw', 'engine_displacement']
        for field in numeric_fields:
            if field in cleaned and not isinstance(cleaned[field], (int, float)):
                try:
                    cleaned[field] = float(cleaned[field])
                except (ValueError, TypeError):
                    del cleaned[field]
        
        return cleaned
