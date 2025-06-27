# Automotive Scraper API Documentation

## Overview

The Automotive Scraper API provides comprehensive access to scraped automotive data from GruppoAutoUno.it. The API includes endpoints for searching vehicles, managing scraper operations, monitoring system health, and maintaining data quality.

## Base URL
```
http://localhost:8000/api/v1/automotive
```

## Authentication
Currently, the API does not require authentication. This may be added in future versions for production deployments.

## Vehicle Data Endpoints

### Search Vehicles
**GET** `/vehicles`

Search and filter vehicle listings with pagination support.

**Query Parameters:**
- `make` (string, optional): Vehicle make (e.g., "Volkswagen", "Peugeot")
- `model` (string, optional): Vehicle model
- `year_min` (integer, optional): Minimum year (1900-2030)
- `year_max` (integer, optional): Maximum year (1900-2030)
- `price_min` (float, optional): Minimum price in EUR
- `price_max` (float, optional): Maximum price in EUR
- `mileage_max` (integer, optional): Maximum mileage in km
- `fuel_type` (string, optional): Fuel type ("gasoline", "diesel", "electric", "hybrid")
- `transmission` (string, optional): Transmission type ("manual", "automatic")
- `city` (string, optional): City location
- `page` (integer, default: 1): Page number
- `page_size` (integer, default: 20, max: 100): Items per page

**Example Request:**
```bash
GET /api/v1/automotive/vehicles?make=Volkswagen&fuel_type=diesel&price_max=25000&page=1&page_size=20
```

**Response:**
```json
{
  "vehicles": [
    {
      "id": 1,
      "external_id": "vw-golf-123",
      "listing_url": "https://gruppoautouno.it/usato/volkswagen-golf-123/",
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
      "dealer_name": "Autouno Group",
      "primary_image_url": "https://gruppoautouno.it/images/golf-123.jpg",
      "scraped_at": "2024-01-15T10:30:00Z",
      "is_active": true,
      "images": [],
      "price_history": []
    }
  ],
  "total_count": 156,
  "page": 1,
  "page_size": 20,
  "total_pages": 8,
  "filters_applied": {
    "make": "Volkswagen",
    "fuel_type": "diesel",
    "price_max": 25000.0,
    "is_active": true
  }
}
```

### Get Vehicle Details
**GET** `/vehicles/{vehicle_id}`

Get detailed information about a specific vehicle.

**Path Parameters:**
- `vehicle_id` (integer): Vehicle ID

