# 🚂 Railway Deployment Guide - Auto Scouter

## ✅ COMPLETED PREPARATIONS
- [x] Rust-free requirements.txt verified
- [x] All local tests passing (4/4)
- [x] Railway configuration files created
- [x] Code committed and pushed to GitHub
- [x] Railway project "gallant-enchantment" created

## 🔧 RAILWAY DASHBOARD CONFIGURATION

### Step 1: Add PostgreSQL Database
1. In Railway dashboard → Click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Wait for provisioning (1-2 minutes)
4. ✅ Verify DATABASE_URL appears in environment variables

### Step 2: Configure Environment Variables
Go to your FastAPI service → **Variables** tab → Add these:

```
SECRET_KEY=auto-scouter-railway-secret-key-2025-change-in-production-12345
ENVIRONMENT=production
PROJECT_NAME=Auto Scouter
VERSION=1.0.0
API_V1_STR=/api/v1
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=*
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

### Step 3: Set Build Commands
Go to **Settings** → **Build & Deploy**:

**Build Command:**
```
cd backend && pip install -r requirements.txt
```

**Start Command:**
```
cd backend && gunicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --timeout 120
```

### Step 4: Deploy
1. Click **"Deploy Now"** or push to GitHub
2. Monitor build logs for success indicators

## 📊 BUILD LOG SUCCESS INDICATORS

✅ **Look for these in Railway logs:**
```
Successfully installed fastapi-0.95.1 uvicorn-0.21.1 pydantic-2.3.0
✅ Database tables created/verified
INFO: Started server process
INFO: Application startup complete.
```

❌ **Should NOT see:**
- "maturin", "cargo", "Rust compilation"
- Import errors
- Database connection failures

## 🧪 TESTING DEPLOYED APPLICATION

Once deployed, Railway provides URL like:
`https://gallant-enchantment-production.up.railway.app`

### Test Commands:

**1. Health Check:**
```bash
curl https://your-railway-url/health
```
Expected: `{"status": "healthy", "database": "healthy"}`

**2. Root Endpoint:**
```bash
curl https://your-railway-url/
```
Expected: `{"message": "Vehicle Scout API", "version": "1.0.0"}`

**3. API Documentation:**
Visit: `https://your-railway-url/docs`

**4. Test Authentication:**
```bash
curl -X POST https://your-railway-url/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "TestPassword123!"}'
```

## 🔧 TROUBLESHOOTING

### Issue: Build Fails
- Check requirements.txt is in backend/ folder
- Verify build command path: `cd backend && ...`

### Issue: App Won't Start
- Check start command uses `$PORT` variable
- Verify gunicorn is in requirements.txt

### Issue: Database Connection Fails
- Ensure PostgreSQL service is running
- Check DATABASE_URL is automatically provided

### Issue: Import Errors
- Verify all dependencies in requirements.txt
- Check Python path in start command

## 📈 EXPECTED TIMELINE
- Database setup: 1-2 minutes
- Build process: 2-3 minutes
- App startup: 30 seconds
- **Total: 3-5 minutes**

## 🎯 SUCCESS CRITERIA
- [ ] Build completes without Rust compilation
- [ ] Application starts successfully
- [ ] Health endpoint returns 200
- [ ] Database connection working
- [ ] API documentation accessible
- [ ] Authentication endpoints functional

## 📞 NEXT STEPS AFTER SUCCESS
1. Update mobile app with new Railway URL
2. Test all API endpoints thoroughly
3. Monitor Railway metrics dashboard
4. Set up custom domain (optional)
5. Configure production logging/monitoring
