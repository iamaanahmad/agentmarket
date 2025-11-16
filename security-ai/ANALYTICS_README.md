# SecurityGuard AI - Analytics and Scan History System

## Overview

The Analytics and Scan History System provides comprehensive data management, user analytics, and platform-wide security metrics for SecurityGuard AI. It implements privacy-compliant data handling with automatic retention policies and supports GDPR/CCPA compliance features.

## Features

### 1. Scan History Management
- **Persistent Storage**: Scan results stored in PostgreSQL with proper indexing
- **Privacy Compliance**: Automatic data expiry (30-day retention policy)
- **Performance Optimization**: Cached queries and efficient database design
- **Filtering Support**: Filter by risk level, date range, and scan type

### 2. User Analytics
- **Comprehensive Statistics**: Total scans, threats detected, payment history
- **Performance Metrics**: Average scan times, threat prevention scores
- **Activity Tracking**: Daily activity patterns and usage statistics
- **Risk Assessment**: Personal risk exposure and protection effectiveness

### 3. Platform Security Metrics
- **Real-time Statistics**: Total scans, threats blocked, users protected
- **Performance Monitoring**: Response times, success rates, system health
- **Threat Intelligence**: Top threat patterns and attack trends
- **Operational Metrics**: Cache performance, database health, ML model accuracy

### 4. Data Privacy & Compliance
- **Data Export**: Complete user data export for GDPR compliance
- **Right to be Forgotten**: Secure data deletion with audit trails
- **Retention Policies**: Automatic cleanup of expired data
- **Anonymization**: Payment records anonymized after user deletion

## Architecture

### Database Schema

```sql
-- Scan History (30-day retention)
CREATE TABLE scan_history (
    id UUID PRIMARY KEY,
    scan_id VARCHAR(100) UNIQUE NOT NULL,
    user_wallet VARCHAR(44),
    risk_level VARCHAR(10) NOT NULL,
    risk_score INTEGER NOT NULL,
    confidence REAL NOT NULL,
    scan_time_ms INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP  -- Auto-cleanup after 30 days
);

-- User Profiles (persistent)
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY,
    wallet_address VARCHAR(44) UNIQUE NOT NULL,
    total_scans INTEGER DEFAULT 0,
    threats_detected INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW()
);

-- Pattern Match Tracking
CREATE TABLE scan_pattern_matches (
    id INTEGER PRIMARY KEY,
    scan_id UUID REFERENCES scan_history(id),
    pattern_id INTEGER REFERENCES exploit_patterns(id),
    match_confidence REAL NOT NULL,
    match_evidence JSON
);
```

### Service Architecture

```python
# Analytics Service Components
AnalyticsService
├── save_scan_result()          # Store scan results
├── get_user_scan_history()     # Retrieve user history
├── get_user_analytics()        # Generate user statistics
├── get_platform_security_stats() # Platform metrics
├── export_user_data()          # GDPR data export
├── delete_user_data()          # Right to be forgotten
└── cleanup_expired_data()      # Automated cleanup

DataCleanupScheduler
├── start()                     # Start cleanup scheduler
├── stop()                      # Stop cleanup scheduler
└── run_manual_cleanup()        # Manual cleanup trigger
```

## API Endpoints

### User Analytics Endpoints

#### GET /api/analytics/user
Get comprehensive user analytics and statistics.

**Authentication**: Required  
**Response**:
```json
{
  "user_profile": {
    "wallet_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    "username": "security_user",
    "member_since": "2024-01-15T10:30:00Z",
    "last_active": "2024-01-20T14:22:00Z"
  },
  "scan_statistics": {
    "total_scans": 47,
    "safe_scans": 32,
    "caution_scans": 12,
    "danger_scans": 3,
    "threats_detected": 15,
    "avg_risk_score": 23.4,
    "avg_scan_time_ms": 1650,
    "threat_prevention_score": 31.9
  },
  "payment_statistics": {
    "total_payments": 12,
    "successful_payments": 12,
    "total_spent_sol": 0.12,
    "avg_payment_sol": 0.01
  },
  "daily_activity": {
    "2024-01-20": {"scans": 5, "threats": 1},
    "2024-01-19": {"scans": 8, "threats": 2}
  }
}
```