**Response:**
```json
{
  "id": 1,
  "external_id": "vw-golf-123",
  "listing_url": "https://gruppoautouno.it/usato/volkswagen-golf-123/",
  "make": "Volkswagen",
  "model": "Golf",
  "variant": "Golf 1.6 TDI Comfortline",
  "year": 2020,
  "registration_date": "2020-03-15T00:00:00Z",
  "price": 18500.0,
  "currency": "EUR",
  "mileage": 45000,
  "fuel_type": "diesel",
  "transmission": "manual",
  "engine_displacement": 1598,
  "engine_power_kw": 85,
  "engine_power_hp": 115,
  "doors": 5,
  "seats": 5,
  "condition": "used",
  "city": "Napoli",
  "region": "Campania",
  "country": "IT",
  "dealer_name": "Autouno Group",
  "primary_image_url": "https://gruppoautouno.it/images/golf-123.jpg",
  "description": "Volkswagen Golf in excellent condition...",
  "features": "[\"ABS\", \"ESP\", \"Air Conditioning\", \"Cruise Control\"]",
  "scraped_at": "2024-01-15T10:30:00Z",
  "last_updated": "2024-01-15T10:30:00Z",
  "is_active": true,
  "images": [
    {
      "id": 1,
      "vehicle_id": 1,
      "image_url": "https://gruppoautouno.it/images/golf-123-1.jpg",
      "image_type": "exterior",
      "image_order": 0,
      "alt_text": "Volkswagen Golf exterior view"
    }
  ],
  "price_history": [
    {
      "id": 1,
      "vehicle_id": 1,
      "price": 18500.0,
      "currency": "EUR",
      "recorded_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Get Available Makes
**GET** `/makes`

Get list of available vehicle makes with counts.

**Response:**
```json
[
  {
    "make": "Volkswagen",
    "count": 45
  },
  {
    "make": "Peugeot",
    "count": 32
  },
  {
    "make": "Citroën",
    "count": 28
  }
]
```

### Get Available Models
**GET** `/models`

Get list of available vehicle models, optionally filtered by make.

**Query Parameters:**
- `make` (string, optional): Filter models by make

**Response:**
```json
[
  {
    "make": "Volkswagen",
    "model": "Golf",
    "count": 15
  },
  {
    "make": "Volkswagen",
    "model": "Polo",
    "count": 12
  },
  {
    "make": "Volkswagen",
    "model": "T-Roc",
    "count": 8
  }
]
```

### Get Analytics
**GET** `/analytics`

Get analytics and statistics about the vehicle data.

**Response:**
```json
{
  "data_quality": {
    "total_vehicles": 185,
    "active_vehicles": 178,
    "completeness_scores": {
      "make": 100.0,
      "model": 100.0,
      "price": 98.5,
      "year": 95.2,
      "mileage": 92.1,
      "fuel_type": 89.7
    },
    "average_price": 19750.50,
    "min_price": 5500.0,
    "max_price": 65000.0,
    "overall_completeness": 95.9
  },
  "overview": {
    "totals": {
      "total_vehicles": 185,
      "active_vehicles": 178,
      "recent_additions_24h": 12
    },
    "pricing": {
      "average_price": 19750.50,
      "min_price": 5500.0,
      "max_price": 65000.0
    },
    "top_makes": [
      {"make": "Volkswagen", "count": 45},
      {"make": "Peugeot", "count": 32}
    ],
    "fuel_distribution": [
      {"fuel_type": "diesel", "count": 89},
      {"fuel_type": "gasoline", "count": 67}
    ]
  },
  "timestamp": "2024-01-15T15:30:00Z"
}
```

## Scraper Management Endpoints

### Get Scraper Status
**GET** `/scraper/status`

Get current status of the scraper system.

**Response:**
```json
{
  "scheduler": {
    "scheduler_running": true,
    "current_session_id": null,
    "jobs": [
      {
        "id": "main_scraping_job",
        "name": "Main Automotive Scraping Job",
        "next_run_time": "2024-01-15T20:00:00Z",
        "trigger": "interval[0:08:00:00]"
      }
    ]
  },
  "compliance": {
    "robots_txt": {
      "robots_url": "https://gruppoautouno.it/robots.txt",
      "last_checked": "2024-01-15T10:00:00Z",
      "crawl_delay": null,
      "respect_robots": true
    },
    "rate_limiting": {
      "requests_last_minute": 2,
      "requests_last_hour": 45,
      "minute_limit": 30,
      "hour_limit": 1000,
      "minute_utilization": 6.7,
      "hour_utilization": 4.5
    },
    "blocked_urls": 0,
    "warning_count": 0,
    "compliance_score": 100.0
  },
  "timestamp": "2024-01-15T15:30:00Z"
}
```

### Trigger Manual Scrape
**POST** `/scraper/trigger`

Trigger a manual scraping run.

**Response:**
```json
{
  "message": "Manual scraping job triggered successfully",
  "job_id": "manual_scrape_20240115_153000"
}
```

### Get Scraper Health
**GET** `/scraper/health`

Get comprehensive health check of the scraper system.

**Response:**
```json
{
  "timestamp": "2024-01-15T15:30:00Z",
  "system_health": {
    "uptime_seconds": 86400,
    "system": {
      "cpu_percent": 15.2,
      "memory_percent": 45.8,
      "memory_available_gb": 4.2,
      "disk_percent": 35.1,
      "disk_free_gb": 125.8
    },
    "services": {
      "network": {
        "status": "ok",
        "response_code": 200,
        "response_time_ms": 245.6,
        "target_url": "https://gruppoautouno.it"
      },
      "database": {
        "status": "ok",
        "query_time_ms": 12.3,
        "total_vehicles": 185
      }
    },
    "overall_status": "healthy"
  },
  "scraping_metrics_24h": {
    "period_hours": 24,
    "sessions": {
      "total": 3,
      "successful": 3,
      "failed": 0,
      "success_rate": 100.0
    },
    "vehicles": {
      "total_found": 185,
      "new": 12,
      "updated": 8,
      "errors": 2
    },
    "performance": {
      "average_response_time_ms": 1250.5,
      "total_requests": 195,
      "error_rate_percent": 1.0
    }
  },
  "alerts": []
}
```

### Get Scraping Sessions
**GET** `/scraper/sessions`

Get recent scraping sessions.

**Query Parameters:**
- `limit` (integer, default: 10, max: 100): Number of sessions to return

### Get Scraping Logs
**GET** `/scraper/logs`

Get scraping logs with optional filters.

**Query Parameters:**
- `session_id` (string, optional): Filter by session ID
- `status` (string, optional): Filter by status ("success", "error")
- `limit` (integer, default: 50, max: 200): Number of logs to return

### Get Compliance Info
**GET** `/scraper/compliance`

Get compliance and ethical guidelines information.

## Data Management Endpoints

### Run Data Cleanup
**POST** `/maintenance/cleanup`

Run data cleanup and maintenance tasks.

**Query Parameters:**
- `retention_days` (integer, default: 365, range: 30-1095): Data retention period in days

### Get Data Quality Report
**GET** `/maintenance/quality`

Get detailed data quality report.

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid parameter value"
}
```

### 404 Not Found
```json
{
  "detail": "Vehicle not found"
}
```

### 409 Conflict
```json
{
  "detail": "Scraping session already in progress"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error message describing the issue"
}
```

## Rate Limiting

The API implements rate limiting to ensure fair usage:
- **Per minute**: 100 requests
- **Per hour**: 5000 requests

When rate limits are exceeded, the API returns a 429 status code.

## Data Freshness

- Vehicle data is updated every 8 hours by default
- The `scraped_at` and `last_updated` fields indicate data freshness
- Inactive listings are automatically marked after 30 days without updates

## Interactive Documentation

When the backend is running, you can access interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
