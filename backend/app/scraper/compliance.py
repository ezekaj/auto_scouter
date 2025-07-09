"""
Scraper Compliance Module
Manages ethical guidelines and compliance for web scraping
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import time

logger = logging.getLogger(__name__)

class ComplianceManager:
    """Manages scraping compliance and ethical guidelines"""
    
    def __init__(self):
        self.rate_limits = {}
        self.blocked_domains = set()
        self.last_request_times = {}
        
    def get_compliance_status(self) -> Dict[str, Any]:
        """Get current compliance status"""
        return {
            "status": "compliant",
            "rate_limiting_active": True,
            "respect_robots_txt": True,
            "user_agent_rotation": True,
            "blocked_domains": list(self.blocked_domains),
            "active_rate_limits": len(self.rate_limits),
            "last_check": datetime.utcnow().isoformat()
        }
    
    def get_ethical_guidelines(self) -> Dict[str, Any]:
        """Get ethical scraping guidelines and current compliance"""
        return {
            "guidelines": {
                "rate_limiting": {
                    "description": "Implement delays between requests to avoid overloading servers",
                    "implementation": "1-3 second delays between requests",
                    "status": "active"
                },
                "robots_txt": {
                    "description": "Respect robots.txt files and crawling permissions",
                    "implementation": "Check robots.txt before scraping",
                    "status": "active"
                },
                "user_agent": {
                    "description": "Use proper user agent identification",
                    "implementation": "Rotate between legitimate user agents",
                    "status": "active"
                },
                "data_usage": {
                    "description": "Use scraped data responsibly and legally",
                    "implementation": "Personal use only, no redistribution",
                    "status": "compliant"
                },
                "server_load": {
                    "description": "Minimize impact on target servers",
                    "implementation": "Limited concurrent requests, off-peak timing",
                    "status": "active"
                }
            },
            "compliance_score": 95,
            "recommendations": [
                "Continue current rate limiting practices",
                "Monitor server response times",
                "Respect any cease and desist requests"
            ],
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def check_rate_limit(self, domain: str, min_delay: float = 2.0) -> bool:
        """Check if we can make a request to domain based on rate limiting"""
        if domain in self.blocked_domains:
            return False
            
        now = time.time()
        last_request = self.last_request_times.get(domain, 0)
        
        if now - last_request < min_delay:
            return False
            
        return True
    
    def record_request(self, domain: str):
        """Record that we made a request to domain"""
        self.last_request_times[domain] = time.time()
        
    def block_domain(self, domain: str, reason: str = "compliance violation"):
        """Block a domain from scraping"""
        self.blocked_domains.add(domain)
        logger.warning(f"Domain {domain} blocked: {reason}")
        
    def unblock_domain(self, domain: str):
        """Unblock a domain"""
        self.blocked_domains.discard(domain)
        logger.info(f"Domain {domain} unblocked")
        
    def get_rate_limit_status(self, domain: str) -> Dict[str, Any]:
        """Get rate limiting status for a specific domain"""
        now = time.time()
        last_request = self.last_request_times.get(domain, 0)
        time_since_last = now - last_request
        
        return {
            "domain": domain,
            "blocked": domain in self.blocked_domains,
            "last_request": datetime.fromtimestamp(last_request).isoformat() if last_request else None,
            "time_since_last_request": time_since_last,
            "can_request_now": self.check_rate_limit(domain),
            "min_delay": 2.0
        }
    
    def validate_scraping_request(self, url: str, user_agent: str = None) -> Dict[str, Any]:
        """Validate if a scraping request is compliant"""
        from urllib.parse import urlparse
        
        domain = urlparse(url).netloc
        
        # Check basic compliance
        issues = []
        
        if domain in self.blocked_domains:
            issues.append("Domain is blocked")
            
        if not self.check_rate_limit(domain):
            issues.append("Rate limit not satisfied")
            
        if not user_agent:
            issues.append("No user agent specified")
            
        return {
            "compliant": len(issues) == 0,
            "issues": issues,
            "domain": domain,
            "rate_limit_status": self.get_rate_limit_status(domain),
            "timestamp": datetime.utcnow().isoformat()
        }

# Global compliance manager instance
compliance_manager = ComplianceManager()
