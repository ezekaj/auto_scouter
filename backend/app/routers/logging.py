"""
Logging Management API Router

This module provides API endpoints for logging management and monitoring.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.models.base import get_db
from app.models.scout import User
from app.services.logging_service import LoggingService

router = APIRouter()


class LogStatsResponse(BaseModel):
    """Response model for log statistics"""
    period_hours: int
    total_requests: int
    error_count: int
    security_events: int
    performance_issues: int
    top_endpoints: List[Dict[str, Any]]
    error_types: Dict[str, int]
    response_time_avg: float
    status_codes: Dict[str, int]
    status: str


class LogSearchResponse(BaseModel):
    """Response model for log search"""
    query: str
    log_type: str
    level: Optional[str]
    hours: int
    results: List[Dict[str, Any]]
    total_matches: int


class SecurityEventsResponse(BaseModel):
    """Response model for security events"""
    period_hours: int
    total_events: int
    event_types: Dict[str, int]
    top_ips: Dict[str, int]
    recent_events: List[Dict[str, Any]]


class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics"""
    period_hours: int
    total_requests: int
    avg_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    slow_requests_count: int
    slowest_endpoints: List[Dict[str, Any]]
    recent_slow_requests: List[Dict[str, Any]]


@router.get("/stats", response_model=LogStatsResponse)
async def get_log_stats(
    hours: int = Query(24, ge=1, le=168),  # Max 1 week
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive logging statistics"""
    # TODO: Add admin check
    # For now, allow all authenticated users
    
    logging_service = LoggingService()
    stats = logging_service.get_log_stats(hours)
    
    if 'error' in stats:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get log stats: {stats['error']}"
        )
    
    return LogStatsResponse(**stats)


@router.get("/search", response_model=LogSearchResponse)
async def search_logs(
    query: str = Query(..., min_length=1),
    log_type: str = Query("app", pattern="^(app|error|security|performance)$"),
    level: Optional[str] = Query(None, pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"),
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search logs with filters"""
    # TODO: Add admin check
    # For now, allow all authenticated users
    
    logging_service = LoggingService()
    results = logging_service.search_logs(query, log_type, level, hours)
    
    if 'error' in results:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search logs: {results['error']}"
        )
    
    return LogSearchResponse(**results)


@router.get("/security-events", response_model=SecurityEventsResponse)
async def get_security_events(
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get security events from logs"""
    # TODO: Add admin check
    # For now, allow all authenticated users
    
    logging_service = LoggingService()
    events = logging_service.get_security_events(hours)
    
    if 'error' in events:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security events: {events['error']}"
        )
    
    return SecurityEventsResponse(**events)


@router.get("/performance-metrics", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get performance metrics from logs"""
    # TODO: Add admin check
    # For now, allow all authenticated users
    
    logging_service = LoggingService()
    metrics = logging_service.get_performance_metrics(hours)
    
    if 'error' in metrics:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {metrics['error']}"
        )
    
    return PerformanceMetricsResponse(**metrics)


@router.get("/health")
async def get_logging_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get logging system health status"""
    logging_service = LoggingService()
    
    # Check if log directory exists and is writable
    log_dir_exists = logging_service.log_dir.exists()
    log_dir_writable = log_dir_exists and os.access(logging_service.log_dir, os.W_OK)
    
    # Check log file sizes
    log_file_info = {}
    total_log_size = 0
    
    for log_type, filename in logging_service.log_files.items():
        log_path = logging_service.log_dir / filename
        if log_path.exists():
            size = log_path.stat().st_size
            log_file_info[log_type] = {
                'exists': True,
                'size_bytes': size,
                'size_mb': round(size / (1024 * 1024), 2)
            }
            total_log_size += size
        else:
            log_file_info[log_type] = {
                'exists': False,
                'size_bytes': 0,
                'size_mb': 0
            }
    
    # Determine health status
    health_status = "healthy"
    issues = []
    
    if not log_dir_exists:
        health_status = "critical"
        issues.append("Log directory does not exist")
    elif not log_dir_writable:
        health_status = "critical"
        issues.append("Log directory is not writable")
    
    # Check for large log files (>100MB)
    for log_type, info in log_file_info.items():
        if info['size_mb'] > 100:
            health_status = "warning" if health_status == "healthy" else health_status
            issues.append(f"{log_type} log file is large ({info['size_mb']}MB)")
    
    return {
        "status": health_status,
        "log_directory": {
            "path": str(logging_service.log_dir),
            "exists": log_dir_exists,
            "writable": log_dir_writable
        },
        "log_files": log_file_info,
        "total_log_size_mb": round(total_log_size / (1024 * 1024), 2),
        "issues": issues,
        "timestamp": "2025-07-06T01:35:00Z"
    }


@router.get("/config")
async def get_logging_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current logging configuration"""
    # TODO: Add admin check
    # For now, allow all authenticated users
    
    from app.core.config import settings
    
    return {
        "log_level": settings.LOG_LEVEL,
        "log_to_file": settings.LOG_TO_FILE,
        "log_json_format": settings.LOG_JSON_FORMAT,
        "log_max_size": settings.LOG_MAX_SIZE,
        "log_backup_count": settings.LOG_BACKUP_COUNT,
        "log_directory": "logs/",
        "available_log_types": ["app", "error", "security", "performance"]
    }


@router.post("/test")
async def test_logging(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test logging functionality by generating sample log entries"""
    from app.core.logging_config import get_logger, log_security_event, log_performance_event
    
    logger = get_logger(__name__)
    
    # Generate test log entries
    logger.info("Test info message from logging API")
    logger.warning("Test warning message from logging API")
    logger.error("Test error message from logging API")
    
    # Generate test security event
    log_security_event(
        logger,
        'test_event',
        'This is a test security event',
        str(current_user.id),
        '127.0.0.1'
    )
    
    # Generate test performance event
    log_performance_event(
        logger,
        'test_operation',
        1.5,
        {'test': True, 'user_id': current_user.id}
    )
    
    return {
        "message": "Test log entries generated successfully",
        "entries_created": 5,
        "types": ["info", "warning", "error", "security", "performance"],
        "user_id": current_user.id,
        "timestamp": "2025-07-06T01:35:00Z"
    }


@router.get("/tail/{log_type}")
async def tail_log(
    log_type: str = Path(..., pattern="^(app|error|security|performance)$"),
    lines: int = Query(50, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the last N lines from a specific log file"""
    # TODO: Add admin check
    # For now, allow all authenticated users
    
    logging_service = LoggingService()
    
    if log_type not in logging_service.log_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid log type. Available types: {list(logging_service.log_files.keys())}"
        )
    
    log_file = logging_service.log_dir / logging_service.log_files[log_type]
    
    if not log_file.exists():
        return {
            "log_type": log_type,
            "lines_requested": lines,
            "lines_returned": 0,
            "entries": [],
            "message": "Log file does not exist"
        }
    
    try:
        # Read last N lines
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        # Parse log entries
        entries = []
        for line in last_lines:
            line = line.strip()
            if line:
                try:
                    # Try to parse as JSON
                    import json
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError:
                    # Handle non-JSON lines
                    entries.append({"raw_line": line})
        
        return {
            "log_type": log_type,
            "lines_requested": lines,
            "lines_returned": len(entries),
            "entries": entries
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read log file: {str(e)}"
        )
