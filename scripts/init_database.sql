-- AgentMarket Database Schema
-- This script creates all required tables for the marketplace

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table for off-chain user data
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    wallet_address VARCHAR(44) UNIQUE NOT NULL,
    username VARCHAR(50),
    email VARCHAR(255),
    profile_image_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_wallet ON users(wallet_address);

-- Agents table for off-chain agent metadata
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(44) NOT NULL UNIQUE,
    creator_wallet VARCHAR(44) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    capabilities JSONB DEFAULT '[]'::jsonb,
    pricing JSONB DEFAULT '{}'::jsonb,
    endpoint TEXT,
    ipfs_hash VARCHAR(100),
    nft_mint VARCHAR(44),
    active BOOLEAN DEFAULT true,
    total_earnings BIGINT DEFAULT 0,
    total_services INTEGER DEFAULT 0,
    average_rating DECIMAL(3,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agents_creator ON agents(creator_wallet);
CREATE INDEX IF NOT EXISTS idx_agents_active ON agents(active);
CREATE INDEX IF NOT EXISTS idx_agents_rating ON agents(average_rating DESC);
CREATE INDEX IF NOT EXISTS idx_agents_created ON agents(created_at DESC);

-- Service requests table
CREATE TABLE IF NOT EXISTS service_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id VARCHAR(44) NOT NULL UNIQUE,
    agent_id VARCHAR(44) NOT NULL,
    user_wallet VARCHAR(44) NOT NULL,
    amount BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    request_data JSONB DEFAULT '{}'::jsonb,
    result_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    CONSTRAINT fk_agent FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_requests_agent ON service_requests(agent_id);
CREATE INDEX IF NOT EXISTS idx_requests_user ON service_requests(user_wallet);
CREATE INDEX IF NOT EXISTS idx_requests_status ON service_requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_created ON service_requests(created_at DESC);

-- Ratings table for agent reviews
CREATE TABLE IF NOT EXISTS ratings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rating_id VARCHAR(44) NOT NULL UNIQUE,
    agent_id VARCHAR(44) NOT NULL,
    user_wallet VARCHAR(44) NOT NULL,
    request_id VARCHAR(44) NOT NULL UNIQUE,
    stars INTEGER NOT NULL CHECK (stars >= 1 AND stars <= 5),
    quality INTEGER CHECK (quality >= 1 AND quality <= 5),
    speed INTEGER CHECK (speed >= 1 AND speed <= 5),
    value INTEGER CHECK (value >= 1 AND value <= 5),
    review_text TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_agent_rating FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE,
    CONSTRAINT fk_request_rating FOREIGN KEY (request_id) REFERENCES service_requests(request_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ratings_agent ON ratings(agent_id);
CREATE INDEX IF NOT EXISTS idx_ratings_stars ON ratings(stars DESC);
CREATE INDEX IF NOT EXISTS idx_ratings_created ON ratings(created_at DESC);

-- Disputes table for handling service disputes
CREATE TABLE IF NOT EXISTS disputes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dispute_id VARCHAR(44) NOT NULL UNIQUE,
    request_id VARCHAR(44) NOT NULL,
    agent_id VARCHAR(44) NOT NULL,
    user_wallet VARCHAR(44) NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    resolution TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    CONSTRAINT fk_request_dispute FOREIGN KEY (request_id) REFERENCES service_requests(request_id) ON DELETE CASCADE,
    CONSTRAINT fk_agent_dispute FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_disputes_request ON disputes(request_id);
CREATE INDEX IF NOT EXISTS idx_disputes_agent ON disputes(agent_id);
CREATE INDEX IF NOT EXISTS idx_disputes_status ON disputes(status);
CREATE INDEX IF NOT EXISTS idx_disputes_created ON disputes(created_at DESC);

-- SecurityGuard scan history
CREATE TABLE IF NOT EXISTS security_scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id VARCHAR(44) NOT NULL UNIQUE,
    user_wallet VARCHAR(44),
    transaction_hash VARCHAR(88),
    risk_level VARCHAR(10) NOT NULL CHECK (risk_level IN ('SAFE', 'CAUTION', 'DANGER')),
    risk_score INTEGER NOT NULL CHECK (risk_score >= 0 AND risk_score <= 100),
    scan_time_ms INTEGER NOT NULL,
    confidence DECIMAL(3,2) NOT NULL,
    threats_detected JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scans_user ON security_scans(user_wallet);
CREATE INDEX IF NOT EXISTS idx_scans_risk ON security_scans(risk_level);
CREATE INDEX IF NOT EXISTS idx_scans_created ON security_scans(created_at DESC);

-- Analytics table for platform metrics
CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB DEFAULT '{}'::jsonb,
    user_wallet VARCHAR(44),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analytics_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_user ON analytics_events(user_wallet);
CREATE INDEX IF NOT EXISTS idx_analytics_created ON analytics_events(created_at DESC);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for agents table
DROP TRIGGER IF EXISTS update_agents_updated_at ON agents;
CREATE TRIGGER update_agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default platform configuration
CREATE TABLE IF NOT EXISTS platform_config (
    key VARCHAR(50) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO platform_config (key, value) VALUES
    ('royalty_split', '{"creator": 85, "platform": 10, "treasury": 5}'::jsonb),
    ('platform_wallet', '"PLATFORM_WALLET_ADDRESS_HERE"'::jsonb),
    ('treasury_wallet', '"TREASURY_WALLET_ADDRESS_HERE"'::jsonb)
ON CONFLICT (key) DO NOTHING;

-- Create view for agent statistics
CREATE OR REPLACE VIEW agent_stats AS
SELECT 
    a.agent_id,
    a.name,
    a.creator_wallet,
    a.total_earnings,
    a.total_services,
    a.average_rating,
    COUNT(DISTINCT sr.id) as pending_requests,
    COUNT(DISTINCT r.id) as total_ratings
FROM agents a
LEFT JOIN service_requests sr ON a.agent_id = sr.agent_id AND sr.status IN ('pending', 'in_progress')
LEFT JOIN ratings r ON a.agent_id = r.agent_id
WHERE a.active = true
GROUP BY a.agent_id, a.name, a.creator_wallet, a.total_earnings, a.total_services, a.average_rating;

-- Create view for user statistics
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    sr.user_wallet,
    COUNT(DISTINCT sr.id) as total_requests,
    SUM(sr.amount) as total_spent,
    COUNT(DISTINCT CASE WHEN sr.status = 'approved' THEN sr.id END) as completed_requests,
    COUNT(DISTINCT r.id) as total_ratings_given,
    COUNT(DISTINCT ss.id) as total_scans
FROM service_requests sr
LEFT JOIN ratings r ON sr.user_wallet = r.user_wallet
LEFT JOIN security_scans ss ON sr.user_wallet = ss.user_wallet
GROUP BY sr.user_wallet;

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO agentadmin;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO agentadmin;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO agentadmin;

COMMENT ON TABLE agents IS 'Stores off-chain metadata for registered AI agents';
COMMENT ON TABLE service_requests IS 'Tracks all service requests and their status';
COMMENT ON TABLE ratings IS 'Stores user ratings and reviews for agents';
COMMENT ON TABLE disputes IS 'Handles disputed service requests';
COMMENT ON TABLE security_scans IS 'Logs all SecurityGuard AI transaction scans';
COMMENT ON TABLE analytics_events IS 'Tracks platform usage and events for analytics';
