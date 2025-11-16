-- Database Optimization Script
-- This script adds missing indexes and optimizes query performance

-- ============================================
-- 1. ADD MISSING INDEXES FOR PERFORMANCE
-- ============================================

-- Full-text search index for agent name and description
-- This significantly improves ILIKE queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agents_name_trgm 
ON agents USING gin(name gin_trgm_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agents_description_trgm 
ON agents USING gin(description gin_trgm_ops);

-- Enable pg_trgm extension if not already enabled
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Composite index for service requests filtering
-- Covers common query patterns: user + status, agent + status
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_requests_user_status_created 
ON service_requests(user_wallet, status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_requests_agent_status_created 
ON service_requests(agent_id, status, created_at DESC);

-- Composite index for security scans filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scans_user_risk_created 
ON security_scans(user_wallet, risk_level, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scans_risk_created 
ON security_scans(risk_level, created_at DESC);

-- Index for ratings aggregation (already exists but verify)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ratings_agent_stars 
ON ratings(agent_id, stars);

-- ============================================
-- 2. CREATE MATERIALIZED VIEW FOR AGENT STATS
-- ============================================

-- Materialized view to cache agent statistics
-- This eliminates the need for expensive JOIN and GROUP BY on every request
CREATE MATERIALIZED VIEW IF NOT EXISTS agent_stats_mv AS
SELECT 
  a.id,
  a.agent_id,
  a.name,
  a.description,
  a.capabilities,
  a.pricing,
  a.endpoint,
  a.creator_wallet,
  a.active,
  a.created_at,
  a.total_earnings,
  a.total_services,
  COALESCE(AVG(r.stars), 0)::float as avg_rating,
  COUNT(r.id)::int as rating_count
FROM agents a
LEFT JOIN ratings r ON a.agent_id = r.agent_id
GROUP BY a.id;

-- Create index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_stats_mv_id ON agent_stats_mv(id);
CREATE INDEX IF NOT EXISTS idx_agent_stats_mv_active_created ON agent_stats_mv(active, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_stats_mv_name_trgm ON agent_stats_mv USING gin(name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_agent_stats_mv_description_trgm ON agent_stats_mv USING gin(description gin_trgm_ops);

-- Function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_agent_stats()
RETURNS void AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY agent_stats_mv;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 3. OPTIMIZE QUERY PLANNER STATISTICS
-- ============================================

-- Increase statistics target for frequently queried columns
ALTER TABLE agents ALTER COLUMN name SET STATISTICS 1000;
ALTER TABLE agents ALTER COLUMN description SET STATISTICS 1000;
ALTER TABLE agents ALTER COLUMN active SET STATISTICS 1000;

ALTER TABLE service_requests ALTER COLUMN user_wallet SET STATISTICS 1000;
ALTER TABLE service_requests ALTER COLUMN agent_id SET STATISTICS 1000;
ALTER TABLE service_requests ALTER COLUMN status SET STATISTICS 1000;

ALTER TABLE security_scans ALTER COLUMN user_wallet SET STATISTICS 1000;
ALTER TABLE security_scans ALTER COLUMN risk_level SET STATISTICS 1000;

-- ============================================
-- 4. UPDATE TABLE STATISTICS
-- ============================================

ANALYZE agents;
ANALYZE service_requests;
ANALYZE ratings;
ANALYZE security_scans;

-- ============================================
-- 5. PERFORMANCE MONITORING VIEWS
-- ============================================

-- View to monitor slow queries
CREATE OR REPLACE VIEW slow_queries AS
SELECT 
  query,
  calls,
  total_exec_time,
  mean_exec_time,
  max_exec_time,
  stddev_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100  -- queries taking more than 100ms on average
ORDER BY mean_exec_time DESC
LIMIT 20;

-- View to monitor index usage
CREATE OR REPLACE VIEW index_usage_stats AS
SELECT 
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch,
  pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- ============================================
-- 6. MAINTENANCE RECOMMENDATIONS
-- ============================================

-- Schedule regular VACUUM ANALYZE (add to cron or AWS RDS maintenance)
-- VACUUM ANALYZE agents;
-- VACUUM ANALYZE service_requests;
-- VACUUM ANALYZE ratings;
-- VACUUM ANALYZE security_scans;

-- Refresh materialized view regularly (every 5 minutes recommended)
-- SELECT refresh_agent_stats();

-- ============================================
-- 7. QUERY OPTIMIZATION NOTES
-- ============================================

-- For agent listing:
-- - Use agent_stats_mv instead of joining agents + ratings
-- - Use pg_trgm indexes for ILIKE searches
-- - Consider caching results for 1-5 minutes

-- For service request listing:
-- - Use composite indexes for user_wallet + status filters
-- - Limit result set size (max 50 per page)
-- - Consider partitioning by created_at for very large datasets

-- For security scan listing:
-- - Use composite indexes for user_wallet + risk_level filters
-- - Cache statistics query results for 5-10 minutes
-- - Consider time-based partitioning for historical data

-- ============================================
-- 8. VERIFY OPTIMIZATIONS
-- ============================================

-- Check that new indexes were created
SELECT 
  schemaname,
  tablename,
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

-- Verify materialized view was created
SELECT 
  schemaname,
  matviewname,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) as size
FROM pg_matviews
WHERE schemaname = 'public';

COMMENT ON MATERIALIZED VIEW agent_stats_mv IS 'Cached agent statistics to improve query performance. Refresh every 5 minutes.';
COMMENT ON FUNCTION refresh_agent_stats() IS 'Refreshes the agent_stats_mv materialized view. Call this periodically (every 5 minutes recommended).';
