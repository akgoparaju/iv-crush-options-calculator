-- Initialize the Options Trading Database
-- This file runs automatically when the PostgreSQL container starts

-- Create the main database (already created by POSTGRES_DB env var)
-- Extensions for UUID and other utilities
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create tables for future use (Phase 5)
-- Users table for authentication system
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Analysis results cache table
CREATE TABLE IF NOT EXISTS analysis_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(10) NOT NULL,
    parameters JSONB NOT NULL,
    result JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create index for cache lookups
CREATE INDEX IF NOT EXISTS idx_analysis_cache_symbol_params 
ON analysis_cache USING gin(symbol, parameters);

-- Create index for cache expiration cleanup
CREATE INDEX IF NOT EXISTS idx_analysis_cache_expires_at 
ON analysis_cache(expires_at);

-- Portfolio management tables (Phase 5.2)
CREATE TABLE IF NOT EXISTS portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    initial_capital DECIMAL(15,4) NOT NULL,
    current_value DECIMAL(15,4) DEFAULT 0,
    total_invested DECIMAL(15,4) DEFAULT 0,
    available_cash DECIMAL(15,4) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, name)
);

-- Positions table
CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    strategy_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'open',
    entry_date DATE NOT NULL,
    exit_date DATE,
    entry_cost DECIMAL(15,4) NOT NULL,
    exit_value DECIMAL(15,4),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Option legs table
CREATE TABLE IF NOT EXISTS option_legs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    position_id UUID REFERENCES positions(id) ON DELETE CASCADE,
    option_type VARCHAR(10) NOT NULL, -- 'call' or 'put'
    strike_price DECIMAL(10,4) NOT NULL,
    expiration_date DATE NOT NULL,
    action VARCHAR(20) NOT NULL, -- 'buy_to_open', 'sell_to_open', etc.
    contracts INTEGER NOT NULL,
    premium DECIMAL(10,4) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_positions_portfolio_id ON positions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_option_legs_position_id ON option_legs(position_id);
CREATE INDEX IF NOT EXISTS idx_option_legs_expiration ON option_legs(expiration_date);

-- Legacy portfolio positions table (keeping for backward compatibility)
CREATE TABLE IF NOT EXISTS portfolio_positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    contracts INTEGER NOT NULL,
    entry_price DECIMAL(10,4) NOT NULL,
    entry_date DATE NOT NULL,
    expiration_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for portfolio lookups
CREATE INDEX IF NOT EXISTS idx_portfolio_user_symbol 
ON portfolio_positions(user_id, symbol);

-- Market screening tables (Phase 5.3)
CREATE TABLE IF NOT EXISTS screens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    criteria JSONB NOT NULL,
    symbols TEXT[],
    frequency VARCHAR(20) NOT NULL DEFAULT 'hourly',
    is_active BOOLEAN DEFAULT TRUE,
    alert_threshold INTEGER DEFAULT 5,
    last_run TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, name)
);

