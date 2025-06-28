# Auto Scouter Production Deployment Checklist

## 🚀 Pre-Deployment Checklist

### Infrastructure Requirements
- [ ] **Server Setup**
  - [ ] Ubuntu 20.04+ or CentOS 8+ server
  - [ ] Minimum 4GB RAM, 2 CPU cores
  - [ ] 50GB+ storage space
  - [ ] SSL certificate for HTTPS

- [ ] **Database**
  - [ ] PostgreSQL 12+ installed and configured
  - [ ] Database user created with appropriate permissions
  - [ ] Database backup strategy in place

- [ ] **Redis**
  - [ ] Redis server installed and running
  - [ ] Redis persistence configured
  - [ ] Redis memory limits set

- [ ] **Web Server**
  - [ ] Nginx installed and configured
  - [ ] SSL/TLS certificates installed
  - [ ] Rate limiting configured

### Security Configuration
- [ ] **Environment Variables**
  - [ ] SECRET_KEY changed from default
  - [ ] Database passwords are strong and unique
  - [ ] API keys and tokens are secure
  - [ ] CORS origins properly configured

- [ ] **System Security**
  - [ ] Firewall configured (ports 80, 443, 22 only)
  - [ ] SSH key-based authentication
  - [ ] Regular security updates enabled
  - [ ] Non-root user for application

### Application Configuration
- [ ] **Environment Files**
  - [ ] `.env.production` configured with production values
  - [ ] Database URL points to production database
  - [ ] Redis URL configured correctly
  - [ ] Email settings configured for notifications

- [ ] **Logging**
  - [ ] Log level set to INFO or WARNING
  - [ ] Log rotation configured
  - [ ] Error monitoring set up

## 🔧 Deployment Steps

### 1. System Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib redis-server nginx supervisor

# Create application user
sudo useradd -m -s /bin/bash autoscouter
sudo usermod -aG sudo autoscouter
```

### 2. Application Deployment
```bash
# Clone repository
cd /opt
sudo git clone https://github.com/your-repo/auto-scouter.git
sudo chown -R autoscouter:autoscouter auto-scouter

# Create virtual environment
cd /opt/auto-scouter/backend
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Set up environment
cp .env.production .env
# Edit .env with production values
```

### 3. Database Setup
```bash
# Create database
sudo -u postgres createdb auto_scouter_prod
sudo -u postgres createuser autoscouter

# Set password and permissions
sudo -u postgres psql -c "ALTER USER autoscouter PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE auto_scouter_prod TO autoscouter;"

# Run migrations
python create_db.py
```

### 4. Service Configuration
```bash
# Copy systemd service files
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable auto-scouter-api auto-scouter-worker auto-scouter-beat
sudo systemctl start auto-scouter-api auto-scouter-worker auto-scouter-beat
```

### 5. Nginx Configuration
```bash
# Copy nginx configuration
sudo cp deploy/nginx/auto-scouter /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/auto-scouter /etc/nginx/sites-enabled/

# Test and reload nginx
sudo nginx -t
sudo systemctl reload nginx
```

## ✅ Post-Deployment Verification

### Health Checks
- [ ] **API Health**
  - [ ] `curl https://your-domain.com/health` returns 200
  - [ ] `curl https://your-domain.com/health/detailed` shows all components healthy
  - [ ] API documentation accessible at `/docs`

- [ ] **Database Connectivity**
  - [ ] Application can connect to PostgreSQL
  - [ ] Database tables created successfully
  - [ ] Sample data can be inserted and retrieved

- [ ] **Background Jobs**
  - [ ] Celery workers are running
  - [ ] Celery beat scheduler is active
  - [ ] Scraping tasks execute successfully
  - [ ] Alert matching tasks work correctly

- [ ] **Real-time Features**
  - [ ] WebSocket connections work
  - [ ] Server-Sent Events stream properly
  - [ ] Notifications are delivered

### Performance Testing
- [ ] **Load Testing**
  - [ ] API can handle expected concurrent users
  - [ ] Response times are acceptable (<500ms)
  - [ ] Memory usage is stable
  - [ ] No memory leaks detected

- [ ] **Scraping Performance**
  - [ ] Scraper completes within time limits
  - [ ] No rate limiting issues
  - [ ] Data quality is maintained

### Monitoring Setup
- [ ] **System Monitoring**
  - [ ] CPU, memory, disk usage monitoring
  - [ ] Database performance monitoring
  - [ ] Redis monitoring
  - [ ] Log aggregation and analysis

- [ ] **Application Monitoring**
  - [ ] API response time monitoring
  - [ ] Error rate tracking
  - [ ] Background job monitoring
  - [ ] Alert system monitoring

### Backup and Recovery
- [ ] **Backup Strategy**
  - [ ] Database backups scheduled
  - [ ] Application files backed up
  - [ ] Backup restoration tested
  - [ ] Backup retention policy defined

- [ ] **Disaster Recovery**
  - [ ] Recovery procedures documented
  - [ ] Recovery time objectives defined
  - [ ] Recovery point objectives defined
  - [ ] Failover procedures tested

## 🔄 Maintenance Tasks

### Daily
- [ ] Check system health dashboard
- [ ] Review error logs
- [ ] Monitor scraping performance
- [ ] Verify backup completion

### Weekly
- [ ] Review system performance metrics
- [ ] Check disk space usage
- [ ] Update security patches
- [ ] Review alert effectiveness

### Monthly
- [ ] Database maintenance and optimization
- [ ] Log rotation and cleanup
- [ ] Performance tuning
- [ ] Security audit

## 🚨 Troubleshooting

### Common Issues

**API Not Responding**
1. Check service status: `sudo systemctl status auto-scouter-api`
2. Check logs: `sudo journalctl -u auto-scouter-api -f`
3. Verify database connectivity
4. Check nginx configuration

**Scraping Not Working**
1. Check worker status: `sudo systemctl status auto-scouter-worker`
2. Check beat scheduler: `sudo systemctl status auto-scouter-beat`
3. Verify Redis connectivity
4. Check scraper logs

**High Memory Usage**
1. Monitor Celery worker memory
2. Check for memory leaks in scraper
3. Adjust worker concurrency
4. Restart workers if necessary

**Database Performance Issues**
1. Check slow query log
2. Analyze query performance
3. Update database statistics
4. Consider indexing optimization

## 📞 Support Contacts

- **System Administrator**: [admin@your-domain.com]
- **Development Team**: [dev@your-domain.com]
- **Emergency Contact**: [emergency@your-domain.com]

## 📚 Additional Resources

- [API Documentation](https://your-domain.com/docs)
- [System Architecture](./docs/architecture.md)
- [Troubleshooting Guide](./docs/troubleshooting.md)
- [Performance Tuning](./docs/performance.md)

---

**Last Updated**: 2024-12-28
**Version**: 1.0.0
