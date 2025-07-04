# Vehicle Scout Troubleshooting Guide

## Common Issues and Solutions

### Frontend Issues

#### Issue: Frontend won't start with `npm run dev`
**Symptoms:**
- Error: `crypto.hash is not a function`
- Node.js compatibility errors
- Vite dev server crashes

**Solution:**
Use production build instead of dev server:
```bash
cd frontend
npm run build
npx serve -s dist -l 3000
```

**Root Cause:** Node.js version compatibility with Vite's crypto functions.

#### Issue: Frontend shows blank page
**Symptoms:**
- White screen on load
- No console errors
- Network requests failing

**Solutions:**
1. Check if backend is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Verify build process:
   ```bash
   cd frontend
   npm run build
   ls -la dist/
   ```

3. Check browser console for errors
4. Verify API endpoints are accessible

#### Issue: API calls failing with CORS errors
**Symptoms:**
- CORS policy errors in browser console
- Network requests blocked

**Solution:**
Verify backend CORS configuration in `backend/app/core/config.py`:
```python
ALLOWED_HOSTS = ["http://localhost:3000", "http://127.0.0.1:3000"]
```

### Backend Issues

#### Issue: Backend won't start
**Symptoms:**
- Import errors
- Database connection failures
- Port already in use

**Solutions:**
1. Check Python environment:
   ```bash
   cd backend
   source venv/bin/activate
   python --version
   pip list
   ```

2. Install missing dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Check port availability:
   ```bash
   lsof -i :8000
   # Kill process if needed
   kill -9 <PID>
   ```

4. Verify database setup:
   ```bash
   python setup_scraper.py
   ```

#### Issue: Database connection errors
**Symptoms:**
- `psycopg2.OperationalError: connection refused`
- SQLAlchemy connection errors

**Solutions:**
1. **PostgreSQL not running:**
   ```bash
   # Ubuntu/Debian
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   
   # macOS
   brew services start postgresql
   ```

2. **Use SQLite fallback:**
   The application automatically falls back to SQLite if PostgreSQL is unavailable.

3. **Check database credentials:**
   Verify `.env` file in backend directory:
   ```env
   DATABASE_URL=postgresql://user:password@localhost/dbname
   ```

#### Issue: Redis/Celery not working
**Symptoms:**
- System status shows Redis "disconnected"
- Background tasks not processing
- Celery worker errors

**Solutions:**
1. **Start Redis:**
   ```bash
   # Ubuntu/Debian
   sudo systemctl start redis-server
   
   # macOS
   brew services start redis
   
   # Docker
   docker run -d -p 6379:6379 redis:alpine
   ```

2. **Start Celery worker:**
   ```bash
   cd backend
   celery -A app.tasks.celery_app worker --loglevel=info
   ```

3. **Check Redis connection:**
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

### Scraping Issues

#### Issue: Scraper not finding vehicles
**Symptoms:**
- Empty vehicle results
- Scraping jobs complete but no data
- Website structure changes

**Solutions:**
1. **Test website accessibility:**
   ```bash
   curl -I https://gruppoautouno.it
   ```

2. **Check robots.txt compliance:**
   ```bash
   curl https://gruppoautouno.it/robots.txt
   ```

3. **Run scraper test:**
   ```bash
   cd backend
   python test_scraper.py
   ```

4. **Update scraper selectors:**
   Website structure may have changed. Check `backend/app/scraper/` files.

#### Issue: Scraper blocked by website
**Symptoms:**
- HTTP 403/429 errors
- Captcha challenges
- IP blocking

**Solutions:**
1. **Increase delays:**
   Modify `REQUEST_DELAY` in scraper configuration.

2. **Respect robots.txt:**
   Ensure scraper follows website guidelines.

3. **Use proxy rotation:**
   Implement proxy rotation for large-scale scraping.

### Performance Issues

#### Issue: Slow API responses
**Symptoms:**
- Long response times
- Timeouts
- High CPU usage

