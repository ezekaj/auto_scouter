# Vehicle Scout API Documentation

## Overview

The Vehicle Scout API provides comprehensive endpoints for vehicle search, real-time updates, and system monitoring. Built with FastAPI, it offers automatic OpenAPI documentation and high-performance async operations.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication

Currently, the API supports basic authentication for protected endpoints. Future versions will include JWT-based authentication.

## Core Endpoints

### Health & System Status

#### GET /health
Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-01T10:00:00Z"
}
```

#### GET /api/v1/system/status
Comprehensive system status including component health.

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "api": "running",
    "database": "connected",
    "redis": "disconnected",
    "celery": "unknown",
    "notification_system": "inactive"
  },
  "version": "1.0.0"
}
```

### Vehicle Search

#### GET /api/v1/automotive/vehicles
Search vehicles with advanced filtering options.

**Query Parameters:**
- `make` (string): Vehicle manufacturer
- `model` (string): Vehicle model
- `year_min` (integer): Minimum year
- `year_max` (integer): Maximum year
- `price_min` (float): Minimum price
- `price_max` (float): Maximum price
- `mileage_max` (integer): Maximum mileage
- `fuel_type` (string): Fuel type (gasoline, diesel, electric, hybrid)
- `transmission` (string): Transmission type (manual, automatic)
- `body_type` (string): Body type (sedan, hatchback, suv, etc.)
- `city` (string): City location
- `region` (string): Region/state
- `page` (integer): Page number (default: 1)
- `page_size` (integer): Items per page (default: 20)
- `sort_by` (string): Sort field
- `sort_order` (string): Sort order (asc, desc)

**Response:**
```json
{
  "vehicles": [
    {
      "id": 1,
      "external_id": "vw-golf-123",
      "make": "Volkswagen",
      "model": "Golf",
      "variant": "Golf 1.6 TDI Comfortline",
      "year": 2020,
      "price": 18500.0,
      "currency": "EUR",
      "mileage": 45000,
      "fuel_type": "diesel",
      "transmission": "manual",
      "doors": 5,
      "seats": 5,
      "city": "Napoli",
      "region": "Campania",
      "country": "IT",
      "listing_url": "https://gruppoautouno.it/usato/vw-golf-123/",
      "image_urls": ["https://example.com/image1.jpg"],
      "dealer_name": "Autouno Group",
      "source_website": "gruppoautouno.it",
      "scraped_at": "2025-07-01T10:00:00Z",
      "is_active": true
    }
  ],
  "total_count": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "filters_applied": {
    "make": null,
    "model": null,
    "year_min": null,
    "year_max": null,
    "price_min": null,
    "price_max": null,
    "mileage_max": null,
    "fuel_type": null,
    "transmission": null,
    "body_type": null,
    "condition": null,
    "city": null,
    "region": null,
    "is_active": true
  }
}
```

#### GET /api/v1/automotive/makes
Get list of available vehicle makes.

**Response:**
```json
["Volkswagen", "Peugeot", "BMW", "Mercedes-Benz", "Audi"]
```

#### GET /api/v1/automotive/models/{make}
Get models for a specific make.

**Response:**
```json
["Golf", "Polo", "Passat", "Tiguan"]
```

### Search Filters

#### GET /api/v1/search/filters
Get all available search filter options.

**Response:**
```json
{
  "makes": ["Volkswagen", "Peugeot", "BMW"],
  "fuel_types": ["gasoline", "diesel", "electric", "hybrid"],
  "transmissions": ["manual", "automatic"],
  "body_types": ["sedan", "hatchback", "suv", "coupe"],
  "cities": ["Napoli", "Roma", "Milano"],
  "sources": ["gruppoautouno.it"],
  "price_range": {
    "min": 5000,
    "max": 100000
  },
  "year_range": {
    "min": 1990,
    "max": 2025
  },
  "conditions": ["new", "used", "demo"],
  "sort_options": [
    {"field": "scraped_at", "label": "Date Added"},
    {"field": "price", "label": "Price"},
    {"field": "year", "label": "Year"},
    {"field": "mileage", "label": "Mileage"}
  ],
  "timestamp": "2025-07-01T10:00:00Z"
}
```

### Web Scraping

#### POST /api/v1/automotive/scraper/trigger
Manually trigger a scraping job.

**Request Body:**
```json
{
  "source": "gruppoautouno.it",
  "priority": "high"
}
```

**Response:**
```json
{
  "message": "Scraping job triggered successfully",
  "job_id": "scrape-123456",
  "status": "queued",
  "timestamp": "2025-07-01T10:00:00Z"
}
```

#### GET /api/v1/automotive/scraper/status/{job_id}
Get status of a specific scraping job.

**Response:**
```json
{
  "job_id": "scrape-123456",
  "status": "completed",
  "started_at": "2025-07-01T10:00:00Z",
  "completed_at": "2025-07-01T10:05:00Z",
  "vehicles_scraped": 150,
  "errors": 0
}
```

### Real-time Updates (Server-Sent Events)

#### GET /api/v1/realtime/sse/system-status
Real-time system status updates via Server-Sent Events.

**Response Stream:**
```
data: {"type": "connected", "timestamp": "2025-07-01T10:00:00Z"}

data: {"type": "system_status", "data": {"timestamp": "2025-07-01T10:00:00Z", "vehicles_last_hour": 25, "active_alerts": 5, "notifications_last_hour": 3, "total_active_vehicles": 1250, "system_health": "healthy"}}
```

#### GET /api/v1/realtime/sse/vehicle-matches
Real-time vehicle match notifications via Server-Sent Events.

**Response Stream:**
```
data: {"type": "connected", "timestamp": "2025-07-01T10:00:00Z"}

data: {"type": "vehicle_match", "data": {"vehicle_id": 123, "alert_id": 456, "match_score": 0.95, "vehicle": {...}}}
```

## Error Handling

The API uses standard HTTP status codes and returns detailed error information:

```json
{
  "detail": "Vehicle not found",
  "status_code": 404,
  "timestamp": "2025-07-01T10:00:00Z"
}
```

## Rate Limiting

- **Default**: 100 requests per minute per IP
- **Authenticated**: 1000 requests per minute per user
- **Scraper endpoints**: 10 requests per minute per IP

## Interactive Documentation

When the backend is running, access interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
