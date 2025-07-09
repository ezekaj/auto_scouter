# Auto Scouter Frontend - Deployment Instructions

## Backend Deployment Status

✅ **Backend deployed to Render**: https://auto-scouter-backend.onrender.com

## Mobile App Configuration

### Current Configuration
The `.env` file is configured to connect to the Render backend:

```
VITE_API_URL=https://auto-scouter-backend.onrender.com/api/v1
VITE_WS_BASE_URL=wss://auto-scouter-backend.onrender.com/ws
```

### Update Instructions

**If the Render app URL is different**, update the `.env` file:

1. **Get your actual Render app URL** from the Render dashboard
2. **Update the .env file**:
   ```bash
   # Replace with your actual Render app URL
   VITE_API_URL=https://your-actual-app-name.onrender.com/api/v1
   VITE_WS_BASE_URL=wss://your-actual-app-name.onrender.com/ws
   ```

## Testing the Connection

### 1. Test Backend Health
```bash
curl https://auto-scouter-backend.onrender.com/health
```

**Expected Response**:
```json
{
    "status": "healthy",
    "environment": "production",
    "database": "healthy",
    "scraper": "running",
    "timestamp": "2025-07-09T...",
    "version": "2.0.0-alerts-enabled",
    "api_endpoints": {
        "alerts_get": "/api/v1/alerts/",
        "alerts_post": "/api/v1/alerts/",
        "vehicles": "/api/v1/automotive/vehicles/simple",
        "scraper_test": "/api/v1/scraper/autouno/test"
    },
    "features": ["AutoUno Scraper", "Alert System", "Database Integration"]
}
```

### 2. Test API Endpoints
```bash
# Test vehicle listings
curl https://auto-scouter-backend.onrender.com/api/v1/automotive/vehicles/simple?limit=3

# Test alert creation
curl -X POST https://auto-scouter-backend.onrender.com/api/v1/alerts/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Alert", "make": "BMW", "max_price": 25000}'

# Test alert retrieval
curl https://auto-scouter-backend.onrender.com/api/v1/alerts/
```

## Mobile App Development

### 1. Install Dependencies
```bash
npm install
```

### 2. Start Development Server
```bash
npm run dev
```

### 3. Build for Production
```bash
npm run build
```

### 4. Test Mobile App
```bash
# Start the app and test alert creation
npm run dev

# Open in browser: http://localhost:5173
# Navigate to Alert Management
# Try creating a new alert
```

## Deployment Options

### Option 1: Vercel (Recommended)
1. Connect GitHub repository to Vercel
2. Deploy automatically on push to main branch
3. Environment variables are automatically loaded from `.env`

### Option 2: Netlify
1. Connect GitHub repository to Netlify
2. Build command: `npm run build`
3. Publish directory: `dist`

### Option 3: Render Static Site
1. Create new Static Site on Render
2. Connect GitHub repository
3. Build command: `npm run build`
4. Publish directory: `dist`

## Troubleshooting

### Backend Connection Issues
1. **Check backend status**: Visit https://auto-scouter-backend.onrender.com/health
2. **Verify URL**: Ensure `.env` has correct Render app URL
3. **Check CORS**: Backend should allow frontend domain

### Mobile App Issues
1. **Clear cache**: Delete `node_modules` and run `npm install`
2. **Check console**: Look for API errors in browser console
3. **Test endpoints**: Use curl to verify backend is working

### Common Issues
- **404 errors**: Backend might be sleeping (Render free tier)
- **CORS errors**: Check backend CORS configuration
- **Timeout errors**: Render free tier has cold start delays

## Production Checklist

- [ ] Backend deployed to Render and responding
- [ ] Database connected and working
- [ ] All API endpoints returning correct responses
- [ ] Frontend `.env` updated with correct backend URL
- [ ] Mobile app can create and manage alerts
- [ ] End-to-end workflow tested and working
