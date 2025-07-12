# 🚀 Auto Scouter - Supabase Deployment Guide

## 📋 **Overview**

Auto Scouter is now fully deployed on Supabase as a production-ready vehicle scraping and alert system. This guide covers the complete Supabase setup, deployment, and maintenance procedures.

---

## 🏗️ **Architecture Overview**

### **Backend Stack:**
- **Supabase** - Backend-as-a-Service platform
- **PostgreSQL** - Production database with real-time features
- **Edge Functions** - Serverless API endpoints (Deno runtime)
- **Real-time Subscriptions** - Live data synchronization
- **Global CDN** - Worldwide content delivery

### **Frontend Stack:**
- **React 18** - Modern frontend framework
- **TypeScript** - Type-safe development
- **Capacitor 6.0** - Native mobile bridge
- **Vite 5.4** - Fast build tool
- **Tailwind CSS** - Utility-first styling

### **Data Sources:**
- **carmarket.ayvens.com** - Primary vehicle data source
- **Firebase** - Push notification delivery
- **Real-time WebSockets** - Live data synchronization

---

## 🔧 **Supabase Project Configuration**

### **Project Details:**
- **Project URL:** `https://rwonkzncpzirokqnuoyx.supabase.co`
- **Project ID:** `rwonkzncpzirokqnuoyx`
- **Region:** `us-east-1` (Global CDN enabled)
- **Database:** PostgreSQL 15 with real-time enabled

### **Environment Variables:**
```bash
# Supabase Configuration
VITE_SUPABASE_URL=https://rwonkzncpzirokqnuoyx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# API Configuration
VITE_API_BASE_URL=https://rwonkzncpzirokqnuoyx.supabase.co/functions/v1/vehicle-api
VITE_API_TIMEOUT=30000

# Scraper Configuration
VITE_SCRAPER_ENDPOINT=https://rwonkzncpzirokqnuoyx.supabase.co/functions/v1/vehicle-scraper

# App Configuration
VITE_APP_NAME=Auto Scouter
VITE_APP_VERSION=2.0.0
VITE_APP_ENVIRONMENT=production
```

---

## 📊 **Database Schema**

### **Core Tables:**