**Solutions:**
1. **Database optimization:**
   ```sql
   -- Add indexes for common queries
   CREATE INDEX idx_vehicle_make ON vehicle_listings(make);
   CREATE INDEX idx_vehicle_price ON vehicle_listings(price);
   CREATE INDEX idx_vehicle_year ON vehicle_listings(year);
   ```

2. **Enable caching:**
   Ensure Redis is running for caching.

3. **Monitor database queries:**
   Enable SQL logging in development.

#### Issue: High memory usage
**Symptoms:**
- Out of memory errors
- Slow performance
- System freezing

**Solutions:**
1. **Limit concurrent scraping:**
   Reduce number of Celery workers.

2. **Optimize database queries:**
   Use pagination and limit result sets.

3. **Monitor memory usage:**
   ```bash
   htop
   # or
   ps aux | grep python
   ```

### Development Issues

#### Issue: TypeScript compilation errors
**Symptoms:**
- Build failures
- Type errors
- Missing dependencies

**Solutions:**
1. **Check TypeScript configuration:**
   ```bash
   cd frontend
   npx tsc --noEmit
   ```

2. **Update type definitions:**
   ```bash
   npm install --save-dev @types/node @types/react @types/react-dom
   ```

3. **Fix import paths:**
   Ensure all imports use correct relative paths.

#### Issue: Hot reload not working
**Symptoms:**
- Changes not reflected
- Manual refresh required

**Solution:**
Use production build method instead of dev server due to Node.js compatibility issues.

### Deployment Issues

#### Issue: Production build fails
**Symptoms:**
- Build process errors
- Missing assets
- 404 errors

**Solutions:**
1. **Check build output:**
   ```bash
   cd frontend
   npm run build
   ls -la dist/
   ```

2. **Verify asset paths:**
   Check `vite.config.ts` base configuration.

3. **Test production build locally:**
   ```bash
   npx serve -s dist -l 3000
   ```

#### Issue: Nginx configuration errors
**Symptoms:**
- 502 Bad Gateway
- Static files not served
- API routes not working

**Solutions:**
1. **Test Nginx configuration:**
   ```bash
   sudo nginx -t
   ```

2. **Check Nginx logs:**
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

3. **Verify proxy settings:**
   Ensure backend is running on correct port.

## Diagnostic Commands

### System Health Check
```bash
# Backend health
curl http://localhost:8000/health

# System status
curl http://localhost:8000/api/v1/system/status

# Database connection
cd backend && python -c "from app.models.base import engine; print('DB OK' if engine else 'DB Error')"

# Redis connection
redis-cli ping

# Frontend accessibility
curl -I http://localhost:3000
```

### Log Analysis
```bash
# Backend logs (if using systemd)
sudo journalctl -u vehicle-scout-api -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Application logs
cd backend && python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

### Performance Monitoring
```bash
# System resources
htop
df -h
free -h

# Network connections
netstat -tulpn | grep :8000
netstat -tulpn | grep :3000

# Process monitoring
ps aux | grep python
ps aux | grep node
```

## Getting Help

1. **Check logs first** - Most issues are revealed in application logs
2. **Verify prerequisites** - Ensure all required services are running
3. **Test components individually** - Isolate frontend, backend, database issues
4. **Check GitHub issues** - Look for similar problems and solutions
5. **Create detailed bug reports** - Include logs, system info, and reproduction steps

## Emergency Recovery

### Complete System Reset
```bash
# Stop all services
sudo systemctl stop vehicle-scout-api vehicle-scout-worker nginx

# Reset database
sudo -u postgres dropdb vehicle_scout
sudo -u postgres createdb vehicle_scout

# Reinstall dependencies
cd backend
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cd ../frontend
rm -rf node_modules dist
npm install
npm run build

# Restart services
python setup_scraper.py
sudo systemctl start vehicle-scout-api vehicle-scout-worker nginx
```

### Backup and Restore
```bash
# Create backup
pg_dump vehicle_scout > backup.sql
tar -czf app_backup.tar.gz /opt/vehicle_scout

# Restore from backup
sudo -u postgres psql vehicle_scout < backup.sql
tar -xzf app_backup.tar.gz -C /
```
