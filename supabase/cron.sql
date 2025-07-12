-- Auto Scouter Cron Jobs Configuration
-- This file sets up automated scraping schedules using pg_cron extension

-- Enable pg_cron extension (requires superuser privileges)
-- This should be run by Supabase administrators
-- CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule vehicle scraping every 2 hours
-- This will call the scheduled-scraper Edge Function
SELECT cron.schedule(
    'auto-scouter-scraping',
    '0 */2 * * *', -- Every 2 hours
    $$
    SELECT
      net.http_post(
        url := 'https://rwonkzncpzirokqnuoyx.supabase.co/functions/v1/scheduled-scraper',
        headers := '{"Content-Type": "application/json", "Authorization": "Bearer ' || current_setting('app.supabase_service_role_key') || '"}'::jsonb,
        body := '{"source": "cron_job"}'::jsonb
      ) as request_id;
    $$
);

-- Schedule daily cleanup of old scraping logs (keep last 30 days)
SELECT cron.schedule(
    'auto-scouter-cleanup-logs',
    '0 2 * * *', -- Daily at 2 AM
    $$
    DELETE FROM scraping_logs 
    WHERE created_at < NOW() - INTERVAL '30 days';
    $$
);

-- Schedule weekly cleanup of old notifications (keep last 90 days)
SELECT cron.schedule(
    'auto-scouter-cleanup-notifications',
    '0 3 * * 0', -- Weekly on Sunday at 3 AM
    $$
    DELETE FROM notifications 
    WHERE created_at < NOW() - INTERVAL '90 days';
    $$
);

-- Schedule daily cleanup of inactive vehicle listings (older than 7 days)
SELECT cron.schedule(
    'auto-scouter-cleanup-vehicles',
    '0 4 * * *', -- Daily at 4 AM
    $$
    UPDATE vehicle_listings 
    SET is_active = false 
    WHERE is_active = true 
    AND scraped_at < NOW() - INTERVAL '7 days';
    $$
);

-- Schedule hourly alert processing for new vehicles
SELECT cron.schedule(
    'auto-scouter-process-alerts',
    '30 * * * *', -- Every hour at 30 minutes past
    $$
    SELECT
      net.http_post(
        url := 'https://rwonkzncpzirokqnuoyx.supabase.co/functions/v1/scheduled-scraper',
        headers := '{"Content-Type": "application/json", "Authorization": "Bearer ' || current_setting('app.supabase_service_role_key') || '"}'::jsonb,
        body := '{"source": "alert_check", "alerts_only": true}'::jsonb
      ) as request_id;
    $$
);

-- View current cron jobs
-- SELECT * FROM cron.job;

-- To remove a cron job (if needed):
-- SELECT cron.unschedule('auto-scouter-scraping');

-- Alternative: Manual trigger function for testing
CREATE OR REPLACE FUNCTION trigger_manual_scraping()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result json;
BEGIN
    -- Call the scheduled scraper function
    SELECT net.http_post(
        url := 'https://rwonkzncpzirokqnuoyx.supabase.co/functions/v1/scheduled-scraper',
        headers := '{"Content-Type": "application/json", "Authorization": "Bearer ' || current_setting('app.supabase_service_role_key') || '"}'::jsonb,
        body := '{"source": "manual_trigger"}'::jsonb
    ) INTO result;
    
    RETURN result;
END;
$$;

-- Function to check scraping status
CREATE OR REPLACE FUNCTION get_scraping_status()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    status_result json;
BEGIN
    SELECT json_build_object(
        'active_sessions', (
            SELECT COUNT(*) 
            FROM scraping_sessions 
            WHERE status = 'running' 
            AND started_at > NOW() - INTERVAL '1 hour'
        ),
        'last_successful_scrape', (
            SELECT MAX(completed_at) 
            FROM scraping_sessions 
            WHERE status = 'completed'
        ),
        'total_vehicles', (
            SELECT COUNT(*) 
            FROM vehicle_listings 
            WHERE is_active = true
        ),
        'vehicles_today', (
            SELECT COUNT(*) 
            FROM vehicle_listings 
            WHERE created_at > CURRENT_DATE
        ),
        'pending_notifications', (
            SELECT COUNT(*) 
            FROM notifications 
            WHERE is_read = false
        ),
        'active_alerts', (
            SELECT COUNT(*) 
            FROM alerts 
            WHERE is_active = true
        )
    ) INTO status_result;
    
    RETURN status_result;
END;
$$;

-- Function to get scraping statistics
CREATE OR REPLACE FUNCTION get_scraping_stats(days_back integer DEFAULT 7)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    stats_result json;
BEGIN
    SELECT json_build_object(
        'period_days', days_back,
        'total_sessions', (
            SELECT COUNT(*) 
            FROM scraping_sessions 
            WHERE started_at > NOW() - (days_back || ' days')::interval
        ),
        'successful_sessions', (
            SELECT COUNT(*) 
            FROM scraping_sessions 
            WHERE status = 'completed' 
            AND started_at > NOW() - (days_back || ' days')::interval
        ),
        'total_vehicles_scraped', (
            SELECT COALESCE(SUM(total_vehicles_found), 0) 
            FROM scraping_sessions 
            WHERE started_at > NOW() - (days_back || ' days')::interval
        ),
        'new_vehicles_added', (
            SELECT COALESCE(SUM(total_vehicles_new), 0) 
            FROM scraping_sessions 
            WHERE started_at > NOW() - (days_back || ' days')::interval
        ),
        'vehicles_updated', (
            SELECT COALESCE(SUM(total_vehicles_updated), 0) 
            FROM scraping_sessions 
            WHERE started_at > NOW() - (days_back || ' days')::interval
        ),
        'total_errors', (
            SELECT COALESCE(SUM(total_errors), 0) 
            FROM scraping_sessions 
            WHERE started_at > NOW() - (days_back || ' days')::interval
        ),
        'average_session_duration', (
            SELECT COALESCE(
                AVG(EXTRACT(EPOCH FROM (completed_at - started_at))), 
                0
            ) 
            FROM scraping_sessions 
            WHERE status = 'completed' 
            AND started_at > NOW() - (days_back || ' days')::interval
        ),
        'last_update', NOW()
    ) INTO stats_result;
    
    RETURN stats_result;
END;
$$;

-- Create indexes for better performance on cron operations
CREATE INDEX IF NOT EXISTS idx_scraping_sessions_status_started 
ON scraping_sessions(status, started_at);

CREATE INDEX IF NOT EXISTS idx_vehicle_listings_active_scraped 
ON vehicle_listings(is_active, scraped_at);

CREATE INDEX IF NOT EXISTS idx_notifications_read_created 
ON notifications(is_read, created_at);

CREATE INDEX IF NOT EXISTS idx_scraping_logs_created 
ON scraping_logs(created_at);

-- Grant necessary permissions for cron operations
-- GRANT USAGE ON SCHEMA cron TO postgres;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cron TO postgres;
