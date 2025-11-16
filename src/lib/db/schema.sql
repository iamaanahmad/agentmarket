-- AgentMarket DB schema
-- Created: automated helper

-- Users / Wallets
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  wallet_address TEXT NOT NULL UNIQUE,
  username TEXT,
  preferences JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Agents
CREATE TABLE IF NOT EXISTS agents (
  id SERIAL PRIMARY KEY,
  agent_id TEXT NOT NULL UNIQUE, -- on-chain agent id or uuid
  name TEXT NOT NULL,
  description TEXT,
  capabilities JSONB,
  pricing JSONB,
  endpoint TEXT,
  creator_wallet TEXT,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Service Requests / Jobs
CREATE TABLE IF NOT EXISTS service_requests (
  id SERIAL PRIMARY KEY,
  request_id TEXT NOT NULL UNIQUE,
  agent_id TEXT NOT NULL,
  user_wallet TEXT NOT NULL,
  amount NUMERIC(18,6) NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending', -- pending, funded, completed, disputed, cancelled
  payload JSONB,
  result JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Ratings and Reviews
CREATE TABLE IF NOT EXISTS ratings (
  id SERIAL PRIMARY KEY,
  agent_id TEXT NOT NULL,
  user_wallet TEXT NOT NULL,
  stars INTEGER CHECK (stars >= 0 AND stars <= 5),
  quality_score INTEGER,
  speed_score INTEGER,
  value_score INTEGER,
  comment TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Analytics / Events
CREATE TABLE IF NOT EXISTS analytics_events (
  id SERIAL PRIMARY KEY,
  event_type TEXT NOT NULL,
  payload JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_agents_creator ON agents (creator_wallet);
CREATE INDEX IF NOT EXISTS idx_requests_agent ON service_requests (agent_id);
CREATE INDEX IF NOT EXISTS idx_ratings_agent ON ratings (agent_id);
