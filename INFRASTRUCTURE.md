# SecurityGuard AI - Production Infrastructure Guide

## Overview

This document describes the production infrastructure setup for SecurityGuard AI, including deployment, monitoring, backup, and disaster recovery procedures.

## Architecture Components

### Core Services
- **SecurityGuard AI Application**: FastAPI-based security analysis service
- **PostgreSQL Database**: Primary data storage for patterns, analytics, and user data
- **Redis Cache**: High-performance caching and session storage
- **Nginx Load Balancer**: Request routing and rate limiting

### Monitoring Stack
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization dashboards and monitoring
- **Health Monitors**: Application and infrastructure health checks
- **APM Service**: Application performance monitoring

### Infrastructure
- **Docker Containers**: Containerized application deployment
- **Kubernetes**: Container orchestration and auto-scaling
- **Horizontal Pod Autoscaler**: Automatic scaling based on CPU/memory
- **Ingress Controller**: External traffic routing

## Deployment

### Prerequisites
- Docker and Docker Compose
- Kubernetes cluster (local or cloud)
- kubectl configured
- Container registry access

### Quick Start with Docker Compose

```bash
# Clone repository
git clone <repository-url>
cd security-guard-ai

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Start services
docker-compose up -d

# Check health
curl http://localhost/health
```

### Production Kubernetes Deployment

```bash
# Build and deploy
./scripts/deploy.sh v1.0.0

# Setup monitoring
./scripts/monitoring_setup.sh

# Check deployment status
kubectl get pods -n default
kubectl get hpa -n default
```

### Environment Variables

Required environment variables:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379
CLAUDE_API_KEY=your-claude-api-key
JWT_SECRET=your-jwt-secret
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
ENVIRONMENT=production
```

## Monitoring and Observability

### Health Checks

The application provides multiple health check endpoints:

- `/health` - Basic health status
- `/health/detailed` - Comprehensive component status
- `/health/ready` - Kubernetes readiness probe
- `/health/live` - Kubernetes liveness probe

### Metrics

Prometheus metrics are available at `/metrics`:

- HTTP request metrics (rate, duration, errors)
- Business metrics (scans, revenue, users)
- System metrics (CPU, memory, disk)
- ML model performance metrics

### Dashboards

Grafana dashboards provide real-time monitoring:

1. **System Overview**: Service status, request rate, response times
2. **Security Metrics**: Scan volumes, threat detection rates
3. **Performance**: Response times, error rates, resource usage
4. **Business KPIs**: Revenue, active users, scan success rates

### Alerting

Prometheus alerts are configured for:

- High error rates (>5%)
- Slow response times (>2 seconds)
- System resource usage (CPU >80%, Memory >85%)
- Service downtime
- ML model accuracy degradation

## Performance Optimization

### Caching Strategy

- **Redis Cache**: Pattern matches, ML predictions, scan results
- **Application Cache**: Frequently accessed data
- **CDN**: Static assets and API responses (if applicable)

### Database Optimization

- **Connection Pooling**: Optimized database connections
- **Indexing**: Proper indexes on frequently queried columns
- **Query Optimization**: Efficient queries with proper joins
- **Partitioning**: Time-based partitioning for large tables

### Auto-scaling

Horizontal Pod Autoscaler (HPA) configuration:

- **Min Replicas**: 3 (high availability)
- **Max Replicas**: 20 (traffic spikes)
- **CPU Target**: 70% utilization
- **Memory Target**: 80% utilization
- **Scale-up**: 50% increase or 2 pods per minute
- **Scale-down**: 10% decrease per minute (with 5-minute stabilization)

## Backup and Disaster Recovery

### Automated Backups

The backup system creates:

- **Database Backups**: Daily PostgreSQL dumps
- **Configuration Backups**: Daily config file archives
- **Log Backups**: Weekly log file archives
- **Retention**: 30 days local, 90 days cloud storage

### Backup Commands

```bash
# Create full backup
python scripts/backup_restore.py backup --type full

# Database backup only
python scripts/backup_restore.py backup --type database

# List available backups
python scripts/backup_restore.py list

# Restore database
python scripts/backup_restore.py restore --type database --file /path/to/backup.sql
```

### Disaster Recovery Procedures

#### Database Recovery

1. **Identify Issue**: Check database connectivity and logs
2. **Stop Application**: Scale down to prevent data corruption
3. **Restore Database**: Use latest backup
4. **Verify Data**: Run data integrity checks
5. **Restart Application**: Scale back up and monitor

```bash
# Emergency database restore
kubectl scale deployment security-guard-ai --replicas=0
python scripts/backup_restore.py restore --type database --file latest_backup.sql
kubectl scale deployment security-guard-ai --replicas=3
```

#### Complete System Recovery

1. **Assess Damage**: Determine scope of failure
2. **Deploy Infrastructure**: Recreate Kubernetes resources
3. **Restore Data**: Database and configuration restore
4. **Verify Services**: Health checks and functionality tests
5. **Resume Operations**: Gradual traffic restoration

### Recovery Time Objectives (RTO)

- **Database Recovery**: 15 minutes
- **Application Recovery**: 5 minutes
- **Complete System Recovery**: 30 minutes
- **Data Loss (RPO)**: Maximum 1 hour

## Security Considerations

### Network Security

- **TLS Encryption**: All external communications encrypted
- **Rate Limiting**: API rate limits to prevent abuse
- **Firewall Rules**: Restricted network access
- **VPC/Network Policies**: Isolated network segments

### Application Security

- **Input Validation**: All inputs sanitized and validated
- **Authentication**: JWT-based authentication with Solana wallets
- **Authorization**: Role-based access control
- **Secrets Management**: Kubernetes secrets for sensitive data

### Data Privacy

- **Data Minimization**: Only necessary data stored
- **Encryption at Rest**: Database encryption enabled
- **Data Retention**: Automatic cleanup of old data
- **Privacy Compliance**: GDPR/CCPA compliant data handling

## Troubleshooting

### Common Issues

#### High Response Times

1. Check system resources (CPU, memory)
2. Review database performance metrics
3. Analyze cache hit rates
4. Check for slow queries

```bash
# Check resource usage
kubectl top pods
kubectl top nodes

