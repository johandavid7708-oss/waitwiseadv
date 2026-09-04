-- WaitWise v2.0 Database Schema
-- PostgreSQL with PostGIS for geospatial queries

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS uuid-ossp;

-- ============================================================================
-- LOCATIONS TABLE
-- ============================================================================
CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(50) NOT NULL, -- 'shopping_mall', 'restaurant', 'park', 'hospital', 'store', etc.
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    geom GEOMETRY(POINT, 4326) GENERATED ALWAYS AS (ST_MakePoint(longitude, latitude)) STORED,
    capacity INT,
    typical_peak_start INT DEFAULT 18, -- hour of day (0-23)
    typical_peak_end INT DEFAULT 21,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_locations_geom ON locations USING GIST(geom);
CREATE INDEX idx_locations_category ON locations(category);
CREATE INDEX idx_locations_active ON locations(is_active);

-- ============================================================================
-- USERS TABLE
-- ============================================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    preferences JSONB DEFAULT '{}', -- stores user preferences
    is_trusted_reporter BOOLEAN DEFAULT FALSE, -- verified crowd report contributor
    reputation_score INT DEFAULT 0, -- earned from accurate reports
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_trusted ON users(is_trusted_reporter);

-- ============================================================================
-- USER PREFERENCES (for learning)
-- ============================================================================
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preferred_categories TEXT[], -- categories they visit often
    avoid_crowded BOOLEAN DEFAULT FALSE,
    prefer_quiet BOOLEAN DEFAULT FALSE,
    max_wait_tolerance INT DEFAULT 30, -- minutes
    travel_preferences JSONB DEFAULT '{}', -- car/walk/transit preferences
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_prefs_user_id ON user_preferences(user_id);

-- ============================================================================
-- CROWD REPORTS (Real user-submitted data)
-- ============================================================================
CREATE TABLE crowd_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    crowd_level INT NOT NULL CHECK (crowd_level >= 1 AND crowd_level <= 5), -- 1=empty, 5=packed
    wait_time_minutes INT,
    confidence DECIMAL(3, 2) DEFAULT 0.5, -- 0-1, how confident reporter is
    comment TEXT,
    photo_url VARCHAR(500),
    
    -- For tracking report quality
    accuracy_votes INT DEFAULT 0, -- upvotes if report is accurate
    accuracy_score DECIMAL(3, 2) DEFAULT 0.5, -- AI-calculated accuracy
    is_verified BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reports_location ON crowd_reports(location_id);
CREATE INDEX idx_reports_user ON crowd_reports(user_id);
CREATE INDEX idx_reports_created ON crowd_reports(created_at DESC);
CREATE INDEX idx_reports_verified ON crowd_reports(is_verified);

-- ============================================================================
-- HOURLY AGGREGATED DATA (for fast queries)
-- ============================================================================
CREATE TABLE crowd_aggregates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    hour_timestamp TIMESTAMP NOT NULL, -- rounded to nearest hour
    avg_crowd_level DECIMAL(3, 2),
    max_crowd_level INT,
    min_crowd_level INT,
    avg_wait_time INT,
    report_count INT,
    confidence DECIMAL(3, 2), -- how confident we are in this hour's data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_aggregates_location_time ON crowd_aggregates(location_id, hour_timestamp DESC);
CREATE UNIQUE INDEX idx_aggregates_unique ON crowd_aggregates(location_id, hour_timestamp);

-- ============================================================================
-- PREDICTIONS TABLE (AI-generated forecasts)
-- ============================================================================
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    
    -- Prediction details
    predicted_crowd_level DECIMAL(3, 2),
    predicted_wait_time INT,
    confidence_score DECIMAL(3, 2),
    prediction_horizon INT, -- minutes ahead (30, 60, 120, etc)
    
    -- For measuring prediction accuracy
    actual_crowd_level DECIMAL(3, 2),
    actual_wait_time INT,
    accuracy_error DECIMAL(5, 2), -- difference from actual
    
    -- Model version
    model_version VARCHAR(50),
    
    predicted_at TIMESTAMP NOT NULL,
    forecast_for TIMESTAMP NOT NULL, -- when this prediction is for
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_predictions_location_forecast ON predictions(location_id, forecast_for DESC);
CREATE INDEX idx_predictions_verified ON predictions(verified_at) WHERE verified_at IS NOT NULL;

