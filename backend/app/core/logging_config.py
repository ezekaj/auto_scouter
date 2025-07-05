"""
Comprehensive Logging Configuration

This module provides structured logging configuration including:
- Multiple log levels and handlers
- JSON structured logging for production
- File rotation and retention
- Request/response logging
- Performance monitoring
- Error tracking and alerting
- Security event logging
"""

import os
import sys
import logging
import logging.handlers
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class ContextFilter(logging.Filter):
    """Filter to add context information to log records"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context information to log record"""
        # Add application context
        record.app_name = settings.PROJECT_NAME
        record.app_version = getattr(settings, 'VERSION', '1.0.0')
        record.environment = getattr(settings, 'ENVIRONMENT', 'development')
        
        return True


class SecurityFilter(logging.Filter):
    """Filter for security-related events"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter security events"""
        security_keywords = [
            'authentication', 'authorization', 'login', 'logout',
            'password', 'token', 'security', 'breach', 'attack',
            'unauthorized', 'forbidden', 'rate_limit', 'suspicious'
        ]
        
        message = record.getMessage().lower()
        record.is_security_event = any(keyword in message for keyword in security_keywords)
        
        return True


class PerformanceFilter(logging.Filter):
    """Filter for performance-related events"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter performance events"""
        performance_keywords = [
            'slow', 'timeout', 'performance', 'latency',
            'response_time', 'query_time', 'memory', 'cpu'
        ]
        
        message = record.getMessage().lower()
        record.is_performance_event = any(keyword in message for keyword in performance_keywords)
        
        return True