#### **vehicle_listings**
```sql
CREATE TABLE vehicle_listings (
  id BIGSERIAL PRIMARY KEY,
  make TEXT NOT NULL,
  model TEXT NOT NULL,
  year INTEGER,
  price NUMERIC,
  currency TEXT DEFAULT 'EUR',
  mileage INTEGER,
  fuel_type TEXT,
  transmission TEXT,
  body_type TEXT,
  city TEXT,
  country TEXT DEFAULT 'Italy',
  url TEXT NOT NULL,
  source_website TEXT NOT NULL DEFAULT 'carmarket.ayvens.com',
  primary_image_url TEXT,
  description TEXT,
  is_active BOOLEAN DEFAULT true,
  scraped_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### **alerts**
```sql
CREATE TABLE alerts (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  make TEXT,
  model TEXT,
  min_year INTEGER,
  max_year INTEGER,
  min_price NUMERIC,
  max_price NUMERIC,
  max_mileage INTEGER,
  fuel_type TEXT,
  transmission TEXT,
  body_type TEXT,
  city TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### **notifications**
```sql
CREATE TABLE notifications (
  id BIGSERIAL PRIMARY KEY,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  data JSONB,
  is_read BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### **favorites**
```sql
CREATE TABLE favorites (
  id BIGSERIAL PRIMARY KEY,
  vehicle_id BIGINT REFERENCES vehicle_listings(id),
  notes TEXT,
  added_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### **scraping_sessions**
```sql
CREATE TABLE scraping_sessions (
  id BIGSERIAL PRIMARY KEY,
  session_id TEXT UNIQUE NOT NULL,
  source_website TEXT NOT NULL,
  scraper_version TEXT,
  status TEXT NOT NULL,
  total_vehicles_found INTEGER DEFAULT 0,
  total_vehicles_new INTEGER DEFAULT 0,
  total_vehicles_updated INTEGER DEFAULT 0,
  total_errors INTEGER DEFAULT 0,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## ⚡ **Edge Functions**

### **1. vehicle-api**
- **Path:** `/functions/v1/vehicle-api`
- **Purpose:** Main API for vehicle operations
- **Endpoints:**
  - `GET /search` - Search vehicles with filters
  - `GET /stats` - Get system statistics
  - `POST /alerts` - Create new alerts
  - `GET /alerts` - Get user alerts
  - `POST /favorites` - Add to favorites
  - `GET /favorites` - Get user favorites

### **2. vehicle-scraper**
- **Path:** `/functions/v1/vehicle-scraper`
- **Purpose:** Scrape carmarket.ayvens.com for vehicle data
- **Features:**
  - Automated authentication with Ayvens
  - HTML parsing and data extraction
  - Image URL collection
  - Database storage with deduplication

### **3. scheduled-scraper**
- **Path:** `/functions/v1/scheduled-scraper`
- **Purpose:** Cron-triggered automated scraping
- **Schedule:** Every 2 hours
- **Features:**
  - Prevents duplicate scraping sessions
  - Alert matching and notification creation
  - Error handling and logging

---

## 🔄 **Real-time Features**

### **Enabled Subscriptions:**
- **Vehicle Updates** - New vehicles and price changes
- **Alert Notifications** - Real-time alert matches
- **Favorites Changes** - Add/remove favorites
- **Scraping Sessions** - Live scraping progress
- **Price History** - Price change tracking

### **WebSocket Configuration:**
```typescript
// Real-time subscription example
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

---

## 📱 **Mobile Application**

### **Production APK:**
- **File:** `AutoScouter-Supabase-Production-Final.apk`
- **Version:** 2.0.0
- **Size:** ~7-8 MB
- **Target:** Android 7.0+ (API 24+)

### **Features:**
- ✅ Real-time vehicle search and browsing
- ✅ Smart alert system with notifications
- ✅ Favorites management
- ✅ Push notifications via Firebase
- ✅ Offline capability with sync
- ✅ Global accessibility

### **Installation:**
```bash
# Install via ADB
adb install AutoScouter-Supabase-Production-Final.apk

# Or transfer to device and install manually
```

---

## 🔧 **Deployment Steps**

### **1. Supabase Project Setup**
1. Create new Supabase project
2. Enable real-time features
3. Configure database schema
4. Set up Row Level Security (RLS)
5. Deploy Edge Functions

### **2. Database Migration**
```sql
-- Run migration scripts
\i supabase/migrations/001_initial_schema.sql
\i supabase/migrations/002_rls_policies.sql
\i supabase/migrations/003_functions.sql
```

### **3. Edge Functions Deployment**
```bash
# Deploy all functions
supabase functions deploy vehicle-api
supabase functions deploy vehicle-scraper
supabase functions deploy scheduled-scraper
```

### **4. Cron Jobs Setup**
```sql
-- Enable automated scraping
\i supabase/cron.sql
```

### **5. Frontend Build & Deploy**
```bash
# Build production frontend
cd frontend
npm run build
npx cap sync android
cd android && ./gradlew assembleRelease
```

---

## 📊 **Monitoring & Maintenance**

### **Health Checks:**
- **Database:** Monitor connection and query performance
- **Edge Functions:** Check function logs and error rates
- **Scraping:** Verify automated scraping operations
- **Real-time:** Monitor WebSocket connections

### **Key Metrics:**
- **Vehicles Scraped:** Daily/weekly totals
- **Active Alerts:** Number of user alerts
- **Notifications Sent:** Alert match notifications
- **API Response Times:** Function performance
- **Error Rates:** Failed operations

### **Maintenance Tasks:**
- **Daily:** Check scraping logs and error rates
- **Weekly:** Review database performance
- **Monthly:** Clean up old data and optimize queries
- **Quarterly:** Update dependencies and security patches

---

## 🚨 **Troubleshooting**

### **Common Issues:**

#### **Scraping Failures**
- Check Ayvens authentication credentials
- Verify network connectivity
- Review scraping logs in database

#### **Real-time Connection Issues**
- Check WebSocket connection status
- Verify Supabase project settings
- Review browser console for errors

#### **Mobile App Issues**
- Clear app cache and data
- Check internet connectivity
- Verify notification permissions

### **Support Contacts:**
- **Technical Issues:** Check Supabase dashboard logs
- **Scraping Problems:** Review scraping_logs table
- **Mobile App:** Check device compatibility

---

## 🎯 **Success Metrics**

**The deployment is successful when:**
- ✅ Automated scraping runs every 2 hours
- ✅ Real-time notifications work globally
- ✅ Mobile app installs and functions properly
- ✅ Alert system matches and notifies correctly
- ✅ Database performance is optimal
- ✅ All Edge Functions respond within 5 seconds

**Auto Scouter is now production-ready with global accessibility via Supabase!** 🚀
