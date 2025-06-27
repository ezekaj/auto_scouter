"""
Compliance and Ethics Module

This module handles robots.txt compliance, rate limiting,
and ethical scraping practices.
"""

import time
import requests
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from app.scraper.config import scraper_settings

logger = logging.getLogger(__name__)


class RobotsChecker:
    """Check and enforce robots.txt compliance"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.robots_url = urljoin(base_url, '/robots.txt')
        self.robot_parser = RobotFileParser()
        self.robot_parser.set_url(self.robots_url)
        self.last_check = None
        self.cache_duration = timedelta(hours=24)  # Cache robots.txt for 24 hours
        
    def update_robots_txt(self) -> bool:
        """Fetch and parse the latest robots.txt"""
        try:
            logger.info(f"Fetching robots.txt from {self.robots_url}")
            self.robot_parser.read()
            self.last_check = datetime.utcnow()
            logger.info("Successfully updated robots.txt")
            return True
        except Exception as e:
            logger.error(f"Error fetching robots.txt: {e}")
            return False
    
    def is_fetch_allowed(self, url: str, user_agent: str = '*') -> bool:
        """
        Check if fetching a URL is allowed according to robots.txt
        
        Args:
            url: URL to check
            user_agent: User agent string
        
        Returns:
            True if allowed, False otherwise
        """
        if not scraper_settings.RESPECT_ROBOTS_TXT:
            return True
        
        # Update robots.txt if cache is stale
        if (not self.last_check or 
            datetime.utcnow() - self.last_check > self.cache_duration):
            self.update_robots_txt()
        
        try:
            return self.robot_parser.can_fetch(user_agent, url)
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            # Default to allowed if we can't check
            return True
    
    def get_crawl_delay(self, user_agent: str = '*') -> Optional[float]:
        """Get the crawl delay specified in robots.txt"""
        try:
            return self.robot_parser.crawl_delay(user_agent)
        except Exception:
            return None
    
    def get_robots_info(self) -> Dict[str, Any]:
        """Get information about robots.txt rules"""
        try:
            return {
                'robots_url': self.robots_url,
                'last_checked': self.last_check.isoformat() if self.last_check else None,
                'crawl_delay': self.get_crawl_delay(),
                'respect_robots': scraper_settings.RESPECT_ROBOTS_TXT
            }
        except Exception as e:
            logger.error(f"Error getting robots info: {e}")
            return {'error': str(e)}


class ComplianceManager:
    """Manage overall scraping compliance and ethics"""
    
    def __init__(self):
        self.robots_checker = RobotsChecker(scraper_settings.BASE_URL)
        self.request_history = []
        self.blocked_urls = set()
        self.warning_count = 0
        
    def check_url_compliance(self, url: str, user_agent: str = '*') -> Dict[str, Any]:
        """
        Comprehensive compliance check for a URL
        
        Args:
            url: URL to check
            user_agent: User agent string
        
        Returns:
            Dictionary with compliance status and recommendations
        """
        result = {
            'url': url,
            'allowed': True,
            'reasons': [],
            'recommendations': []
        }
        
        # Check robots.txt
        if not self.robots_checker.is_fetch_allowed(url, user_agent):
            result['allowed'] = False
            result['reasons'].append('Blocked by robots.txt')
            self.blocked_urls.add(url)
        
        # Check if URL is in blocked list
        if url in self.blocked_urls:
            result['allowed'] = False
            result['reasons'].append('Previously blocked URL')
        
        # Check rate limiting
        rate_limit_check = self.check_rate_limits()
        if not rate_limit_check['allowed']:
            result['allowed'] = False
            result['reasons'].append(f"Rate limit exceeded: {rate_limit_check['reason']}")
            result['recommendations'].append(f"Wait {rate_limit_check['wait_time']} seconds")
        
        # Add general recommendations
        if result['allowed']:
            crawl_delay = self.robots_checker.get_crawl_delay(user_agent)
            if crawl_delay:
                result['recommendations'].append(f"Respect crawl delay: {crawl_delay} seconds")
        
        return result
    
    def check_rate_limits(self) -> Dict[str, Any]:
        """Check if current request rate is within limits"""
        current_time = time.time()
        
        # Clean old requests (older than 1 hour)
        self.request_history = [
            req_time for req_time in self.request_history 
            if current_time - req_time < 3600
        ]
        
        # Check minute limit
        minute_requests = [
            req_time for req_time in self.request_history 
            if current_time - req_time < 60
        ]
        
        if len(minute_requests) >= scraper_settings.REQUESTS_PER_MINUTE:
            oldest_request = min(minute_requests)
            wait_time = 60 - (current_time - oldest_request)
            return {
                'allowed': False,
                'reason': f'Minute limit exceeded ({len(minute_requests)}/{scraper_settings.REQUESTS_PER_MINUTE})',
                'wait_time': max(0, wait_time)
            }
        
        # Check hour limit
        if len(self.request_history) >= scraper_settings.REQUESTS_PER_HOUR:
            oldest_request = min(self.request_history)
            wait_time = 3600 - (current_time - oldest_request)
            return {
                'allowed': False,
                'reason': f'Hour limit exceeded ({len(self.request_history)}/{scraper_settings.REQUESTS_PER_HOUR})',
                'wait_time': max(0, wait_time)
            }
        
        return {'allowed': True}
    
    def record_request(self, url: str, response_code: int, response_time: float):
        """Record a request for rate limiting and monitoring"""
        current_time = time.time()
        self.request_history.append(current_time)
        
        # Check for problematic response codes
        if response_code == 429:  # Too Many Requests
            self.warning_count += 1
            logger.warning(f"Received 429 Too Many Requests for {url}")
            
            # Add temporary block for this URL
            self.blocked_urls.add(url)
            
        elif response_code >= 500:  # Server errors
            self.warning_count += 1
            logger.warning(f"Server error {response_code} for {url}")
        
        # Log slow responses
        if response_time > 10:  # Slower than 10 seconds
            logger.warning(f"Slow response ({response_time:.2f}s) for {url}")
    
    def get_compliance_status(self) -> Dict[str, Any]:
        """Get overall compliance status and statistics"""
        current_time = time.time()
        
        # Calculate recent request rates
        minute_requests = len([
            req_time for req_time in self.request_history 
            if current_time - req_time < 60
        ])
        
        hour_requests = len(self.request_history)
        
        return {
            'robots_txt': self.robots_checker.get_robots_info(),
            'rate_limiting': {
                'requests_last_minute': minute_requests,
                'requests_last_hour': hour_requests,
                'minute_limit': scraper_settings.REQUESTS_PER_MINUTE,
                'hour_limit': scraper_settings.REQUESTS_PER_HOUR,
                'minute_utilization': (minute_requests / scraper_settings.REQUESTS_PER_MINUTE) * 100,
                'hour_utilization': (hour_requests / scraper_settings.REQUESTS_PER_HOUR) * 100
            },
            'blocked_urls': len(self.blocked_urls),
            'warning_count': self.warning_count,
            'compliance_score': self.calculate_compliance_score()
        }
    
    def calculate_compliance_score(self) -> float:
        """Calculate a compliance score from 0-100"""
        score = 100.0
        
        # Deduct points for warnings
        score -= min(self.warning_count * 5, 30)  # Max 30 points deduction
        
        # Deduct points for blocked URLs
        score -= min(len(self.blocked_urls) * 2, 20)  # Max 20 points deduction
        
        # Check rate limit utilization
        current_time = time.time()
        minute_requests = len([
            req_time for req_time in self.request_history 
            if current_time - req_time < 60
        ])
        
        minute_utilization = (minute_requests / scraper_settings.REQUESTS_PER_MINUTE) * 100
        if minute_utilization > 80:
            score -= 10  # High rate utilization
        
        return max(0, score)
    
    def reset_warnings(self):
        """Reset warning counters (for maintenance)"""
        self.warning_count = 0
        self.blocked_urls.clear()
        logger.info("Compliance warnings reset")
    
    def add_blocked_url(self, url: str, reason: str = "Manual block"):
        """Manually add a URL to the blocked list"""
        self.blocked_urls.add(url)
        logger.info(f"Added {url} to blocked list: {reason}")
    
    def remove_blocked_url(self, url: str):
        """Remove a URL from the blocked list"""
        self.blocked_urls.discard(url)
        logger.info(f"Removed {url} from blocked list")
    
    def get_ethical_guidelines(self) -> Dict[str, Any]:
        """Get ethical scraping guidelines and current compliance"""
        return {
            'guidelines': {
                'respect_robots_txt': {
                    'description': 'Always check and respect robots.txt directives',
                    'current_status': scraper_settings.RESPECT_ROBOTS_TXT,
                    'compliant': scraper_settings.RESPECT_ROBOTS_TXT
                },
                'rate_limiting': {
                    'description': 'Implement reasonable delays between requests',
                    'current_delay': scraper_settings.REQUEST_DELAY,
                    'compliant': scraper_settings.REQUEST_DELAY >= 1.0
                },
                'politeness_delay': {
                    'description': 'Add random delays to appear more human-like',
                    'current_status': scraper_settings.ENABLE_POLITENESS_DELAY,
                    'compliant': scraper_settings.ENABLE_POLITENESS_DELAY
                },
                'user_agent': {
                    'description': 'Use descriptive and honest user agent strings',
                    'current_agents': len(scraper_settings.USER_AGENTS),
                    'compliant': len(scraper_settings.USER_AGENTS) > 0
                },
                'error_handling': {
                    'description': 'Handle errors gracefully and back off on failures',
                    'max_retries': scraper_settings.MAX_RETRIES,
                    'compliant': scraper_settings.MAX_RETRIES <= 3
                }
            },
            'compliance_score': self.calculate_compliance_score(),
            'recommendations': self.get_compliance_recommendations()
        }
    
    def get_compliance_recommendations(self) -> List[str]:
        """Get recommendations for improving compliance"""
        recommendations = []
        
        if not scraper_settings.RESPECT_ROBOTS_TXT:
            recommendations.append("Enable robots.txt compliance")
        
        if scraper_settings.REQUEST_DELAY < 1.0:
            recommendations.append("Increase request delay to at least 1 second")
        
        if not scraper_settings.ENABLE_POLITENESS_DELAY:
            recommendations.append("Enable politeness delays for more natural behavior")
        
        if self.warning_count > 10:
            recommendations.append("Reduce request frequency - too many warnings")
        
        if len(self.blocked_urls) > 5:
            recommendations.append("Review and clean up blocked URLs list")
        
        # Check current rate utilization
        current_time = time.time()
        minute_requests = len([
            req_time for req_time in self.request_history 
            if current_time - req_time < 60
        ])
        
        minute_utilization = (minute_requests / scraper_settings.REQUESTS_PER_MINUTE) * 100
        if minute_utilization > 80:
            recommendations.append("Current request rate is too high - consider reducing frequency")
        
        if not recommendations:
            recommendations.append("Compliance status is good - maintain current practices")
        
        return recommendations


# Global compliance manager instance
compliance_manager = ComplianceManager()