-- ============================================================================
-- LEARNING PATTERNS (for AI model training)
-- ============================================================================
CREATE TABLE learning_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    
    -- Pattern characteristics
    day_of_week INT, -- 0-6
    hour_of_day INT, -- 0-23
    
    -- Aggregated statistics
    avg_crowd_level DECIMAL(3, 2),
    std_dev_crowd DECIMAL(3, 2),
    avg_wait_time INT,
    peak_probability DECIMAL(3, 2), -- likelihood of peak hour
    
    -- Weather correlation
    weather_condition VARCHAR(50),
    temperature_range VARCHAR(50),
    
    -- Event correlation
    has_events BOOLEAN DEFAULT FALSE,
    is_holiday BOOLEAN DEFAULT FALSE,
    is_weekend BOOLEAN DEFAULT FALSE,
    
    -- Training metadata
    sample_count INT DEFAULT 0, -- how many data points this represents
    confidence DECIMAL(3, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_patterns_location_time ON learning_patterns(location_id, day_of_week, hour_of_day);
CREATE UNIQUE INDEX idx_patterns_unique ON learning_patterns(location_id, day_of_week, hour_of_day);

-- ============================================================================
-- RECOMMENDATIONS TABLE (smart suggestions)
-- ============================================================================
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Alternative locations
    current_location_id UUID REFERENCES locations(id) ON DELETE CASCADE,
    recommended_location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    
    -- Scores
    wait_time_savings INT, -- minutes saved
    distance_km DECIMAL(5, 2),
    travel_time_minutes INT,
    recommendation_score DECIMAL(5, 2), -- overall score
    
    -- Reasoning
    reason VARCHAR(100), -- 'less_crowded', 'closer', 'better_time', etc
    
    -- Feedback
    was_helpful BOOLEAN,
    user_chose BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_recommendations_user ON recommendations(user_id);
CREATE INDEX idx_recommendations_current_location ON recommendations(current_location_id);

-- ============================================================================
-- ALERTS & NOTIFICATIONS
-- ============================================================================
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    location_id UUID REFERENCES locations(id) ON DELETE CASCADE,
    
    -- Alert configuration
    alert_type VARCHAR(50) NOT NULL, -- 'crowd_spike', 'peak_starting', 'less_crowded_alternative'
    trigger_condition JSONB, -- stores the condition that triggered this
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    was_sent BOOLEAN DEFAULT FALSE,
    
    -- Notification details
    title VARCHAR(255),
    message TEXT,
    sent_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alerts_user ON alerts(user_id);
CREATE INDEX idx_alerts_active ON alerts(is_active);

-- ============================================================================
-- FEEDBACK TABLE (for model improvement)
-- ============================================================================
CREATE TABLE user_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    prediction_id UUID REFERENCES predictions(id) ON DELETE SET NULL,
    
    -- Feedback type
    feedback_type VARCHAR(50), -- 'prediction_accurate', 'recommendation_helpful', etc
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_feedback_prediction ON user_feedback(prediction_id);
CREATE INDEX idx_feedback_user ON user_feedback(user_id);

-- ============================================================================
-- MODEL PERFORMANCE TABLE (tracking AI accuracy over time)
-- ============================================================================
CREATE TABLE model_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Model info
    model_version VARCHAR(50),
    location_id UUID REFERENCES locations(id) ON DELETE CASCADE,
    
    -- Metrics
    mean_absolute_error DECIMAL(5, 2),
    root_mean_square_error DECIMAL(5, 2),
    r_squared DECIMAL(5, 4),
    accuracy_percentage DECIMAL(5, 2),
    
    -- Period
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    predictions_evaluated INT
);

CREATE INDEX idx_model_perf_version_location ON model_performance(model_version, location_id);

-- ============================================================================
-- ACTIVITY LOG (for debugging and analysis)
-- ============================================================================
CREATE TABLE activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action_type VARCHAR(100), -- 'report_submitted', 'prediction_requested', 'recommendation_viewed'
    location_id UUID REFERENCES locations(id) ON DELETE SET NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_activity_user ON activity_log(user_id);
CREATE INDEX idx_activity_action ON activity_log(action_type);
CREATE INDEX idx_activity_created ON activity_log(created_at DESC);

-- ============================================================================
-- SEED DATA (Sample Locations)
-- ============================================================================
INSERT INTO locations (name, description, category, latitude, longitude, capacity, typical_peak_start, typical_peak_end) VALUES
    ('Central Mall', 'Major shopping center in downtown', 'shopping_mall', 40.7128, -74.0060, 5000, 18, 21),
    ('Burger House', 'Popular burger restaurant', 'restaurant', 40.7150, -74.0050, 200, 12, 14),
    ('Tech Store', 'Electronics retail shop', 'store', 40.7180, -74.0080, 300, 15, 19),
    ('City Park', 'Large urban park', 'park', 40.7200, -74.0100, 10000, 10, 18),
    ('Cafe Central', 'Coffee shop in business district', 'restaurant', 40.7160, -74.0070, 100, 9, 11),
    ('Times Square', 'Tourism destination', 'landmark', 40.7580, -73.9855, 15000, 12, 23),
    ('Westfield Mall', 'Shopping mall', 'shopping_mall', 40.7350, -74.0200, 3000, 17, 20),
    ('Brookfield Place', 'Shopping center', 'shopping_mall', 40.7130, -74.0130, 2500, 12, 20)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- TRIGGERS FOR TIMESTAMPS
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_locations_updated_at BEFORE UPDATE ON locations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_crowd_reports_updated_at BEFORE UPDATE ON crowd_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_prefs_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_patterns_updated_at BEFORE UPDATE ON learning_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recommendations_updated_at BEFORE UPDATE ON recommendations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alerts_updated_at BEFORE UPDATE ON alerts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
