"""
OAuth Configuration

This module provides OAuth configuration for Google, Facebook, and GitHub authentication.
"""

import os
from typing import Dict, Any, Optional
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

# Load configuration
config = Config('.env')

class OAuthConfig:
    """OAuth configuration for different providers"""
    
    def __init__(self):
        # Google OAuth
        self.GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
        self.GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
        
        # Facebook OAuth
        self.FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID", "")
        self.FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET", "")
        
        # GitHub OAuth
        self.GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
        self.GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
        
        # OAuth redirect URIs
        self.OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/api/v1/auth/oauth/callback")
        
        # Initialize OAuth
        self.oauth = OAuth()
        self._setup_providers()
    
    def _setup_providers(self):
        """Setup OAuth providers"""
        
        # Google OAuth setup
        if self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET:
            self.oauth.register(
                name='google',
                client_id=self.GOOGLE_CLIENT_ID,
                client_secret=self.GOOGLE_CLIENT_SECRET,
                server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
                client_kwargs={
                    'scope': 'openid email profile'
                }
            )
        
        # Facebook OAuth setup
        if self.FACEBOOK_CLIENT_ID and self.FACEBOOK_CLIENT_SECRET:
            self.oauth.register(
                name='facebook',
                client_id=self.FACEBOOK_CLIENT_ID,
                client_secret=self.FACEBOOK_CLIENT_SECRET,
                access_token_url='https://graph.facebook.com/oauth/access_token',
                authorize_url='https://www.facebook.com/dialog/oauth',
                api_base_url='https://graph.facebook.com/',
                client_kwargs={'scope': 'email'}
            )
        
        # GitHub OAuth setup
        if self.GITHUB_CLIENT_ID and self.GITHUB_CLIENT_SECRET:
            self.oauth.register(
                name='github',
                client_id=self.GITHUB_CLIENT_ID,
                client_secret=self.GITHUB_CLIENT_SECRET,
                access_token_url='https://github.com/login/oauth/access_token',
                authorize_url='https://github.com/login/oauth/authorize',
                api_base_url='https://api.github.com/',
                client_kwargs={'scope': 'user:email'}
            )
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific OAuth provider"""
        configs = {
            'google': {
                'client_id': self.GOOGLE_CLIENT_ID,
                'enabled': bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET),
                'scopes': ['openid', 'email', 'profile'],
                'name': 'Google',
                'icon': 'google'
            },
            'facebook': {
                'client_id': self.FACEBOOK_CLIENT_ID,
                'enabled': bool(self.FACEBOOK_CLIENT_ID and self.FACEBOOK_CLIENT_SECRET),
                'scopes': ['email'],
                'name': 'Facebook',
                'icon': 'facebook'
            },
            'github': {
                'client_id': self.GITHUB_CLIENT_ID,
                'enabled': bool(self.GITHUB_CLIENT_ID and self.GITHUB_CLIENT_SECRET),
                'scopes': ['user:email'],
                'name': 'GitHub',
                'icon': 'github'
            }
        }
        return configs.get(provider, {})
    
    def get_enabled_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get all enabled OAuth providers"""
        providers = {}
        for provider in ['google', 'facebook', 'github']:
            config = self.get_provider_config(provider)
            if config.get('enabled'):
                providers[provider] = config
        return providers
    
    def is_provider_enabled(self, provider: str) -> bool:
        """Check if a specific provider is enabled"""
        return self.get_provider_config(provider).get('enabled', False)


# Global OAuth configuration instance
oauth_config = OAuthConfig()


class OAuthUserInfo:
    """Standardized user information from OAuth providers"""
    
    def __init__(self, provider: str, user_data: Dict[str, Any]):
        self.provider = provider
        self.raw_data = user_data
        
        # Standardize user information across providers
        self.id = self._extract_id()
        self.email = self._extract_email()
        self.name = self._extract_name()
        self.username = self._extract_username()
        self.avatar_url = self._extract_avatar_url()
        self.profile_url = self._extract_profile_url()
    
    def _extract_id(self) -> str:
        """Extract user ID from provider data"""
        if self.provider == 'google':
            return self.raw_data.get('sub', '')
        elif self.provider == 'facebook':
            return str(self.raw_data.get('id', ''))
        elif self.provider == 'github':
            return str(self.raw_data.get('id', ''))
        return ''
    
    def _extract_email(self) -> str:
        """Extract email from provider data"""
        return self.raw_data.get('email', '')
    
    def _extract_name(self) -> str:
        """Extract full name from provider data"""
        if self.provider == 'google':
            return self.raw_data.get('name', '')
        elif self.provider == 'facebook':
            return self.raw_data.get('name', '')
        elif self.provider == 'github':
            return self.raw_data.get('name', '') or self.raw_data.get('login', '')
        return ''
    
    def _extract_username(self) -> str:
        """Extract username from provider data"""
        if self.provider == 'google':
            # Google doesn't provide username, use email prefix
            email = self.raw_data.get('email', '')
            return email.split('@')[0] if email else ''
        elif self.provider == 'facebook':
            # Facebook doesn't provide username, use name or email
            return self.raw_data.get('name', '').replace(' ', '_').lower()
        elif self.provider == 'github':
            return self.raw_data.get('login', '')
        return ''
    
    def _extract_avatar_url(self) -> str:
        """Extract avatar URL from provider data"""
        if self.provider == 'google':
            return self.raw_data.get('picture', '')
        elif self.provider == 'facebook':
            return f"https://graph.facebook.com/{self.id}/picture?type=large"
        elif self.provider == 'github':
            return self.raw_data.get('avatar_url', '')
        return ''
    
    def _extract_profile_url(self) -> str:
        """Extract profile URL from provider data"""
        if self.provider == 'google':
            return ''  # Google doesn't provide public profile URL
        elif self.provider == 'facebook':
            return f"https://facebook.com/{self.id}"
        elif self.provider == 'github':
            return self.raw_data.get('html_url', '')
        return ''
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'provider': self.provider,
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'username': self.username,
            'avatar_url': self.avatar_url,
            'profile_url': self.profile_url,
            'raw_data': self.raw_data
        }
