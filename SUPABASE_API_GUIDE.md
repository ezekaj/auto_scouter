# 🔌 Auto Scouter Supabase API Guide

This guide provides comprehensive documentation for the Auto Scouter Supabase API endpoints, Edge Functions, and real-time features.

## 🌐 Base URLs

```
Supabase Project: https://rwonkzncpzirokqnuoyx.supabase.co
Vehicle API: https://rwonkzncpzirokqnuoyx.supabase.co/functions/v1/vehicle-api
Scraper API: https://rwonkzncpzirokqnuoyx.supabase.co/functions/v1/vehicle-scraper
Scheduled Scraper: https://rwonkzncpzirokqnuoyx.supabase.co/functions/v1/scheduled-scraper
Database: Direct Supabase client connection
Real-time: WebSocket via Supabase real-time
```

## 🔐 Authentication

Auto Scouter uses Supabase's built-in authentication system with anonymous access for single-user deployment.

### Headers Required
```http
Authorization: Bearer YOUR_SUPABASE_ANON_KEY
apikey: YOUR_SUPABASE_ANON_KEY
Content-Type: application/json
```

## 📊 Response Format

All Edge Function responses follow a consistent JSON format:

```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully",
  "timestamp": "2025-07-12T10:30:00Z",
  "source": "supabase-edge-function"
}
```

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {}
  },
  "timestamp": "2025-07-12T10:30:00Z",
  "source": "supabase-edge-function"
}
```

## 🚗 Vehicle API Endpoints

### Search Vehicles
**Endpoint**: `POST /functions/v1/vehicle-api`
**Body**: 
```json
{
  "action": "search",
  "filters": {
    "make": "BMW",
    "model": "X3",
    "min_price": 20000,
    "max_price": 50000,
    "min_year": 2018,
    "max_year": 2023,
    "max_mileage": 100000,
    "fuel_type": "diesel",
    "transmission": "automatic",
    "body_type": "suv",
    "city": "Rome",
    "limit": 20,
    "offset": 0
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "vehicles": [
      {
        "id": 1,
        "make": "BMW",
        "model": "X3",
        "year": 2020,
        "price": 35000,
        "mileage": 45000,
        "fuel_type": "diesel",
        "transmission": "automatic",
        "body_type": "suv",
        "city": "Rome",
        "url": "https://carmarket.ayvens.com/vehicle/123",
        "source_website": "carmarket.ayvens.com",
        "primary_image_url": "https://example.com/image.jpg",
        "created_at": "2025-07-12T10:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "limit": 20
  }
}
```

### Get Statistics
**Endpoint**: `POST /functions/v1/vehicle-api`
**Body**: 
```json
{
  "action": "stats"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "total_vehicles": 1250,
    "total_alerts": 15,
    "total_favorites": 8,
    "vehicles_today": 45,
    "last_scrape": "2025-07-12T09:30:00Z",
    "active_sessions": 0
  }
}
```

### Create Alert
**Endpoint**: `POST /functions/v1/vehicle-api`
**Body**: 
```json
{
  "action": "create_alert",
  "alert": {
    "name": "BMW X3 Alert",
    "make": "BMW",
    "model": "X3",
    "min_year": 2018,
    "max_year": 2023,
    "min_price": 20000,
    "max_price": 50000,
    "max_mileage": 100000,
    "fuel_type": "diesel",
    "transmission": "automatic",
    "body_type": "suv",
    "city": "Rome"
  }
}
```

### Get Alerts
**Endpoint**: `POST /functions/v1/vehicle-api`
**Body**: 
```json
{
  "action": "get_alerts"
}
```

### Add to Favorites
**Endpoint**: `POST /functions/v1/vehicle-api`
**Body**: 
```json
{
  "action": "add_favorite",
  "vehicle_id": 123,
  "notes": "Interested in this vehicle"
}
```

### Get Favorites
**Endpoint**: `POST /functions/v1/vehicle-api`
**Body**: 
```json
{
  "action": "get_favorites"
}
```

## 🔍 Scraper API Endpoints

### Trigger Manual Scraping
**Endpoint**: `POST /functions/v1/vehicle-scraper`
**Body**: 
```json
{
  "source": "manual_trigger",
  "max_vehicles": 100,
  "force_scrape": false
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "session_id": "scrape_20250712_103000",
    "vehicles_found": 45,
    "vehicles_new": 12,
    "vehicles_updated": 8,
    "errors": 0,
    "duration_seconds": 120
  }
}
```

### Get Scraping Status
**Endpoint**: `GET /functions/v1/vehicle-scraper`

**Response**:
```json
{
  "success": true,
  "data": {
    "status": "idle",
    "last_session": {
      "id": "scrape_20250712_103000",
      "started_at": "2025-07-12T10:30:00Z",
      "completed_at": "2025-07-12T10:32:00Z",
      "vehicles_found": 45,
      "status": "completed"
    },
    "next_scheduled": "2025-07-12T12:00:00Z"
  }
}
```

## ⏰ Scheduled Scraper

### Trigger Scheduled Run
**Endpoint**: `POST /functions/v1/scheduled-scraper`
**Body**: 
```json
{
  "source": "manual_trigger"
}
```

**Features**:
- Prevents duplicate scraping sessions
- Automatic alert matching
- Notification creation for matches
- Error handling and logging

## 🔄 Real-time Subscriptions

### Vehicle Updates
```typescript
const channel = supabase
  .channel('vehicle_listings')
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'vehicle_listings'
  }, (payload) => {
    console.log('New vehicle:', payload.new)
  })
  .subscribe()