-- Screening results table
CREATE TABLE IF NOT EXISTS screening_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    screen_id UUID REFERENCES screens(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    current_price DECIMAL(10,4) NOT NULL,
    score DECIMAL(5,2) NOT NULL,
    rank VARCHAR(20) NOT NULL,
    criteria_scores JSONB NOT NULL,
    market_data JSONB NOT NULL,
    opportunity_details JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    screen_id UUID REFERENCES screens(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    alert_types TEXT[] NOT NULL,
    conditions JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alert notifications table
CREATE TABLE IF NOT EXISTS alert_notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_id UUID REFERENCES alerts(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    screen_name VARCHAR(100) NOT NULL,
    opportunities_count INTEGER NOT NULL,
    message TEXT NOT NULL,
    alert_types TEXT[] NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for screening tables
CREATE INDEX IF NOT EXISTS idx_screens_user_id ON screens(user_id);
CREATE INDEX IF NOT EXISTS idx_screens_active ON screens(is_active);
CREATE INDEX IF NOT EXISTS idx_screens_frequency ON screens(frequency);
CREATE INDEX IF NOT EXISTS idx_screening_results_screen_id ON screening_results(screen_id);
CREATE INDEX IF NOT EXISTS idx_screening_results_symbol ON screening_results(symbol);
CREATE INDEX IF NOT EXISTS idx_screening_results_timestamp ON screening_results(timestamp);
CREATE INDEX IF NOT EXISTS idx_screening_results_score ON screening_results(score DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_screen_id ON alerts(screen_id);
CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(is_active);
CREATE INDEX IF NOT EXISTS idx_alert_notifications_user_id ON alert_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_notifications_unread ON alert_notifications(is_read);

-- Educational content tables (Phase 5.4)
CREATE TABLE IF NOT EXISTS educational_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(200) NOT NULL,
    subtitle VARCHAR(300),
    content_type VARCHAR(50) NOT NULL,
    difficulty_level VARCHAR(50) NOT NULL,
    learning_paths TEXT[] DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    summary TEXT NOT NULL,
    content_body TEXT NOT NULL,
    author_id UUID REFERENCES users(id) ON DELETE CASCADE,
    estimated_read_time INTEGER NOT NULL,
    prerequisites TEXT[] DEFAULT '{}',
    key_concepts TEXT[] DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'draft',
    is_premium BOOLEAN DEFAULT FALSE,
    featured BOOLEAN DEFAULT FALSE,
    views_count INTEGER DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    bookmarks_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User interactions table (likes, bookmarks, views, etc.)
CREATE TABLE IF NOT EXISTS user_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content_id UUID REFERENCES educational_content(id) ON DELETE CASCADE,
    interaction_type VARCHAR(50) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, content_id, interaction_type)
);

-- Comments table
CREATE TABLE IF NOT EXISTS content_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID REFERENCES educational_content(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    parent_comment_id UUID REFERENCES content_comments(id) ON DELETE CASCADE,
    likes_count INTEGER DEFAULT 0,
    is_edited BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Educational quizzes table
CREATE TABLE IF NOT EXISTS educational_quizzes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    content_id UUID REFERENCES educational_content(id) ON DELETE SET NULL,
    author_id UUID REFERENCES users(id) ON DELETE CASCADE,
    difficulty_level VARCHAR(50) NOT NULL,
    learning_paths TEXT[] DEFAULT '{}',
    questions JSONB NOT NULL,
    passing_score INTEGER DEFAULT 70,
    time_limit INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Quiz attempts table
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    quiz_id UUID REFERENCES educational_quizzes(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    score INTEGER NOT NULL,
    passed BOOLEAN NOT NULL,
    time_taken INTEGER NOT NULL,
    answers JSONB NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User profiles table for additional user information
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    bio TEXT,
    avatar_url VARCHAR(500),
    expertise_level VARCHAR(50) DEFAULT 'beginner',
    learning_preferences JSONB DEFAULT '{}',
    achievements TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for educational content tables
CREATE INDEX IF NOT EXISTS idx_educational_content_author_id ON educational_content(author_id);
CREATE INDEX IF NOT EXISTS idx_educational_content_status ON educational_content(status);
CREATE INDEX IF NOT EXISTS idx_educational_content_content_type ON educational_content(content_type);
CREATE INDEX IF NOT EXISTS idx_educational_content_difficulty ON educational_content(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_educational_content_learning_paths ON educational_content USING gin(learning_paths);
CREATE INDEX IF NOT EXISTS idx_educational_content_tags ON educational_content USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_educational_content_featured ON educational_content(featured);
CREATE INDEX IF NOT EXISTS idx_educational_content_published_at ON educational_content(published_at);
CREATE INDEX IF NOT EXISTS idx_educational_content_views ON educational_content(views_count DESC);
CREATE INDEX IF NOT EXISTS idx_educational_content_likes ON educational_content(likes_count DESC);
CREATE INDEX IF NOT EXISTS idx_educational_content_text_search ON educational_content USING gin(to_tsvector('english', title || ' ' || summary || ' ' || content_body));

CREATE INDEX IF NOT EXISTS idx_user_interactions_user_id ON user_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_interactions_content_id ON user_interactions(content_id);
CREATE INDEX IF NOT EXISTS idx_user_interactions_type ON user_interactions(interaction_type);

CREATE INDEX IF NOT EXISTS idx_content_comments_content_id ON content_comments(content_id);
CREATE INDEX IF NOT EXISTS idx_content_comments_user_id ON content_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_content_comments_parent_id ON content_comments(parent_comment_id);

CREATE INDEX IF NOT EXISTS idx_educational_quizzes_content_id ON educational_quizzes(content_id);
CREATE INDEX IF NOT EXISTS idx_educational_quizzes_author_id ON educational_quizzes(author_id);
CREATE INDEX IF NOT EXISTS idx_educational_quizzes_active ON educational_quizzes(is_active);

CREATE INDEX IF NOT EXISTS idx_quiz_attempts_quiz_id ON quiz_attempts(quiz_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user_id ON quiz_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_passed ON quiz_attempts(passed);

-- Insert sample data for development (will be ignored if already exists)
INSERT INTO users (email, username, hashed_password) 
VALUES ('demo@example.com', 'demo', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LebrHM6tzuffsbeKG') 
ON CONFLICT (email) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;