# 🔌 Auto Scouter API Guide

This document provides comprehensive information about the Auto Scouter REST API, including authentication, endpoints, request/response formats, and usage examples.

## 🌐 Base URL

**Production**: `https://auto-scouter-backend-production.up.railway.app/api/v1`
**Local Development**: `http://localhost:8000/api/v1`

## 🔐 Authentication

Auto Scouter uses JWT (JSON Web Token) based authentication. All protected endpoints require a valid JWT token in the Authorization header.

### Authentication Flow

1. **Register** a new user account
2. **Login** to receive a JWT access token
3. **Include token** in subsequent requests
4. **Refresh token** when it expires

### Token Format

```http
Authorization: Bearer <your-jwt-token>
```

### Token Expiration

- **Access Token**: 24 hours (configurable)
- **Refresh Token**: 7 days (configurable)

## 📋 API Endpoints

### 🔑 Authentication Endpoints

#### Register User

Create a new user account.

```http
POST /auth/register
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data
- `409 Conflict`: Email already registered

#### Login

Authenticate user and receive JWT tokens.

```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded
```

**Request Body:**
```
username=user@example.com&password=securepassword123
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `400 Bad Request`: Missing username or password

#### Get Current User

Retrieve information about the authenticated user.

```http
GET /auth/me
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-15T14:20:00Z"
}
```

#### Refresh Token

Get a new access token using a refresh token.

