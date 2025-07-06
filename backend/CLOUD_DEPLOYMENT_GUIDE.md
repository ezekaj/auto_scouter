# 🌐 Cloud Deployment Guide - 24/7 Operation

**Vehicle Scout - Complete Cloud Deployment for Continuous Operation**

## 🚨 **CRITICAL: NO MORE PC DEPENDENCY**

This guide deploys Vehicle Scout to run **24/7 in the cloud** without requiring your PC to be running.

---

## 🚀 **PHASE 1: RAILWAY DEPLOYMENT (RECOMMENDED)**

### **Prerequisites**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Or download from: https://railway.app/cli
```

### **Step 1: Prepare for Deployment**
```bash
cd backend

# Verify all cloud files are present
ls -la railway.json Procfile deploy_to_railway.py app/main_cloud.py

# Install cloud dependencies (optional - Railway will do this)
pip install -r requirements.txt
```

### **Step 2: Deploy to Railway**
```bash
# Run the automated deployment script
python deploy_to_railway.py

# OR deploy manually:
railway login
railway init
railway add --database postgresql
railway add --database redis
railway up
```

### **Step 3: Configure Environment Variables**
Railway will automatically set these, but verify:
```bash
railway variables set ENVIRONMENT=production
railway variables set SCRAPING_INTERVAL_MINUTES=5
railway variables set MAX_VEHICLES_PER_SCRAPE=50
railway variables set SECRET_KEY=your-production-secret-key
```

### **Step 4: Verify Deployment**
```bash
# Check deployment status
railway status

# Get your app URL
railway domain

# Test health endpoint
curl https://your-app.railway.app/health
```

---

## 🔄 **PHASE 2: AUTOMATED SCRAPING (24/7)**

### **Background Tasks Configuration**

The system automatically runs these tasks in the cloud:

#### **AutoUno Scraping**
- **Frequency:** Every 5 minutes
- **Task:** `cloud_scrape_autouno_task`
- **Purpose:** Scrape new Albanian car listings

#### **AutoScout24 Scraping**
- **Frequency:** Every 10 minutes  
- **Task:** `scrape_autoscout24_task`
- **Purpose:** Scrape European car listings

#### **Notification Processing**
- **Frequency:** Every minute
- **Task:** `process_pending_notifications`
- **Purpose:** Send push notifications for matches

### **Monitoring Scraping**
```bash
# Check scraping status via API
curl https://your-app.railway.app/cloud/scraper/status

# Get scraping statistics
curl https://your-app.railway.app/cloud/status

# Manually trigger scraping (for testing)
curl -X POST https://your-app.railway.app/cloud/scraper/trigger
```

---

## 🗄️ **PHASE 3: CLOUD DATABASE**

### **PostgreSQL Configuration**
Railway automatically provides PostgreSQL with these benefits:
- ✅ **24/7 Availability:** Database runs continuously
- ✅ **Automatic Backups:** Daily backups included
- ✅ **Scaling:** Automatic scaling as needed
- ✅ **SSL Security:** Encrypted connections

### **Database Migration**
The system automatically:
1. Creates all required tables
2. Migrates existing SQLite data (if any)
3. Sets up proper indexes and relationships

### **Database Monitoring**
```bash
# Check database connection
curl https://your-app.railway.app/health

