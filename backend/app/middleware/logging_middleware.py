"""
Logging Middleware

This module provides comprehensive request/response logging middleware including:
- HTTP request/response logging
- Performance monitoring
- Error tracking
- Security event logging
- User activity tracking
"""

import time
import logging
import json
from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from app.core.logging_config import get_logger, log_request, log_security_event, log_performance_event


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request/response logging"""
    
    def __init__(self, app, log_requests: bool = True, log_responses: bool = False):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.logger = get_logger(__name__)
        
        # Paths to exclude from logging
        self.exclude_paths = {
            '/health',
            '/docs',
            '/redoc',
            '/openapi.json',
            '/favicon.ico'
        }
        
        # Sensitive headers to mask
        self.sensitive_headers = {
            'authorization',
            'cookie',
            'x-api-key',
            'x-auth-token'
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with comprehensive logging"""
        
        # Skip logging for excluded paths
        if self._should_skip_logging(request):
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Extract request information
        request_info = await self._extract_request_info(request)
        
        # Log incoming request
        if self.log_requests:
            self._log_incoming_request(request_info)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Extract response information
            response_info = self._extract_response_info(response, response_time)
            
            # Log outgoing response
            self._log_outgoing_response(request_info, response_info)
            
            # Log performance if slow
            if response_time > 1.0:  # Log if response takes more than 1 second
                log_performance_event(
                    self.logger,
                    f"{request_info['method']} {request_info['path']}",
                    response_time,
                    {
                        'status_code': response_info['status_code'],
                        'user_id': request_info.get('user_id'),
                        'ip_address': request_info.get('ip_address')
                    }
                )
            
            # Log security events
            self._check_security_events(request_info, response_info)
            
            return response
            
        except Exception as e:
            # Calculate response time for errors
            response_time = time.time() - start_time
            
            # Log error
            self.logger.error(
                f"Request failed: {request_info['method']} {request_info['path']} - {str(e)}",
                extra={
                    'event_type': 'request_error',
                    'method': request_info['method'],
                    'path': request_info['path'],
                    'response_time': response_time,
                    'user_id': request_info.get('user_id'),
                    'ip_address': request_info.get('ip_address'),
                    'error': str(e)
                },
                exc_info=True
            )
            
            # Re-raise the exception
            raise
    
    def _should_skip_logging(self, request: Request) -> bool:
        """Check if logging should be skipped for this request"""
        return request.url.path in self.exclude_paths
    
    async def _extract_request_info(self, request: Request) -> Dict[str, Any]:
        """Extract comprehensive request information"""
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Get user ID if authenticated
        user_id = self._get_user_id(request)
        
        # Get request headers (masked)
        headers = self._mask_sensitive_headers(dict(request.headers))
        
        # Get query parameters
        query_params = dict(request.query_params)
        
        # Get request body for POST/PUT requests (be careful with large bodies)
        body = None
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                # Only log body for certain content types and if not too large
                content_type = request.headers.get('content-type', '')
                if 'application/json' in content_type:
                    # Clone the request to read body without consuming it
                    body_bytes = await request.body()
                    if len(body_bytes) < 10000:  # Only log if less than 10KB
                        body = body_bytes.decode('utf-8')
                        # Try to parse as JSON for better logging
                        try:
                            body = json.loads(body)
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                self.logger.debug(f"Could not read request body: {str(e)}")
        
        return {
            'method': request.method,
            'path': request.url.path,
            'full_url': str(request.url),
            'ip_address': client_ip,
            'user_id': user_id,
            'headers': headers,
            'query_params': query_params,
            'body': body,
            'user_agent': request.headers.get('user-agent'),
            'referer': request.headers.get('referer')
        }
    
    def _extract_response_info(self, response: Response, response_time: float) -> Dict[str, Any]:
        """Extract response information"""
        # Get response headers (masked)
        headers = self._mask_sensitive_headers(dict(response.headers))
        
        return {
            'status_code': response.status_code,
            'response_time': response_time,
            'headers': headers,
            'content_type': response.headers.get('content-type')
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        # Check for forwarded headers (for reverse proxies)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else 'unknown'
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request (if authenticated)"""
        # This would typically extract from JWT token or session
        # For now, we'll check if there's an Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            # In a real implementation, you'd decode the JWT here
            # For now, we'll create a hash of the token
            import hashlib
            token = auth_header[7:]  # Remove 'Bearer '
            return hashlib.md5(token.encode()).hexdigest()[:16]
        return None
    
    def _mask_sensitive_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Mask sensitive header values"""
        masked_headers = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                masked_headers[key] = '***MASKED***'
            else:
                masked_headers[key] = value
        return masked_headers
    
    def _log_incoming_request(self, request_info: Dict[str, Any]):
        """Log incoming request"""
        self.logger.info(
            f"Incoming request: {request_info['method']} {request_info['path']}",
            extra={
                'event_type': 'incoming_request',
                'method': request_info['method'],
                'path': request_info['path'],
                'ip_address': request_info['ip_address'],
                'user_id': request_info.get('user_id'),
                'user_agent': request_info.get('user_agent'),
                'query_params': request_info.get('query_params')
            }
        )
    
    def _log_outgoing_response(self, request_info: Dict[str, Any], response_info: Dict[str, Any]):
        """Log outgoing response"""
        log_request(
            self.logger,
            request_info['method'],
            request_info['path'],
            response_info['status_code'],
            response_info['response_time'],
            request_info.get('user_id')
        )
    
    def _check_security_events(self, request_info: Dict[str, Any], response_info: Dict[str, Any]):
        """Check for security events and log them"""
        
        # Failed authentication attempts
        if (request_info['path'].endswith('/login') and 
            response_info['status_code'] in [401, 403]):
            log_security_event(
                self.logger,
                'failed_login',
                f"Failed login attempt from {request_info['ip_address']}",
                request_info.get('user_id'),
                request_info['ip_address']
            )
        
        # Unauthorized access attempts
        if response_info['status_code'] == 401:
            log_security_event(
                self.logger,
                'unauthorized_access',
                f"Unauthorized access attempt to {request_info['path']}",
                request_info.get('user_id'),
                request_info['ip_address']
            )
        
        # Forbidden access attempts
        if response_info['status_code'] == 403:
            log_security_event(
                self.logger,
                'forbidden_access',
                f"Forbidden access attempt to {request_info['path']}",
                request_info.get('user_id'),
                request_info['ip_address']
            )
        
        # Rate limiting events
        if response_info['status_code'] == 429:
            log_security_event(
                self.logger,
                'rate_limit_exceeded',
                f"Rate limit exceeded for {request_info['ip_address']} on {request_info['path']}",
                request_info.get('user_id'),
                request_info['ip_address']
            )
        
        # Suspicious patterns
        self._check_suspicious_patterns(request_info, response_info)
    
    def _check_suspicious_patterns(self, request_info: Dict[str, Any], response_info: Dict[str, Any]):
        """Check for suspicious request patterns"""
        
        # SQL injection patterns
        suspicious_sql_patterns = [
            'union select', 'drop table', 'insert into', 'delete from',
            'update set', 'exec(', 'execute(', '--', '/*', '*/'
        ]
        
        # XSS patterns
        suspicious_xss_patterns = [
            '<script', 'javascript:', 'onload=', 'onerror=', 'onclick='
        ]
        
        # Check query parameters and body
        all_params = str(request_info.get('query_params', '')) + str(request_info.get('body', ''))
        all_params_lower = all_params.lower()
        
        # Check for SQL injection
        for pattern in suspicious_sql_patterns:
            if pattern in all_params_lower:
                log_security_event(
                    self.logger,
                    'sql_injection_attempt',
                    f"Potential SQL injection attempt detected: {pattern}",
                    request_info.get('user_id'),
                    request_info['ip_address']
                )
                break
        
        # Check for XSS
        for pattern in suspicious_xss_patterns:
            if pattern in all_params_lower:
                log_security_event(
                    self.logger,
                    'xss_attempt',
                    f"Potential XSS attempt detected: {pattern}",
                    request_info.get('user_id'),
                    request_info['ip_address']
                )
                break