```http
POST /auth/refresh
Authorization: Bearer <refresh_token>
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 🚗 Vehicle Endpoints

#### List Vehicles

Retrieve a paginated list of vehicles with optional filtering.

```http
GET /vehicles?skip=0&limit=20&make=BMW&min_price=10000&max_price=50000
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum number of records to return (default: 20, max: 100)
- `make` (string): Filter by vehicle make
- `model` (string): Filter by vehicle model
- `min_price` (int): Minimum price filter
- `max_price` (int): Maximum price filter
- `min_year` (int): Minimum year filter
- `max_year` (int): Maximum year filter
- `max_mileage` (int): Maximum mileage filter
- `fuel_type` (string): Filter by fuel type
- `transmission` (string): Filter by transmission type
- `location` (string): Filter by location

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": 1,
      "title": "BMW 3 Series 320d",
      "make": "BMW",
      "model": "3 Series",
      "year": 2020,
      "price": 25000,
      "mileage": 45000,
      "fuel_type": "Diesel",
      "transmission": "Automatic",
      "location": "Berlin",
      "description": "Well maintained BMW 3 Series...",
      "images": ["https://example.com/image1.jpg"],
      "source_url": "https://autoscout24.de/listing/123",
      "scraped_at": "2024-01-15T12:00:00Z",
      "is_available": true
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 20,
  "has_more": true
}
```

#### Get Vehicle Details

Retrieve detailed information about a specific vehicle.

```http
GET /vehicles/{vehicle_id}
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "BMW 3 Series 320d",
  "make": "BMW",
  "model": "3 Series",
  "year": 2020,
  "price": 25000,
  "mileage": 45000,
  "fuel_type": "Diesel",
  "transmission": "Automatic",
  "location": "Berlin",
  "description": "Well maintained BMW 3 Series with full service history...",
  "images": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg"
  ],
  "specifications": {
    "engine_size": "2.0L",
    "power": "190 HP",
    "doors": 4,
    "seats": 5,
    "color": "Black"
  },
  "source_url": "https://autoscout24.de/listing/123",
  "scraped_at": "2024-01-15T12:00:00Z",
  "updated_at": "2024-01-15T12:00:00Z",
  "is_available": true
}
```

**Error Responses:**
- `404 Not Found`: Vehicle not found

#### Advanced Vehicle Search

Perform advanced search with complex filtering criteria.

```http
POST /vehicles/search
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "filters": {
    "make": ["BMW", "Audi"],
    "model": ["3 Series", "A4"],
    "price_range": {
      "min": 15000,
      "max": 40000
    },
    "year_range": {
      "min": 2018,
      "max": 2023
    },
    "mileage_max": 80000,
    "fuel_types": ["Diesel", "Petrol"],
    "transmissions": ["Automatic"],
    "locations": ["Berlin", "Munich"]
  },
  "sort": {
    "field": "price",
    "order": "asc"
  },
  "pagination": {
    "skip": 0,
    "limit": 20
  }
}
```

**Response**: Same format as List Vehicles endpoint

### 🔔 Alert Endpoints

#### List User Alerts

Retrieve all alerts created by the authenticated user.

```http
GET /alerts
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": 1,
      "name": "BMW 3 Series Alert",
      "make": "BMW",
      "model": "3 Series",
      "min_price": 15000,
      "max_price": 35000,
      "max_mileage": 100000,
      "min_year": 2018,
      "fuel_type": "Diesel",
      "transmission": "Automatic",
      "location": "Berlin",
      "is_active": true,
      "created_at": "2024-01-15T10:00:00Z",
      "last_triggered": "2024-01-15T14:30:00Z",
      "match_count": 5
    }
  ],
  "total": 3
}
```

#### Create Alert

Create a new vehicle alert with specified criteria.

```http
POST /alerts
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "BMW 3 Series Alert",
  "make": "BMW",
  "model": "3 Series",
  "min_price": 15000,
  "max_price": 35000,
  "max_mileage": 100000,
  "min_year": 2018,
  "fuel_type": "Diesel",
  "transmission": "Automatic",
  "location": "Berlin"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "name": "BMW 3 Series Alert",
  "make": "BMW",
  "model": "3 Series",
  "min_price": 15000,
  "max_price": 35000,
  "max_mileage": 100000,
  "min_year": 2018,
  "fuel_type": "Diesel",
  "transmission": "Automatic",
  "location": "Berlin",
  "is_active": true,
  "created_at": "2024-01-15T10:00:00Z",
  "user_id": 1
}
```

#### Update Alert

Update an existing alert.

```http
PUT /alerts/{alert_id}
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Updated BMW Alert",
  "max_price": 40000,
  "is_active": false
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Updated BMW Alert",
  "make": "BMW",
  "model": "3 Series",
  "min_price": 15000,
  "max_price": 40000,
  "max_mileage": 100000,
  "min_year": 2018,
  "fuel_type": "Diesel",
  "transmission": "Automatic",
  "location": "Berlin",
  "is_active": false,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T16:00:00Z",
  "user_id": 1
}
```

#### Delete Alert

Delete an alert.

```http
DELETE /alerts/{alert_id}
Authorization: Bearer <access_token>
```

**Response (204 No Content)**

#### Test Alert

Test an alert against current vehicle listings.

```http
POST /alerts/{alert_id}/test
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "alert_id": 1,
  "matches": [
    {
      "vehicle_id": 123,
      "title": "BMW 3 Series 320d",
      "price": 28000,
      "match_score": 0.95
    }
  ],
  "total_matches": 1,
  "tested_at": "2024-01-15T16:30:00Z"
}
```

### 📊 System Endpoints

#### Health Check

Check the health status of the API.

```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "environment": "production",
  "database_url": "configured",
  "timestamp": "2024-01-15T16:45:00Z",
  "version": "1.0.0"
}
```

#### System Status

Get detailed system status information (requires authentication).

```http
GET /system/status
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "status": "operational",
  "database": {
    "status": "connected",
    "total_vehicles": 1250,
    "last_scrape": "2024-01-15T16:00:00Z"
  },
  "scraping": {
    "status": "active",
    "last_run": "2024-01-15T16:00:00Z",
    "next_run": "2024-01-15T16:05:00Z",
    "success_rate": 0.98
  },
  "alerts": {
    "total_active": 45,
    "last_processed": "2024-01-15T16:00:00Z"
  }
}
```

### 📱 Real-time Endpoints

#### WebSocket Connection

Connect to real-time updates via WebSocket.

```
WSS /ws
Authorization: Bearer <access_token>
```

**Message Types:**
- `vehicle_update`: New vehicle listings
- `alert_match`: Alert matches found
- `system_status`: System status updates

**Example Message:**
```json
{
  "type": "vehicle_update",
  "data": {
    "vehicle_id": 123,
    "action": "created",
    "vehicle": { /* vehicle object */ }
  },
  "timestamp": "2024-01-15T16:50:00Z"
}
```

## 📝 Request/Response Format

### Content Types

- **Request**: `application/json` (except login: `application/x-www-form-urlencoded`)
- **Response**: `application/json`

### Standard Response Structure

**Success Response:**
```json
{
  "data": { /* response data */ },
  "message": "Success",
  "timestamp": "2024-01-15T16:00:00Z"
}
```

**Error Response:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
  },
  "timestamp": "2024-01-15T16:00:00Z"
}
```

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `204 No Content`: Request successful, no content returned
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required or invalid
- `403 Forbidden`: Access denied
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource already exists
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## 🔧 Usage Examples

