-- Auto Scouter Supabase Migration Script
-- This script creates all necessary tables for the Auto Scouter application

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Vehicle Listings Table (Main table)
CREATE TABLE IF NOT EXISTS vehicle_listings (
    id BIGSERIAL PRIMARY KEY,
    
    -- Basic vehicle information
    make VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    year INTEGER,
    price INTEGER,
    currency VARCHAR(3) DEFAULT 'EUR',
    mileage INTEGER,
    
    -- Technical specifications
    fuel_type VARCHAR(20),
    transmission VARCHAR(20),
    engine_size DECIMAL(3,1),
    engine_power INTEGER,
    body_type VARCHAR(30),
    doors INTEGER,
    seats INTEGER,
    color_exterior VARCHAR(50),
    color_interior VARCHAR(50),
    
    -- Condition and history
    condition VARCHAR(20) DEFAULT 'used',
    accident_history BOOLEAN DEFAULT FALSE,
    service_history BOOLEAN DEFAULT TRUE,
    previous_owners INTEGER,
    
    -- Location information
    dealer_name VARCHAR(200),
    dealer_location VARCHAR(200),
    city VARCHAR(100),
    region VARCHAR(100),
    country VARCHAR(50) DEFAULT 'IT',
    
    -- Media and content
    primary_image_url VARCHAR(500),
    description TEXT,
    features TEXT,
    
    -- Source and metadata
    source_website VARCHAR(100) NOT NULL,
    source VARCHAR(50) DEFAULT 'unknown',
    source_country VARCHAR(3) DEFAULT 'IT',
    external_id VARCHAR(100),
    url VARCHAR(500) UNIQUE,
    
    -- Data quality
    data_quality_score DECIMAL(3,2) DEFAULT 0.0,
    duplicate_hash VARCHAR(64),
    duplicate_of BIGINT REFERENCES vehicle_listings(id),
    is_duplicate BOOLEAN DEFAULT FALSE,
    confidence_score DECIMAL(3,2) DEFAULT 1.0,
    
    -- Status and timestamps
    is_active BOOLEAN DEFAULT TRUE,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vehicle Images Table
CREATE TABLE vehicle_images (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id BIGINT NOT NULL REFERENCES vehicle_listings(id) ON DELETE CASCADE,
    image_url VARCHAR(500) NOT NULL,
    image_type VARCHAR(20) DEFAULT 'exterior',
    display_order INTEGER DEFAULT 0,
    alt_text VARCHAR(200),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Price History Table
CREATE TABLE price_history (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id BIGINT NOT NULL REFERENCES vehicle_listings(id) ON DELETE CASCADE,
    old_price INTEGER,
    new_price INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    price_change INTEGER,
    change_percentage DECIMAL(5,2),
    change_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alerts Table (Single-user mode)
CREATE TABLE alerts (
    id BIGSERIAL PRIMARY KEY,
    
    -- Alert identification
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Vehicle criteria
    make VARCHAR(50),
    model VARCHAR(100),
    min_year INTEGER,
    max_year INTEGER,
    min_price INTEGER,
    max_price INTEGER,
    max_mileage INTEGER,
    fuel_type VARCHAR(20),
    transmission VARCHAR(20),
    body_type VARCHAR(30),
    
    -- Location criteria
    city VARCHAR(100),
    region VARCHAR(100),
    location_radius INTEGER,
    
    -- Advanced criteria
    min_engine_power INTEGER,
    max_engine_power INTEGER,
    condition VARCHAR(20),
    
    -- Alert behavior
    is_active BOOLEAN DEFAULT TRUE,
    notification_frequency VARCHAR(20) DEFAULT 'immediate',
    last_triggered TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,
    max_notifications_per_day INTEGER DEFAULT 5,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Notifications Table
CREATE TABLE notifications (
    id BIGSERIAL PRIMARY KEY,
    
    -- Relationships
    alert_id BIGINT REFERENCES alerts(id) ON DELETE SET NULL,
    listing_id BIGINT REFERENCES vehicle_listings(id) ON DELETE SET NULL,
    
    -- Notification details
    notification_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    
    -- Content
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    content_data JSONB,
    
    -- Delivery tracking
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    
    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Additional fields
    external_id VARCHAR(100),
    priority INTEGER DEFAULT 1,
    is_read BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Favorites Table (for user favorites)
CREATE TABLE favorites (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id BIGINT NOT NULL REFERENCES vehicle_listings(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT
);

-- Scraping Logs Table
CREATE TABLE scraping_logs (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id BIGINT REFERENCES vehicle_listings(id) ON DELETE SET NULL,
    session_id VARCHAR(100),
    source_website VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    response_time_ms INTEGER,
    data_extracted JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Scraping Sessions Table
CREATE TABLE scraping_sessions (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    source_website VARCHAR(100) NOT NULL,
    scraper_version VARCHAR(20),
    user_agent VARCHAR(500),
    
    -- Statistics
    total_pages_scraped INTEGER DEFAULT 0,
    total_vehicles_found INTEGER DEFAULT 0,
    total_vehicles_new INTEGER DEFAULT 0,
    total_vehicles_updated INTEGER DEFAULT 0,
    total_vehicles_skipped INTEGER DEFAULT 0,
    total_duplicates_found INTEGER DEFAULT 0,
    total_errors INTEGER DEFAULT 0,
    
    -- Performance metrics
    average_response_time DECIMAL(8,2),
    total_data_transferred BIGINT,
    
    -- Session timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    status VARCHAR(20) DEFAULT 'running',
    error_message TEXT
);

-- Create Indexes for Performance
CREATE INDEX idx_vehicle_listings_make ON vehicle_listings(make);
CREATE INDEX idx_vehicle_listings_model ON vehicle_listings(model);
CREATE INDEX idx_vehicle_listings_price ON vehicle_listings(price);
CREATE INDEX idx_vehicle_listings_year ON vehicle_listings(year);
CREATE INDEX idx_vehicle_listings_mileage ON vehicle_listings(mileage);
CREATE INDEX idx_vehicle_listings_city ON vehicle_listings(city);
CREATE INDEX idx_vehicle_listings_source ON vehicle_listings(source_website);
CREATE INDEX idx_vehicle_listings_active ON vehicle_listings(is_active);
CREATE INDEX idx_vehicle_listings_scraped ON vehicle_listings(scraped_at);
CREATE INDEX idx_vehicle_listings_duplicate ON vehicle_listings(is_duplicate);

CREATE INDEX idx_vehicle_images_vehicle ON vehicle_images(vehicle_id);
CREATE INDEX idx_price_history_vehicle ON price_history(vehicle_id);
CREATE INDEX idx_price_history_date ON price_history(change_date);

CREATE INDEX idx_alerts_active ON alerts(is_active);
CREATE INDEX idx_alerts_criteria ON alerts(make, model, min_price, max_price);
CREATE INDEX idx_alerts_location ON alerts(city, region);

CREATE INDEX idx_notifications_alert ON notifications(alert_id);
CREATE INDEX idx_notifications_listing ON notifications(listing_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_type ON notifications(notification_type);

CREATE INDEX idx_favorites_vehicle ON favorites(vehicle_id);
CREATE INDEX idx_scraping_logs_session ON scraping_logs(session_id);
CREATE INDEX idx_scraping_sessions_website ON scraping_sessions(source_website);

-- Enable Row Level Security (RLS)
ALTER TABLE vehicle_listings ENABLE ROW LEVEL SECURITY;
ALTER TABLE vehicle_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE price_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraping_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraping_sessions ENABLE ROW LEVEL SECURITY;

-- Create RLS Policies (Public access for single-user app)
CREATE POLICY "Allow all operations on vehicle_listings" ON vehicle_listings FOR ALL USING (true);
CREATE POLICY "Allow all operations on vehicle_images" ON vehicle_images FOR ALL USING (true);
CREATE POLICY "Allow all operations on price_history" ON price_history FOR ALL USING (true);
CREATE POLICY "Allow all operations on alerts" ON alerts FOR ALL USING (true);
CREATE POLICY "Allow all operations on notifications" ON notifications FOR ALL USING (true);
CREATE POLICY "Allow all operations on favorites" ON favorites FOR ALL USING (true);
CREATE POLICY "Allow all operations on scraping_logs" ON scraping_logs FOR ALL USING (true);
CREATE POLICY "Allow all operations on scraping_sessions" ON scraping_sessions FOR ALL USING (true);

-- Enable Real-time for key tables
ALTER PUBLICATION supabase_realtime ADD TABLE vehicle_listings;
ALTER PUBLICATION supabase_realtime ADD TABLE alerts;
ALTER PUBLICATION supabase_realtime ADD TABLE notifications;
ALTER PUBLICATION supabase_realtime ADD TABLE favorites;

-- Create Functions for Common Operations
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create Triggers for Updated At
CREATE TRIGGER update_vehicle_listings_updated_at BEFORE UPDATE ON vehicle_listings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alerts_updated_at BEFORE UPDATE ON alerts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notifications_updated_at BEFORE UPDATE ON notifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create Search Function
CREATE OR REPLACE FUNCTION search_vehicles(
    p_make TEXT DEFAULT NULL,
    p_model TEXT DEFAULT NULL,
    p_min_price INTEGER DEFAULT NULL,
    p_max_price INTEGER DEFAULT NULL,
    p_min_year INTEGER DEFAULT NULL,
    p_max_year INTEGER DEFAULT NULL,
    p_max_mileage INTEGER DEFAULT NULL,
    p_city TEXT DEFAULT NULL,
    p_fuel_type TEXT DEFAULT NULL,
    p_transmission TEXT DEFAULT NULL,
    p_body_type TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 50,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    id BIGINT,
    make VARCHAR(50),
    model VARCHAR(100),
    year INTEGER,
    price INTEGER,
    mileage INTEGER,
    fuel_type VARCHAR(20),
    transmission VARCHAR(20),
    body_type VARCHAR(30),
    city VARCHAR(100),
    primary_image_url VARCHAR(500),
    url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        vl.id, vl.make, vl.model, vl.year, vl.price, vl.mileage,
        vl.fuel_type, vl.transmission, vl.body_type, vl.city,
        vl.primary_image_url, vl.url, vl.created_at
    FROM vehicle_listings vl
    WHERE
        vl.is_active = true
        AND (p_make IS NULL OR vl.make ILIKE '%' || p_make || '%')
        AND (p_model IS NULL OR vl.model ILIKE '%' || p_model || '%')
        AND (p_min_price IS NULL OR vl.price >= p_min_price)
        AND (p_max_price IS NULL OR vl.price <= p_max_price)
        AND (p_min_year IS NULL OR vl.year >= p_min_year)
        AND (p_max_year IS NULL OR vl.year <= p_max_year)
        AND (p_max_mileage IS NULL OR vl.mileage <= p_max_mileage)
        AND (p_city IS NULL OR vl.city ILIKE '%' || p_city || '%')
        AND (p_fuel_type IS NULL OR vl.fuel_type = p_fuel_type)
        AND (p_transmission IS NULL OR vl.transmission = p_transmission)
        AND (p_body_type IS NULL OR vl.body_type = p_body_type)
    ORDER BY vl.created_at DESC
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;
