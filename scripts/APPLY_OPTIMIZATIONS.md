# Quick Guide: Apply Database Performance Optimizations

## Prerequisites

- PostgreSQL database access
- Database credentials configured in environment variables
- Backup of current database (recommended)

## Step 1: Backup Current State

```bash
# Backup current API routes
cp src/app/api/agents/route.ts src/app/api/agents/route.backup.ts
cp src/app/api/requests/route.ts src/app/api/requests/route.backup.ts
cp src/app/api/security/scan/route.ts src/app/api/security/scan/route.backup.ts

# Backup database (optional but recommended)
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql
```

## Step 2: Apply Database Optimizations

```bash
# Connect to PostgreSQL
psql -h $DB_HOST -U $DB_USER -d $DB_NAME

# Run optimization script
\i scripts/optimize_database.sql

# Verify indexes were created
SELECT indexname, tablename 
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

# Verify materialized view was created
SELECT matviewname, pg_size_pretty(pg_total_relation_size('public.'||matviewname)) as size
FROM pg_matviews 
WHERE schemaname = 'public';

# Exit psql
\q
```

## Step 3: Replace API Routes

```bash
# Replace with optimized versions
mv src/app/api/agents/route.optimized.ts src/app/api/agents/route.ts
mv src/app/api/requests/route.optimized.ts src/app/api/requests/route.ts
mv src/app/api/security/scan/route.optimized.ts src/app/api/security/scan/route.ts
```

## Step 4: Test Performance

```bash
# Install dependencies if needed
npm install

# Start your Next.js development server
npm run dev

# In another terminal, run performance tests
export API_BASE_URL=http://localhost:3000
npx ts-node scripts/test_api_performance.ts

# Review results
cat performance_test_results.json
```

## Step 5: Set Up Materialized View Refresh

### Option A: PostgreSQL Cron (if pg_cron extension available)

```sql
-- Enable pg_cron extension
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule refresh every 5 minutes
SELECT cron.schedule(
  'refresh-agent-stats',
  '*/5 * * * *',
  'SELECT refresh_agent_stats()'
);
```

### Option B: AWS Lambda (Recommended for AWS deployment)

Create a Lambda function that runs every 5 minutes:

```typescript
// lambda/refresh-agent-stats.ts
import { Pool } from 'pg'

export async function handler() {
  const pool = new Pool({
    host: process.env.DB_HOST,
    port: parseInt(process.env.DB_PORT || '5432'),
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
    ssl: { rejectUnauthorized: false }
  })
  
  try {
    const client = await pool.connect()
    await client.query('SELECT refresh_agent_stats()')
    client.release()
    
    console.log('Materialized view refreshed successfully')
    return { statusCode: 200, body: 'Success' }
  } catch (error) {
    console.error('Failed to refresh materialized view:', error)
    throw error
  } finally {
    await pool.end()
  }
}
```

Configure EventBridge rule:
```bash
# Create EventBridge rule to trigger every 5 minutes
aws events put-rule \
  --name refresh-agent-stats \
  --schedule-expression "rate(5 minutes)"

# Add Lambda as target
aws events put-targets \
  --rule refresh-agent-stats \
  --targets "Id"="1","Arn"="arn:aws:lambda:REGION:ACCOUNT:function:refresh-agent-stats"
```

### Option C: Manual Refresh (Development only)

```bash
# Connect to database
psql -h $DB_HOST -U $DB_USER -d $DB_NAME

# Manually refresh
SELECT refresh_agent_stats();
```

## Step 6: Monitor Performance

### CloudWatch Alarms (AWS)

```bash
# Create alarm for high Lambda latency
aws cloudwatch put-metric-alarm \
  --alarm-name api-high-latency \
  --alarm-description "API P95 latency exceeds threshold" \
  --metric-name Duration \
  --namespace AWS/Lambda \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 500 \
  --comparison-operator GreaterThanThreshold

# Create alarm for high RDS CPU
aws cloudwatch put-metric-alarm \
  --alarm-name rds-high-cpu \
  --alarm-description "RDS CPU utilization exceeds 70%" \
  --metric-name CPUUtilization \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 70 \
  --comparison-operator GreaterThanThreshold
```

