"""
Ayvens Carmarket Scraper

Scrapes vehicle listings from carmarket.ayvens.com
Implements robust data extraction with image downloading capabilities
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import os
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
from urllib.parse import urljoin, urlparse
import re
from pathlib import Path

from .base import BaseScraper
from .config import scraper_settings
from .image_downloader import ImageDownloader, ImageUrlExtractor
from .session_manager import get_session_manager, require_auth, AuthenticatedRequest

logger = logging.getLogger(__name__)


class AyvensCarmarketScraper(BaseScraper):
    """Scraper for carmarket.ayvens.com vehicle listings"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://carmarket.ayvens.com"
        self.search_url = "https://carmarket.ayvens.com/lots"
        self.source_name = "carmarket.ayvens.com"
        self.source_country = "EU"  # Multi-country platform
        self.session_id = str(uuid.uuid4())

        # Session manager for authentication
        self.session_manager = get_session_manager()

        # Rate limiting
        self.min_delay = 3.0  # Minimum delay between requests
        self.max_delay = 7.0  # Maximum delay between requests

        # Image downloader setup
        self.image_downloader = ImageDownloader("ayvens")
        

    
    def _make_request(self, url: str, retries: int = 3) -> Optional[requests.Response]:
        """Make authenticated HTTP request with retry logic and rate limiting"""
        for attempt in range(retries):
            try:
                # Random delay to avoid detection
                delay = random.uniform(self.min_delay, self.max_delay)
                time.sleep(delay)

                logger.info(f"Fetching URL: {url} (attempt {attempt + 1})")

                # Use authenticated session
                with AuthenticatedRequest(self.session_manager) as session:
                    response = session.get(url, timeout=30)
                    response.raise_for_status()

                    logger.info(f"Successfully fetched: {url} - Status: {response.status_code}")
                    return response

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt == retries - 1:
                    logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None

                # Exponential backoff
                time.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Authentication or session error: {e}")
                if attempt == retries - 1:
                    return None
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
            
        # Extract numbers from mileage text
        numbers = re.findall(r'[\d,]+', mileage_text)
        if numbers:
            # Remove commas and convert to int
            mileage_str = numbers[0].replace(',', '')
            try:
                return int(mileage_str)
            except ValueError:
                pass
        
        return None
    
    def _extract_year(self, text: str) -> Optional[int]:
        """Extract year from text"""
        if not text:
            return None
            
        # Look for 4-digit years
        years = re.findall(r'\b(19|20)\d{2}\b', text)
        if years:
            try:
                year = int(years[0])
                # Validate reasonable year range
                if 1990 <= year <= datetime.now().year + 1:
                    return year
            except ValueError:
                pass
        
        return None
    
    def download_image(self, image_url: str, vehicle_id: str) -> Optional[str]:
        """Download vehicle image and return local path"""
        return self.image_downloader.download_image(image_url, vehicle_id)
    
    def _parse_listing(self, listing_element, base_url: str) -> Optional[Dict[str, Any]]:
        """Parse individual vehicle listing"""
        try:
            # Extract basic information using comprehensive selectors
            title_selectors = [
                # Ayvens-specific
                '.lot-title', '.vehicle-title', '.car-title', '.listing-title',
                # Generic title selectors
                'h1', 'h2', 'h3', 'h4', '.title', '.name', '.model',
                '[class*="title"]', '[class*="name"]', '[class*="model"]',
                # Fallback - any text that looks like a car name
                '[data-title]', '[title]'
            ]

            price_selectors = [
                # Ayvens-specific
                '.lot-price', '.auction-price', '.sale-price',
                # Generic price selectors
                '.price', '.cost', '.amount', '.value', '.bid',
                '[class*="price"]', '[class*="cost"]', '[class*="amount"]',
                '[class*="bid"]', '[class*="value"]',
                # Data attributes
                '[data-price]', '[data-amount]'
            ]

            image_selectors = [
                # All img tags in the listing
                'img',
                # Specific image containers
                '.vehicle-image img', '.car-image img', '.lot-image img',
                '.listing-image img', '.photo img', '.picture img',
                '[class*="image"] img', '[class*="photo"] img'
            ]

            link_selectors = [
                # Links to vehicle details
                'a[href*="lot"]', 'a[href*="vehicle"]', 'a[href*="car"]',
                'a[href*="auction"]', 'a[href*="tender"]',
                # Generic links
                'a', '.link', '[href]'
            ]
            
            # Extract title with fallback strategies
            title = None
            for selector in title_selectors:
                elements = listing_element.select(selector)
                for element in elements:
                    text = self.extract_text(element)
                    if text and len(text.strip()) > 3:  # Must have meaningful content
                        title = text.strip()
                        break
                if title:
                    break

            # Fallback: extract any text that looks like a vehicle name
            if not title:
                all_text = listing_element.get_text(separator=' ', strip=True)
                # Look for patterns like "BMW 320d" or "Mercedes C220"
                car_pattern = re.search(r'(BMW|Mercedes|Audi|Volkswagen|Ford|Peugeot|Renault|Volvo|Toyota|Honda|Nissan|Hyundai|Kia|Mazda|Mitsubishi|Subaru|Skoda|Seat|Citroen|Alfa Romeo|Fiat|Opel|Porsche|Jaguar|Land Rover|Mini|Smart|Dacia)\s+[A-Za-z0-9\s-]+', all_text, re.I)
                if car_pattern:
                    title = car_pattern.group(0).strip()

            if not title or len(title.strip()) < 3:
                logger.debug("No valid title found, skipping listing")
                return None
            
            # Extract price
            price = None
            for selector in price_selectors:
                element = listing_element.select_one(selector)
                if element:
                    price_text = self.extract_text(element)
                    price = self._extract_price(price_text)
                    if price:
                        break
            
            # Extract image URLs (primary and additional)
            image_urls = ImageUrlExtractor.extract_from_element(listing_element, base_url)
            image_url = image_urls[0] if image_urls else None

            # Also try CSS background images
            bg_images = ImageUrlExtractor.extract_from_css_background(listing_element)
            if bg_images and not image_url:
                image_url = urljoin(base_url, bg_images[0])
            
            # Extract listing URL
            listing_url = None
            for selector in link_selectors:
                element = listing_element.select_one(selector)
                if element:
                    href = element.get('href')
                    if href:
                        listing_url = urljoin(base_url, href)
                        break
            
            # Parse make and model from title
            make, model = self._parse_make_model(title)
            
            # Extract year from title
            year = self._extract_year(title)
            
            # Generate external ID
            external_id = f"ayvens_{uuid.uuid4().hex[:12]}"
            
            # Download primary image if enabled
            local_image_path = self.download_image(image_url, external_id) if image_url else None

            # Download additional images if available
            additional_image_paths = []
            if len(image_urls) > 1:
                additional_image_paths = self.image_downloader.download_multiple_images(
                    image_urls[1:], external_id, max_images=4
                )
            
            vehicle_data = {
                'external_id': external_id,
                'listing_url': listing_url or f"{base_url}/vehicle/{external_id}",
                'make': make,
                'model': model,
                'year': year,
                'price': price,
                'currency': 'EUR',  # Ayvens typically uses EUR
                'mileage': None,  # Will be extracted from detail page if available
                'fuel_type': None,
                'transmission': None,
                'condition': 'used',
                'city': None,
                'country': 'EU',
                'source_website': self.source_name,
                'source_country': self.source_country,
                'scraped_at': datetime.utcnow(),
                'is_active': True,
                'primary_image_url': local_image_path or image_url,
                'additional_images': additional_image_paths,
                'confidence_score': 0.7,  # Medium confidence for parsed data
                'data_quality_score': self._calculate_data_quality(make, model, year, price, None),
                'title': title,
                'description': title  # Use title as description for now
            }
            
            return vehicle_data
            
        except Exception as e:
            logger.error(f"Error parsing listing: {e}")
            return None
    
    def _parse_make_model(self, title: str) -> tuple:
        """Parse make and model from title"""
        # Common car makes
        makes = [
            'BMW', 'Mercedes', 'Mercedes-Benz', 'Audi', 'Volkswagen', 'VW',
            'Ford', 'Opel', 'Peugeot', 'Renault', 'Fiat', 'Toyota', 'Honda',
            'Nissan', 'Hyundai', 'Kia', 'Mazda', 'Mitsubishi', 'Subaru',
            'Volvo', 'Skoda', 'Seat', 'Citroen', 'Alfa Romeo', 'Lancia',
            'Porsche', 'Jaguar', 'Land Rover', 'Mini', 'Smart', 'Dacia'
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
    
    def _calculate_data_quality(self, make: str, model: str, year: Optional[int], 
                              price: Optional[float], mileage: Optional[int]) -> float:
        """Calculate data quality score based on available fields"""
        score = 0.0
        total_fields = 5
        
        if make and make != 'Unknown':
            score += 0.2
        if model and model != 'Unknown':
            score += 0.2
        if year:
            score += 0.2
        if price:
            score += 0.2
        if mileage:
            score += 0.2
        
        return score

    @require_auth
    def scrape_all_listings(self, max_vehicles: int = 50) -> List[Dict[str, Any]]:
        """Scrape vehicle listings from Ayvens Carmarket"""
        logger.info(f"Starting Ayvens scraping session {self.session_id} (max: {max_vehicles} vehicles)")

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

                # Find listing containers using Ayvens-specific and generic selectors
                listing_selectors = [
                    # Ayvens-specific selectors (based on common patterns)
                    '.lot-card', '.lot-item', '.vehicle-lot', '.auction-lot',
                    '.car-lot', '.listing-card', '.vehicle-card', '.car-item',
                    '.auction-item', '.tender-item', '.sale-item',
                    # Generic selectors for vehicle listings
                    '[class*="lot"]', '[class*="vehicle"]', '[class*="car"]',
                    '[class*="listing"]', '[class*="auction"]', '[class*="tender"]',
                    # Broad selectors as fallback
                    '.card', '.item', '.product', '.result',
                    # Container-based selectors
                    '.results .item', '.listings .card', '.vehicles .lot',
                    # Grid/list item selectors
                    '.grid-item', '.list-item', '.row .col'
                ]

                listings = []
                for selector in listing_selectors:
                    try:
                        found_listings = soup.select(selector)
                        # Filter out empty or very small elements
                        valid_listings = [listing for listing in found_listings
                                        if listing.get_text(strip=True) and len(listing.get_text(strip=True)) > 20]

                        if valid_listings:
                            listings = valid_listings
                            logger.info(f"Found {len(listings)} valid listings using selector: {selector}")
                            break
                    except Exception as e:
                        logger.debug(f"Error with selector {selector}: {e}")
                        continue

                if not listings:
                    # Debug: Log page content to understand structure
                    logger.warning(f"No vehicle listings found on page {page}")

                    # Check if page has any content at all
                    page_text = soup.get_text(strip=True)
                    logger.debug(f"Page text length: {len(page_text)}")

                    if len(page_text) < 100:
                        logger.warning("Page appears to be mostly empty - might be JavaScript-heavy")

                    # Look for any elements that might contain vehicle data
                    potential_elements = soup.find_all(['div', 'article', 'section'],
                                                     string=re.compile(r'(€|EUR|\$|USD|km|miles|[0-9]{4})', re.I))
                    if potential_elements:
                        logger.info(f"Found {len(potential_elements)} elements with potential vehicle data")
                        # Try to extract from these elements
                        for elem in potential_elements[:5]:  # Check first 5
                            parent = elem.parent
                            if parent and len(parent.get_text(strip=True)) > 50:
                                listings.append(parent)

                        if listings:
                            logger.info(f"Extracted {len(listings)} listings from potential elements")

                    if not listings:
                        logger.warning(f"No vehicle listings found on page {page}, stopping")
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
                    logger.info("No vehicles found on this page, stopping pagination")
                    break

                page += 1

        except Exception as e:
            logger.error(f"Error during scraping: {e}")

        logger.info(f"Ayvens scraping completed. Total vehicles: {len(vehicles)}")
        return vehicles

    @require_auth
    def scrape_vehicle_details(self, listing_url: str) -> Optional[Dict[str, Any]]:
        """Scrape detailed information from individual vehicle page"""
        try:
            response = self._make_request(listing_url)
            if not response:
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract additional details from vehicle detail page
            details = {}

            # Look for mileage
            mileage_selectors = [
                '[class*="mileage"]', '[class*="km"]', '[class*="miles"]',
                'td:contains("Mileage")', 'td:contains("Kilomètres")',
                '.spec-mileage', '.vehicle-mileage'
            ]

            for selector in mileage_selectors:
                element = soup.select_one(selector)
                if element:
                    mileage_text = self.extract_text(element)
                    mileage = self._extract_mileage(mileage_text)
                    if mileage:
                        details['mileage'] = mileage
                        break

            # Look for fuel type
            fuel_selectors = [
                '[class*="fuel"]', '[class*="engine"]',
                'td:contains("Fuel")', 'td:contains("Carburant")',
                '.spec-fuel', '.vehicle-fuel'
            ]

            for selector in fuel_selectors:
                element = soup.select_one(selector)
                if element:
                    fuel_text = self.extract_text(element).lower()
                    if any(fuel in fuel_text for fuel in ['diesel', 'gasoline', 'petrol', 'electric', 'hybrid']):
                        details['fuel_type'] = fuel_text
                        break

            # Look for transmission
            transmission_selectors = [
                '[class*="transmission"]', '[class*="gearbox"]',
                'td:contains("Transmission")', 'td:contains("Boîte")',
                '.spec-transmission', '.vehicle-transmission'
            ]

            for selector in transmission_selectors:
                element = soup.select_one(selector)
                if element:
                    trans_text = self.extract_text(element).lower()
                    if 'automatic' in trans_text or 'auto' in trans_text:
                        details['transmission'] = 'automatic'
                    elif 'manual' in trans_text:
                        details['transmission'] = 'manual'
                    break

            # Look for additional images
            image_selectors = [
                '.gallery img', '.vehicle-images img', '.car-images img',
                '.image-gallery img', '[class*="gallery"] img'
            ]

            additional_images = []
            for selector in image_selectors:
                images = soup.select(selector)
                for img in images[:5]:  # Limit to 5 additional images
                    img_url = img.get('src') or img.get('data-src')
                    if img_url:
                        full_url = urljoin(listing_url, img_url)
                        additional_images.append(full_url)

            if additional_images:
                details['additional_images'] = additional_images

            return details

        except Exception as e:
            logger.error(f"Error scraping vehicle details from {listing_url}: {e}")
            return None


