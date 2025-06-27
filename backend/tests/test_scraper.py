"""
Tests for Automotive Scraper
"""

import pytest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

from app.scraper.automotive_scraper import GruppoAutoUnoScraper
from app.scraper.base import BaseScraper


class TestBaseScraper:
    """Test cases for BaseScraper"""
    
    def test_clean_price(self):
        """Test price cleaning functionality"""
        scraper = BaseScraper()
        
        # Test various price formats
        assert scraper.clean_price("€ 18.500") == 18500.0
        assert scraper.clean_price("18,500 EUR") == 18500.0
        assert scraper.clean_price("18.500,50") == 1850050.0  # Italian format
        assert scraper.clean_price("€18500") == 18500.0
        assert scraper.clean_price("invalid") is None
        assert scraper.clean_price("") is None
    
    def test_clean_number(self):
        """Test number extraction functionality"""
        scraper = BaseScraper()
        
        assert scraper.clean_number("45.000 km") == 45000
        assert scraper.clean_number("1,598 cc") == 1598
        assert scraper.clean_number("85 kW") == 85
        assert scraper.clean_number("no numbers") is None
        assert scraper.clean_number("") is None
    
    def test_normalize_fuel_type(self):
        """Test fuel type normalization"""
        scraper = BaseScraper()
        
        assert scraper.normalize_fuel_type("Benzina") == "gasoline"
        assert scraper.normalize_fuel_type("Diesel") == "diesel"
        assert scraper.normalize_fuel_type("Elettrica") == "electric"
        assert scraper.normalize_fuel_type("Ibrida") == "hybrid"
        assert scraper.normalize_fuel_type("GPL") == "lpg"
        assert scraper.normalize_fuel_type("Metano") == "cng"
        assert scraper.normalize_fuel_type("Unknown") == "unknown"
    
    def test_normalize_transmission(self):
        """Test transmission type normalization"""
        scraper = BaseScraper()
        
        assert scraper.normalize_transmission("Automatico") == "automatic"
        assert scraper.normalize_transmission("Manuale") == "manual"
        assert scraper.normalize_transmission("Unknown") == "unknown"