### Query Performance Monitoring

```sql
-- Check slow queries (requires pg_stat_statements extension)
SELECT 
  query,
  calls,
  mean_exec_time,
  max_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check index usage
SELECT 
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

## Step 7: Verify Everything Works

### Checklist

- [ ] All indexes created successfully
- [ ] Materialized view created and populated
- [ ] API routes replaced with optimized versions
- [ ] Performance tests pass (P95 < 500ms for GET, < 1s for POST)
- [ ] Materialized view refresh scheduled
- [ ] CloudWatch alarms configured
- [ ] No errors in application logs
- [ ] Database connection pool operating normally

### Test Endpoints

```bash
# Test agent listing
curl http://localhost:3000/api/agents?page=1&limit=10

# Test agent search
curl http://localhost:3000/api/agents?search=test

# Test request listing
curl http://localhost:3000/api/requests?page=1&limit=20

# Test security scan history
curl http://localhost:3000/api/security/scan?page=1&limit=20
```

## Rollback Procedure (If Needed)

```bash
# Restore original API routes
mv src/app/api/agents/route.backup.ts src/app/api/agents/route.ts
mv src/app/api/requests/route.backup.ts src/app/api/requests/route.ts
mv src/app/api/security/scan/route.backup.ts src/app/api/security/scan/route.ts

# Drop materialized view (optional)
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "DROP MATERIALIZED VIEW IF EXISTS agent_stats_mv;"

# Drop new indexes (optional)
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
DROP INDEX IF EXISTS idx_agents_name_trgm;
DROP INDEX IF EXISTS idx_agents_description_trgm;
DROP INDEX IF EXISTS idx_requests_user_status_created;
DROP INDEX IF EXISTS idx_requests_agent_status_created;
DROP INDEX IF EXISTS idx_scans_user_risk_created;
DROP INDEX IF EXISTS idx_scans_risk_created;
"
```

## Troubleshooting

### Issue: Materialized view not found

**Solution:** The optimized routes fall back to regular queries if the materialized view doesn't exist. Verify it was created:

```sql
SELECT * FROM pg_matviews WHERE matviewname = 'agent_stats_mv';
```

### Issue: pg_trgm extension not available

**Solution:** Install the extension:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

If you don't have permissions, contact your database administrator.

### Issue: Performance tests fail

**Solution:** 
1. Check if database optimizations were applied
2. Verify indexes exist
3. Run ANALYZE on all tables
4. Check database connection pool settings

### Issue: High memory usage after optimization

**Solution:** Materialized views consume memory. Monitor with:

```sql
SELECT 
  matviewname,
  pg_size_pretty(pg_total_relation_size('public.'||matviewname)) as size
FROM pg_matviews;
```

If too large, consider:
- Reducing refresh frequency
- Adding WHERE clause to materialized view
- Using partial indexes instead

## Maintenance Schedule

### Daily
- Monitor CloudWatch metrics
- Check for slow queries

### Weekly
- Run VACUUM ANALYZE on all tables
- Review index usage statistics
- Check materialized view refresh status

### Monthly
- Analyze query patterns
- Review and optimize slow queries
- Update statistics targets if needed

## Support

For issues or questions:
1. Check `.kiro/specs/marketplace-api/PERFORMANCE_OPTIMIZATION.md`
2. Review CloudWatch logs
3. Run `scripts/analyze_query_performance.sql` for diagnostics
4. Check database connection pool metrics

## Success Criteria

✅ All GET endpoints respond in <500ms (P95)
✅ All POST endpoints respond in <1s (P95)
✅ No errors in application logs
✅ Database CPU utilization <70%
✅ Connection pool operating efficiently
✅ Materialized view refreshing successfully
