"""
Ayvens Carmarket Authentication Module

Handles authentication and session management for carmarket.ayvens.com
"""

import requests
import logging
import time
import re
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Hardcoded credentials for single-user application
AYVENS_USERNAME = "Pndoj"
AYVENS_PASSWORD = "Asdfgh,.&78"

logger = logging.getLogger(__name__)


class AyvensAuthenticator:
    """Handles authentication with carmarket.ayvens.com"""
    
    def __init__(self):
        self.base_url = "https://carmarket.ayvens.com"
        self.login_url = f"{self.base_url}/en-fr/"  # Main page where login modal is triggered
        self.auth_endpoint = f"{self.base_url}/api/auth/login"  # Likely AJAX endpoint
        self.session = requests.Session()
        self.is_authenticated = False
        self.auth_expires_at = None
        self.last_auth_check = None
        
        # Setup session headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
    
    def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with carmarket.ayvens.com using hardcoded credentials

        Returns:
            Dictionary with authentication results
        """
        auth_result = {
            "success": False,
            "authenticated": False,
            "error": None,
            "message": "",
            "session_expires_at": None
        }

        try:
            # Use hardcoded credentials
            username = AYVENS_USERNAME
            password = AYVENS_PASSWORD

            logger.info(f"Attempting authentication for user: {username}")

            # Step 1: Get main page and establish session
            session_result = self._establish_session()
            if not session_result["success"]:
                auth_result.update(session_result)
                return auth_result

            # Step 2: Attempt AJAX login
            login_result = self._submit_ajax_login(username, password)
            if not login_result["success"]:
                # Fallback to form-based login if AJAX fails
                login_result = self._try_form_login(username, password)
            
            if login_result["success"]:
                self.is_authenticated = True
                self.auth_expires_at = datetime.utcnow() + timedelta(hours=2)  # Assume 2-hour session
                self.last_auth_check = datetime.utcnow()
                
                auth_result["success"] = True
                auth_result["authenticated"] = True
                auth_result["message"] = "Successfully authenticated with carmarket.ayvens.com"
                auth_result["session_expires_at"] = self.auth_expires_at.isoformat()
                
                logger.info("Authentication successful")
            else:
                auth_result.update(login_result)
                
        except Exception as e:
            logger.error(f"Authentication failed with exception: {e}")
            auth_result["error"] = "exception"
            auth_result["message"] = f"Authentication failed: {str(e)}"
        
        return auth_result
    
    def _establish_session(self) -> Dict[str, Any]:
        """Establish session by visiting main page and extracting necessary tokens"""
        result = {
            "success": False,
            "error": None,
            "message": "",
            "tokens": {}
        }

        try:
            logger.debug("Establishing session...")
            response = self.session.get(self.login_url, timeout=30)
            response.raise_for_status()

            # Parse HTML to extract any CSRF tokens or session data
            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for common token patterns
            tokens = {}

            # Check for CSRF tokens in meta tags
            csrf_meta = soup.find('meta', {'name': re.compile(r'csrf|token', re.I)})
            if csrf_meta:
                tokens['csrf_token'] = csrf_meta.get('content', '')

            # Check for tokens in hidden inputs
            hidden_inputs = soup.find_all('input', {'type': 'hidden'})
            for hidden_input in hidden_inputs:
                name = hidden_input.get('name', '')
                value = hidden_input.get('value', '')
                if 'token' in name.lower() or 'csrf' in name.lower():
                    tokens[name] = value

            # Check for tokens in script tags (common in modern web apps)
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for token patterns in JavaScript
                    token_match = re.search(r'["\'](?:csrf_token|csrfToken|_token)["\']:\s*["\']([^"\']+)["\']', script.string)
                    if token_match:
                        tokens['csrf_token'] = token_match.group(1)
                        break

            result["success"] = True
            result["tokens"] = tokens
            result["message"] = "Session established successfully"

            logger.debug(f"Extracted tokens: {list(tokens.keys())}")

        except requests.exceptions.RequestException as e:
            result["error"] = "network_error"
            result["message"] = f"Network error establishing session: {str(e)}"

        except Exception as e:
            result["error"] = "session_error"
            result["message"] = f"Error establishing session: {str(e)}"

        return result

    def _submit_ajax_login(self, username: str, password: str) -> Dict[str, Any]:
        """Attempt AJAX-based login (common for modal logins)"""
        result = {
            "success": False,
            "error": None,
            "message": ""
        }

        try:
            # Common AJAX login endpoints
            ajax_endpoints = [
                f"{self.base_url}/api/auth/login",
                f"{self.base_url}/login",
                f"{self.base_url}/auth/login",
                f"{self.base_url}/account/login",
                f"{self.base_url}/user/login"
            ]

            # Prepare login data
            login_data = {
                "username": username,
                "password": password,
                "email": username,  # Some sites use email field
                "login": username   # Alternative field name
            }

            # Set AJAX headers
            ajax_headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': self.login_url
            }

            # Try each endpoint
            for endpoint in ajax_endpoints:
                try:
                    logger.debug(f"Trying AJAX login at: {endpoint}")

                    # Try JSON payload first
                    response = self.session.post(
                        endpoint,
                        json=login_data,
                        headers=ajax_headers,
                        timeout=30
                    )

                    if response.status_code == 200:
                        # Check if login was successful
                        if self._check_ajax_login_success(response):
                            result["success"] = True
                            result["message"] = "AJAX login successful"
                            return result

                    # Try form data if JSON failed
                    form_headers = ajax_headers.copy()
                    form_headers['Content-Type'] = 'application/x-www-form-urlencoded'

                    response = self.session.post(
                        endpoint,
                        data=login_data,
                        headers=form_headers,
                        timeout=30
                    )

                    if response.status_code == 200:
                        if self._check_ajax_login_success(response):
                            result["success"] = True
                            result["message"] = "AJAX login successful"
                            return result

                except requests.exceptions.RequestException:
                    continue  # Try next endpoint

            result["error"] = "ajax_failed"
            result["message"] = "All AJAX login attempts failed"

        except Exception as e:
            result["error"] = "ajax_error"
            result["message"] = f"Error during AJAX login: {str(e)}"

        return result

    def _check_ajax_login_success(self, response: requests.Response) -> bool:
        """Check if AJAX login response indicates success"""
        try:
            # Check for JSON response
            if 'application/json' in response.headers.get('content-type', ''):
                json_data = response.json()

                # Common success indicators in JSON
                success_indicators = ['success', 'authenticated', 'logged_in', 'valid']
                for indicator in success_indicators:
                    if json_data.get(indicator) is True:
                        return True

                # Check for error indicators
                error_indicators = ['error', 'message', 'errors']
                for indicator in error_indicators:
                    if indicator in json_data:
                        error_msg = json_data[indicator]
                        if isinstance(error_msg, str) and any(err in error_msg.lower() for err in ['invalid', 'incorrect', 'failed']):
                            return False

                # If no explicit success/error, assume success if no error fields
                return 'error' not in json_data and 'errors' not in json_data

            # For non-JSON responses, check status and content
            return response.status_code == 200 and 'error' not in response.text.lower()

        except Exception as e:
            logger.debug(f"Error checking AJAX response: {e}")
            return False

    def _try_form_login(self, username: str, password: str) -> Dict[str, Any]:
        """Fallback form-based login attempt"""
        result = {
            "success": False,
            "error": None,
            "message": ""
        }

        try:
            logger.debug("Attempting fallback form-based login...")

            # Try to find any login forms on the main page
            response = self.session.get(self.login_url, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for any forms that might be login forms
            forms = soup.find_all('form')
            login_form = None

            for form in forms:
                # Check if form has password field
                if form.find('input', {'type': 'password'}):
                    login_form = form
                    break

            if not login_form:
                result["error"] = "no_form_found"
                result["message"] = "No login form found for fallback"
                return result

            # Extract form data
            form_action = login_form.get('action', '')
            if form_action:
                form_action = urljoin(self.login_url, form_action)
            else:
                form_action = self.login_url

            # Prepare form data
            login_data = {}

            # Add hidden fields
            hidden_inputs = login_form.find_all('input', {'type': 'hidden'})
            for hidden_input in hidden_inputs:
                name = hidden_input.get('name')
                value = hidden_input.get('value', '')
                if name:
                    login_data[name] = value

            # Find and add credentials
            username_field = login_form.find('input', {'type': 'email'}) or \
                           login_form.find('input', {'name': re.compile(r'email|username|user', re.I)})
            password_field = login_form.find('input', {'type': 'password'})

            if username_field:
                login_data[username_field.get('name', 'email')] = username
            if password_field:
                login_data[password_field.get('name', 'password')] = password

            # Submit form
            logger.debug(f"Submitting fallback form to: {form_action}")
            response = self.session.post(
                form_action,
                data=login_data,
                timeout=30,
                allow_redirects=True
            )

            # Check if login was successful
            if self._check_authentication_success(response):
                result["success"] = True
                result["message"] = "Fallback form login successful"
            else:
                result["error"] = "invalid_credentials"
                result["message"] = "Fallback login failed - invalid credentials or form structure"

        except requests.exceptions.RequestException as e:
            result["error"] = "network_error"
            result["message"] = f"Network error during fallback login: {str(e)}"

        except Exception as e:
            result["error"] = "login_error"
            result["message"] = f"Error during fallback login: {str(e)}"

        return result
    
    def _check_authentication_success(self, response: requests.Response) -> bool:
        """Check if authentication was successful based on response"""
        try:
            # Check status code
            if response.status_code not in [200, 302, 301]:
                return False

            # Check URL - successful login usually redirects away from login
            current_url = response.url.lower()

            # If we're redirected to a protected area, likely successful
            protected_paths = ['/lots', '/dashboard', '/account', '/profile', '/vehicles']
            if any(path in current_url for path in protected_paths):
                logger.info(f"Redirected to protected area: {response.url}")
                return True

            # Check if we're still on login page with error
            if 'login' in current_url and any(err in current_url for err in ['error', 'failed', 'invalid']):
                return False

            # Check content for success/error indicators
            content = response.text.lower()

            # Strong negative indicators
            strong_error_indicators = [
                'invalid credentials',
                'incorrect password',
                'login failed',
                'authentication failed',
                'wrong username',
                'error logging in',
                'access denied',
                'unauthorized'
            ]

            if any(indicator in content for indicator in strong_error_indicators):
                logger.debug("Found error indicator in response content")
                return False

            # Strong positive indicators (Ayvens-specific)
            ayvens_success_indicators = [
                'carmarket.ayvens.com/lots',
                'logout',
                'my account',
                'user profile',
                'welcome',
                'dashboard',
                'auction',
                'tender',
                'fixed price'
            ]

            if any(indicator in content for indicator in ayvens_success_indicators):
                logger.info("Found success indicator in response content")
                return True

            # Check for authentication cookies
            auth_cookies = ['sessionid', 'auth_token', 'login_token', 'user_session']
            for cookie_name in auth_cookies:
                if cookie_name in self.session.cookies:
                    logger.info(f"Found authentication cookie: {cookie_name}")
                    return True

            # If we're not on login page anymore and no error indicators, likely successful
            if 'login' not in current_url and 'sign' not in current_url:
                logger.info("Redirected away from login page, assuming success")
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking authentication success: {e}")
            return False
    
    def is_session_valid(self) -> bool:
        """Check if current session is still valid"""
        if not self.is_authenticated:
            return False
        
        if self.auth_expires_at and datetime.utcnow() > self.auth_expires_at:
            self.is_authenticated = False
            return False
        
        # Check session validity every 30 minutes
        if (self.last_auth_check and 
            datetime.utcnow() - self.last_auth_check > timedelta(minutes=30)):
            return self._verify_session()
        
        return True
    
    def _verify_session(self) -> bool:
        """Verify session is still active by making a test request"""
        try:
            # Try to access a protected page
            test_url = f"{self.base_url}/lots"
            response = self.session.get(test_url, timeout=15)
            
            self.last_auth_check = datetime.utcnow()
            
            # If redirected to login, session expired
            if 'login' in response.url.lower():
                self.is_authenticated = False
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Session verification failed: {e}")
            return False
    
    def logout(self):
        """Logout and clear session"""
        try:
            # Try to find and use logout URL
            logout_url = f"{self.base_url}/logout"
            self.session.get(logout_url, timeout=10)
        except:
            pass  # Ignore logout errors
        
        # Clear session and authentication state
        self.session.cookies.clear()
        self.is_authenticated = False
        self.auth_expires_at = None
        self.last_auth_check = None
        
        logger.info("Logged out and cleared session")
    
    def get_authenticated_session(self) -> Optional[requests.Session]:
        """Get authenticated session for making requests"""
        if self.is_session_valid():
            return self.session
        return None
    
    def get_auth_status(self) -> Dict[str, Any]:
        """Get current authentication status"""
        return {
            "authenticated": self.is_authenticated,
            "session_valid": self.is_session_valid(),
            "expires_at": self.auth_expires_at.isoformat() if self.auth_expires_at else None,
            "last_check": self.last_auth_check.isoformat() if self.last_auth_check else None,
            "has_hardcoded_credentials": True
        }
