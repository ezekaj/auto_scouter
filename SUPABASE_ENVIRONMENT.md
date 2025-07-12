# 🔧 Supabase Environment Configuration Guide

This guide provides detailed information about configuring environment variables for the Auto Scouter application using Supabase as the backend platform.

## 📋 Overview

Auto Scouter uses Supabase for all backend operations:
- **Database**: PostgreSQL with real-time subscriptions
- **Edge Functions**: Serverless API endpoints
- **Real-time**: WebSocket connections
- **Storage**: File and image storage
- **Authentication**: User management (simplified for single-user)

## 🏗️ Environment Structure

```
auto_scouter/
├── frontend/
│   ├── .env.development       # Local development with Supabase local
│   ├── .env.production        # Production with Supabase cloud
│   └── .env.example          # Template file
├── supabase/
│   ├── config.toml           # Supabase project configuration
│   ├── functions/            # Edge Functions
│   └── migrations/           # Database migrations
└── capacitor.config.ts       # Mobile app configuration
```

## 🌐 Frontend Environment Variables

### Development Environment (.env.development)
```bash
# Supabase Configuration (Local Development)
VITE_SUPABASE_URL=http://127.0.0.1:54321
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0

# API Configuration
VITE_API_BASE_URL=http://127.0.0.1:54321/functions/v1/vehicle-api
VITE_API_TIMEOUT=30000

# App Configuration
VITE_APP_NAME=Auto Scouter
VITE_APP_VERSION=2.0.0
VITE_APP_ENVIRONMENT=development
VITE_DEBUG=true

# Feature Flags
VITE_ENABLE_REAL_TIME=true
VITE_ENABLE_NOTIFICATIONS=true
VITE_ENABLE_FAVORITES=true
VITE_ENABLE_ALERTS=true

# Scraper Configuration
VITE_SCRAPER_ENDPOINT=http://127.0.0.1:54321/functions/v1/vehicle-scraper

# Cache Configuration
VITE_CACHE_VERSION=2.0.0
```

### Production Environment (.env.production)
```bash
# Supabase Configuration (Production)
VITE_SUPABASE_URL=https://rwonkzncpzirokqnuoyx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ3b25rem5jcHppcm9rcW51b3l4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjA3ODI2NzQsImV4cCI6MjAzNjM1ODY3NH0.YOUR_ACTUAL_ANON_KEY

# API Configuration
VITE_API_BASE_URL=https://rwonkzncpzirokqnuoyx.supabase.co/functions/v1/vehicle-api
VITE_API_TIMEOUT=30000

# App Configuration
VITE_APP_NAME=Auto Scouter
VITE_APP_VERSION=2.0.0
VITE_APP_ENVIRONMENT=production
VITE_DEBUG=false

# Feature Flags
VITE_ENABLE_REAL_TIME=true
VITE_ENABLE_NOTIFICATIONS=true
VITE_ENABLE_FAVORITES=true
VITE_ENABLE_ALERTS=true

# Scraper Configuration
VITE_SCRAPER_ENDPOINT=https://rwonkzncpzirokqnuoyx.supabase.co/functions/v1/vehicle-scraper

# Cache Configuration
VITE_CACHE_VERSION=2.0.0

# Performance Optimization
VITE_ENABLE_COMPRESSION=true
VITE_ENABLE_MINIFICATION=true
```

## ⚡ Supabase Edge Functions Environment

### Function Environment Variables
```bash
# Supabase Internal (Automatically provided)
SUPABASE_URL=https://rwonkzncpzirokqnuoyx.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Custom Environment Variables (Set in Supabase Dashboard)
AYVENS_USERNAME=Pndoj
AYVENS_PASSWORD=Asdfgh,.&78
SCRAPER_MAX_VEHICLES=100
SCRAPER_TIMEOUT=300000
ALERT_CHECK_INTERVAL=3600000
```

## 📊 Supabase Project Configuration

### config.toml
```toml
[api]
enabled = true
port = 54321
schemas = ["public", "graphql_public"]
extra_search_path = ["public", "extensions"]
max_rows = 1000

[db]
port = 54322
shadow_port = 54320
major_version = 15

[studio]
enabled = true
port = 54323

[inbucket]
enabled = true
port = 54324
smtp_port = 54325
pop3_port = 54326

[storage]
enabled = true
port = 54327
image_transformation = {enabled = true}

[auth]
enabled = false  # Disabled for single-user app
port = 54328

[edge_functions]
enabled = true
port = 54329

[analytics]
enabled = false
```