# Review logs
kubectl logs -f deployment/security-guard-ai

# Check database performance
kubectl exec -it postgres-pod -- psql -c "SELECT * FROM pg_stat_activity;"
```

#### Service Unavailability

1. Check pod status and logs
2. Verify database connectivity
3. Check Redis cache status
4. Review ingress configuration

```bash
# Check pod status
kubectl get pods -o wide

# Check service endpoints
kubectl get endpoints

# Test internal connectivity
kubectl run debug --image=curlimages/curl --rm -i --restart=Never -- curl -f http://service-name/health
```

#### Memory Issues

1. Review memory usage patterns
2. Check for memory leaks
3. Adjust resource limits
4. Scale horizontally if needed

```bash
# Check memory usage
kubectl top pods --sort-by=memory

# Adjust resources
kubectl patch deployment security-guard-ai -p '{"spec":{"template":{"spec":{"containers":[{"name":"security-guard-ai","resources":{"limits":{"memory":"4Gi"}}}]}}}}'
```

### Log Analysis

Logs are structured and include:

- **Request ID**: Trace requests across services
- **Performance Metrics**: Response times and component breakdown
- **Error Details**: Stack traces and error context
- **Business Events**: Scan results and user actions

```bash
# View recent logs
kubectl logs -f deployment/security-guard-ai --tail=100

# Search for errors
kubectl logs deployment/security-guard-ai | grep ERROR

# Filter by request ID
kubectl logs deployment/security-guard-ai | grep "request_id=abc123"
```

## Maintenance

### Regular Maintenance Tasks

#### Daily
- Monitor system health and alerts
- Review error logs and performance metrics
- Check backup completion status

#### Weekly
- Review and update security patches
- Analyze performance trends
- Clean up old logs and temporary files

#### Monthly
- Update dependencies and base images
- Review and optimize database performance
- Test disaster recovery procedures
- Security audit and vulnerability assessment

### Update Procedures

#### Application Updates

1. **Build New Image**: Create and test new container image
2. **Rolling Update**: Deploy with zero downtime
3. **Health Verification**: Confirm all pods are healthy
4. **Rollback Plan**: Ready to rollback if issues occur

```bash
# Rolling update
kubectl set image deployment/security-guard-ai security-guard-ai=new-image:tag

# Monitor rollout
kubectl rollout status deployment/security-guard-ai

# Rollback if needed
kubectl rollout undo deployment/security-guard-ai
```

#### Infrastructure Updates

1. **Plan Maintenance Window**: Schedule during low traffic
2. **Backup Critical Data**: Ensure recent backups exist
3. **Update Components**: Update one component at a time
4. **Verify Functionality**: Test all critical paths

## Performance Targets

### Service Level Objectives (SLOs)

- **Availability**: 99.9% uptime
- **Response Time**: 95% of requests < 2 seconds
- **Error Rate**: < 0.5% of requests
- **Throughput**: 100+ concurrent requests
- **ML Accuracy**: > 99.8% threat detection

### Capacity Planning

- **CPU**: Plan for 70% average utilization
- **Memory**: Plan for 80% average utilization
- **Storage**: Monitor growth and plan for 6 months ahead
- **Network**: Monitor bandwidth and plan for traffic spikes

## Cost Optimization

### Resource Optimization

- **Right-sizing**: Regular review of resource requests/limits
- **Auto-scaling**: Efficient scaling policies
- **Spot Instances**: Use for non-critical workloads
- **Reserved Capacity**: Long-term commitments for stable workloads

### Monitoring Costs

- Track resource usage and costs
- Set up billing alerts
- Regular cost reviews and optimization
- Implement resource tagging for cost allocation

## Support and Escalation

### Support Levels

1. **Level 1**: Basic monitoring and alerting
2. **Level 2**: Application troubleshooting and recovery
3. **Level 3**: Infrastructure and architecture issues
4. **Level 4**: Vendor escalation and critical incidents

### Contact Information

- **On-call Engineer**: [Contact details]
- **Infrastructure Team**: [Contact details]
- **Security Team**: [Contact details]
- **Management Escalation**: [Contact details]

### Incident Response

1. **Detection**: Automated alerts or manual reporting
2. **Assessment**: Determine severity and impact
3. **Response**: Immediate actions to restore service
4. **Communication**: Status updates to stakeholders
5. **Resolution**: Root cause analysis and prevention
6. **Post-mortem**: Document lessons learned

This infrastructure guide provides comprehensive coverage of deployment, monitoring, backup, and maintenance procedures for SecurityGuard AI in production environments.