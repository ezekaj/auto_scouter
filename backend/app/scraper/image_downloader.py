"""
Image Downloader for Vehicle Scrapers

Handles downloading, processing, and storage of vehicle images
with proper error handling and optimization
"""

import os
import uuid
import hashlib
import requests
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, urljoin
import logging
from PIL import Image
import io

from .config import scraper_settings

logger = logging.getLogger(__name__)


class ImageDownloader:
    """Handles image downloading and processing for vehicle scrapers"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.base_dir = Path(scraper_settings.IMAGE_STORAGE_PATH)
        self.source_dir = self.base_dir / source_name
        self.session = requests.Session()
        
        # Setup directories
        self.setup_directories()
        
        # Image processing settings
        self.max_image_size = (1200, 800)  # Max dimensions for resizing
        self.quality = 85  # JPEG quality
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.webp'}
        
    def setup_directories(self):
        """Create necessary directories for image storage"""
        try:
            self.source_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Image storage setup at: {self.source_dir}")
        except Exception as e:
            logger.error(f"Failed to create image directory: {e}")
    
    def download_image(self, image_url: str, vehicle_id: str, 
                      resize: bool = True) -> Optional[str]:
        """
        Download and process a single image
        
        Args:
            image_url: URL of the image to download
            vehicle_id: Unique identifier for the vehicle
            resize: Whether to resize the image
            
        Returns:
            Local file path if successful, None otherwise
        """
        if not scraper_settings.ENABLE_IMAGE_DOWNLOAD or not image_url:
            return image_url
        
        try:
            # Validate URL
            parsed_url = urlparse(image_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                logger.warning(f"Invalid image URL: {image_url}")
                return None
            
            # Generate filename
            file_extension = self._get_file_extension(parsed_url.path)
            if file_extension not in self.supported_formats:
                file_extension = '.jpg'  # Default to JPEG
            
            filename = f"{vehicle_id}_{self._generate_hash(image_url)[:8]}{file_extension}"
            file_path = self.source_dir / filename
            
            # Check if file already exists
            if file_path.exists():
                logger.debug(f"Image already exists: {filename}")
                return str(file_path)
            
            # Download image
            response = self.session.get(image_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                logger.warning(f"Invalid content type for image: {content_type}")
                return None
            
            # Process and save image
            image_data = response.content
            if resize:
                image_data = self._process_image(image_data)
            
            if image_data:
                with open(file_path, 'wb') as f:
                    f.write(image_data)
                
                logger.info(f"Downloaded and processed image: {filename}")
                return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to download image {image_url}: {e}")
        
        return None
    
    def download_multiple_images(self, image_urls: List[str], vehicle_id: str,
                                max_images: int = 5) -> List[str]:
        """
        Download multiple images for a vehicle
        
        Args:
            image_urls: List of image URLs
            vehicle_id: Unique identifier for the vehicle
            max_images: Maximum number of images to download
            
        Returns:
            List of local file paths
        """
        downloaded_paths = []
        
        for i, url in enumerate(image_urls[:max_images]):
            if not url:
                continue
                
            # Add index to vehicle_id for multiple images
            indexed_vehicle_id = f"{vehicle_id}_img{i+1}"
            
            local_path = self.download_image(url, indexed_vehicle_id)
            if local_path:
                downloaded_paths.append(local_path)
        
        logger.info(f"Downloaded {len(downloaded_paths)} images for vehicle {vehicle_id}")
        return downloaded_paths
    
    def _process_image(self, image_data: bytes) -> Optional[bytes]:
        """
        Process image: resize, optimize, and convert format if needed
        
        Args:
            image_data: Raw image data
            
        Returns:
            Processed image data or None if processing failed
        """
        try:
            # Open image with PIL
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary (for JPEG compatibility)
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # Resize if image is too large
            if image.size[0] > self.max_image_size[0] or image.size[1] > self.max_image_size[1]:
                image.thumbnail(self.max_image_size, Image.Resampling.LANCZOS)
                logger.debug(f"Resized image to {image.size}")
            
            # Save to bytes buffer
            output_buffer = io.BytesIO()
            image.save(output_buffer, format='JPEG', quality=self.quality, optimize=True)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            return image_data  # Return original data as fallback
    
    def _get_file_extension(self, path: str) -> str:
        """Extract file extension from path"""
        extension = os.path.splitext(path)[1].lower()
        return extension if extension else '.jpg'
    
    def _generate_hash(self, text: str) -> str:
        """Generate hash for filename uniqueness"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def cleanup_old_images(self, days_old: int = 30):
        """
        Clean up old images to save disk space
        
        Args:
            days_old: Remove images older than this many days
        """
        try:
            import time
            from datetime import datetime, timedelta
            
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            removed_count = 0
            
            for file_path in self.source_dir.glob('*'):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        removed_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to remove old image {file_path}: {e}")
            
            logger.info(f"Cleaned up {removed_count} old images from {self.source_dir}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old images: {e}")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics for this source"""
        try:
            total_files = 0
            total_size = 0
            
            for file_path in self.source_dir.glob('*'):
                if file_path.is_file():
                    total_files += 1
                    total_size += file_path.stat().st_size
            
            return {
                'source': self.source_name,
                'total_files': total_files,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'storage_path': str(self.source_dir)
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {
                'source': self.source_name,
                'total_files': 0,
                'total_size_mb': 0,
                'storage_path': str(self.source_dir),
                'error': str(e)
            }


class ImageUrlExtractor:
    """Utility class for extracting image URLs from HTML elements"""
    
    @staticmethod
    def extract_from_element(element, base_url: str = "") -> List[str]:
        """
        Extract image URLs from a BeautifulSoup element
        
        Args:
            element: BeautifulSoup element
            base_url: Base URL for resolving relative URLs
            
        Returns:
            List of image URLs
        """
        image_urls = []
        
        # Find all img tags
        img_tags = element.find_all('img')
        
        for img in img_tags:
            # Try different attributes
            for attr in ['src', 'data-src', 'data-original', 'data-lazy']:
                url = img.get(attr)
                if url:
                    # Resolve relative URLs
                    if base_url and not url.startswith(('http://', 'https://')):
                        url = urljoin(base_url, url)
                    
                    # Filter out placeholder/loading images
                    if not ImageUrlExtractor._is_placeholder_image(url):
                        image_urls.append(url)
                    break
        
        return list(set(image_urls))  # Remove duplicates
    
    @staticmethod
    def _is_placeholder_image(url: str) -> bool:
        """Check if URL is a placeholder or loading image"""
        placeholder_indicators = [
            'placeholder', 'loading', 'spinner', 'blank',
            'data:image', '1x1', 'pixel', 'transparent'
        ]
        
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in placeholder_indicators)
    
    @staticmethod
    def extract_from_css_background(element) -> List[str]:
        """Extract image URLs from CSS background-image properties"""
        image_urls = []
        
        # Check style attribute
        style = element.get('style', '')
        if 'background-image' in style:
            import re
            urls = re.findall(r'url\(["\']?([^"\']+)["\']?\)', style)
            image_urls.extend(urls)
        
        return image_urls
