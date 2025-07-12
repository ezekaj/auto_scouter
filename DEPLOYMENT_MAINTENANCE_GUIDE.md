# 🚀 Auto Scouter Deployment & Maintenance Guide

## 📋 **Overview**

This guide provides comprehensive instructions for deploying, maintaining, and monitoring the Auto Scouter application on Supabase infrastructure.

## 🏗️ **System Architecture**

```
carmarket.ayvens.com → Supabase Edge Functions → PostgreSQL Database → Real-time Subscriptions → Mobile App
                                ↓
                        Cron Jobs → Alert Processing → Firebase → Push Notifications
```

---

## 🚀 **DEPLOYMENT PROCEDURES**

### **Current Deployment Status**
- **Status**: ✅ **FULLY DEPLOYED AND OPERATIONAL**
- **Platform**: Supabase (https://rwonkzncpzirokqnuoyx.supabase.co)
- **Environment**: Production
- **Last Deployment**: July 12, 2025

### **Supabase Project Configuration**
```bash
Project ID: rwonkzncpzirokqnuoyx
Region: us-east-1
Database: PostgreSQL 15
Real-time: Enabled
Edge Functions: Deployed globally
```

### **Deployed Components**
1. **Database Schema**: All tables and indexes created
2. **Edge Functions**: 
   - vehicle-api (API endpoints)
   - vehicle-scraper (Ayvens scraping)
   - scheduled-scraper (Automated scraping)
3. **Real-time Subscriptions**: Enabled for all tables
4. **Cron Jobs**: Automated scraping every 2 hours
5. **Row Level Security**: Configured for data protection

---

## 🔧 **MAINTENANCE PROCEDURES**

### **Daily Maintenance (Automated)**
- **Automated Scraping**: Runs every 2 hours via cron
- **Database Cleanup**: Old logs cleaned automatically
- **Health Monitoring**: Continuous system monitoring
- **Backup Creation**: Automated daily backups

### **Weekly Maintenance (Manual)**
1. **Performance Review**
   ```bash
   # Check Supabase dashboard metrics
   # Review Edge Function performance
   # Monitor database query performance
   # Validate real-time connection health
   ```

2. **Data Quality Check**
   ```sql
   -- Check recent scraping sessions
   SELECT * FROM scraping_sessions 
   WHERE started_at > NOW() - INTERVAL '7 days'
   ORDER BY started_at DESC;
   
   -- Verify vehicle data freshness
   SELECT COUNT(*), MAX(created_at) 
   FROM vehicle_listings 
   WHERE is_active = true;
   
   -- Check alert processing
   SELECT COUNT(*) FROM notifications 
   WHERE created_at > NOW() - INTERVAL '7 days';
   ```

3. **Error Log Review**
   ```sql
   -- Check for errors in scraping logs
   SELECT * FROM scraping_logs 
   WHERE log_level = 'ERROR' 
   AND created_at > NOW() - INTERVAL '7 days';
   ```

### **Monthly Maintenance**
1. **Security Updates**
   - Review and update dependencies
   - Check for Supabase platform updates
   - Validate security configurations

2. **Performance Optimization**
   - Analyze database performance
   - Optimize slow queries
   - Review and update indexes

3. **Capacity Planning**
   - Monitor storage usage
   - Review API usage patterns
   - Plan for scaling needs

---

## 📊 **MONITORING & HEALTH CHECKS**

### **Key Metrics to Monitor**

#### **System Health**
- **Supabase Project Status**: Online/Offline
- **Database Connections**: Active connections count
- **Edge Function Response Times**: <2 seconds target
- **Real-time Connections**: Active WebSocket connections
- **Error Rates**: <1% target

#### **Application Metrics**
- **Scraping Success Rate**: >99% target
- **Vehicle Data Freshness**: <4 hours since last update
- **Alert Processing Time**: <30 seconds target
- **Notification Delivery Rate**: >95% target
- **Mobile App Crash Rate**: <0.1% target

### **Monitoring Tools**

#### **Supabase Dashboard**
- **URL**: https://supabase.com/dashboard/project/rwonkzncpzirokqnuoyx
- **Metrics**: Database performance, API usage, real-time connections
- **Logs**: Edge Function logs, database logs, real-time logs
- **Alerts**: Automated alerts for critical issues

#### **Database Monitoring**
```sql
-- System health check function
SELECT * FROM get_scraping_status();

-- Performance metrics
SELECT * FROM get_scraping_stats(7); -- Last 7 days
```

#### **Edge Function Monitoring**
- **Logs**: Available in Supabase dashboard
- **Metrics**: Response times, error rates, invocation counts
- **Alerts**: Automatic alerts for function failures

---

## 🚨 **TROUBLESHOOTING GUIDE**

### **Common Issues and Solutions**

#### **Scraping Failures**
**Symptoms**: No new vehicles, scraping session errors
**Diagnosis**:
```sql
SELECT * FROM scraping_sessions 
WHERE status = 'failed' 
ORDER BY started_at DESC LIMIT 5;
```
**Solutions**:
1. Check carmarket.ayvens.com accessibility
2. Verify authentication credentials
3. Review scraping logs for specific errors
4. Restart scraping manually if needed

#### **Real-time Connection Issues**
**Symptoms**: Mobile app not receiving updates
**Diagnosis**: Check Supabase real-time dashboard
**Solutions**:
1. Verify real-time is enabled in Supabase
2. Check WebSocket connection limits
3. Restart mobile app to reconnect
4. Review real-time subscription configuration

#### **Database Performance Issues**
**Symptoms**: Slow API responses, timeouts
**Diagnosis**:
```sql
-- Check slow queries
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC LIMIT 10;
```
**Solutions**:
1. Optimize slow queries
2. Add missing indexes
3. Update table statistics
4. Consider query caching

#### **Mobile App Issues**
**Symptoms**: App crashes, connection failures
**Diagnosis**: Check device logs and Supabase logs
**Solutions**:
1. Verify internet connectivity
2. Check Supabase service status
3. Clear app cache and restart
4. Reinstall app if necessary

---

## 🔄 **BACKUP & RECOVERY**

### **Automated Backups**
- **Database**: Daily automated backups via Supabase
- **Retention**: 30 days for free tier, longer for paid plans
- **Location**: Supabase managed backup storage
- **Recovery**: Point-in-time recovery available

### **Manual Backup Procedures**
```bash
# Export database schema
supabase db dump --schema-only > schema_backup.sql

# Export data
supabase db dump --data-only > data_backup.sql

# Full backup
supabase db dump > full_backup.sql
```

### **Recovery Procedures**
```bash
# Restore from backup
supabase db reset
supabase db push
# Restore data from backup file if needed
```

---

## 🔐 **SECURITY MAINTENANCE**

### **Security Checklist**
- [ ] Review and rotate API keys quarterly
- [ ] Monitor access logs for suspicious activity
- [ ] Update dependencies for security patches
- [ ] Validate Row Level Security policies
- [ ] Check SSL certificate status
- [ ] Review user permissions and access

### **Security Monitoring**
```sql
-- Monitor authentication attempts
SELECT * FROM auth.audit_log_entries 
WHERE created_at > NOW() - INTERVAL '24 hours';

-- Check for unusual database activity
SELECT * FROM pg_stat_activity 
WHERE state = 'active';
```

---

## 📈 **SCALING CONSIDERATIONS**

### **Current Capacity**
- **Database**: Supabase free tier (500MB limit)
- **API Requests**: 50,000 per month
- **Real-time**: 200 concurrent connections
- **Edge Functions**: 500,000 invocations per month

### **Scaling Triggers**
- Database storage >80% capacity
- API requests >80% of monthly limit
- Real-time connections >80% of limit
- Edge Function invocations >80% of limit

### **Scaling Actions**
1. **Upgrade Supabase Plan**: Move to Pro plan for higher limits
2. **Optimize Queries**: Reduce database load
3. **Implement Caching**: Reduce API calls
4. **Archive Old Data**: Clean up historical data

---

## 📞 **SUPPORT CONTACTS**

### **Technical Support**
- **Supabase Support**: https://supabase.com/support
- **Documentation**: https://supabase.com/docs
- **Community**: https://github.com/supabase/supabase/discussions

### **Emergency Procedures**
1. **System Down**: Check Supabase status page
2. **Data Loss**: Restore from automated backups
3. **Security Breach**: Rotate keys, review logs
4. **Performance Issues**: Scale resources, optimize queries

---

## 📅 **MAINTENANCE SCHEDULE**

### **Daily (Automated)**
- Automated scraping every 2 hours
- Health checks and monitoring
- Automated backups

### **Weekly (Manual)**
- Performance review
- Error log analysis
- Data quality checks

### **Monthly (Manual)**
- Security updates
- Performance optimization
- Capacity planning

### **Quarterly (Manual)**
- Comprehensive security review
- Dependency updates
- Disaster recovery testing

---

## ✅ **DEPLOYMENT CHECKLIST**

### **Pre-Deployment**
- [ ] Code review completed
- [ ] Tests passing
- [ ] Security scan completed
- [ ] Performance testing done
- [ ] Documentation updated

### **Deployment**
- [ ] Database migrations applied
- [ ] Edge Functions deployed
- [ ] Configuration updated
- [ ] Health checks passing
- [ ] Monitoring configured

### **Post-Deployment**
- [ ] System health verified
- [ ] Performance metrics normal
- [ ] User acceptance testing
- [ ] Documentation updated
- [ ] Team notified

---

**Maintenance Guide Version**: 2.0.0  
**Last Updated**: July 12, 2025  
**Next Review**: August 12, 2025  
**Maintained By**: Auto Scouter Team