#### GET /api/security/history
Get user's scan history with optional filtering.

**Authentication**: Required  
**Parameters**:
- `limit` (int): Maximum records to return (default: 50)
- `offset` (int): Records to skip (default: 0)  
- `risk_level` (string): Filter by SAFE/CAUTION/DANGER

**Response**:
```json
[
  {
    "scan_id": "scan_12345",
    "risk_level": "CAUTION",
    "risk_score": 45,
    "explanation": "Risk level: CAUTION. Programs: 3, Patterns: 2",
    "scan_time_ms": 1850,
    "timestamp": "2024-01-20T14:22:00Z",
    "transaction_summary": "Programs: 3, Instructions: 8"
  }
]
```

### Data Privacy Endpoints

#### GET /api/analytics/export
Export complete user data for GDPR compliance.

**Authentication**: Required  
**Parameters**:
- `format` (string): Export format (currently 'json')

**Response**:
```json
{
  "export_metadata": {
    "user_wallet": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    "export_date": "2024-01-20T15:30:00Z",
    "data_retention_policy": "30 days for scan history"
  },
  "user_profile": { /* complete profile data */ },
  "scan_history": [ /* all scan records */ ],
  "payment_records": [ /* payment history */ ],
  "service_access_logs": [ /* access logs */ ]
}
```

#### DELETE /api/analytics/user
Delete all user data (right to be forgotten).

**Authentication**: Required  
**Warning**: This action is irreversible

**Response**:
```json
{
  "success": true,
  "deleted_counts": {
    "scan_history": 47,
    "access_logs": 156,
    "payments_anonymized": 12,
    "user_profile": 1
  },
  "deletion_date": "2024-01-20T15:45:00Z"
}
```

### Platform Statistics Endpoints

#### GET /api/security/stats
Get platform-wide security statistics (public endpoint).

**Authentication**: Not required  
**Response**:
```json
{
  "total_scans": 125847,
  "threats_blocked": 8934,
  "users_protected": 4567,
  "success_rate": 99.8,
  "avg_response_time_ms": 1650,
  "p95_response_time_ms": 1950,
  "top_threats": [
    "Wallet Drainer Contracts",
    "Unlimited Token Approvals",
    "Authority Theft Attempts"
  ],
  "daily_scans": {
    "2024-01-20": {"scans": 1247, "threats": 89},
    "2024-01-19": {"scans": 1156, "threats": 76}
  },
  "uptime_percentage": 99.9,
  "last_updated": "2024-01-20T15:30:00Z"
}
```

### Admin Endpoints

#### GET /api/analytics/admin/stats
Get detailed admin analytics with system metrics.

**Authentication**: Required (admin privileges)  
**Response**: Extended platform stats with admin-specific metrics

#### POST /api/analytics/admin/cleanup
Run manual data cleanup process.

**Authentication**: Required (admin privileges)  
**Response**:
```json
{
  "success": true,
  "cleanup_result": {
    "expired_scans_deleted": 1247,
    "expired_cache_deleted": 89,
    "cleanup_date": "2024-01-20T16:00:00Z"
  }
}
```

## Data Retention & Privacy

### Retention Policies

1. **Scan History**: 30-day automatic expiry
2. **User Profiles**: Persistent until user deletion
3. **Payment Records**: Anonymized after user deletion (financial compliance)
4. **Access Logs**: 90-day retention for security auditing
5. **Cache Data**: 5-minute to 1-hour TTL based on data type

### Privacy Compliance