### Python Example

```python
import requests

# Base URL
BASE_URL = "https://auto-scouter-backend-production.up.railway.app/api/v1"

# Login
login_data = {
    "username": "user@example.com",
    "password": "password123"
}
response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
token = response.json()["access_token"]

# Headers for authenticated requests
headers = {"Authorization": f"Bearer {token}"}

# Get vehicles
vehicles = requests.get(f"{BASE_URL}/vehicles", headers=headers)
print(vehicles.json())

# Create alert
alert_data = {
    "name": "BMW Alert",
    "make": "BMW",
    "max_price": 30000
}
alert = requests.post(f"{BASE_URL}/alerts", json=alert_data, headers=headers)
print(alert.json())
```

### JavaScript Example

```javascript
const BASE_URL = 'https://auto-scouter-backend-production.up.railway.app/api/v1';

// Login
const login = async (email, password) => {
  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `username=${email}&password=${password}`
  });
  const data = await response.json();
  return data.access_token;
};

// Get vehicles
const getVehicles = async (token) => {
  const response = await fetch(`${BASE_URL}/vehicles`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
};

// Usage
const token = await login('user@example.com', 'password123');
const vehicles = await getVehicles(token);
console.log(vehicles);
```

### cURL Examples

```bash
# Login
curl -X POST "https://auto-scouter-backend-production.up.railway.app/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"

# Get vehicles (replace TOKEN with actual token)
curl -X GET "https://auto-scouter-backend-production.up.railway.app/api/v1/vehicles" \
  -H "Authorization: Bearer TOKEN"

# Create alert
curl -X POST "https://auto-scouter-backend-production.up.railway.app/api/v1/alerts" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"BMW Alert","make":"BMW","max_price":30000}'
```

## 🚨 Error Handling

### Common Error Codes

- `AUTH_REQUIRED`: Authentication token required
- `AUTH_INVALID`: Invalid or expired token
- `VALIDATION_ERROR`: Request validation failed
- `RESOURCE_NOT_FOUND`: Requested resource not found
- `PERMISSION_DENIED`: Insufficient permissions
- `RATE_LIMIT_EXCEEDED`: Too many requests

### Best Practices

1. **Always check HTTP status codes**
2. **Handle authentication errors gracefully**
3. **Implement retry logic for transient errors**
4. **Validate input data before sending requests**
5. **Use appropriate timeouts for requests**

## 📚 Interactive Documentation

Visit the interactive API documentation at:
- **Swagger UI**: https://auto-scouter-backend-production.up.railway.app/docs
- **ReDoc**: https://auto-scouter-backend-production.up.railway.app/redoc

These interfaces allow you to:
- Explore all available endpoints
- Test API calls directly in the browser
- View detailed request/response schemas
- Download OpenAPI specification

---

**For more information, visit the [main documentation](README.md) or check the [deployment guide](DEPLOYMENT.md).**