```

### Alert Notifications
```typescript
const channel = supabase
  .channel('notifications')
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'notifications'
  }, (payload) => {
    console.log('New notification:', payload.new)
  })
  .subscribe()
```

### Price Changes
```typescript
const channel = supabase
  .channel('price_history')
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'price_history'
  }, (payload) => {
    console.log('Price change:', payload.new)
  })
  .subscribe()
```

## 📊 Database Direct Access

### Using Supabase Client
```typescript
import { supabase } from '@/lib/supabase'

// Get vehicles
const { data, error } = await supabase
  .from('vehicle_listings')
  .select('*')
  .eq('is_active', true)
  .order('created_at', { ascending: false })
  .limit(20)

// Create alert
const { data, error } = await supabase
  .from('alerts')
  .insert({
    name: 'BMW X3 Alert',
    make: 'BMW',
    model: 'X3',
    min_price: 20000,
    max_price: 50000
  })
```

## 🚨 Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Invalid input parameters |
| `SCRAPING_ERROR` | Error during scraping operation |
| `DATABASE_ERROR` | Database operation failed |
| `AUTHENTICATION_ERROR` | Invalid or missing authentication |
| `RATE_LIMIT_ERROR` | Too many requests |
| `INTERNAL_ERROR` | Internal server error |

## 📈 Rate Limits

- **Edge Functions**: 1000 requests per minute
- **Database Operations**: No specific limit (Supabase managed)
- **Real-time Subscriptions**: 100 concurrent connections
- **Scraping Operations**: 1 per minute (to prevent abuse)

## 🔧 Development Examples

### Frontend Integration
```typescript
// Search vehicles
const searchVehicles = async (filters: any) => {
  const response = await fetch(`${SUPABASE_URL}/functions/v1/vehicle-api`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
      'apikey': SUPABASE_ANON_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      action: 'search',
      filters
    })
  })
  return response.json()
}
```

### Real-time Integration
```typescript
import { supabaseRealtimeService } from '@/services/supabaseRealtimeService'

// Subscribe to vehicle updates
const unsubscribe = supabaseRealtimeService.subscribeToVehicleUpdates((vehicle) => {
  console.log('New vehicle:', vehicle)
  // Update UI
})

// Cleanup
unsubscribe()
```

## 📞 Support

For API issues:
- Check Supabase dashboard logs
- Review Edge Function logs
- Verify authentication headers
- Check rate limits

**Last Updated**: July 12, 2025  
**API Version**: 2.0.0 - Supabase Production