# View database info
railway logs
```

---

## 📱 **PHASE 4: MOBILE APP CLOUD CONNECTION**

### **Update APK Configuration**

1. **Update API Base URL**
   ```typescript
   // In frontend/src/config/api.ts
   export const API_BASE_URL = 'https://your-app.railway.app';
   ```

2. **Rebuild APK**
   ```bash
   cd frontend
   npm run build
   npm run cap:sync
   cd android
   ./gradlew assembleRelease
   ```

3. **Test Cloud Connection**
   - Install updated APK
   - Verify vehicle data loads from cloud
   - Test user registration with cloud backend
   - Confirm notifications work

---

## 🔔 **PHASE 5: PUSH NOTIFICATIONS**

### **Firebase Setup (Optional)**
For production push notifications:

1. **Create Firebase Project**
   - Go to https://console.firebase.google.com
   - Create new project
   - Enable Cloud Messaging

2. **Configure Backend**
   ```bash
   railway variables set FIREBASE_PROJECT_ID=your-project-id
   railway variables set FIREBASE_CREDENTIALS_PATH=/app/firebase-key.json
   ```

3. **Update Mobile App**
   - Add Firebase SDK to mobile app
   - Configure push notification handling

---

## 📊 **PHASE 6: MONITORING & HEALTH CHECKS**

### **Built-in Monitoring**
The cloud deployment includes:

#### **Health Endpoints**
- `/health` - Overall system health
- `/cloud/status` - Cloud deployment status
- `/cloud/scraper/status` - Scraping system status

#### **Automatic Monitoring**
- Database connection checks
- Scraping task monitoring
- Error logging and alerts
- Performance metrics

### **Railway Monitoring**
```bash
# View logs
railway logs

# Monitor resource usage
railway status

# Check deployments
railway deployments
```

---

## 💰 **PHASE 7: COST OPTIMIZATION**

### **Railway Free Tier**
- ✅ **$5/month credit** (enough for small apps)
- ✅ **PostgreSQL included**
- ✅ **Redis included**
- ✅ **Automatic scaling**

### **Optimization Tips**
1. **Scraping Frequency:** Adjust `SCRAPING_INTERVAL_MINUTES` if needed
2. **Vehicle Limits:** Set `MAX_VEHICLES_PER_SCRAPE` appropriately
3. **Database Cleanup:** Automatic cleanup of old data
4. **Resource Monitoring:** Monitor usage in Railway dashboard

---

## 🚀 **DEPLOYMENT COMMANDS SUMMARY**

### **Quick Deployment**
```bash
# 1. Deploy to Railway
cd backend
python deploy_to_railway.py

# 2. Update mobile app
cd ../frontend
# Update API_BASE_URL to Railway domain
npm run build && npm run cap:sync
cd android && ./gradlew assembleRelease

# 3. Test deployment
curl https://your-app.railway.app/health
```

### **Verification Checklist**
- [ ] ✅ Backend deployed to Railway
- [ ] ✅ PostgreSQL database connected
- [ ] ✅ Redis for background tasks
- [ ] ✅ Scraping running every 5 minutes
- [ ] ✅ Mobile app connects to cloud
- [ ] ✅ Notifications working
- [ ] ✅ No PC dependency

---

## 🎯 **SUCCESS CRITERIA**

### **24/7 Operation Verified**
1. **Turn off your PC** ✅
2. **Check scraping continues** via Railway logs ✅
3. **Verify new vehicles appear** in mobile app ✅
4. **Confirm notifications work** without PC ✅

### **Complete Independence**
- ✅ **Cloud Backend:** Railway hosting
- ✅ **Cloud Database:** PostgreSQL
- ✅ **Cloud Tasks:** Celery + Redis
- ✅ **Cloud Monitoring:** Built-in health checks
- ✅ **Mobile App:** Connects to cloud URLs

---

## 🆘 **TROUBLESHOOTING**

### **Common Issues**

#### **Deployment Fails**
```bash
# Check Railway CLI
railway --version

# Re-login if needed
railway login

# Check logs
railway logs
```

#### **Database Connection Issues**
```bash
# Verify PostgreSQL is added
railway add --database postgresql

# Check environment variables
railway variables
```

#### **Scraping Not Working**
```bash
# Check scraper status
curl https://your-app.railway.app/cloud/scraper/status

# Manually trigger
curl -X POST https://your-app.railway.app/cloud/scraper/trigger
```

#### **Mobile App Can't Connect**
1. Verify Railway domain is correct
2. Check CORS settings in backend
3. Ensure mobile app uses HTTPS URLs
4. Test API endpoints manually

---

## 📞 **SUPPORT**

- **Railway Documentation:** https://docs.railway.app
- **API Documentation:** https://your-app.railway.app/docs
- **Health Check:** https://your-app.railway.app/health
- **Logs:** `railway logs`

---

**🎉 RESULT: Complete 24/7 cloud-based car scouting system with zero PC dependency!**
