# Backend Router Documentation

## Overview

This document describes the FastAPI router structure and recent consolidation changes made to resolve duplicate endpoint conflicts and improve API organization.

## Router Structure

### Active Routers (Currently Registered)

#### Authentication & User Management
- **`auth.py`** - User authentication endpoints
  - `POST /auth/register` - User registration
  - `POST /auth/login` - User login (returns JWT token)
  - `GET /auth/me` - Get current user information (protected)

#### Core Vehicle Features
- **`automotive.py`** - Vehicle data and scraping endpoints
  - `GET /api/v1/automotive/vehicles` - Search vehicles with filters
  - `POST /api/v1/automotive/scraper/trigger` - Trigger manual scraping
  - `GET /api/v1/automotive/scraper/status` - Get scraper status

#### Enhanced Alert System
- **`enhanced_alerts.py`** - Complete alert management (ACTIVE)
  - `GET /api/v1/alerts/` - Get user alerts with pagination
  - `POST /api/v1/alerts/` - Create new alert
  - `PUT /api/v1/alerts/{id}` - Update existing alert
  - `DELETE /api/v1/alerts/{id}` - Delete alert
  - `POST /api/v1/alerts/{id}/test` - Test alert against current listings
  - `POST /api/v1/alerts/{id}/toggle` - Toggle alert active status

#### Enhanced Notification System
- **`enhanced_notifications.py`** - Complete notification management (ACTIVE)
  - `GET /api/v1/notifications/` - Get user notifications with pagination
  - `POST /api/v1/notifications/{id}/read` - Mark notification as read
  - `DELETE /api/v1/notifications/{id}` - Delete notification

#### Real-time Features
- **`realtime.py`** - Server-Sent Events and WebSocket endpoints
  - `GET /api/v1/realtime/sse/system-status` - Real-time system status
  - `GET /api/v1/realtime/sse/vehicle-matches` - Real-time vehicle matches
  - `GET /api/v1/realtime/notifications` - Get unread notifications

#### System Management
- **`dashboard.py`** - Dashboard and analytics endpoints
  - `GET /api/v1/dashboard/overview` - Dashboard overview data
  - `GET /api/v1/dashboard/metrics` - System metrics

- **`monitoring.py`** - System monitoring and health checks
  - `GET /api/v1/monitoring/health` - Health check endpoint
  - `GET /api/v1/monitoring/metrics` - System performance metrics

- **`search.py`** - Advanced search functionality
  - `GET /api/v1/search/filters` - Get available search filters
  - `POST /api/v1/search/advanced` - Advanced vehicle search

#### Additional Features
- **`admin.py`** - Administrative endpoints (protected)
- **`api_docs.py`** - API documentation endpoints
- **`webhooks.py`** - Webhook management
- **`cars.py`** - Car-specific data endpoints
- **`scouts.py`** - Scout management
- **`teams.py`** - Team management
- **`matches.py`** - Match tracking

### Deprecated Routers (Removed from Registration)

#### Legacy Alert System
- **`alerts.py`** - Old alert system (DEPRECATED)
  - **Status**: Router file exists but is NOT registered in main.py
  - **Reason**: Replaced by enhanced_alerts.py with better schema and functionality
  - **Migration**: All functionality moved to enhanced_alerts.py

#### Legacy Notification System
- **`notifications.py`** - Old notification system (DEPRECATED)
  - **Status**: Router file exists but is NOT registered in main.py
  - **Reason**: Replaced by enhanced_notifications.py with pagination and better features
  - **Migration**: All functionality moved to enhanced_notifications.py

## Recent Changes and Fixes

### 1. Duplicate Router Resolution

#### Problem
- Both `alerts.py` and `enhanced_alerts.py` were registered with the same prefix `/api/v1/alerts`
- Both `notifications.py` and `enhanced_notifications.py` were registered with the same prefix `/api/v1/notifications`
- This caused endpoint conflicts and unpredictable behavior

#### Solution
- Removed duplicate router registrations from `backend/app/main.py`
- Only enhanced versions are now registered:
  ```python
  # REMOVED (old routers)
  # app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
  # app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
  
  # ACTIVE (enhanced routers)
  app.include_router(enhanced_alerts.router, prefix="/api/v1/alerts", tags=["enhanced-alerts"])
  app.include_router(enhanced_notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
  ```

### 2. Schema Consolidation

#### Alert Schema Issues
- **Problem**: Old alerts router used incorrect field names (`year` instead of `min_year`/`max_year`)
- **Solution**: Updated old alerts router to use enhanced schema before deprecation
- **Current State**: Enhanced alerts router uses correct schema with proper field validation

#### Pydantic Serialization Fixes
- **Problem**: SQLAlchemy models couldn't be directly serialized by Pydantic
- **Solution**: Implemented manual model-to-dictionary conversion with proper datetime handling
- **Implementation**:
  ```python
  def serialize_alert(alert):
      return {
          "id": alert.id,
          "user_id": alert.user_id,
          "name": alert.name,
          "created_at": alert.created_at.isoformat() if alert.created_at else None,
          "updated_at": alert.updated_at.isoformat() if alert.updated_at else None,
          # ... other fields
      }
  ```

