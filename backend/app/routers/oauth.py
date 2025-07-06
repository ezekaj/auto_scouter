"""
OAuth Authentication API Router

This module provides OAuth authentication endpoints for Google, Facebook, and GitHub.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.models.base import get_db
from app.models.scout import User
from app.services.oauth_service import OAuthService
from app.core.oauth_config import oauth_config
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


class OAuthProviderResponse(BaseModel):
    """OAuth provider information response"""
    provider: str
    name: str
    icon: str
    enabled: bool
    client_id: Optional[str] = None


class OAuthAuthorizationResponse(BaseModel):
    """OAuth authorization URL response"""
    authorization_url: str
    state: str
    provider: str


class OAuthCallbackResponse(BaseModel):
    """OAuth callback response"""
    user: Dict[str, Any]
    token: Dict[str, str]
    oauth_info: Dict[str, Any]


class OAuthAccountResponse(BaseModel):
    """OAuth account response"""
    provider: str
    provider_user_id: str
    connected_at: str
    last_updated: Optional[str] = None


@router.get("/providers", response_model=list[OAuthProviderResponse])
async def get_oauth_providers():
    """Get list of available OAuth providers"""
    providers = []
    
    for provider_name, config in oauth_config.get_enabled_providers().items():
        providers.append(OAuthProviderResponse(
            provider=provider_name,
            name=config['name'],
            icon=config['icon'],
            enabled=config['enabled'],
            client_id=config.get('client_id') if config['enabled'] else None
        ))
    
    return providers


@router.get("/authorize/{provider}", response_model=OAuthAuthorizationResponse)
async def get_oauth_authorization_url(
    provider: str,
    redirect_uri: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get OAuth authorization URL for a provider"""
    oauth_service = OAuthService(db)
    
    try:
        auth_data = oauth_service.get_authorization_url(provider, redirect_uri)
        return OAuthAuthorizationResponse(**auth_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get OAuth authorization URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authorization URL"
        )


@router.get("/login/{provider}")
async def oauth_login_redirect(
    provider: str,
    redirect_uri: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Redirect to OAuth provider for authentication"""
    oauth_service = OAuthService(db)
    
    try:
        auth_data = oauth_service.get_authorization_url(provider, redirect_uri)
        return RedirectResponse(url=auth_data['authorization_url'])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to redirect to OAuth provider: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to redirect to OAuth provider"
        )


@router.get("/callback/{provider}", response_model=OAuthCallbackResponse)
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    redirect_uri: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Handle OAuth callback from provider"""
    if error:
        logger.warning(f"OAuth error from {provider}: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authentication failed: {error}"
        )
    
    oauth_service = OAuthService(db)
    
    try:
        result = await oauth_service.handle_oauth_callback(provider, code, state, redirect_uri)
        return OAuthCallbackResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authentication failed"
        )


@router.get("/accounts", response_model=list[OAuthAccountResponse])
async def get_user_oauth_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get OAuth accounts connected to the current user"""
    oauth_service = OAuthService(db)
    
    try:
        accounts = oauth_service.get_user_oauth_accounts(current_user.id)
        return [OAuthAccountResponse(**account) for account in accounts]
    except Exception as e:
        logger.error(f"Failed to get OAuth accounts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve OAuth accounts"
        )


@router.delete("/accounts/{provider}")
async def disconnect_oauth_account(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect an OAuth account"""
    oauth_service = OAuthService(db)
    
    try:
        success = oauth_service.disconnect_oauth_account(current_user.id, provider)
        
        if success:
            return {
                "message": f"Successfully disconnected {provider} account",
                "provider": provider
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No {provider} account found to disconnect"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disconnect OAuth account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect OAuth account"
        )


@router.post("/connect/{provider}")
async def connect_oauth_account(
    provider: str,
    redirect_uri: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Connect an additional OAuth account to existing user"""
    oauth_service = OAuthService(db)
    
    try:
        # Check if account is already connected
        accounts = oauth_service.get_user_oauth_accounts(current_user.id)
        if any(account['provider'] == provider for account in accounts):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{provider} account is already connected"
            )
        
        # Generate authorization URL
        auth_data = oauth_service.get_authorization_url(provider, redirect_uri)
        
        return {
            "message": f"Authorization URL generated for {provider}",
            "authorization_url": auth_data['authorization_url'],
            "state": auth_data['state'],
            "provider": provider
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to connect OAuth account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect OAuth account"
        )


@router.get("/status")
async def get_oauth_status():
    """Get OAuth system status"""
    enabled_providers = oauth_config.get_enabled_providers()
    
    return {
        "status": "operational",
        "enabled_providers": list(enabled_providers.keys()),
        "total_providers": len(enabled_providers),
        "configuration": {
            provider: {
                "name": config['name'],
                "enabled": config['enabled'],
                "scopes": config['scopes']
            }
            for provider, config in enabled_providers.items()
        }
    }


@router.get("/test/{provider}")
async def test_oauth_provider(
    provider: str,
    db: Session = Depends(get_db)
):
    """Test OAuth provider configuration (development only)"""
    if not oauth_config.is_provider_enabled(provider):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth provider '{provider}' is not enabled"
        )
    
    oauth_service = OAuthService(db)
    
    try:
        # Generate test authorization URL
        auth_data = oauth_service.get_authorization_url(provider)
        
        return {
            "provider": provider,
            "status": "configured",
            "test_authorization_url": auth_data['authorization_url'],
            "configuration": oauth_config.get_provider_config(provider)
        }
    except Exception as e:
        logger.error(f"OAuth provider test failed: {str(e)}")
        return {
            "provider": provider,
            "status": "error",
            "error": str(e),
            "configuration": oauth_config.get_provider_config(provider)
        }