class TestGruppoAutoUnoScraper:
    """Test cases for GruppoAutoUnoScraper"""
    
    def test_extract_external_id_from_url(self):
        """Test extracting external ID from URL"""
        scraper = GruppoAutoUnoScraper()
        
        url = "https://gruppoautouno.it/usato/volkswagen-golf-123/"
        soup = BeautifulSoup("<html></html>", 'html.parser')
        
        external_id = scraper.extract_external_id(url, soup)
        assert external_id == "volkswagen-golf-123"
    
    def test_parse_make_model_from_title(self):
        """Test parsing make and model from title"""
        scraper = GruppoAutoUnoScraper()
        
        # Test various title formats
        result = scraper.parse_make_model_from_title("Volkswagen Golf 1.6 TDI")
        assert result["make"] == "Volkswagen"
        assert result["model"] == "Golf"
        
        result = scraper.parse_make_model_from_title("Peugeot 208 1.2 PureTech")
        assert result["make"] == "Peugeot"
        assert result["model"] == "208"
        
        result = scraper.parse_make_model_from_title("Unknown Car Model")
        assert "make" not in result or "model" not in result
    
    def test_extract_basic_info(self, sample_html_content):
        """Test extracting basic vehicle information"""
        scraper = GruppoAutoUnoScraper()
        soup = BeautifulSoup(sample_html_content, 'html.parser')
        
        basic_info = scraper.extract_basic_info(soup)
        
        assert basic_info["make"] == "Volkswagen"
        assert basic_info["model"] == "Golf"
        assert basic_info["year"] == 2020
        assert "variant" in basic_info
    
    def test_extract_technical_specs(self, sample_html_content):
        """Test extracting technical specifications"""
        scraper = GruppoAutoUnoScraper()
        soup = BeautifulSoup(sample_html_content, 'html.parser')
        
        specs = scraper.extract_technical_specs(soup)
        
        assert specs["mileage"] == 45000
        assert specs["fuel_type"] == "diesel"
        assert specs["transmission"] == "manual"
        assert specs["engine_power_kw"] == 85
        assert specs["engine_displacement"] == 1598
        assert specs["doors"] == 5
        assert specs["seats"] == 5
    
    def test_extract_pricing_info(self, sample_html_content):
        """Test extracting pricing information"""
        scraper = GruppoAutoUnoScraper()
        soup = BeautifulSoup(sample_html_content, 'html.parser')
        
        pricing = scraper.extract_pricing_info(soup)
        
        assert pricing["price"] == 18500.0
        assert pricing["currency"] == "EUR"
    
    def test_extract_images(self, sample_html_content):
        """Test extracting vehicle images"""
        scraper = GruppoAutoUnoScraper()
        soup = BeautifulSoup(sample_html_content, 'html.parser')
        
        images = scraper.extract_images(soup)
        
        assert len(images) == 2
        assert images[0]["image_url"].endswith("/images/golf-1.jpg")
        assert images[1]["image_url"].endswith("/images/golf-2.jpg")
        assert images[0]["image_type"] == "exterior"
        assert images[1]["image_type"] == "detail"
    
    def test_clean_vehicle_data(self):
        """Test cleaning and validating vehicle data"""
        scraper = GruppoAutoUnoScraper()
        
        dirty_data = {
            "make": "Volkswagen",
            "model": "Golf",
            "price": "18500.0",  # String instead of float
            "year": "2020",      # String instead of int
            "mileage": None,     # None value
            "invalid_field": "should be removed"
        }
        
        clean_data = scraper.clean_vehicle_data(dirty_data)
        
        assert clean_data["make"] == "Volkswagen"
        assert clean_data["model"] == "Golf"
        assert clean_data["price"] == 18500.0  # Converted to float
        assert clean_data["year"] == 2020.0    # Converted to float
        assert "mileage" not in clean_data     # None removed
        assert "invalid_field" not in clean_data  # Invalid field removed
        assert clean_data["condition"] == "used"  # Default added
    
    @patch('app.scraper.automotive_scraper.GruppoAutoUnoScraper.get_page')
    def test_scrape_vehicle_detail_success(self, mock_get_page, sample_html_content):
        """Test successful vehicle detail scraping"""
        scraper = GruppoAutoUnoScraper()
        
        # Mock response
        mock_response = Mock()
        mock_response.text = sample_html_content
        mock_get_page.return_value = mock_response
        
        url = "https://gruppoautouno.it/usato/volkswagen-golf-123/"
        result = scraper.scrape_vehicle_detail(url)
        
        assert result is not None
        assert result["listing_url"] == url
        assert result["make"] == "Volkswagen"
        assert result["model"] == "Golf"
        assert result["price"] == 18500.0
        assert "images" in result
    
    @patch('app.scraper.automotive_scraper.GruppoAutoUnoScraper.get_page')
    def test_scrape_vehicle_detail_failure(self, mock_get_page):
        """Test vehicle detail scraping failure"""
        scraper = GruppoAutoUnoScraper()
        
        # Mock failed response
        mock_get_page.return_value = None
        
        url = "https://gruppoautouno.it/usato/invalid-url/"
        result = scraper.scrape_vehicle_detail(url)
        
        assert result is None
    
    def test_extract_vehicle_links(self):
        """Test extracting vehicle links from listing page"""
        scraper = GruppoAutoUnoScraper()
        
        html_content = """
        <html>
        <body>
            <a href="/usato/volkswagen-golf-1/">Golf 1</a>
            <a href="/usato/peugeot-208-2/">208</a>
            <a href="/other-page/">Not a vehicle</a>
            <a href="/usato/citroen-c3-3/">C3</a>
        </body>
        </html>
        """
        
        soup = BeautifulSoup(html_content, 'html.parser')
        links = scraper.extract_vehicle_links(soup)
        
        assert len(links) == 3
        assert "volkswagen-golf-1" in links[0]
        assert "peugeot-208-2" in links[1]
        assert "citroen-c3-3" in links[2]
    
    def test_find_text_by_patterns(self, sample_html_content):
        """Test finding text by regex patterns"""
        scraper = GruppoAutoUnoScraper()
        soup = BeautifulSoup(sample_html_content, 'html.parser')
        
        # Test finding mileage
        km_text = scraper.find_text_by_patterns(soup, [r'Km[:\s]*(\d+[\d.,]*)'])
        assert km_text == "45.000"
        
        # Test finding fuel type
        fuel_text = scraper.find_text_by_patterns(soup, [r'Alimentazione[:\s]*(\w+)'])
        assert fuel_text == "Diesel"
        
        # Test pattern not found
        not_found = scraper.find_text_by_patterns(soup, [r'NotFound[:\s]*(\w+)'])
        assert not_found is None
