"""
Session Management for Authenticated Scraping

Handles session persistence, recovery, and error handling for carmarket.ayvens.com
"""

import json
import logging
import time
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps

from app.core.config import settings
from app.scraper.ayvens_auth import AyvensAuthenticator

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages authenticated sessions with automatic recovery"""
    
    def __init__(self):
        self.authenticator = AyvensAuthenticator()
        self.session_file = Path(settings.DATA_DIR) / "sessions" / "ayvens_session.json"
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Session state
        self.session_data = {}
        self.retry_count = 0
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
        # Load existing session if available
        self._load_session()
    
    def _load_session(self):
        """Load session data from file"""
        try:
            if self.session_file.exists():
                with open(self.session_file, 'r') as f:
                    self.session_data = json.load(f)
                
                # Check if session is still valid
                expires_at = self.session_data.get('expires_at')
                if expires_at:
                    expires_dt = datetime.fromisoformat(expires_at)
                    if datetime.utcnow() < expires_dt:
                        logger.info("Loaded existing session data")
                        return
                
                # Session expired, clear it
                self.session_data = {}
                logger.info("Previous session expired, cleared session data")
                
        except Exception as e:
            logger.warning(f"Failed to load session data: {e}")
            self.session_data = {}
    
    def _save_session(self):
        """Save session data to file"""
        try:
            with open(self.session_file, 'w') as f:
                json.dump(self.session_data, f, indent=2)
            logger.debug("Session data saved")
        except Exception as e:
            logger.error(f"Failed to save session data: {e}")
    
    def ensure_authenticated(self) -> Dict[str, Any]:
        """
        Ensure we have a valid authenticated session
        
        Returns:
            Dictionary with authentication status and details
        """
        result = {
            "success": False,
            "authenticated": False,
            "error": None,
            "message": "",
            "retry_count": self.retry_count
        }
        
        try:
            # Check if current session is valid
            if self.authenticator.is_session_valid():
                result["success"] = True
                result["authenticated"] = True
                result["message"] = "Session is valid"
                return result
            
            # Need to authenticate
            logger.info("Session invalid, attempting authentication...")
            auth_result = self.authenticator.authenticate()
            
            if auth_result["success"]:
                # Update session data
                self.session_data = {
                    "authenticated_at": datetime.utcnow().isoformat(),
                    "expires_at": auth_result.get("session_expires_at"),
                    "last_used": datetime.utcnow().isoformat()
                }
                self._save_session()
                
                result["success"] = True
                result["authenticated"] = True
                result["message"] = "Authentication successful"
                self.retry_count = 0  # Reset retry count on success
                
            else:
                result.update(auth_result)
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            result["error"] = "exception"
            result["message"] = f"Authentication failed: {str(e)}"
        
        return result
    
    def get_authenticated_session(self):
        """Get authenticated session for making requests"""
        auth_result = self.ensure_authenticated()
        if auth_result["success"]:
            return self.authenticator.get_authenticated_session()
        return None
    
    def handle_auth_error(self, response=None) -> bool:
        """
        Handle authentication errors and attempt recovery
        
        Args:
            response: Optional response object that triggered the error
            
        Returns:
            True if recovery was successful, False otherwise
        """
        if self.retry_count >= self.max_retries:
            logger.error(f"Max retries ({self.max_retries}) exceeded for authentication")
            return False
        
        self.retry_count += 1
        logger.warning(f"Authentication error detected, attempting recovery (attempt {self.retry_count}/{self.max_retries})")
        
        # Clear current session
        self.authenticator.logout()
        self.session_data = {}
        
        # Wait before retry
        time.sleep(self.retry_delay * self.retry_count)  # Exponential backoff
        
        # Attempt re-authentication
        auth_result = self.ensure_authenticated()
        return auth_result["success"]
    
    def with_auth_retry(self, func: Callable, *args, **kwargs):
        """
        Execute function with automatic authentication retry on failure
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Function result or None if all retries failed
        """
        for attempt in range(self.max_retries + 1):
            try:
                # Ensure we're authenticated
                auth_result = self.ensure_authenticated()
                if not auth_result["success"]:
                    logger.error(f"Authentication failed: {auth_result['message']}")
                    return None
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Reset retry count on success
                self.retry_count = 0
                return result
                
            except Exception as e:
                logger.warning(f"Function execution failed (attempt {attempt + 1}): {e}")
                
                # Check if this looks like an auth error
                if self._is_auth_error(e):
                    if not self.handle_auth_error():
                        break
                else:
                    # Non-auth error, don't retry
                    raise e
        
        logger.error(f"Function execution failed after {self.max_retries + 1} attempts")
        return None
    
    def _is_auth_error(self, error) -> bool:
        """Check if error is likely authentication-related"""
        error_str = str(error).lower()
        auth_error_indicators = [
            'unauthorized',
            'forbidden',
            'authentication',
            'login required',
            'session expired',
            'access denied',
            '401',
            '403'
        ]
        return any(indicator in error_str for indicator in auth_error_indicators)
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get current session status"""
        auth_status = self.authenticator.get_auth_status()
        
        return {
            "session_manager": {
                "retry_count": self.retry_count,
                "max_retries": self.max_retries,
                "session_file_exists": self.session_file.exists(),
                "session_data": {
                    "has_data": bool(self.session_data),
                    "authenticated_at": self.session_data.get("authenticated_at"),
                    "expires_at": self.session_data.get("expires_at"),
                    "last_used": self.session_data.get("last_used")
                }
            },
            "authenticator": auth_status
        }
    
    def clear_session(self):
        """Clear all session data and logout"""
        try:
            self.authenticator.logout()
            self.session_data = {}
            
            if self.session_file.exists():
                self.session_file.unlink()
            
            self.retry_count = 0
            logger.info("Session cleared successfully")
            
        except Exception as e:
            logger.error(f"Error clearing session: {e}")


def require_auth(func):
    """
    Decorator to ensure function is called with valid authentication
    
    Usage:
        @require_auth
        def scrape_vehicles(self):
            # This function will only run if authenticated
            pass
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'session_manager'):
            raise AttributeError("Object must have a session_manager attribute")
        
        return self.session_manager.with_auth_retry(func, self, *args, **kwargs)
    
    return wrapper


class AuthenticatedRequest:
    """Context manager for making authenticated requests"""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.session = None
    
    def __enter__(self):
        self.session = self.session_manager.get_authenticated_session()
        if not self.session:
            raise Exception("Failed to get authenticated session")
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Handle authentication errors
        if exc_type and self.session_manager._is_auth_error(exc_val):
            logger.warning("Authentication error detected in context manager")
            self.session_manager.handle_auth_error()
        
        # Don't suppress exceptions
        return False


# Global session manager instance
_session_manager = None

def get_session_manager() -> SessionManager:
    """Get global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def reset_session_manager():
    """Reset global session manager (useful for testing)"""
    global _session_manager
    if _session_manager:
        _session_manager.clear_session()
    _session_manager = None