class LoggingConfig:
    """Centralized logging configuration"""
    
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Log levels
        self.log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        
        # Log file settings
        self.max_bytes = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5
        
        # Initialize logging
        self.setup_logging()
    
    def setup_logging(self):
        """Setup comprehensive logging configuration"""
        # Clear existing handlers
        logging.getLogger().handlers.clear()
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Add context filter to all loggers
        context_filter = ContextFilter()
        security_filter = SecurityFilter()
        performance_filter = PerformanceFilter()
        
        # Console handler
        console_handler = self._create_console_handler()
        console_handler.addFilter(context_filter)
        console_handler.addFilter(security_filter)
        console_handler.addFilter(performance_filter)
        root_logger.addHandler(console_handler)
        
        # File handlers
        if settings.LOG_TO_FILE:
            # General application log
            app_handler = self._create_file_handler('app.log')
            app_handler.addFilter(context_filter)
            app_handler.addFilter(security_filter)
            app_handler.addFilter(performance_filter)
            root_logger.addHandler(app_handler)
            
            # Error log
            error_handler = self._create_file_handler('error.log', logging.ERROR)
            error_handler.addFilter(context_filter)
            root_logger.addHandler(error_handler)
            
            # Security log
            security_handler = self._create_security_handler()
            security_handler.addFilter(context_filter)
            security_handler.addFilter(security_filter)
            root_logger.addHandler(security_handler)
            
            # Performance log
            performance_handler = self._create_performance_handler()
            performance_handler.addFilter(context_filter)
            performance_handler.addFilter(performance_filter)
            root_logger.addHandler(performance_handler)
        
        # Configure specific loggers
        self._configure_specific_loggers()
        
        # Log startup message
        logger = logging.getLogger(__name__)
        logger.info(
            f"Logging configured - Level: {logging.getLevelName(self.log_level)}, "
            f"File logging: {settings.LOG_TO_FILE}, "
            f"JSON format: {settings.LOG_JSON_FORMAT}"
        )
    
    def _create_console_handler(self) -> logging.StreamHandler:
        """Create console handler"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.log_level)
        
        if settings.LOG_JSON_FORMAT:
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        handler.setFormatter(formatter)
        return handler
    
    def _create_file_handler(self, filename: str, level: int = None) -> logging.handlers.RotatingFileHandler:
        """Create rotating file handler"""
        filepath = self.log_dir / filename
        handler = logging.handlers.RotatingFileHandler(
            filepath,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count
        )
        
        handler.setLevel(level or self.log_level)
        
        if settings.LOG_JSON_FORMAT:
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s - '
                '[%(filename)s:%(lineno)d]'
            )
        
        handler.setFormatter(formatter)
        return handler
    
    def _create_security_handler(self) -> logging.handlers.RotatingFileHandler:
        """Create security events handler"""
        filepath = self.log_dir / 'security.log'
        handler = logging.handlers.RotatingFileHandler(
            filepath,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count
        )
        
        handler.setLevel(logging.WARNING)
        
        # Custom filter for security events only
        class SecurityOnlyFilter(logging.Filter):
            def filter(self, record):
                return getattr(record, 'is_security_event', False)
        
        handler.addFilter(SecurityOnlyFilter())
        
        if settings.LOG_JSON_FORMAT:
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - SECURITY - %(levelname)s - %(message)s - '
                '[%(filename)s:%(lineno)d]'
            )
        
        handler.setFormatter(formatter)
        return handler
    
    def _create_performance_handler(self) -> logging.handlers.RotatingFileHandler:
        """Create performance events handler"""
        filepath = self.log_dir / 'performance.log'
        handler = logging.handlers.RotatingFileHandler(
            filepath,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count
        )
        
        handler.setLevel(logging.INFO)
        
        # Custom filter for performance events only
        class PerformanceOnlyFilter(logging.Filter):
            def filter(self, record):
                return getattr(record, 'is_performance_event', False)
        
        handler.addFilter(PerformanceOnlyFilter())
        
        if settings.LOG_JSON_FORMAT:
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - PERFORMANCE - %(levelname)s - %(message)s - '
                '[%(filename)s:%(lineno)d]'
            )
        
        handler.setFormatter(formatter)
        return handler
    
    def _configure_specific_loggers(self):
        """Configure specific loggers with appropriate levels"""
        # Database logger
        db_logger = logging.getLogger('sqlalchemy.engine')
        db_logger.setLevel(logging.WARNING if settings.LOG_LEVEL != 'DEBUG' else logging.INFO)
        
        # HTTP client logger
        http_logger = logging.getLogger('httpx')
        http_logger.setLevel(logging.WARNING)
        
        # FastAPI logger
        fastapi_logger = logging.getLogger('fastapi')
        fastapi_logger.setLevel(logging.INFO)
        
        # Uvicorn logger
        uvicorn_logger = logging.getLogger('uvicorn')
        uvicorn_logger.setLevel(logging.INFO)
        
        # Application loggers
        app_logger = logging.getLogger('app')
        app_logger.setLevel(self.log_level)


# Global logging configuration instance
logging_config = None


def setup_logging():
    """Initialize logging configuration"""
    global logging_config
    if logging_config is None:
        logging_config = LoggingConfig()
    return logging_config


def get_logger(name: str) -> logging.Logger:
    """Get logger with proper configuration"""
    if logging_config is None:
        setup_logging()
    return logging.getLogger(name)


# Convenience functions for structured logging
def log_request(logger: logging.Logger, method: str, path: str, 
               status_code: int, response_time: float, user_id: Optional[str] = None):
    """Log HTTP request"""
    logger.info(
        f"HTTP {method} {path} - {status_code} - {response_time:.3f}s",
        extra={
            'event_type': 'http_request',
            'method': method,
            'path': path,
            'status_code': status_code,
            'response_time': response_time,
            'user_id': user_id
        }
    )


def log_security_event(logger: logging.Logger, event_type: str, message: str, 
                      user_id: Optional[str] = None, ip_address: Optional[str] = None):
    """Log security event"""
    logger.warning(
        f"Security event: {event_type} - {message}",
        extra={
            'event_type': 'security',
            'security_event_type': event_type,
            'user_id': user_id,
            'ip_address': ip_address
        }
    )


def log_performance_event(logger: logging.Logger, operation: str, duration: float, 
                         details: Optional[Dict[str, Any]] = None):
    """Log performance event"""
    logger.info(
        f"Performance: {operation} took {duration:.3f}s",
        extra={
            'event_type': 'performance',
            'operation': operation,
            'duration': duration,
            'details': details or {}
        }
    )
