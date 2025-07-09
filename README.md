# 🚗 Auto Scouter - Vehicle Listing & Search Platform

[![Deployment Status](https://img.shields.io/badge/deployment-live-brightgreen)](https://auto-scouter-backend-production.up.railway.app)
[![Backend](https://img.shields.io/badge/backend-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Ionic-blue)](https://ionicframework.com/)
[![Database](https://img.shields.io/badge/database-PostgreSQL-336791)](https://postgresql.org/)
[![Cloud](https://img.shields.io/badge/cloud-Railway-0B0D0E)](https://railway.app/)

Auto Scouter is a comprehensive vehicle listing and search platform that allows users to discover, search, and get alerts for vehicles from multiple sources. The application features a FastAPI backend deployed on Railway cloud platform and a React/Ionic mobile frontend.

## 🌐 Live Deployment

- **Backend API**: https://auto-scouter-backend-production.up.railway.app
- **API Documentation**: https://auto-scouter-backend-production.up.railway.app/docs
- **Health Check**: https://auto-scouter-backend-production.up.railway.app/health
- **Mobile APK**: `frontend/dist/apk/VehicleScout-cloud-release.apk` (5.8MB)

## 🎯 **CURRENT STATUS: CLOUD DEPLOYED & FULLY FUNCTIONAL**

✅ **Cloud Backend**: FastAPI deployed on Railway with PostgreSQL
✅ **Mobile App**: Production-ready Android APK (5.8MB) with cloud connectivity
✅ **Database**: PostgreSQL managed service on Railway
✅ **API Endpoints**: Full REST API with authentication and vehicle management
✅ **Real-time Features**: WebSocket support and live updates
✅ **Production Ready**: HTTPS, security headers, and monitoring

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Mobile App    │    │   Backend API   │    │   PostgreSQL    │
│  (React/Ionic)  │◄──►│   (FastAPI)     │◄──►│   Database      │
│                 │    │                 │    │   (Railway)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Capacitor     │    │   Railway       │    │   Managed DB    │
│   (Android)     │    │   Platform      │    │   Service       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack

**Backend:**
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL (Railway managed)
- **Authentication**: JWT tokens
- **API Documentation**: OpenAPI/Swagger
- **Background Tasks**: Celery + Redis
- **Web Scraping**: Selenium + BeautifulSoup
- **Deployment**: Railway cloud platform

**Frontend:**
- **Framework**: React + TypeScript
- **Mobile**: Ionic + Capacitor
- **UI Components**: Tailwind CSS + shadcn/ui
- **State Management**: TanStack Query
- **Build Tool**: Vite
- **Target Platform**: Android APK

**Infrastructure:**
- **Cloud Platform**: Railway
- **Database**: PostgreSQL (managed service)
- **Environment**: Production with HTTPS
- **Monitoring**: Health checks and logging

## 🚀 Features

- **Vehicle Search**: Advanced search and filtering with cloud backend
- **Real-time Updates**: Live vehicle data updates via WebSocket connections
- **Cloud Integration**: Fully deployed backend with PostgreSQL database
- **Alert System**: Custom alerts for vehicle matches based on user criteria
- **Dashboard**: Comprehensive system monitoring and analytics
- **Notification Center**: Real-time notifications for new matches and system events
- **User Authentication**: JWT-based authentication with secure cloud backend
- **Mobile App**: Native Android APK with offline capabilities
- **Modern UI**: Responsive React interface with TypeScript and Tailwind CSS
- **RESTful API**: FastAPI backend with automatic documentation and cloud deployment

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Android Studio (for mobile development)
- Git

### 1. Clone Repository

```bash
git clone https://github.com/ezekaj/auto_scouter.git
cd auto_scouter
```

### 2. Backend Setup (Local Development)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create local environment file
cp .env.example .env
# Edit .env with your local settings

# Run the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install

# Configure environment for local development
cp .env.example .env
# Edit .env to point to your local backend

# Run development server
npm run dev

# Build for production
npm run build

# Generate Android APK
./build_cloud_apk.sh
```

## 📱 Mobile App Installation

### Download APK
The production APK is available at: `frontend/dist/apk/VehicleScout-cloud-release.apk`

### Installation Steps
1. Download the APK file to your Android device
2. Enable "Unknown Sources" in Settings > Security
3. Tap the APK file to install
4. Launch "Auto Scouter" app
5. Register/login to start using the app

### Features
- ✅ Real-time vehicle listings from cloud backend
- ✅ User registration and authentication
- ✅ Advanced vehicle search and filtering
- ✅ Alert creation and management
- ✅ Offline mode with cached data
- ✅ Push notifications (when Firebase configured)

## 🏗️ Project Structure

```
auto_scouter/
├── frontend/          # React + TypeScript frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API services
│   │   ├── hooks/         # Custom React hooks
│   │   ├── lib/           # Utilities and configurations
│   │   └── types/         # TypeScript type definitions
│   ├── dist/apk/          # Generated Android APK
│   ├── package.json
│   └── build_cloud_apk.sh # APK build script
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── core/          # Configuration and settings
│   │   ├── models/        # SQLAlchemy database models
│   │   ├── routers/       # API endpoint routers
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic services
│   │   ├── scraper/       # Web scraping modules
│   │   └── tasks/         # Background tasks
│   ├── railway.json       # Railway deployment config
│   └── migrate_to_cloud_db.py # Database migration script
│   ├── requirements.txt
│   └── setup_scraper.py   # Setup and initialization script
└── README.md
```

## 🛠️ Technology Stack

### Frontend
- **React 18** - Modern UI library with hooks
- **TypeScript** - Type-safe JavaScript development
- **Vite** - Fast build tool and development server
- **Tailwind CSS** - Utility-first CSS framework
- **React Query** - Data fetching and caching
- **React Router** - Client-side routing
- **Lucide React** - Beautiful icon library

### Backend
- **FastAPI** - High-performance Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **SQLite/PostgreSQL** - Database support (SQLite for dev, PostgreSQL for production)
- **Pydantic** - Data validation using Python type annotations
- **Uvicorn** - ASGI server
- **Celery** - Distributed task queue for background jobs
- **Redis** - In-memory data store for caching and task queuing
- **BeautifulSoup** - Web scraping and HTML parsing
- **APScheduler** - Advanced Python Scheduler for automated tasks

## 📋 Prerequisites

- **Node.js** (v18 or higher) - JavaScript runtime
- **Python** (v3.8 or higher) - Backend runtime
- **npm** or **yarn** - Package manager for frontend
- **pip** - Package manager for Python
- **Redis** (optional) - For background tasks and caching
- **PostgreSQL** (optional) - For production database

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/ezekaj/auto_scouter.git
cd auto_scouter
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Run setup script to initialize database and create sample data
python setup_scraper.py

# Start the backend server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at: http://localhost:8000

### 3. Frontend Setup

```bash
cd frontend

# Install Node.js dependencies
npm install

# Build the frontend for production
npm run build

# Serve the built frontend
npx serve -s dist -l 3000
```

The frontend will be available at: http://localhost:3000

### 4. Development Mode (Alternative)

For development with hot reload:

```bash
cd frontend
npm run dev
```

**Note**: If you encounter Node.js compatibility issues with the dev server, use the production build method above.

## 🔧 Development

### Running Both Services

For development, you'll need to run both the frontend and backend simultaneously:

1. **Terminal 1** (Backend):
   ```bash
   cd backend
   source venv/bin/activate  # Activate virtual environment
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Terminal 2** (Frontend):
   ```bash
   cd frontend
   npm run build && npx serve -s dist -l 3000
   ```

### API Documentation

When the backend is running, you can access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **System Status**: http://localhost:8000/api/v1/system/status

### Key API Endpoints

#### Public Endpoints
- `POST /auth/register` - User registration
- `POST /auth/login` - User login (returns JWT token)
- `GET /health` - Health check
- `GET /api/v1/system/status` - System status

#### Protected Endpoints (Require Authentication)
- `GET /api/v1/automotive/vehicles` - Search vehicles with filters
- `GET /api/v1/search/filters` - Get available search filters
- `POST /api/v1/automotive/scraper/trigger` - Trigger manual scraping
- `GET /api/v1/alerts/` - Get user alerts
- `POST /api/v1/alerts/` - Create new alert
- `PUT /api/v1/alerts/{id}` - Update alert
- `DELETE /api/v1/alerts/{id}` - Delete alert
- `POST /api/v1/alerts/{id}/test` - Test alert against current listings
- `GET /api/v1/notifications/` - Get user notifications
- `GET /api/v1/realtime/sse/system-status` - Real-time system status via SSE
- `GET /api/v1/realtime/sse/vehicle-matches` - Real-time vehicle matches via SSE

### Authentication

The application uses JWT (JSON Web Token) based authentication:

1. **Registration**: Create a new account at `/auth/register`
2. **Login**: Authenticate at `/auth/login` to receive a JWT token
3. **Token Usage**: Include the token in the `Authorization` header as `Bearer <token>`
4. **Protected Routes**: All user-specific features require authentication

#### Frontend Authentication Flow
- Login/Registration forms handle user authentication
- JWT tokens are stored in localStorage
- API interceptors automatically include tokens in requests
- Protected routes redirect to login when unauthenticated

#### Backend Authentication
- JWT tokens are validated on all protected endpoints
- Tokens expire after 24 hours (configurable)
- User context is available in all authenticated requests

### Environment Variables

Create a `.env` file in the backend directory:

```env
DATABASE_URL=sqlite:///./auto_scouter.db
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=["http://localhost:3000", "http://127.0.0.1:3000"]
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 📊 Database Schema

### Core Models

- **VehicleListing**: Scraped vehicle data with specifications and pricing
- **User**: User accounts and authentication
- **Alert**: User-defined search alerts and criteria
- **Notification**: System notifications and user alerts
- **ScrapingJob**: Background scraping job tracking
- **SystemLog**: System activity and error logging

### Key Features

- **Real-time Updates**: Server-Sent Events for live data streaming
- **Background Processing**: Celery tasks for automated scraping
- **Alert Matching**: Automatic matching of vehicles to user alerts
- **Multi-source Scraping**: Support for multiple automotive websites

## 🔧 Configuration

### Environment Variables

**Backend (.env):**
```bash
DATABASE_URL=postgresql://user:pass@host:port/db
SECRET_KEY=your-secret-key
ENVIRONMENT=production
LOG_LEVEL=INFO
```

**Frontend (.env.production):**
```bash
VITE_API_URL=https://auto-scouter-backend-production.up.railway.app/api/v1
VITE_WS_BASE_URL=wss://auto-scouter-backend-production.up.railway.app/ws
VITE_APP_ENVIRONMENT=production
VITE_ENABLE_HTTPS_ONLY=true
```

## 🌐 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh token

### Vehicles
- `GET /api/v1/vehicles` - List vehicles with filters
- `GET /api/v1/vehicles/{id}` - Get vehicle details
- `POST /api/v1/vehicles/search` - Advanced search

### Alerts
- `GET /api/v1/alerts` - List user alerts
- `POST /api/v1/alerts` - Create new alert
- `PUT /api/v1/alerts/{id}` - Update alert
- `DELETE /api/v1/alerts/{id}` - Delete alert

### System
- `GET /health` - Health check
- `GET /docs` - API documentation

## 🚀 Deployment

### Railway Backend Deployment

The backend is automatically deployed to Railway. For manual deployment:

```bash
cd backend
railway login
railway link
railway up
```

### Mobile App Build

```bash
cd frontend
./build_cloud_apk.sh
```

This generates:
- `dist/apk/VehicleScout-cloud-release.apk` - Production APK
- `dist/apk/DEPLOYMENT_INFO.md` - Deployment information

## 📊 Monitoring & Health

- **Health Endpoint**: https://auto-scouter-backend-production.up.railway.app/health
- **API Docs**: https://auto-scouter-backend-production.up.railway.app/docs
- **Railway Dashboard**: Monitor deployment status and logs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: See additional docs in the project root
- **Issues**: Create an issue on GitHub
- **Backend Logs**: Check Railway deployment logs
- **API Testing**: Use the interactive docs at `/docs`

---

**Built with ❤️ using FastAPI, React, Ionic, and Railway**

### Commit Message Format

- `Add: new feature or functionality`
- `Edit: modifications to existing code`
- `Fix: bug fixes`
- `Remove: deleted code or features`

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [API documentation](http://localhost:8000/docs) when backend is running
2. Review the console logs for error messages
3. Create an issue on GitHub

## 🧪 Testing

### Backend Tests

```bash
cd backend
python -m pytest tests/ -v
```

### Frontend Tests

```bash
cd frontend
npm test
```

### ✅ COMPREHENSIVE END-TO-END TESTING COMPLETED

**🔐 Authentication System Testing**:
- ✅ User Registration & Login Flow - JWT tokens properly generated
- ✅ Protected Route Access - All endpoints require authentication
- ✅ Token Validation - Bearer token authentication working correctly
- ✅ Session Management - Login/logout functionality operational

**🚨 Alert Management Testing**:
- ✅ Create Alert - POST /api/v1/alerts/ working with full validation
- ✅ Retrieve Alerts - GET /api/v1/alerts/ with pagination support
- ✅ Toggle Alert - POST /api/v1/alerts/{id}/toggle for activation/deactivation
- ✅ Test Alert - POST /api/v1/alerts/{id}/test against vehicle listings
- ✅ Update Alert - PUT /api/v1/alerts/{id} for property modifications
- ✅ Delete Alert - DELETE /api/v1/alerts/{id} for alert removal

**🔔 Notification System Testing**:
- ✅ Get Notifications - GET /api/v1/notifications/ with pagination
- ✅ Notification Structure - Proper JSON response format
- ✅ Real-time Updates - SSE streaming operational

**🚗 Vehicle & Scraper Testing**:
- ✅ Vehicle Search - GET /api/v1/automotive/vehicles with filtering
- ✅ Scraper Trigger - POST /api/v1/automotive/scraper/trigger working
- ✅ Dashboard Overview - GET /api/v1/dashboard/overview data retrieval

**🌐 Frontend Integration Testing**:
- ✅ React Application - Loading correctly on port 3001
- ✅ Authentication UI - Login/register forms functional
- ✅ Button Functionality - All interactive elements working
- ✅ API Communication - Frontend-backend integration verified
- ✅ Mobile Responsiveness - Optimized for mobile devices

**🎯 Complete User Workflow Verification**:
1. ✅ User Registration → Login → JWT Token Authentication
2. ✅ Create Alert → Backend Storage → User Confirmation
3. ✅ Alert Management → Toggle/Update/Delete Operations
4. ✅ Vehicle Search → Real-time Data Display
5. ✅ Notification System → Alert Triggering & Display
6. ✅ Dashboard Access → System Overview & Statistics

**🔒 Security & Performance Testing**:
- ✅ JWT Authentication - Secure token-based access control
- ✅ API Protection - All endpoints properly secured
- ✅ Error Handling - Graceful error responses and user feedback
- ✅ Data Validation - Input validation and sanitization working

**📱 Production Readiness**:
- ✅ Backend Server - Stable on port 8000 with full API coverage
- ✅ Frontend Server - Stable on port 3001 with responsive design
- ✅ Database Integration - SQLAlchemy models and operations working
- ✅ Real-time Features - SSE streaming and live updates operational

**FINAL RESULT**: 🎉 **ALL SYSTEMS OPERATIONAL - PRODUCTION READY**

## 🚀 Production Deployment

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Manual Deployment

1. Set up PostgreSQL database
2. Configure Redis for background tasks
3. Set production environment variables
4. Build frontend: `npm run build`
5. Deploy backend with production ASGI server

## 🔮 Future Enhancements

- [x] ~~Advanced user authentication and role-based access~~ ✅ **COMPLETED**
- [ ] Mobile app support (React Native)
- [ ] Advanced analytics dashboard with charts
- [ ] Multi-language support
- [ ] Email notifications for alerts
- [ ] Vehicle comparison features
- [ ] Price history tracking
- [ ] Machine learning for price predictions
- [ ] API rate limiting and throttling
- [ ] Comprehensive logging and monitoring
- [ ] Advanced role-based permissions (Admin, Moderator, etc.)
- [ ] OAuth integration (Google, Facebook, GitHub)
- [ ] Two-factor authentication (2FA)
