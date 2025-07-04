# Vehicle Scout Deployment Guide

## Overview

This guide covers deployment options for the Vehicle Scout application, from development setup to production deployment.

## Development Deployment

### Prerequisites

- Node.js 18+
- Python 3.8+
- Git

### Quick Setup

1. **Clone and Setup**
   ```bash
   git clone https://github.com/ezekaj/auto_scouter.git
   cd auto_scouter
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python setup_scraper.py
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

4. **Start Services**
   ```bash
   # Terminal 1 - Backend
   cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Terminal 2 - Frontend
   cd frontend && npx serve -s dist -l 3000
   ```

## Production Deployment

### Option 1: Docker Deployment (Recommended)

1. **Prerequisites**
   - Docker
   - Docker Compose

2. **Environment Setup**
   ```bash
   # Create production environment file
   cp backend/.env.example backend/.env
   # Edit backend/.env with production values
   ```

3. **Deploy with Docker Compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Option 2: Manual Production Deployment

#### Backend Deployment

1. **Server Setup**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip python3-venv postgresql redis-server nginx
   
   # CentOS/RHEL
   sudo yum install python3 python3-pip postgresql-server redis nginx
   ```

2. **Database Setup**
   ```bash
   # PostgreSQL setup
   sudo -u postgres createdb vehicle_scout
   sudo -u postgres createuser vehicle_scout_user
   sudo -u postgres psql -c "ALTER USER vehicle_scout_user PASSWORD 'secure_password';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE vehicle_scout TO vehicle_scout_user;"
   ```

3. **Application Setup**
   ```bash
   # Create application directory
   sudo mkdir -p /opt/vehicle_scout
   sudo chown $USER:$USER /opt/vehicle_scout
   cd /opt/vehicle_scout
   
   # Clone and setup
   git clone https://github.com/ezekaj/auto_scouter.git .
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   # Create production environment file
   cat > backend/.env << EOF
   DATABASE_URL=postgresql://vehicle_scout_user:secure_password@localhost/vehicle_scout
   SECRET_KEY=your-super-secure-secret-key-here
   ALLOWED_HOSTS=["https://yourdomain.com"]
   REDIS_URL=redis://localhost:6379/0
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   ENVIRONMENT=production
   EOF
   ```

5. **Systemd Service Setup**
   ```bash
   # Create systemd service for FastAPI
   sudo tee /etc/systemd/system/vehicle-scout-api.service << EOF
   [Unit]
   Description=Vehicle Scout API
   After=network.target
   
   [Service]
   Type=exec
   User=www-data
   Group=www-data
   WorkingDirectory=/opt/vehicle_scout/backend
   Environment=PATH=/opt/vehicle_scout/backend/venv/bin
   ExecStart=/opt/vehicle_scout/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   # Create systemd service for Celery worker
   sudo tee /etc/systemd/system/vehicle-scout-worker.service << EOF
   [Unit]
   Description=Vehicle Scout Celery Worker
   After=network.target
   
   [Service]
   Type=exec
   User=www-data
   Group=www-data
   WorkingDirectory=/opt/vehicle_scout/backend
   Environment=PATH=/opt/vehicle_scout/backend/venv/bin
   ExecStart=/opt/vehicle_scout/backend/venv/bin/celery -A app.tasks.celery_app worker --loglevel=info
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   # Enable and start services
   sudo systemctl daemon-reload
   sudo systemctl enable vehicle-scout-api vehicle-scout-worker
   sudo systemctl start vehicle-scout-api vehicle-scout-worker
   ```

#### Frontend Deployment

1. **Build Frontend**
   ```bash
   cd /opt/vehicle_scout/frontend
   npm install
   npm run build
   ```

2. **Nginx Configuration**
   ```bash
   sudo tee /etc/nginx/sites-available/vehicle-scout << EOF
   server {
       listen 80;
       server_name yourdomain.com www.yourdomain.com;
       
       # Frontend
       location / {
           root /opt/vehicle_scout/frontend/dist;
           index index.html;
           try_files \$uri \$uri/ /index.html;
       }
       
       # API
       location /api/ {
           proxy_pass http://localhost:8000;
           proxy_set_header Host \$host;
           proxy_set_header X-Real-IP \$remote_addr;
           proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto \$scheme;
       }
       
       # Health check
       location /health {
           proxy_pass http://localhost:8000;
           proxy_set_header Host \$host;
           proxy_set_header X-Real-IP \$remote_addr;
       }
       
       # Docs
       location /docs {
           proxy_pass http://localhost:8000;
           proxy_set_header Host \$host;
           proxy_set_header X-Real-IP \$remote_addr;
       }
   }
   EOF
   
   # Enable site
   sudo ln -s /etc/nginx/sites-available/vehicle-scout /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

3. **SSL Setup with Let's Encrypt**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

### Option 3: Cloud Platform Deployment

#### Railway Deployment

1. **Prepare for Railway**
   ```bash
   # Ensure railway.json exists in backend/
   cd backend
   railway login
   railway init
   railway up
   ```

#### Heroku Deployment

1. **Prepare for Heroku**
   ```bash
   # Create Procfile in backend/
   echo "web: uvicorn app.main:app --host 0.0.0.0 --port \$PORT" > backend/Procfile
   echo "worker: celery -A app.tasks.celery_app worker --loglevel=info" >> backend/Procfile
   
   # Deploy
   heroku create vehicle-scout-app
   heroku addons:create heroku-postgresql:hobby-dev
   heroku addons:create heroku-redis:hobby-dev
   git push heroku main
   ```

## Monitoring and Maintenance

### Health Checks

- **API Health**: `GET /health`
- **System Status**: `GET /api/v1/system/status`
- **Database**: Check connection in system status
- **Redis**: Check connection in system status

### Logs

```bash
# Application logs
sudo journalctl -u vehicle-scout-api -f
sudo journalctl -u vehicle-scout-worker -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Backup

```bash
# Database backup
pg_dump -h localhost -U vehicle_scout_user vehicle_scout > backup_$(date +%Y%m%d).sql

# Application backup
tar -czf vehicle_scout_backup_$(date +%Y%m%d).tar.gz /opt/vehicle_scout
```

### Updates

```bash
# Update application
cd /opt/vehicle_scout
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart vehicle-scout-api vehicle-scout-worker

# Update frontend
cd ../frontend
npm install
npm run build
```

## Security Considerations

1. **Environment Variables**: Never commit sensitive data
2. **Database**: Use strong passwords and limit access
3. **API Keys**: Rotate regularly
4. **HTTPS**: Always use SSL in production
5. **Firewall**: Limit open ports
6. **Updates**: Keep dependencies updated

## Troubleshooting

### Common Issues

1. **Frontend not loading**: Check Nginx configuration and build process
2. **API not responding**: Check systemd service status
3. **Database connection**: Verify credentials and PostgreSQL status
4. **Redis connection**: Check Redis service status
5. **Scraping not working**: Check Celery worker status

### Debug Commands

```bash
# Check service status
sudo systemctl status vehicle-scout-api
sudo systemctl status vehicle-scout-worker

# Check logs
sudo journalctl -u vehicle-scout-api --since "1 hour ago"

# Test API directly
curl http://localhost:8000/health

# Test database connection
cd /opt/vehicle_scout/backend && python -c "from app.models.base import engine; print(engine.execute('SELECT 1').scalar())"
```