### 3. Authentication Integration

#### JWT Token Validation
- All enhanced routers now properly integrate with JWT authentication
- Protected endpoints require valid Bearer tokens
- User context is automatically injected into request handlers

#### Error Handling
- Standardized authentication error responses
- Proper 401 Unauthorized responses for missing/invalid tokens
- Consistent error message format across all endpoints

## Current Router Registration

### Main Application (`backend/app/main.py`)

```python
from app.routers import (
    scouts, teams, matches, automotive, auth, cars, admin,
    enhanced_notifications, enhanced_alerts, webhooks, 
    realtime, monitoring, dashboard, search, api_docs
)

# Authentication routes
app.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Core vehicle features
app.include_router(automotive.router, prefix="/api/v1/automotive", tags=["automotive"])

# Enhanced systems (ACTIVE)
app.include_router(enhanced_alerts.router, prefix="/api/v1/alerts", tags=["enhanced-alerts"])
app.include_router(enhanced_notifications.router, prefix="/api/v1/notifications", tags=["notifications"])

# Real-time features
app.include_router(realtime.router, prefix="/api/v1/realtime", tags=["realtime"])

# System management
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["monitoring"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])

# Additional features
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(api_docs.router, prefix="/api/v1/docs", tags=["documentation"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(cars.router, prefix="/api/v1/cars", tags=["cars"])
app.include_router(scouts.router, prefix="/api/v1/scouts", tags=["scouts"])
app.include_router(teams.router, prefix="/api/v1/teams", tags=["teams"])
app.include_router(matches.router, prefix="/api/v1/matches", tags=["matches"])
```

## API Endpoint Summary

### Public Endpoints (No Authentication Required)
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /health` - Health check
- `GET /api/v1/system/status` - System status

### Protected Endpoints (JWT Token Required)

#### Alert Management
- `GET /api/v1/alerts/` - List user alerts
- `POST /api/v1/alerts/` - Create alert
- `PUT /api/v1/alerts/{id}` - Update alert
- `DELETE /api/v1/alerts/{id}` - Delete alert
- `POST /api/v1/alerts/{id}/test` - Test alert
- `POST /api/v1/alerts/{id}/toggle` - Toggle alert

#### Notification Management
- `GET /api/v1/notifications/` - List user notifications
- `POST /api/v1/notifications/{id}/read` - Mark as read
- `DELETE /api/v1/notifications/{id}` - Delete notification

#### Vehicle Operations
- `GET /api/v1/automotive/vehicles` - Search vehicles
- `POST /api/v1/automotive/scraper/trigger` - Trigger scraping
- `GET /api/v1/automotive/scraper/status` - Scraper status

#### Real-time Features
- `GET /api/v1/realtime/sse/system-status` - SSE system status
- `GET /api/v1/realtime/sse/vehicle-matches` - SSE vehicle matches
- `GET /api/v1/realtime/notifications` - Unread notifications

## Testing Router Endpoints

### Authentication Flow
```bash
# 1. Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'

# 2. Login to get token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'

# 3. Use token for protected endpoints
curl -X GET http://localhost:8000/api/v1/alerts/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Alert Management Testing
```bash
# Create alert
curl -X POST http://localhost:8000/api/v1/alerts/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"name": "Test Alert", "make": "BMW", "max_price": 30000}'

# Test alert
curl -X POST http://localhost:8000/api/v1/alerts/1/test \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"test_days": 7, "max_listings": 100}'
```

## Troubleshooting

### Common Router Issues

#### 404 Not Found
- **Check**: Ensure router is registered in main.py
- **Verify**: Correct prefix and endpoint path
- **Solution**: Review router registration and URL construction

#### 401 Unauthorized
- **Check**: JWT token is included in Authorization header
- **Verify**: Token format is `Bearer <token>`
- **Solution**: Re-authenticate to get valid token

#### 422 Validation Error
- **Check**: Request body matches expected schema
- **Verify**: Required fields are included
- **Solution**: Review API documentation for correct request format

#### Internal Server Error (500)
- **Check**: Backend logs for detailed error information
- **Common Causes**: Database connection issues, schema mismatches
- **Solution**: Review server logs and fix underlying issues

## Future Router Improvements

### Planned Enhancements
- [ ] API versioning strategy (v2, v3, etc.)
- [ ] Rate limiting middleware for all routers
- [ ] Comprehensive request/response logging
- [ ] Router-level caching for performance
- [ ] OpenAPI schema validation middleware
- [ ] Automated router testing framework

### Code Organization
- [ ] Router grouping by feature domain
- [ ] Shared middleware extraction
- [ ] Common response model standardization
- [ ] Router dependency injection improvements
