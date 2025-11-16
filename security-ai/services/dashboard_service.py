"""
Real-time performance dashboard and business metrics tracking
"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
import redis
from services.apm_service import get_apm_service
from services.health_monitor import get_health_monitor

@dataclass
class DashboardMetric:
    name: str
    value: float
    unit: str
    timestamp: datetime
    trend: Optional[str] = None  # "up", "down", "stable"
    target: Optional[float] = None

@dataclass
class AlertStatus:
    name: str
    status: str  # "ok", "warning", "critical"
    message: str
    timestamp: datetime

class BusinessMetricsTracker:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.metrics_cache_ttl = 300  # 5 minutes
    
    async def track_scan_request(self, user_id: Optional[str], risk_level: str, 
                               processing_time_ms: float, payment_amount: float = 0.01):
        """Track a security scan request"""
        timestamp = datetime.utcnow()
        
        # Increment counters
        await self.redis.incr("metrics:scans:total")
        await self.redis.incr(f"metrics:scans:risk_level:{risk_level.lower()}")
        
        # Track processing time
        await self.redis.lpush("metrics:processing_times", processing_time_ms)
        await self.redis.ltrim("metrics:processing_times", 0, 999)  # Keep last 1000
        
        # Track revenue
        if payment_amount > 0:
            await self.redis.incrbyfloat("metrics:revenue:total", payment_amount)
            await self.redis.incrbyfloat(f"metrics:revenue:daily:{timestamp.strftime('%Y-%m-%d')}", payment_amount)
        
        # Track hourly metrics
        hour_key = f"metrics:hourly:{timestamp.strftime('%Y-%m-%d:%H')}"
        await self.redis.hincrby(hour_key, "scans", 1)
        await self.redis.hincrby(hour_key, f"risk_{risk_level.lower()}", 1)
        await self.redis.expire(hour_key, 86400 * 7)  # Keep for 7 days
    
    async def track_user_activity(self, user_id: str, action: str):
        """Track user activity"""
        timestamp = datetime.utcnow()
        
        # Track unique users
        await self.redis.sadd("metrics:users:active", user_id)
        await self.redis.expire("metrics:users:active", 86400)  # Daily active users
        
        # Track user actions
        await self.redis.incr(f"metrics:actions:{action}")
        
        # Track user session
        session_key = f"metrics:user_session:{user_id}"
        await self.redis.setex(session_key, 1800, timestamp.isoformat())  # 30 min session
    
    async def track_threat_detection(self, threat_type: str, severity: int, 
                                   pattern_matches: int, ml_confidence: float):
        """Track threat detection metrics"""
        # Track threat types
        await self.redis.incr(f"metrics:threats:{threat_type}")
        await self.redis.incr(f"metrics:threats:severity:{severity}")
        
        # Track detection accuracy
        await self.redis.lpush("metrics:ml_confidence", ml_confidence)
        await self.redis.ltrim("metrics:ml_confidence", 0, 999)
        
        # Track pattern matching effectiveness
        await self.redis.lpush("metrics:pattern_matches", pattern_matches)
        await self.redis.ltrim("metrics:pattern_matches", 0, 999)
    
    async def get_business_metrics(self) -> Dict[str, Any]:
        """Get comprehensive business metrics"""
        # Get basic counters
        total_scans = await self.redis.get("metrics:scans:total") or 0
        total_revenue = await self.redis.get("metrics:revenue:total") or 0.0
        active_users = await self.redis.scard("metrics:users:active")
        
        # Get risk level distribution
        risk_levels = {}
        for level in ["safe", "caution", "danger"]:
            count = await self.redis.get(f"metrics:scans:risk_level:{level}") or 0
            risk_levels[level] = int(count)
        
        # Get processing times
        processing_times = await self.redis.lrange("metrics:processing_times", 0, -1)
        processing_times = [float(t) for t in processing_times]
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Get ML confidence scores
        ml_confidences = await self.redis.lrange("metrics:ml_confidence", 0, -1)
        ml_confidences = [float(c) for c in ml_confidences]
        
        avg_ml_confidence = sum(ml_confidences) / len(ml_confidences) if ml_confidences else 0
        
        # Get hourly metrics for the last 24 hours
        hourly_metrics = []
        for i in range(24):
            hour = (datetime.utcnow() - timedelta(hours=i)).strftime('%Y-%m-%d:%H')
            hour_key = f"metrics:hourly:{hour}"
            hour_data = await self.redis.hgetall(hour_key)
            
            hourly_metrics.append({
                "hour": hour,
                "scans": int(hour_data.get("scans", 0)),
                "risk_safe": int(hour_data.get("risk_safe", 0)),
                "risk_caution": int(hour_data.get("risk_caution", 0)),
                "risk_danger": int(hour_data.get("risk_danger", 0))
            })
        
        return {
            "total_scans": int(total_scans),
            "total_revenue": float(total_revenue),
            "active_users_24h": active_users,
            "risk_distribution": risk_levels,
            "avg_processing_time_ms": avg_processing_time,
            "avg_ml_confidence": avg_ml_confidence,
            "hourly_metrics": list(reversed(hourly_metrics)),  # Most recent first
            "timestamp": datetime.utcnow().isoformat()
        }

class DashboardService:
    def __init__(self):
        self.redis_client = None
        self.business_tracker = None
        self.apm_service = get_apm_service()
        
    async def initialize(self):
        """Initialize dashboard service"""
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.business_tracker = BusinessMetricsTracker(self.redis_client)
    
    async def get_real_time_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive real-time dashboard data"""
        if not self.business_tracker:
            await self.initialize()
        
        # Get health status
        health_monitor = await get_health_monitor()
        system_health = await health_monitor.get_comprehensive_health()
        
        # Get performance metrics
        performance_data = self.apm_service.get_performance_dashboard()
        
        # Get business metrics
        business_metrics = await self.business_tracker.get_business_metrics()
        
        # Calculate key performance indicators
        kpis = await self._calculate_kpis(business_metrics, performance_data)
        
        # Get alerts
        alerts = await self._get_active_alerts(system_health, performance_data)
        
        return {
            "status": system_health.overall_status.value,
            "kpis": kpis,
            "system_health": {
                "overall_status": system_health.overall_status.value,
                "components": {
                    name: {
                        "status": comp.status.value,
                        "response_time_ms": comp.response_time_ms,
                        "error_message": comp.error_message
                    }
                    for name, comp in system_health.components.items()
                },
                "system_metrics": system_health.system_metrics
            },
            "performance": {
                "uptime_seconds": performance_data["uptime_seconds"],
                "overall_stats": performance_data["overall_stats"],
                "endpoint_stats": performance_data["endpoint_stats"]
            },
            "business_metrics": business_metrics,
            "alerts": alerts,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _calculate_kpis(self, business_metrics: Dict, performance_data: Dict) -> List[DashboardMetric]:
        """Calculate key performance indicators"""
        kpis = []
        
        # Scan volume KPI
        total_scans = business_metrics.get("total_scans", 0)
        kpis.append(DashboardMetric(
            name="Total Scans",
            value=total_scans,
            unit="scans",
            timestamp=datetime.utcnow(),
            target=1000  # Target: 1000 scans
        ))
        
        # Revenue KPI
        total_revenue = business_metrics.get("total_revenue", 0.0)
        kpis.append(DashboardMetric(
            name="Total Revenue",
            value=total_revenue,
            unit="SOL",
            timestamp=datetime.utcnow(),
            target=10.0  # Target: 10 SOL
        ))
        
        # Performance KPI
        avg_response_time = performance_data["overall_stats"].get("avg_response_time_ms", 0)
        kpis.append(DashboardMetric(
            name="Avg Response Time",
            value=avg_response_time,
            unit="ms",
            timestamp=datetime.utcnow(),
            target=2000  # Target: <2 seconds
        ))
        
        # Error rate KPI
        error_rate = performance_data["overall_stats"].get("overall_error_rate", 0) * 100
        kpis.append(DashboardMetric(
            name="Error Rate",
            value=error_rate,
            unit="%",
            timestamp=datetime.utcnow(),
            target=1.0  # Target: <1% error rate
        ))
        
        # Active users KPI
        active_users = business_metrics.get("active_users_24h", 0)
        kpis.append(DashboardMetric(
            name="Active Users (24h)",
            value=active_users,
            unit="users",
            timestamp=datetime.utcnow(),
            target=100  # Target: 100 active users
        ))
        
        # ML confidence KPI
        ml_confidence = business_metrics.get("avg_ml_confidence", 0) * 100
        kpis.append(DashboardMetric(
            name="ML Confidence",
            value=ml_confidence,
            unit="%",
            timestamp=datetime.utcnow(),
            target=95.0  # Target: >95% confidence
        ))
        
        return kpis
    
    async def _get_active_alerts(self, system_health, performance_data) -> List[AlertStatus]:
        """Get active system alerts"""
        alerts = []
        
        # System health alerts
        for name, component in system_health.components.items():
            if component.status.value == "unhealthy":
                alerts.append(AlertStatus(
                    name=f"{name.title()} Down",
                    status="critical",
                    message=component.error_message or f"{name} is not responding",
                    timestamp=component.last_check
                ))
            elif component.status.value == "degraded":
                alerts.append(AlertStatus(
                    name=f"{name.title()} Degraded",
                    status="warning",
                    message=f"{name} response time is high ({component.response_time_ms:.0f}ms)",
                    timestamp=component.last_check
                ))
        
        # Performance alerts
        overall_stats = performance_data["overall_stats"]
        
        if overall_stats["avg_response_time_ms"] > 2000:
            alerts.append(AlertStatus(
                name="High Response Time",
                status="warning",
                message=f"Average response time is {overall_stats['avg_response_time_ms']:.0f}ms",
                timestamp=datetime.utcnow()
            ))
        
        if overall_stats["overall_error_rate"] > 0.05:  # 5% error rate
            alerts.append(AlertStatus(
                name="High Error Rate",
                status="critical",
                message=f"Error rate is {overall_stats['overall_error_rate']*100:.1f}%",
                timestamp=datetime.utcnow()
            ))
        
        # System resource alerts
        system_metrics = system_health.system_metrics
        
        if system_metrics.get("cpu_percent", 0) > 80:
            alerts.append(AlertStatus(
                name="High CPU Usage",
                status="warning",
                message=f"CPU usage is {system_metrics['cpu_percent']:.1f}%",
                timestamp=datetime.utcnow()
            ))
        
        if system_metrics.get("memory_percent", 0) > 85:
            alerts.append(AlertStatus(
                name="High Memory Usage",
                status="warning",
                message=f"Memory usage is {system_metrics['memory_percent']:.1f}%",
                timestamp=datetime.utcnow()
            ))
        
        return alerts
    
    async def track_scan_request(self, user_id: Optional[str], risk_level: str, 
                               processing_time_ms: float, payment_amount: float = 0.01):
        """Track a scan request for business metrics"""
        if not self.business_tracker:
            await self.initialize()
        
        await self.business_tracker.track_scan_request(
            user_id, risk_level, processing_time_ms, payment_amount
        )
    
    async def track_user_activity(self, user_id: str, action: str):
        """Track user activity"""
        if not self.business_tracker:
            await self.initialize()
        
        await self.business_tracker.track_user_activity(user_id, action)
    
    async def track_threat_detection(self, threat_type: str, severity: int, 
                                   pattern_matches: int, ml_confidence: float):
        """Track threat detection metrics"""
        if not self.business_tracker:
            await self.initialize()
        
        await self.business_tracker.track_threat_detection(
            threat_type, severity, pattern_matches, ml_confidence
        )

# Global dashboard service instance
dashboard_service = DashboardService()

async def get_dashboard_service() -> DashboardService:
    """Get the global dashboard service instance"""
    if not dashboard_service.business_tracker:
        await dashboard_service.initialize()
    return dashboard_service