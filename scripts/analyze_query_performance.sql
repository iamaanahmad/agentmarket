-- Query Performance Analysis Script
-- Run this against the PostgreSQL database to analyze query performance

-- ============================================
-- 1. AGENT LISTING QUERY ANALYSIS
-- ============================================

-- Original query with EXPLAIN ANALYZE
EXPLAIN ANALYZE
SELECT 
  a.id, a.agent_id, a.name, a.description, a.capabilities, a.pricing,
  a.endpoint, a.creator_wallet, a.active, a.created_at,
  COALESCE(AVG(r.stars), 0)::float as avg_rating,
  COUNT(r.id) as rating_count
FROM agents a
LEFT JOIN ratings r ON a.agent_id = r.agent_id
WHERE a.active = true
GROUP BY a.id
ORDER BY a.created_at DESC
LIMIT 10 OFFSET 0;

-- With search filter
EXPLAIN ANALYZE
SELECT 
  a.id, a.agent_id, a.name, a.description, a.capabilities, a.pricing,
  a.endpoint, a.creator_wallet, a.active, a.created_at,
  COALESCE(AVG(r.stars), 0)::float as avg_rating,
  COUNT(r.id) as rating_count
FROM agents a
LEFT JOIN ratings r ON a.agent_id = r.agent_id
WHERE a.active = true
  AND (a.name ILIKE '%test%' OR a.description ILIKE '%test%')
GROUP BY a.id
ORDER BY a.created_at DESC
LIMIT 10 OFFSET 0;

-- ============================================
-- 2. SERVICE REQUEST LISTING QUERY ANALYSIS
-- ============================================

-- Original query with filters
EXPLAIN ANALYZE
SELECT 
  sr.id, sr.request_id, sr.agent_id, sr.user_wallet, sr.amount,
  sr.status, sr.request_data, sr.result_data, sr.created_at, sr.completed_at,
  a.name as agent_name
FROM service_requests sr
LEFT JOIN agents a ON sr.agent_id = a.agent_id
WHERE 1=1
  AND sr.user_wallet = 'test_wallet'
  AND sr.status = 'pending'
ORDER BY sr.created_at DESC
LIMIT 20 OFFSET 0;

-- ============================================
-- 3. SECURITY SCAN LISTING QUERY ANALYSIS
-- ============================================

-- Original query with filters
EXPLAIN ANALYZE
SELECT 
  scan_id, user_wallet, transaction_hash, risk_level, risk_score,
  scan_time_ms, confidence, threats_detected, created_at
FROM security_scans
WHERE 1=1
  AND user_wallet = 'test_wallet'
  AND risk_level = 'DANGER'
ORDER BY created_at DESC
LIMIT 20 OFFSET 0;

-- Statistics query
EXPLAIN ANALYZE
SELECT 
  COUNT(*) as total_scans,
  COUNT(CASE WHEN risk_level = 'DANGER' THEN 1 END) as threats_blocked,
  AVG(scan_time_ms)::int as avg_scan_time,
  COUNT(DISTINCT user_wallet) as users_protected
FROM security_scans;

-- ============================================
-- 4. INDEX USAGE VERIFICATION
-- ============================================

-- Check if indexes exist
SELECT 
  schemaname,
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('agents', 'service_requests', 'ratings', 'security_scans')
ORDER BY tablename, indexname;

-- Check index usage statistics
SELECT 
  schemaname,
  tablename,
  indexname,
  idx_scan as index_scans,
  idx_tup_read as tuples_read,
  idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND tablename IN ('agents', 'service_requests', 'ratings', 'security_scans')
ORDER BY tablename, idx_scan DESC;

-- ============================================
-- 5. TABLE STATISTICS
-- ============================================

-- Check table sizes and row counts
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
  n_live_tup as row_count,
  n_dead_tup as dead_rows,
  last_vacuum,
  last_autovacuum,
  last_analyze,
  last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'public'
  AND tablename IN ('agents', 'service_requests', 'ratings', 'security_scans')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- ============================================
-- 6. MISSING INDEX RECOMMENDATIONS
-- ============================================

-- Check for sequential scans that might benefit from indexes
SELECT 
  schemaname,
  tablename,
  seq_scan,
  seq_tup_read,
  idx_scan,
  seq_tup_read / NULLIF(seq_scan, 0) as avg_seq_tup_read
FROM pg_stat_user_tables
WHERE schemaname = 'public'
  AND seq_scan > 0
  AND tablename IN ('agents', 'service_requests', 'ratings', 'security_scans')
ORDER BY seq_tup_read DESC;

-- ============================================
-- 7. QUERY PERFORMANCE RECOMMENDATIONS
-- ============================================

-- Agents table: Add composite index for search queries
-- CREATE INDEX CONCURRENTLY idx_agents_search ON agents USING gin(to_tsvector('english', name || ' ' || description));

-- Service requests: Add composite index for common filter combinations
-- CREATE INDEX CONCURRENTLY idx_requests_user_status ON service_requests(user_wallet, status, created_at DESC);
-- CREATE INDEX CONCURRENTLY idx_requests_agent_status ON service_requests(agent_id, status, created_at DESC);

-- Security scans: Add composite index for common filter combinations
-- CREATE INDEX CONCURRENTLY idx_scans_user_risk ON security_scans(user_wallet, risk_level, created_at DESC);

-- Ratings: Ensure agent_id index exists for JOIN performance
-- Already exists: idx_ratings_agent

-- ============================================
-- 8. VACUUM AND ANALYZE RECOMMENDATIONS
-- ============================================

-- Run VACUUM ANALYZE to update statistics
VACUUM ANALYZE agents;
VACUUM ANALYZE service_requests;
VACUUM ANALYZE ratings;
VACUUM ANALYZE security_scans;
