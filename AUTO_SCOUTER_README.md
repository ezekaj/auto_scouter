# 🚗 Auto Scouter - Supabase Vehicle Discovery Platform

A production-ready vehicle scraping and alert system powered by Supabase that monitors carmarket.ayvens.com and provides real-time notifications for matching vehicles with global accessibility.

## 🌟 Features

- **Ayvens Integration**: Automated data collection from carmarket.ayvens.com
- **Smart Alerts**: Create custom alerts with detailed criteria and real-time matching
- **Real-time Notifications**: Instant alerts via WebSocket and push notifications
- **Global Accessibility**: Worldwide access via Supabase global CDN
- **Mobile App**: Production Android application with offline support
- **Real-time Dashboard**: Live analytics and statistics
- **Favorites Management**: Save and organize interesting vehicles
- **Automated Scraping**: Continuous data collection every 2 hours

## 🏗️ Architecture

### Backend (Supabase)
- **Supabase**: Backend-as-a-Service platform with global CDN
- **PostgreSQL**: Production database with real-time subscriptions
- **Edge Functions**: Serverless API endpoints (Deno runtime)
- **Real-time**: WebSocket-based live data synchronization
- **Global CDN**: Worldwide content delivery and performance

### Frontend
- **React 18**: Modern frontend framework
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Capacitor 6.0**: Native mobile app development
- **Supabase Client**: Real-time data synchronization

### Mobile
- **Android APK**: Production-ready mobile application
- **Firebase**: Push notification delivery
- **Real-time Sync**: Live data updates via Supabase
- **Offline Support**: Local data caching and synchronization

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Android Studio (for mobile development)
- Supabase CLI

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd auto_scouter
```

2. **Install dependencies**
```bash
cd frontend
npm install
```

3. **Configure environment**
```bash
cp .env.example .env.development
# Edit .env.development with your Supabase credentials
```

4. **Start development server**
```bash
npm run dev
```

5. **Build mobile app**
```bash
npm run build
npx cap sync android
cd android && ./gradlew assembleRelease
```

## 📱 Mobile Application

### Production APK
- **File**: `AutoScouter-Supabase-Production-Final.apk`
- **Version**: 2.0.0
- **Size**: ~7-8 MB
- **Compatibility**: Android 7.0+ (API 24+)

### Installation
```bash
# Install via ADB
adb install AutoScouter-Supabase-Production-Final.apk

# Or transfer to device and install manually
```

### Features
- ✅ Real-time vehicle search and browsing
- ✅ Smart alert system with notifications
- ✅ Favorites management
- ✅ Push notifications via Firebase
- ✅ Offline capability with sync
- ✅ Global accessibility

## 🔧 Configuration

### Environment Variables
```bash
# Supabase Configuration
VITE_SUPABASE_URL=https://rwonkzncpzirokqnuoyx.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here

# API Configuration
VITE_API_BASE_URL=https://rwonkzncpzirokqnuoyx.supabase.co/functions/v1/vehicle-api
VITE_API_TIMEOUT=30000

# App Configuration
VITE_APP_NAME=Auto Scouter
VITE_APP_VERSION=2.0.0
VITE_APP_ENVIRONMENT=production
```

### Supabase Setup
1. Create new Supabase project
2. Run database migrations
3. Deploy Edge Functions
4. Configure real-time subscriptions
5. Set up cron jobs for automated scraping

## 📊 API Endpoints

### Vehicle API (`/functions/v1/vehicle-api`)
- `GET /search` - Search vehicles with filters
- `GET /stats` - Get system statistics
- `POST /alerts` - Create new alerts
- `GET /alerts` - Get user alerts
- `POST /favorites` - Add to favorites
- `GET /favorites` - Get user favorites

### Scraper API (`/functions/v1/vehicle-scraper`)
- `POST /` - Trigger manual scraping
- `GET /status` - Get scraping status

### Scheduled Scraper (`/functions/v1/scheduled-scraper`)
- Automated cron-triggered scraping every 2 hours
- Alert matching and notification creation
- Error handling and logging

## 🔄 Real-time Features

### Subscriptions
- **Vehicle Updates**: New vehicles and price changes
- **Alert Notifications**: Real-time alert matches
- **Favorites Changes**: Add/remove favorites
- **Scraping Sessions**: Live scraping progress
- **Price History**: Price change tracking

### Usage Example
```typescript
import { supabaseRealtimeService } from '@/services/supabaseRealtimeService'

// Subscribe to vehicle updates
const unsubscribe = supabaseRealtimeService.subscribeToVehicleUpdates((vehicle) => {
  console.log('New vehicle:', vehicle)
})

// Cleanup
unsubscribe()
```

## 📈 Monitoring

### Health Checks
- Database connection and performance
- Edge Function response times
- Scraping operation success rates
- Real-time connection status

### Key Metrics
- Vehicles scraped per day
- Active alerts count
- Notifications sent
- API response times
- Error rates

## 🚨 Troubleshooting

### Common Issues

**Scraping Failures**
- Check Ayvens authentication credentials
- Verify network connectivity
- Review scraping logs in database

**Real-time Connection Issues**
- Check WebSocket connection status
- Verify Supabase project settings
- Review browser console for errors

**Mobile App Issues**
- Clear app cache and data
- Check internet connectivity
- Verify notification permissions

## 📚 Documentation

- [Supabase Deployment Guide](./SUPABASE_DEPLOYMENT_GUIDE.md)
- [API Documentation](./API_GUIDE.md)
- [Environment Configuration](./ENVIRONMENT.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Production Status

**✅ PRODUCTION READY**

- ✅ Automated scraping runs every 2 hours
- ✅ Real-time notifications work globally
- ✅ Mobile app installs and functions properly
- ✅ Alert system matches and notifies correctly
- ✅ Database performance is optimal
- ✅ All Edge Functions respond within 5 seconds

**Auto Scouter is now production-ready with global accessibility via Supabase!** 🚀

---

## 📞 Support

For technical issues or questions:
- Check Supabase dashboard logs
- Review scraping_logs table in database
- Verify device compatibility for mobile app

**Last Updated**: July 12, 2025  
**Version**: 2.0.0 - Supabase Production Release
