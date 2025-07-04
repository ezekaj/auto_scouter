"""
API Documentation Endpoints

This module provides comprehensive API documentation and endpoint discovery.
"""

from fastapi import APIRouter, Request
from typing import Dict, Any, List

router = APIRouter()


@router.get("/endpoints", response_model=Dict[str, Any])
def get_api_endpoints():
    """Get comprehensive list of all available API endpoints"""
    
    endpoints = {
        "authentication": {
            "base_path": "/api/v1/auth",
            "endpoints": [
                {
                    "method": "POST",
                    "path": "/register",
                    "description": "Register a new user account",
                    "auth_required": False,
                    "request_body": {
                        "username": "string",
                        "email": "string",
                        "password": "string"
                    }
                },
                {
                    "method": "POST",
                    "path": "/login",
                    "description": "Authenticate user and get access token",
                    "auth_required": False,
                    "request_body": {
                        "username": "string",
                        "password": "string"
                    }
                },
                {
                    "method": "GET",
                    "path": "/me",
                    "description": "Get current user profile",
                    "auth_required": True
                },
                {
                    "method": "PUT",
                    "path": "/me",
                    "description": "Update current user profile",
                    "auth_required": True
                },
                {
                    "method": "POST",
                    "path": "/change-password",
                    "description": "Change user password",
                    "auth_required": True
                }
            ]
        },
        "vehicles": {
            "base_path": "/api/v1/cars",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/",
                    "description": "Search vehicles with filters",
                    "auth_required": False,
                    "query_params": [
                        "make", "model", "min_price", "max_price", "year", "limit", "offset"
                    ]
                },
                {
                    "method": "GET",
                    "path": "/new",
                    "description": "Get recently added vehicles",
                    "auth_required": False,
                    "query_params": [
                        "make", "model", "min_price", "max_price", "year", "hours", "limit", "offset"
                    ]
                },
                {
                    "method": "GET",
                    "path": "/{car_id}",
                    "description": "Get detailed vehicle information",
                    "auth_required": False
                },
                {
                    "method": "GET",
                    "path": "/stats/summary",
                    "description": "Get vehicle statistics summary",
                    "auth_required": False
                }
            ]
        },
        "advanced_search": {
            "base_path": "/api/v1/search",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/advanced",
                    "description": "Advanced vehicle search with comprehensive filters",
                    "auth_required": False,
                    "query_params": [
                        "make", "model", "year_min", "year_max", "price_min", "price_max",
                        "mileage_max", "fuel_type", "transmission", "body_type",
                        "engine_power_min", "engine_power_max", "city", "region", "country",
                        "source_website", "source_country", "min_data_quality",
                        "exclude_duplicates", "condition", "max_owners", "no_accidents",
                        "sort_by", "sort_order", "page", "page_size"
                    ]
                },
                {
                    "method": "GET",
                    "path": "/suggestions",
                    "description": "Get search suggestions for autocomplete",
                    "auth_required": False,
                    "query_params": ["field", "query", "limit"]
                },
                {
                    "method": "GET",
                    "path": "/filters",
                    "description": "Get available filter options",
                    "auth_required": False
                }
            ]
        },
        "alerts": {
            "base_path": "/api/v1/alerts",
            "endpoints": [
                {
                    "method": "POST",
                    "path": "/",
                    "description": "Create a new vehicle alert",
                    "auth_required": True,
                    "request_body": {
                        "make": "string (optional)",
                        "model": "string (optional)",
                        "min_price": "number (optional)",
                        "max_price": "number (optional)",
                        "year": "number (optional)",
                        "fuel_type": "string (optional)",
                        "transmission": "string (optional)",
                        "city": "string (optional)"
                    }
                },
                {
                    "method": "GET",
                    "path": "/",
                    "description": "Get user's alerts",
                    "auth_required": True,
                    "query_params": ["active_only"]
                },
                {
                    "method": "GET",
                    "path": "/{alert_id}",
                    "description": "Get specific alert details",
                    "auth_required": True
                },
                {
                    "method": "PUT",
                    "path": "/{alert_id}",
                    "description": "Update an alert",
                    "auth_required": True
                },
                {
                    "method": "DELETE",
                    "path": "/{alert_id}",
                    "description": "Delete an alert",
                    "auth_required": True
                }
            ]
        },
        "dashboard": {
            "base_path": "/api/v1/dashboard",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/overview",
                    "description": "Get comprehensive dashboard overview",
                    "auth_required": True
                },
                {
                    "method": "GET",
                    "path": "/analytics",
                    "description": "Get detailed analytics data",
                    "auth_required": True,
                    "query_params": ["days"]
                },
                {
                    "method": "GET",
                    "path": "/system-health",
                    "description": "Get system health and monitoring info",
                    "auth_required": True
                }
            ]
        },
        "automotive": {
            "base_path": "/api/v1/automotive",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/vehicles",
                    "description": "Search vehicles with advanced filters",
                    "auth_required": False
                },
                {
                    "method": "GET",
                    "path": "/analytics",
                    "description": "Get automotive data analytics",
                    "auth_required": False
                },
                {
                    "method": "GET",
                    "path": "/multi-source-sessions",
                    "description": "Get multi-source scraping sessions",
                    "auth_required": False
                },
                {
                    "method": "GET",
                    "path": "/multi-source-sessions/{session_id}",
                    "description": "Get detailed multi-source session info",
                    "auth_required": False
                },
                {
                    "method": "POST",
                    "path": "/scraper/sources/{source}/scrape",
                    "description": "Trigger scraping from specific source",
                    "auth_required": False
                }
            ]
        },
        "notifications": {
            "base_path": "/api/v1/notifications",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/",
                    "description": "Get user notifications",
                    "auth_required": True
                },
                {
                    "method": "PUT",
                    "path": "/{notification_id}/read",
                    "description": "Mark notification as read",
                    "auth_required": True
                },
                {
                    "method": "POST",
                    "path": "/mark-all-read",
                    "description": "Mark all notifications as read",
                    "auth_required": True
                }
            ]
        },
        "realtime": {
            "base_path": "/api/v1/realtime",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/alerts/stream",
                    "description": "Server-sent events stream for real-time alerts",
                    "auth_required": True
                },
                {
                    "method": "GET",
                    "path": "/vehicles/stream",
                    "description": "Server-sent events stream for new vehicles",
                    "auth_required": False
                }
            ]
        }
    }
    
    return {
        "api_version": "v1",
        "base_url": "/api/v1",
        "authentication": {
            "type": "Bearer Token",
            "header": "Authorization: Bearer <token>",
            "description": "Include JWT token in Authorization header for protected endpoints"
        },
        "endpoints": endpoints,
        "total_endpoints": sum(len(category["endpoints"]) for category in endpoints.values())
    }


@router.get("/schema", response_model=Dict[str, Any])
def get_api_schema():
    """Get API schema information"""
    
    return {
        "openapi_url": "/openapi.json",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "description": "Auto Scouter API provides comprehensive vehicle search and alert functionality",
        "version": "1.0.0",
        "contact": {
            "name": "Auto Scouter API Support",
            "email": "support@autoscouter.com"
        },
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    }


@router.get("/status", response_model=Dict[str, Any])
def get_api_status():
    """Get API status and health information"""
    
    from datetime import datetime
    
    return {
        "status": "operational",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": "Available",
        "services": {
            "database": "operational",
            "scraping": "operational",
            "notifications": "operational",
            "authentication": "operational"
        },
        "features": [
            "Vehicle Search",
            "Advanced Filtering",
            "Price Alerts",
            "Real-time Notifications",
            "Multi-source Scraping",
            "Dashboard Analytics",
            "User Management"
        ]
    }
