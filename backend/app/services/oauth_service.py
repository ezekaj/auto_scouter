"""
OAuth Service

This module provides OAuth authentication services for Google, Facebook, and GitHub.
"""

import secrets
import hashlib
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import requests

from app.core.oauth_config import oauth_config, OAuthUserInfo
from app.models.scout import User, OAuthAccount
from app.core.auth import create_access_token, get_password_hash
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class OAuthService:
    """Service for handling OAuth authentication"""
    
    def __init__(self, db: Session):
        self.db = db
        self.oauth = oauth_config.oauth
    
    def get_authorization_url(self, provider: str, redirect_uri: str = None) -> Dict[str, str]:
        """Get OAuth authorization URL for a provider"""
        if not oauth_config.is_provider_enabled(provider):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth provider '{provider}' is not enabled"
            )
        
        try:
            # Generate state for CSRF protection
            state = secrets.token_urlsafe(32)
            
            # Get OAuth client
            client = self.oauth.create_client(provider)
            if not client:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"OAuth client for '{provider}' not configured"
                )
            
            # Generate authorization URL
            redirect_uri = redirect_uri or oauth_config.OAUTH_REDIRECT_URI
            authorization_url = client.create_authorization_url(
                redirect_uri=redirect_uri,
                state=state
            )
            
            return {
                'authorization_url': authorization_url['url'],
                'state': state,
                'provider': provider
            }
            
        except Exception as e:
            logger.error(f"Failed to generate OAuth URL for {provider}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate OAuth authorization URL"
            )
    
    async def handle_oauth_callback(self, provider: str, code: str, state: str, 
                                  redirect_uri: str = None) -> Dict[str, Any]:
        """Handle OAuth callback and authenticate user"""
        if not oauth_config.is_provider_enabled(provider):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth provider '{provider}' is not enabled"
            )
        
        try:
            # Get OAuth client
            client = self.oauth.create_client(provider)
            if not client:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"OAuth client for '{provider}' not configured"
                )
            
            # Exchange code for token
            redirect_uri = redirect_uri or oauth_config.OAUTH_REDIRECT_URI
            token = await client.authorize_access_token(
                code=code,
                redirect_uri=redirect_uri
            )
            
            # Get user information
            user_info = await self._get_user_info(provider, client, token)
            
            # Find or create user
            user, is_new_user = await self._find_or_create_user(user_info)
            
            # Create or update OAuth account
            oauth_account = await self._create_or_update_oauth_account(user, user_info, token)
            
            # Generate access token
            access_token = create_access_token(data={"sub": user.username})
            
            logger.info(f"OAuth login successful for {provider}: {user.email}")
            
            return {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_active': user.is_active
                },
                'token': {
                    'access_token': access_token,
                    'token_type': 'bearer'
                },
                'oauth_info': {
                    'provider': provider,
                    'is_new_user': is_new_user,
                    'avatar_url': user_info.avatar_url
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"OAuth callback failed for {provider}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OAuth authentication failed"
            )
    
    async def _get_user_info(self, provider: str, client, token: Dict[str, Any]) -> OAuthUserInfo:
        """Get user information from OAuth provider"""
        try:
            if provider == 'google':
                # Google provides user info in the ID token
                user_data = token.get('userinfo', {})
                if not user_data:
                    # Fallback to userinfo endpoint
                    resp = await client.get('https://www.googleapis.com/oauth2/v2/userinfo')
                    user_data = resp.json()
            
            elif provider == 'facebook':
                # Get user info from Facebook Graph API
                resp = await client.get('/me?fields=id,name,email,picture')
                user_data = resp.json()
            
            elif provider == 'github':
                # Get user info from GitHub API
                resp = await client.get('/user')
                user_data = resp.json()
                
                # Get email if not public
                if not user_data.get('email'):
                    email_resp = await client.get('/user/emails')
                    emails = email_resp.json()
                    primary_email = next((e for e in emails if e.get('primary')), None)
                    if primary_email:
                        user_data['email'] = primary_email['email']
            
            else:
                raise ValueError(f"Unsupported provider: {provider}")
            
            return OAuthUserInfo(provider, user_data)
            
        except Exception as e:
            logger.error(f"Failed to get user info from {provider}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user information"
            )
    
    async def _find_or_create_user(self, user_info: OAuthUserInfo) -> Tuple[User, bool]:
        """Find existing user or create new one"""
        # First, check if user exists with this OAuth account
        oauth_account = self.db.query(OAuthAccount).filter(
            OAuthAccount.provider == user_info.provider,
            OAuthAccount.provider_user_id == user_info.id
        ).first()
        
        if oauth_account:
            return oauth_account.user, False
        
        # Check if user exists with this email
        existing_user = self.db.query(User).filter(User.email == user_info.email).first()
        
        if existing_user:
            return existing_user, False
        
        # Create new user
        username = await self._generate_unique_username(user_info.username or user_info.email.split('@')[0])
        
        new_user = User(
            username=username,
            email=user_info.email,
            password_hash=get_password_hash(secrets.token_urlsafe(32)),  # Random password
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        logger.info(f"Created new user via OAuth: {new_user.email}")
        return new_user, True
    
    async def _generate_unique_username(self, base_username: str) -> str:
        """Generate a unique username"""
        # Clean the base username
        base_username = ''.join(c for c in base_username if c.isalnum() or c in '_-').lower()
        if not base_username:
            base_username = 'user'
        
        username = base_username
        counter = 1
        
        while self.db.query(User).filter(User.username == username).first():
            username = f"{base_username}_{counter}"
            counter += 1
        
        return username
    
    async def _create_or_update_oauth_account(self, user: User, user_info: OAuthUserInfo, 
                                            token: Dict[str, Any]) -> OAuthAccount:
        """Create or update OAuth account"""
        oauth_account = self.db.query(OAuthAccount).filter(
            OAuthAccount.user_id == user.id,
            OAuthAccount.provider == user_info.provider
        ).first()
        
        if oauth_account:
            # Update existing account
            oauth_account.provider_user_id = user_info.id
            oauth_account.access_token = token.get('access_token', '')
            oauth_account.refresh_token = token.get('refresh_token', '')
            oauth_account.token_expires_at = self._calculate_token_expiry(token)
            oauth_account.user_data = user_info.raw_data
            oauth_account.updated_at = datetime.utcnow()
        else:
            # Create new OAuth account
            oauth_account = OAuthAccount(
                user_id=user.id,
                provider=user_info.provider,
                provider_user_id=user_info.id,
                access_token=token.get('access_token', ''),
                refresh_token=token.get('refresh_token', ''),
                token_expires_at=self._calculate_token_expiry(token),
                user_data=user_info.raw_data,
                created_at=datetime.utcnow()
            )
            self.db.add(oauth_account)
        
        self.db.commit()
        self.db.refresh(oauth_account)
        
        return oauth_account
    
    def _calculate_token_expiry(self, token: Dict[str, Any]) -> Optional[datetime]:
        """Calculate token expiry time"""
        expires_in = token.get('expires_in')
        if expires_in:
            return datetime.utcnow() + timedelta(seconds=int(expires_in))
        return None
    
    def get_user_oauth_accounts(self, user_id: int) -> list[Dict[str, Any]]:
        """Get all OAuth accounts for a user"""
        accounts = self.db.query(OAuthAccount).filter(OAuthAccount.user_id == user_id).all()
        
        return [
            {
                'provider': account.provider,
                'provider_user_id': account.provider_user_id,
                'connected_at': account.created_at.isoformat(),
                'last_updated': account.updated_at.isoformat() if account.updated_at else None
            }
            for account in accounts
        ]
    
    def disconnect_oauth_account(self, user_id: int, provider: str) -> bool:
        """Disconnect an OAuth account"""
        account = self.db.query(OAuthAccount).filter(
            OAuthAccount.user_id == user_id,
            OAuthAccount.provider == provider
        ).first()
        
        if account:
            self.db.delete(account)
            self.db.commit()
            logger.info(f"Disconnected OAuth account: {provider} for user {user_id}")
            return True
        
        return False
