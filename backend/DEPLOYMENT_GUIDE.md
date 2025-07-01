# Vehicle Scout Backend - Deployment Guide

This guide covers deploying the Vehicle Scout backend to various cloud platforms with 24/7 operation.

## 🚀 Quick Deploy Options

### Option 1: Railway (Recommended)
Railway is perfect for Python apps with automatic scaling and built-in databases.

```bash
# Install Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Deploy
./deploy_to_railway.sh
```

### Option 2: Docker Compose (Local/VPS)
```bash
# Build and run all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Option 3: Manual VPS Deployment
See the "Manual VPS Setup" section below.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   PostgreSQL    │
│   (Mobile App)  │◄──►│   Backend       │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Celery        │◄──►│   Redis         │
                       │   Workers       │    │   (Queue)       │
                       └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Web Scrapers  │
                       │   (24/7 Auto)   │
                       └─────────────────┘
```

## 🔧 Environment Configuration

### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port/0

# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Scraping
SCRAPER_SCRAPING_ENABLED=true
SCRAPER_SCRAPING_INTERVAL_HOURS=6
SCRAPER_MAX_PAGES_TO_SCRAPE=100

# Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 📊 Monitoring & Health Checks

The backend includes built-in monitoring:

- **Health Check**: `GET /health`
- **Metrics**: `GET /metrics`
- **API Status**: `GET /api/v1/status`

## 🔄 Automated Scraping

The system automatically:
1. Scrapes vehicle data every 6 hours
2. Processes and stores data in PostgreSQL
3. Sends notifications for matching alerts
4. Maintains data quality and deduplication

## 🛠️ Manual VPS Setup

### 1. Server Requirements
- Ubuntu 20.04+ or similar
- 2GB+ RAM
- 20GB+ storage
- Python 3.12+
- PostgreSQL 15+
- Redis 7+

### 2. Installation Steps

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv postgresql redis-server nginx

# Create application user
sudo useradd -m -s /bin/bash vehiclescout
sudo su - vehiclescout

# Clone and setup application
git clone <your-repo> vehicle-scout-backend
cd vehicle-scout-backend/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup database
sudo -u postgres createdb auto_scouter
python3 create_db.py

# Setup systemd services
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vehicle-scout-api
sudo systemctl enable vehicle-scout-worker
sudo systemctl enable vehicle-scout-beat
sudo systemctl start vehicle-scout-api
sudo systemctl start vehicle-scout-worker
sudo systemctl start vehicle-scout-beat
```

## 🔐 Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use strong database passwords
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Set up backup strategy
- [ ] Enable monitoring alerts
- [ ] Configure rate limiting
- [ ] Set up log rotation

## 📱 Frontend Integration

After deployment, update your frontend configuration:

```typescript
// frontend/src/config/production.ts
export const config = {
  apiBaseUrl: 'https://your-api-domain.com/api/v1',
  // ... other config
};
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check DATABASE_URL format
   - Verify database is running
   - Check network connectivity

2. **Scraping Not Working**
   - Check SCRAPER_SCRAPING_ENABLED=true
   - Verify Celery workers are running
   - Check Redis connection

3. **High Memory Usage**
   - Reduce SCRAPER_MAX_PAGES_TO_SCRAPE
   - Increase SCRAPER_REQUEST_DELAY
   - Monitor with `docker stats` or `htop`

### Logs and Debugging

```bash
# Railway
railway logs

# Docker Compose
docker-compose logs -f api
docker-compose logs -f celery-worker

# Systemd
sudo journalctl -u vehicle-scout-api -f
```

## 📈 Scaling Considerations

- **Horizontal Scaling**: Add more Celery workers
- **Database**: Use connection pooling
- **Caching**: Implement Redis caching for API responses
- **CDN**: Use CDN for static assets
- **Load Balancer**: Use nginx or cloud load balancer

## 🔄 Maintenance

### Regular Tasks
- Monitor disk usage
- Check log files
- Update dependencies
- Backup database
- Monitor scraping performance

### Updates
```bash
# Pull latest code
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Run migrations (if any)
alembic upgrade head

# Restart services
sudo systemctl restart vehicle-scout-*
```
