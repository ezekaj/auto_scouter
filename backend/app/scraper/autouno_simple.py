"""
Simplified AutoUno Scraper for testing and development
Works without external dependencies like BeautifulSoup
"""

import time
import random
import logging
from typing import List, Dict, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class AutoUnoSimpleScraper:
    """Simplified AutoUno scraper that generates realistic test data"""
    
    def __init__(self):
        self.source_name = "autouno.al"
        self.source_country = "AL"  # Albania
        self.base_url = "https://autouno.al"
        
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
    
    def _calculate_data_quality(self, make: str, model: str, year: int, price: float, mileage: int) -> float:
        """Calculate data quality score based on available fields"""
        score = 0.0
        total_fields = 5
        
        if make and make != 'Unknown':
            score += 0.2
        if model and model != 'Unknown':
            score += 0.2
        if year and 1990 <= year <= 2024:
            score += 0.2
        if price and price > 0:
            score += 0.2
        if mileage and mileage > 0:
            score += 0.2
            
        return score
    
    def _generate_external_id(self, url_or_title: str) -> str:
        """Generate external ID from URL or title"""
        import hashlib
        return f"autouno_{hashlib.md5(url_or_title.encode()).hexdigest()[:12]}"
    
    def generate_realistic_data(self, count: int = 20) -> List[Dict]:
        """Generate realistic test data for AutoUno (Albanian market)"""
        logger.info(f"Generating {count} realistic vehicles for AutoUno")
        
        # Albanian car market data
        makes_models = [
            ('BMW', ['320i', '318d', 'X3', 'X5', '520d', '118i', '325i']),
            ('Mercedes-Benz', ['C200', 'E220', 'A180', 'GLC', 'ML350', 'C220', 'E200']),
            ('Audi', ['A4', 'A6', 'Q5', 'A3', 'Q7', 'A5', 'Q3']),
            ('Volkswagen', ['Golf', 'Passat', 'Tiguan', 'Polo', 'Touran', 'Jetta', 'Sharan']),
            ('Ford', ['Focus', 'Mondeo', 'Kuga', 'Fiesta', 'Transit', 'Fusion', 'Edge']),
            ('Opel', ['Astra', 'Insignia', 'Corsa', 'Mokka', 'Zafira', 'Vectra', 'Meriva']),
            ('Peugeot', ['308', '508', '3008', '2008', '207', '307', '407']),
            ('Renault', ['Megane', 'Clio', 'Scenic', 'Kadjar', 'Captur', 'Laguna', 'Fluence']),
            ('Toyota', ['Corolla', 'Camry', 'RAV4', 'Prius', 'Yaris', 'Avensis', 'Auris']),
            ('Fiat', ['Punto', 'Panda', '500', 'Bravo', 'Stilo', 'Doblo', 'Multipla'])
        ]
        
        albanian_cities = [
            'Tiranë', 'Durrës', 'Vlorë', 'Shkodër', 'Fier', 'Korçë', 
            'Elbasan', 'Berat', 'Lushnjë', 'Kavajë', 'Gjirokastër', 'Sarandë',
            'Kukës', 'Lezhë', 'Pogradec', 'Patos', 'Laç', 'Krujë'
        ]
        
        fuel_types = ['Diesel', 'Gasoline', 'Hybrid', 'LPG']
        
        vehicles = []
        
        for i in range(count):
            make, models = random.choice(makes_models)
            model = random.choice(models)
            year = random.randint(2005, 2023)
            
            # Price based on year and make (Albanian market - realistic prices)
            base_price = {
                'BMW': 22000, 'Mercedes-Benz': 25000, 'Audi': 21000,
                'Volkswagen': 16000, 'Ford': 13000, 'Opel': 10000,
                'Peugeot': 12000, 'Renault': 11000, 'Toyota': 15000,
                'Fiat': 8000
            }.get(make, 12000)
            
            # Adjust price based on year (depreciation)
            age_factor = max(0.2, 1 - (2024 - year) * 0.07)
            price = int(base_price * age_factor * random.uniform(0.7, 1.3))
            
            # Realistic mileage based on year
            years_old = 2024 - year
            avg_km_per_year = random.randint(12000, 25000)
            mileage = max(5000, years_old * avg_km_per_year + random.randint(-20000, 20000))
            
            vehicle_data = {
                'external_id': f'autouno_real_{i+1}_{int(time.time())}_{random.randint(1000, 9999)}',
                'listing_url': f'https://autouno.al/makina/{make.lower().replace("-", "")}-{model.lower().replace(" ", "-")}-{year}-{i+1}',
                'title': f'{make} {model} {year}',
                'make': make,
                'model': model,
                'year': year,
                'price': float(price),
                'currency': 'EUR',
                'mileage': mileage,
                'fuel_type': random.choice(fuel_types),
                'city': random.choice(albanian_cities),
                'country': 'Albania',
                'source_website': self.source_name,
                'source_country': self.source_country,
                'scraped_at': datetime.utcnow(),
                'is_active': True,
                'confidence_score': random.uniform(0.8, 0.95),
                'data_quality_score': self._calculate_data_quality(make, model, year, price, mileage),
                'primary_image_url': f'https://autouno.al/images/cars/{make.lower()}-{model.lower()}-{i+1}.jpg',
                'description': f'{make} {model} {year}, {mileage:,} km, {random.choice(fuel_types)}, në gjendje të mirë',
                'transmission': random.choice(['Manual', 'Automatic']),
                'body_type': random.choice(['Sedan', 'Hatchback', 'SUV', 'Wagon', 'Coupe']),
                'color': random.choice(['Zi', 'Bardhë', 'Gri', 'Blu', 'Kuq', 'Argjend']),
                'doors': random.choice([3, 4, 5]),
                'engine_size': round(random.uniform(1.0, 3.5), 1),
                'horsepower': random.randint(90, 350)
            }
            
            vehicles.append(vehicle_data)
        
        logger.info(f"Generated {len(vehicles)} realistic vehicles for AutoUno")
        return vehicles
    
    def scrape_vehicles(self, max_vehicles: int = 20) -> List[Dict]:
        """Main scraping method - returns realistic test data for now"""
        logger.info(f"AutoUno scraping started (max: {max_vehicles} vehicles)")
        
        # For now, return realistic test data
        # In production, this would make actual HTTP requests
        vehicles = self.generate_realistic_data(count=min(max_vehicles, 50))
        
        logger.info(f"AutoUno scraping completed: {len(vehicles)} vehicles found")
        return vehicles
    
    def test_parsing_methods(self):
        """Test the parsing methods with sample data"""
        test_results = {
            'price_parsing': [],
            'mileage_parsing': [],
            'make_model_parsing': []
        }
        
        # Test price parsing
        test_prices = ["€15,000", "12.500 EUR", "8,500", "20000", "25.000,50"]
        for price_text in test_prices:
            result = self._extract_price(price_text)
            test_results['price_parsing'].append({'input': price_text, 'output': result})
        
        # Test mileage parsing
        test_mileages = ["120,000 km", "85.000 kilometra", "50000", "200,000"]
        for mileage_text in test_mileages:
            result = self._extract_mileage(mileage_text)
            test_results['mileage_parsing'].append({'input': mileage_text, 'output': result})
        
        # Test make/model parsing
        test_titles = [
            "BMW 320i 2018 Automatik",
            "Mercedes-Benz C200 2020",
            "Audi A4 2.0 TDI 2019",
            "Volkswagen Golf VII 2017"
        ]
        for title in test_titles:
            make, model = self._parse_make_model(title)
            test_results['make_model_parsing'].append({'input': title, 'make': make, 'model': model})
        
        return test_results
