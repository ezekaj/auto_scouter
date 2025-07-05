"""
Internationalization Middleware

This middleware handles language detection and response translation
for Albanian and Italian languages.
"""

import json
from typing import Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.i18n import get_user_language, translate_response, SupportedLanguage


class I18nMiddleware(BaseHTTPMiddleware):
    """Middleware for handling internationalization"""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """Process request with language detection and response translation"""
        
        # Detect user language from headers
        accept_language = request.headers.get('Accept-Language')
        user_language = get_user_language(accept_language)
        
        # Store language in request state for use in route handlers
        request.state.language = user_language
        
        # Process the request
        response = await call_next(request)
        
        # Translate response if it's JSON and contains translatable content
        if (response.headers.get('content-type', '').startswith('application/json') and
            hasattr(response, 'body')):
            
            try:
                # Get response body
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                
                # Parse JSON response
                response_data = json.loads(body.decode())
                
                # Translate response
                translated_data = translate_response(response_data, user_language)
                
                # Create new response with translated content
                translated_body = json.dumps(translated_data, ensure_ascii=False)
                
                # Update response
                response = Response(
                    content=translated_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type="application/json"
                )
                
                # Add language header
                response.headers["Content-Language"] = user_language.value
                
            except (json.JSONDecodeError, AttributeError):
                # If response is not JSON or can't be parsed, return as-is
                pass
        
        return response


def get_request_language(request: Request) -> SupportedLanguage:
    """Get the detected language from request state"""
    return getattr(request.state, 'language', SupportedLanguage.ALBANIAN)