- **No Transaction Storage**: Transaction data not persisted beyond analysis
- **Automatic Expiry**: All scan data expires after 30 days
- **Data Minimization**: Only essential metadata stored
- **Encryption**: All data encrypted in transit and at rest
- **Audit Trails**: Complete audit logs for data access and deletion

### GDPR/CCPA Features

- **Data Portability**: Complete data export in machine-readable format
- **Right to be Forgotten**: Secure data deletion with verification
- **Consent Management**: Clear data usage policies and consent tracking
- **Data Processing Records**: Detailed logs of all data processing activities

## Performance Optimization

### Caching Strategy

```python
# Multi-layer caching for optimal performance
Redis Cache (5-minute TTL)
├── Platform statistics
├── User analytics summaries
└── Frequent query results

Database Indexes
├── User wallet + timestamp
├── Risk level + creation date
└── Pattern effectiveness tracking
```

### Query Optimization

- **Composite Indexes**: Multi-column indexes for common query patterns
- **Partitioning**: Time-based partitioning for scan history
- **Connection Pooling**: Optimized database connection management
- **Async Processing**: Non-blocking database operations

### Background Tasks

```python
# Automated maintenance tasks
DataCleanupScheduler (every 6 hours)
├── Delete expired scan history
├── Clean up cache entries
├── Update pattern effectiveness
└── Generate performance reports
```

## Monitoring & Alerting

### Key Metrics

- **Response Time**: P50, P95, P99 response times for all endpoints
- **Error Rate**: Failed requests and database errors
- **Data Growth**: Storage usage and retention compliance
- **Cache Performance**: Hit rates and miss patterns
- **User Activity**: Active users and scan patterns

### Health Checks

```python
# System health monitoring
/health endpoint includes:
├── Database connectivity
├── Cache availability  
├── Data retention compliance
├── Background task status
└── Performance metrics
```

## Integration Examples

### Save Scan Result

```python
# In main scan endpoint
await analytics_service.save_scan_result(
    scan_id=response.scan_id,
    user_wallet=user.wallet_address,
    transaction_hash=None,  # Privacy: not stored
    risk_level=response.risk_level,
    risk_score=response.risk_score,
    confidence=response.confidence,
    scan_time_ms=response.scan_time_ms,
    program_count=analysis_results["program_count"],
    instruction_count=len(parsed_tx["instructions"]),
    pattern_matches_count=len(pattern_matches),
    scan_type=request.scan_type
)
```

### Get User Analytics

```python
# Frontend dashboard integration
analytics = await analytics_service.get_user_analytics(user_wallet)

# Display user statistics
total_scans = analytics["scan_statistics"]["total_scans"]
threat_prevention = analytics["scan_statistics"]["threat_prevention_score"]
```

### Platform Statistics

```python
# Public dashboard
stats = await analytics_service.get_platform_security_stats()

# Real-time metrics display
threats_blocked_today = stats["daily_scans"][today]["threats"]
platform_uptime = stats["uptime_percentage"]
```

## Testing

### Unit Tests

```bash
# Run analytics service tests
cd security-ai
python test_analytics_simple.py
```

### Integration Tests

```bash
# Test complete analytics workflow
python -m pytest tests/test_analytics_integration.py
```

### Performance Tests

```bash
# Load test analytics endpoints
python tests/test_analytics_performance.py
```

## Deployment

### Environment Variables

```bash
# Database configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/securityguard
REDIS_URL=redis://localhost:6379/0

# Analytics settings
ANALYTICS_CACHE_TTL=300
DATA_RETENTION_DAYS=30
CLEANUP_INTERVAL_HOURS=6
```

### Production Considerations

1. **Database Scaling**: Read replicas for analytics queries
2. **Cache Clustering**: Redis cluster for high availability
3. **Backup Strategy**: Daily backups with point-in-time recovery
4. **Monitoring**: Comprehensive metrics and alerting
5. **Compliance**: Regular audits and compliance reporting

This analytics system provides a robust foundation for SecurityGuard AI's data management needs while maintaining strict privacy compliance and optimal performance.