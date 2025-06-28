# Auto Scouter Frontend - Production Deployment Guide

This guide provides step-by-step instructions for deploying the Auto Scouter frontend to production.

## Prerequisites

Before deploying, ensure you have:

1. **Domain name** registered and configured
2. **SSL certificate** (Let's Encrypt recommended)
3. **Web server** (Nginx, Apache, or hosting service)
4. **Backend API** deployed and accessible
5. **Node.js 18+** for building (if building locally)

## Environment Variables

Create a `.env.production` file with the following required variables:

```bash
# Required
VITE_API_BASE_URL=https://api.yourdomain.com/api/v1

# Optional
VITE_APP_NAME=Auto Scouter
VITE_APP_VERSION=1.0.0
VITE_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
VITE_SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

## Deployment Methods

### Method 1: Traditional Web Server Deployment

#### Step 1: Build the Application

```bash
# Clone the repository
git clone <repository-url>
cd auto-scouter/frontend

# Set environment variables
export VITE_API_BASE_URL=https://api.yourdomain.com/api/v1

# Run deployment script
./deploy.sh
```

#### Step 2: Upload to Web Server

```bash
# Upload the dist folder to your web server
scp -r dist/* user@yourserver:/var/www/auto-scouter/

# Or use rsync
rsync -avz dist/ user@yourserver:/var/www/auto-scouter/
```

#### Step 3: Configure Web Server

**For Nginx:**
```bash
# Copy nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/auto-scouter
sudo ln -s /etc/nginx/sites-available/auto-scouter /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**For Apache:**
```bash
# Copy .htaccess file (already included in dist)
# Ensure mod_rewrite is enabled
sudo a2enmod rewrite
sudo systemctl reload apache2
```

### Method 2: Docker Deployment

#### Step 1: Build Docker Image

```bash
# Build the image
docker build -t auto-scouter-frontend \
  --build-arg VITE_API_BASE_URL=https://api.yourdomain.com/api/v1 \
  .

# Or use Docker Compose
docker-compose up -d
```

#### Step 2: Run Container

```bash
# Run with Docker
docker run -d \
  --name auto-scouter-frontend \
  -p 80:80 \
  -p 443:443 \
  auto-scouter-frontend

# Or use Docker Compose
VITE_API_BASE_URL=https://api.yourdomain.com/api/v1 \
DOMAIN=yourdomain.com \
docker-compose up -d
```

### Method 3: Static Hosting Services

#### Netlify

1. Connect your GitHub repository to Netlify
2. Set build command: `npm run build`
3. Set publish directory: `dist`
4. Add environment variables in Netlify dashboard
5. Configure redirects for SPA routing

#### Vercel

1. Connect your GitHub repository to Vercel
2. Set framework preset: `Vite`
3. Add environment variables in Vercel dashboard
4. Deploy automatically on push

#### AWS S3 + CloudFront

1. Build the application locally
2. Upload `dist/` contents to S3 bucket
3. Configure S3 for static website hosting
4. Set up CloudFront distribution
5. Configure custom error pages for SPA routing

## SSL Certificate Setup

### Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Custom Certificate

1. Obtain SSL certificate from your provider
2. Update nginx.conf or .htaccess with certificate paths
3. Restart web server

## DNS Configuration

Configure your domain's DNS records:

```
Type    Name    Value                   TTL
A       @       YOUR_SERVER_IP          300
A       www     YOUR_SERVER_IP          300
CNAME   api     api.yourdomain.com      300
```

## Performance Optimization

### CDN Setup

1. **CloudFlare** (Recommended)
   - Add your domain to CloudFlare
   - Update nameservers
   - Enable caching and optimization features

2. **AWS CloudFront**
   - Create distribution pointing to your origin
   - Configure caching behaviors
   - Set up custom error pages

### Monitoring

1. **Google Analytics**
   - Set `VITE_GOOGLE_ANALYTICS_ID` environment variable
   - Verify tracking in Google Analytics dashboard

2. **Error Monitoring**
   - Set `VITE_SENTRY_DSN` environment variable
   - Configure Sentry project

## Security Checklist

- [ ] HTTPS enabled and HTTP redirected
- [ ] Security headers configured
- [ ] CSP (Content Security Policy) implemented
- [ ] Sensitive files blocked (.env, .git, etc.)
- [ ] Regular security updates applied
- [ ] Firewall configured
- [ ] Access logs monitored

## Troubleshooting

### Common Issues

1. **404 errors on page refresh**
   - Ensure SPA routing is configured in web server
   - Check nginx.conf or .htaccess configuration

2. **API connection errors**
   - Verify VITE_API_BASE_URL is correct
   - Check CORS configuration on backend
   - Verify SSL certificates

3. **Build failures**
   - Check Node.js version (18+ required)
   - Verify all environment variables are set
   - Clear node_modules and reinstall

4. **Performance issues**
   - Enable gzip compression
   - Configure proper caching headers
   - Use CDN for static assets

### Health Checks

```bash
# Check if application is running
curl -f https://yourdomain.com/health

# Check API connectivity
curl -f https://yourdomain.com/api/health

# Monitor logs
tail -f /var/log/nginx/auto-scouter-access.log
```

## Maintenance

### Updates

1. Pull latest code from repository
2. Run deployment script
3. Upload new build to server
4. Clear CDN cache if applicable

### Backups

1. Backup web server configuration
2. Backup SSL certificates
3. Document environment variables

### Monitoring

1. Set up uptime monitoring (UptimeRobot, Pingdom)
2. Monitor error rates in Sentry
3. Track performance metrics in Google Analytics
4. Monitor server resources

## Support

For deployment issues:

1. Check the troubleshooting section above
2. Review server logs
3. Verify environment configuration
4. Contact your hosting provider if needed

## Security Updates

Keep the following updated:

- Node.js and npm packages
- Web server (Nginx/Apache)
- SSL certificates
- Operating system security patches
- Docker images (if using containers)