## 📱 Mobile App Configuration

### capacitor.config.ts
```typescript
const config: CapacitorConfig = {
  appId: 'com.autoscouter.supabase',
  appName: 'Auto Scouter',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
    cleartext: false,
    allowNavigation: [
      'https://rwonkzncpzirokqnuoyx.supabase.co',
      'https://*.supabase.co',
      'https://carmarket.ayvens.com'
    ]
  },
  plugins: {
    App: {
      launchUrl: 'https://rwonkzncpzirokqnuoyx.supabase.co'
    },
    SplashScreen: {
      launchShowDuration: 2000,
      backgroundColor: '#1e40af',
      showSpinner: true,
      spinnerColor: '#ffffff'
    },
    PushNotifications: {
      presentationOptions: ['badge', 'sound', 'alert']
    }
  }
}
```

## 🔐 Security Configuration

### Row Level Security (RLS) Policies
```sql
-- Enable RLS on all tables
ALTER TABLE vehicle_listings ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE favorites ENABLE ROW LEVEL SECURITY;

-- Allow anonymous access for single-user app
CREATE POLICY "Allow anonymous access" ON vehicle_listings FOR ALL USING (true);
CREATE POLICY "Allow anonymous access" ON alerts FOR ALL USING (true);
CREATE POLICY "Allow anonymous access" ON notifications FOR ALL USING (true);
CREATE POLICY "Allow anonymous access" ON favorites FOR ALL USING (true);
```

## 🚀 Deployment Configuration

### Environment-Specific Settings

#### Development
- **Database**: Local Supabase instance
- **Real-time**: Local WebSocket connections
- **Edge Functions**: Local Deno runtime
- **Storage**: Local file system
- **Debugging**: Enabled with detailed logs

#### Production
- **Database**: Supabase cloud PostgreSQL
- **Real-time**: Global WebSocket infrastructure
- **Edge Functions**: Global edge deployment
- **Storage**: Supabase cloud storage
- **Debugging**: Disabled, error logging only

## 📊 Performance Configuration

### Database Optimization
```sql
-- Indexes for better performance
CREATE INDEX idx_vehicle_listings_active ON vehicle_listings(is_active);
CREATE INDEX idx_vehicle_listings_created ON vehicle_listings(created_at DESC);
CREATE INDEX idx_vehicle_listings_price ON vehicle_listings(price);
CREATE INDEX idx_vehicle_listings_make_model ON vehicle_listings(make, model);
CREATE INDEX idx_alerts_active ON alerts(is_active);
CREATE INDEX idx_notifications_read ON notifications(is_read, created_at DESC);
```

### Edge Function Optimization
```typescript
// Function configuration
export const config = {
  runtime: 'edge',
  regions: ['iad1', 'fra1', 'sin1'], // Global deployment
  memory: 128, // MB
  timeout: 30, // seconds
}
```

## 🔧 Development Setup

### Local Development
```bash
# Start Supabase local development
supabase start

# Deploy functions locally
supabase functions serve

# Run frontend development server
cd frontend
npm run dev
```

### Production Deployment
```bash
# Deploy to Supabase
supabase db push
supabase functions deploy

# Build and deploy mobile app
cd frontend
npm run build
npx cap sync android
cd android && ./gradlew assembleRelease
```

## 🚨 Troubleshooting

### Common Environment Issues

**Supabase Connection Errors**
- Verify SUPABASE_URL and SUPABASE_ANON_KEY
- Check network connectivity
- Ensure project is not paused

**Edge Function Errors**
- Check function logs in Supabase dashboard
- Verify environment variables are set
- Ensure proper CORS configuration

**Real-time Connection Issues**
- Verify real-time is enabled in Supabase
- Check WebSocket connection in browser
- Ensure proper subscription setup

**Mobile App Issues**
- Verify capacitor.config.ts settings
- Check allowed navigation URLs
- Ensure proper build configuration

## 📞 Support

For environment configuration issues:
- Check Supabase dashboard logs
- Review Edge Function logs
- Verify environment variable values
- Test local development setup

**Last Updated**: July 12, 2025  
**Configuration Version**: 2.0.0 - Supabase Production
