"""
AutoUno.al Car Scraper

Scrapes car listings from AutoUno.al (Albanian car marketplace)
Implements 5-minute interval checking with robust error handling
"""

import requests
from bs4 import BeautifulSoup
import time
import random
from typing import List, Dict, Optional
from datetime import datetime
import logging
from urllib.parse import urljoin, urlparse
import re

from .base import BaseScraper

logger = logging.getLogger(__name__)

class AutoUnoScraper(BaseScraper):
    """Scraper for AutoUno.al car listings"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://autouno.al"
        self.search_url = "https://autouno.al/kerko"
        self.source_name = "autouno.al"
        self.source_country = "AL"  # Albania
        
        # Request headers to avoid detection
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'sq-AL,sq;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Session for connection reuse
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Rate limiting
        self.min_delay = 2.0  # Minimum delay between requests
        self.max_delay = 5.0  # Maximum delay between requests
        
    def _make_request(self, url: str, retries: int = 3) -> Optional[requests.Response]:
        """Make HTTP request with retry logic and rate limiting"""
        for attempt in range(retries):
            try:
                # Random delay to avoid detection
                delay = random.uniform(self.min_delay, self.max_delay)
                time.sleep(delay)
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                logger.info(f"Successfully fetched: {url}")
                return response
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt == retries - 1:
                    logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None
                
                # Exponential backoff
                time.sleep(2 ** attempt)
        
        return None
    
    def _extract_price(self, price_text: str) -> Optional[float]:
        """Extract price from text"""
        if not price_text:
            return None
            
        # Remove currency symbols and spaces
        price_clean = re.sub(r'[^\d,.]', '', price_text)
        
        # Handle different number formats
        if ',' in price_clean and '.' in price_clean:
            # Format: 1,234.56
            price_clean = price_clean.replace(',', '')
        elif ',' in price_clean:
            # Format: 1,234 or 1234,56
            if len(price_clean.split(',')[1]) <= 2:
                price_clean = price_clean.replace(',', '.')
            else:
                price_clean = price_clean.replace(',', '')
        
        try:
            return float(price_clean)
        except ValueError:
            logger.warning(f"Could not parse price: {price_text}")
            return None
    
    def _extract_mileage(self, mileage_text: str) -> Optional[int]:
        """Extract mileage from text"""
        if not mileage_text:
            return None
            
        # Extract numbers from text
        numbers = re.findall(r'\d+', mileage_text.replace(',', '').replace('.', ''))
        if numbers:
            try:
                return int(''.join(numbers))
            except ValueError:
                pass
        
        return None
    
    def _parse_listing(self, listing_element, base_url: str) -> Optional[Dict]:
        """Parse individual car listing from HTML element"""
        try:
            # Extract basic information
            title_elem = listing_element.find('h3') or listing_element.find('h2') or listing_element.find('.title')
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            
            # Extract make and model from title
            make, model = self._parse_make_model(title)
            
            # Extract price
            price_elem = listing_element.find(class_=re.compile(r'price|çmim', re.I))
            price = None
            if price_elem:
                price = self._extract_price(price_elem.get_text(strip=True))
            
            # Extract year
            year_elem = listing_element.find(class_=re.compile(r'year|vit', re.I))
            year = None
            if year_elem:
                year_text = year_elem.get_text(strip=True)
                year_match = re.search(r'\b(19|20)\d{2}\b', year_text)
                if year_match:
                    year = int(year_match.group())
            
            # Extract mileage
            mileage_elem = listing_element.find(class_=re.compile(r'mileage|km|kilometra', re.I))
            mileage = None
            if mileage_elem:
                mileage = self._extract_mileage(mileage_elem.get_text(strip=True))
            
            # Extract location
            location_elem = listing_element.find(class_=re.compile(r'location|qytet|vend', re.I))
            city = None
            if location_elem:
                city = location_elem.get_text(strip=True)
            
            # Extract fuel type
            fuel_elem = listing_element.find(class_=re.compile(r'fuel|karburant', re.I))
            fuel_type = None
            if fuel_elem:
                fuel_text = fuel_elem.get_text(strip=True).lower()
                if 'benzin' in fuel_text or 'gasoline' in fuel_text:
                    fuel_type = 'Gasoline'
                elif 'diesel' in fuel_text:
                    fuel_type = 'Diesel'
                elif 'hybrid' in fuel_text:
                    fuel_type = 'Hybrid'
                elif 'elektrik' in fuel_text or 'electric' in fuel_text:
                    fuel_type = 'Electric'
            
            # Extract listing URL
            link_elem = listing_element.find('a', href=True)
            listing_url = None
            if link_elem:
                listing_url = urljoin(base_url, link_elem['href'])
            
            # Extract image URL
            img_elem = listing_element.find('img')
            image_url = None
            if img_elem and img_elem.get('src'):
                image_url = urljoin(base_url, img_elem['src'])
            
            # Generate external ID
            external_id = self._generate_external_id(listing_url or title)
            
            # Create vehicle data
            vehicle_data = {
                'external_id': external_id,
                'listing_url': listing_url,
                'make': make,
                'model': model,
                'year': year,
                'price': price,
                'currency': 'EUR',  # AutoUno typically uses EUR
                'mileage': mileage,
                'fuel_type': fuel_type,
                'city': city,
                'country': 'Albania',
                'source_website': self.source_name,
                'source_country': self.source_country,
                'scraped_at': datetime.utcnow(),
                'is_active': True,
                'primary_image_url': image_url,
                'confidence_score': 0.8,  # Medium confidence for parsed data
                'data_quality_score': self._calculate_data_quality(make, model, year, price, mileage)
            }
            
            return vehicle_data
            
        except Exception as e:
            logger.error(f"Error parsing listing: {e}")
            return None
    
    def _parse_make_model(self, title: str) -> tuple:
        """Parse make and model from title"""
        # Common Albanian car makes
        makes = [
            'BMW', 'Mercedes', 'Mercedes-Benz', 'Audi', 'Volkswagen', 'VW',
            'Ford', 'Opel', 'Peugeot', 'Renault', 'Fiat', 'Toyota', 'Honda',
            'Nissan', 'Hyundai', 'Kia', 'Mazda', 'Mitsubishi', 'Subaru',
            'Volvo', 'Skoda', 'Seat', 'Citroen', 'Alfa Romeo', 'Lancia'
        ]
        
        title_upper = title.upper()
        
        for make in makes:
            if make.upper() in title_upper:
                # Extract model (everything after make)
                make_index = title_upper.find(make.upper())
                model_part = title[make_index + len(make):].strip()
                
                # Clean up model name
                model = re.split(r'[\d]{4}|,|\(|\[', model_part)[0].strip()
                model = re.sub(r'^[-\s]+', '', model)  # Remove leading dashes/spaces
                
                return make, model if model else 'Unknown'
        
        # If no make found, try to extract from beginning
        words = title.split()
        if words:
            return words[0], ' '.join(words[1:3]) if len(words) > 1 else 'Unknown'
        
        return 'Unknown', 'Unknown'
    
    def scrape_all_listings(self, max_vehicles: int = 50) -> List[Dict]:
        """Scrape car listings from AutoUno.al"""
        logger.info(f"Starting AutoUno scraping (max: {max_vehicles} vehicles)")
        
        vehicles = []
        page = 1
        max_pages = 10  # Limit to prevent infinite loops
        
        try:
            while len(vehicles) < max_vehicles and page <= max_pages:
                logger.info(f"Scraping page {page}")
                
                # Construct search URL with pagination
                search_url = f"{self.search_url}?page={page}"
                
                response = self._make_request(search_url)
                if not response:
                    logger.error(f"Failed to fetch page {page}")
                    break
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find listing containers (adjust selectors based on actual HTML structure)
                listing_selectors = [
                    '.car-item',
                    '.listing-item',
                    '.vehicle-card',
                    '.ad-item',
                    '[class*="car"]',
                    '[class*="listing"]'
                ]
                
                listings = []
                for selector in listing_selectors:
                    listings = soup.select(selector)
                    if listings:
                        logger.info(f"Found {len(listings)} listings using selector: {selector}")
                        break
                
                if not listings:
                    logger.warning(f"No listings found on page {page}")
                    break
                
                # Parse each listing
                page_vehicles = 0
                for listing in listings:
                    if len(vehicles) >= max_vehicles:
                        break
                    
                    vehicle_data = self._parse_listing(listing, self.base_url)
                    if vehicle_data:
                        vehicles.append(vehicle_data)
                        page_vehicles += 1
                        logger.debug(f"Parsed vehicle: {vehicle_data['make']} {vehicle_data['model']}")
                
                logger.info(f"Page {page}: Found {page_vehicles} vehicles")
                
                # If no vehicles found on this page, stop
                if page_vehicles == 0:
                    break
                
                page += 1
                
                # Random delay between pages
                time.sleep(random.uniform(3, 7))
            
            logger.info(f"AutoUno scraping completed: {len(vehicles)} vehicles found")
            return vehicles
            
        except Exception as e:
            logger.error(f"Error during AutoUno scraping: {e}")
            return vehicles  # Return what we have so far
    
    def generate_test_data(self, count: int = 10) -> List[Dict]:
        """Generate realistic test data for AutoUno (Albanian market)"""
        logger.info(f"Generating {count} test vehicles for AutoUno")
        
        # Albanian car market data
        makes_models = [
            ('BMW', ['320i', '318d', 'X3', 'X5', '520d']),
            ('Mercedes-Benz', ['C200', 'E220', 'A180', 'GLC', 'ML350']),
            ('Audi', ['A4', 'A6', 'Q5', 'A3', 'Q7']),
            ('Volkswagen', ['Golf', 'Passat', 'Tiguan', 'Polo', 'Touran']),
            ('Ford', ['Focus', 'Mondeo', 'Kuga', 'Fiesta', 'Transit']),
            ('Opel', ['Astra', 'Insignia', 'Corsa', 'Mokka', 'Zafira']),
            ('Peugeot', ['308', '508', '3008', '2008', '207']),
            ('Renault', ['Megane', 'Clio', 'Scenic', 'Kadjar', 'Captur'])
        ]
        
        albanian_cities = [
            'Tiranë', 'Durrës', 'Vlorë', 'Shkodër', 'Fier', 'Korçë', 
            'Elbasan', 'Berat', 'Lushnjë', 'Kavajë', 'Gjirokastër', 'Sarandë'
        ]
        
        fuel_types = ['Diesel', 'Gasoline', 'Hybrid']
        
        vehicles = []
        
        for i in range(count):
            make, models = random.choice(makes_models)
            model = random.choice(models)
            year = random.randint(2010, 2023)
            
            # Price based on year and make (Albanian market)
            base_price = {
                'BMW': 25000, 'Mercedes-Benz': 28000, 'Audi': 24000,
                'Volkswagen': 18000, 'Ford': 15000, 'Opel': 12000,
                'Peugeot': 14000, 'Renault': 13000
            }.get(make, 15000)
            
            # Adjust price based on year
            age_factor = max(0.3, 1 - (2024 - year) * 0.08)
            price = int(base_price * age_factor * random.uniform(0.8, 1.2))
            
            vehicle_data = {
                'external_id': f'autouno_test_{i+1}_{int(time.time())}',
                'listing_url': f'https://autouno.al/makina/{make.lower()}-{model.lower()}-{year}-{i+1}',
                'make': make,
                'model': model,
                'year': year,
                'price': float(price),
                'currency': 'EUR',
                'mileage': random.randint(20000, 200000),
                'fuel_type': random.choice(fuel_types),
                'city': random.choice(albanian_cities),
                'country': 'Albania',
                'source_website': self.source_name,
                'source_country': self.source_country,
                'scraped_at': datetime.utcnow(),
                'is_active': True,
                'confidence_score': 0.9,
                'data_quality_score': 0.95,
                'primary_image_url': f'https://autouno.al/images/cars/{i+1}.jpg'
            }
            
            vehicles.append(vehicle_data)
        
        logger.info(f"Generated {len(vehicles)} test vehicles for AutoUno")
        return vehicles
