# Auto Scouter API Documentation

## Overview

The Auto Scouter API provides comprehensive endpoints for automotive data access, user authentication, and alert management. All endpoints follow REST conventions and return JSON responses.

**Base URL**: `http://localhost:8000/api/v1`

## Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Authentication Endpoints

#### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "username": "string (3-50 chars)",
  "email": "valid_email@example.com",
  "password": "string (8+ chars, must include uppercase, lowercase, digit)"
}
```

**Response (201):**
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### POST /auth/login
Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "username": "testuser",  // or email
  "password": "password123"
}
```

**Response (200):**
```json
{
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "is_active": true
  },
  "token": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

#### GET /auth/me
Get current user profile with alerts.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "is_active": true,
  "alerts": [
    {
      "id": 1,
      "make": "Volkswagen",
      "model": "Golf",
      "min_price": 15000,
      "max_price": 25000,
      "is_active": true,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

## Car Listings

### GET /cars
Retrieve cars with filtering and pagination.

**Query Parameters:**
- `make` (string): Filter by car manufacturer
- `model` (string): Filter by car model  
- `min_price` (integer): Minimum price filter (EUR)
- `max_price` (integer): Maximum price filter (EUR)
- `year` (integer): Filter by year (1900-2030)
- `limit` (integer, default 50): Number of results (1-100)
- `offset` (integer, default 0): Pagination offset

**Example Request:**
```
GET /api/v1/cars?make=Volkswagen&min_price=15000&max_price=25000&limit=20&offset=0
```

**Response (200):**
```json
{
  "cars": [
    {
      "id": 1,
      "make": "Volkswagen",
      "model": "Golf",
      "year": 2020,
      "price": 18500.0,
      "mileage": 45000,
      "fuel_type": "diesel",
      "transmission": "manual",
      "city": "Napoli",
      "listing_url": "https://example.com/car1",
      "scraped_at": "2024-01-01T12:00:00Z",
      "is_active": true
    }
  ],
  "pagination": {
    "total_count": 150,
    "total_pages": 8,
    "current_page": 1,
    "limit": 20,
    "offset": 0,
    "has_next": true,
    "has_previous": false
  },
  "filters_applied": {
    "make": "Volkswagen",
    "min_price": 15000,
    "max_price": 25000
  }
}
```

### GET /cars/new
Retrieve recently added cars (last 24-48 hours).

**Query Parameters:**
- Same filtering options as `/cars`
- `hours` (integer, default 48): Hours to look back (1-168)

**Example Request:**
```
GET /api/v1/cars/new?hours=24&make=BMW
```

**Response (200):**
```json
{
  "cars": [...],
  "pagination": {...},
  "filters_applied": {
    "make": "BMW",
    "hours_back": 24,
    "cutoff_time": "2024-01-01T12:00:00Z"
  },
  "metadata": {
    "endpoint": "new_cars",
    "description": "Cars added in the last 24 hours"
  }
}
```

### GET /cars/{car_id}
Get detailed information about a specific car.

**Response (200):**
```json
{
  "id": 1,
  "make": "Volkswagen",
  "model": "Golf",
  "variant": "Golf 1.6 TDI Comfortline",
  "year": 2020,
  "price": 18500.0,
  "mileage": 45000,
  "fuel_type": "diesel",
  "transmission": "manual",
  "engine_displacement": 1598,
  "engine_power_kw": 85,
  "doors": 5,
  "seats": 5,
  "city": "Napoli",
  "dealer_name": "Autouno Group",
  "listing_url": "https://example.com/car1",
  "primary_image_url": "https://example.com/image1.jpg",
  "description": "Excellent condition...",
  "scraped_at": "2024-01-01T12:00:00Z",
  "images": [
    {
      "id": 1,
      "image_url": "https://example.com/image1.jpg",
      "image_type": "exterior",
      "image_order": 0
    }
  ]
}
```

### GET /cars/stats/summary
Get summary statistics about available cars.

**Response (200):**
```json
{
  "total_active_cars": 1250,
  "price_statistics": {
    "min_price": 5000.0,
    "max_price": 85000.0,
    "average_price": 22500.0
  },
  "top_makes": [
    {"make": "Volkswagen", "count": 180},
    {"make": "BMW", "count": 150},
    {"make": "Audi", "count": 120}
  ],
  "recent_additions_24h": 45,
  "last_updated": "2024-01-01T12:00:00Z"
}
```

## Alert Management

### POST /alerts
Create a new price/availability alert.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "make": "Volkswagen",
  "model": "Golf",
  "min_price": 15000,
  "max_price": 25000,
  "year": 2020,
  "fuel_type": "diesel",
  "transmission": "manual",
  "city": "Napoli"
}
```

**Response (201):**
```json
{
  "id": 1,
  "user_id": 1,
  "make": "Volkswagen",
  "model": "Golf",
  "min_price": 15000,
  "max_price": 25000,
  "year": 2020,
  "fuel_type": "diesel",
  "transmission": "manual",
  "city": "Napoli",
  "is_active": true,
  "created_at": "2024-01-01T12:00:00Z"
}
```

### GET /alerts
List all user alerts.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `active_only` (boolean, default true): Return only active alerts

**Response (200):**
```json
[
  {
    "id": 1,
    "make": "Volkswagen",
    "model": "Golf",
    "min_price": 15000,
    "max_price": 25000,
    "is_active": true,
    "created_at": "2024-01-01T12:00:00Z"
  }
]
```

### DELETE /alerts/{alert_id}
Remove a specific alert by ID.

**Headers:** `Authorization: Bearer <token>`

**Response (204):** No content

### GET /alerts/stats/summary
Get alert statistics for the current user.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "total_alerts": 5,
  "active_alerts": 3,
  "inactive_alerts": 2
}
```

## Error Responses

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

API requests are rate-limited to:
- 100 requests per minute for authenticated users
- 20 requests per minute for unauthenticated users

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

## Interactive Documentation

When the server is running, you can access interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
