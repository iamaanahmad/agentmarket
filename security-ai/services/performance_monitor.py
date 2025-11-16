"""
Real-time performance monitoring service for SecurityGuard AI
Tracks response times, throughput, and system metrics
"""

import asyncio
import time
import statistics
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque

from loguru import logger

try:
    from ..core.config import get_settings
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from core.config import get_settings

# Import services with fallback handling
try:
    from .cache_service import cache_service
except ImportError:
    cache_service = None

try:
    from .request_queue import request_queue
except ImportError:
    request_queue = None


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    timestamp: float = field(default_factory=time.time)
    response_time_ms: float = 0.0
    component_times: Dict[str, float] = field(default_factory=dict)
    success: bool = True
    error_type: Optional[str] = None
    request_size_bytes: int = 0
    response_size_bytes: int = 0
    cache_hit: bool = False
    queue_wait_time_ms: float = 0.0


class PerformanceMonitor:
    """
    Real-time performance monitoring with metrics collection,
    alerting, and performance optimization recommendations
    """
    
    def __init__(self, window_size: int = 1000):
        self.settings = get_settings()
        self.window_size = window_size
        
        # Metrics storage (circular buffer for memory efficiency)
        self.metrics: deque = deque(maxlen=window_size)
        self.component_metrics: Dict[str, deque] = {
            'parsing': deque(maxlen=window_size),
            'program_analysis': deque(maxlen=window_size),
            'pattern_matching': deque(maxlen=window_size),
            'ml_detection': deque(maxlen=window_size),
            'account_analysis': deque(maxlen=window_size),
            'explanation_generation': deque(maxlen=window_size)
        }
        
        # Performance targets (from requirements)
        self.targets = {
            'response_time_p95_ms': 2000,  # 95% under 2 seconds
            'response_time_p99_ms': 5000,  # 99% under 5 seconds
            'success_rate_min': 0.995,    # 99.5% success rate
            'throughput_min_rps': 10,     # Minimum 10 requests per second
            'cache_hit_rate_min': 0.7,    # 70% cache hit rate
            'queue_wait_time_p95_ms': 100 # 95% queue waits under 100ms
        }
        
        # Alert thresholds
        self.alert_thresholds = {
            'response_time_critical_ms': 10000,  # 10 seconds
            'error_rate_warning': 0.05,          # 5% error rate
            'error_rate_critical': 0.1,          # 10% error rate
            'queue_size_warning': 500,           # Queue size warning
            'queue_size_critical': 800           # Queue size critical
        }
        
        # Real-time tracking
        self.current_rps = 0.0
        self.last_rps_calculation = time.time()
        self.request_count_window = deque(maxlen=60)  # 1 minute window
        
        # Alerting
        self.alerts: List[Dict[str, Any]] = []
        self.last_alert_check = time.time()
        
        # Performance optimization recommendations
        self.recommendations: List[str] = []
        self.last_recommendation_update = time.time()
    
    def record_request(self, metrics: PerformanceMetrics):
        """Record performance metrics for a request"""
        self.metrics.append(metrics)
        
        # Record component metrics
        for component, time_ms in metrics.component_times.items():
            if component in self.component_metrics:
                self.component_metrics[component].append(time_ms)
        
        # Update RPS tracking
        current_time = time.time()
        self.request_count_window.append(current_time)
        
        # Calculate RPS every second
        if current_time - self.last_rps_calculation >= 1.0:
            self._calculate_rps()
            self.last_rps_calculation = current_time
        
        # Check for alerts
        if current_time - self.last_alert_check >= 5.0:  # Check every 5 seconds
            self._check_alerts()
            self.last_alert_check = current_time
        
        # Update recommendations
        if current_time - self.last_recommendation_update >= 30.0:  # Every 30 seconds
            self._update_recommendations()
            self.last_recommendation_update = current_time
    
    def _calculate_rps(self):
        """Calculate current requests per second"""
        current_time = time.time()
        
        # Count requests in the last second
        recent_requests = [
            t for t in self.request_count_window 
            if current_time - t <= 1.0
        ]
        
        self.current_rps = len(recent_requests)
    
    def _check_alerts(self):
        """Check for performance alerts"""
        if not self.metrics:
            return
        
        current_time = time.time()
        recent_metrics = [
            m for m in self.metrics 
            if current_time - m.timestamp <= 60.0  # Last minute
        ]
        
        if not recent_metrics:
            return
        
        # Check response time alerts
        response_times = [m.response_time_ms for m in recent_metrics]
        if response_times:
            max_response_time = max(response_times)
            if max_response_time > self.alert_thresholds['response_time_critical_ms']:
                self._add_alert(
                    'critical',
                    'response_time',
                    f'Response time exceeded {max_response_time:.0f}ms (critical threshold: {self.alert_thresholds["response_time_critical_ms"]}ms)'
                )
        
        # Check error rate alerts
        error_count = sum(1 for m in recent_metrics if not m.success)
        error_rate = error_count / len(recent_metrics)
        
        if error_rate > self.alert_thresholds['error_rate_critical']:
            self._add_alert(
                'critical',
                'error_rate',
                f'Error rate {error_rate:.1%} exceeds critical threshold {self.alert_thresholds["error_rate_critical"]:.1%}'
            )
        elif error_rate > self.alert_thresholds['error_rate_warning']:
            self._add_alert(
                'warning',
                'error_rate',
                f'Error rate {error_rate:.1%} exceeds warning threshold {self.alert_thresholds["error_rate_warning"]:.1%}'
            )
        
        # Check queue size alerts (if queue service is available)
        try:
            queue_stats = asyncio.create_task(request_queue.get_stats())
            # Note: This is a simplified check - in production, use proper async handling
        except Exception:
            pass  # Queue service not available
    
    def _add_alert(self, severity: str, alert_type: str, message: str):
        """Add a performance alert"""
        alert = {
            'timestamp': time.time(),
            'severity': severity,
            'type': alert_type,
            'message': message
        }
        
        self.alerts.append(alert)
        
        # Keep only recent alerts (last hour)
        current_time = time.time()
        self.alerts = [
            a for a in self.alerts 
            if current_time - a['timestamp'] <= 3600
        ]
        
        # Log alert
        if severity == 'critical':
            logger.error(f"🚨 CRITICAL ALERT: {message}")
        else:
            logger.warning(f"⚠️ WARNING ALERT: {message}")
    
    def _update_recommendations(self):
        """Update performance optimization recommendations"""
        if not self.metrics:
            return
        
        self.recommendations.clear()
        
        # Analyze recent performance
        current_time = time.time()
        recent_metrics = [
            m for m in self.metrics 
            if current_time - m.timestamp <= 300.0  # Last 5 minutes
        ]
        
        if not recent_metrics:
            return
        
        # Response time analysis
        response_times = [m.response_time_ms for m in recent_metrics]
        if response_times:
            p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
            
            if p95_response_time > self.targets['response_time_p95_ms']:
                self.recommendations.append(
                    f"Response time P95 ({p95_response_time:.0f}ms) exceeds target ({self.targets['response_time_p95_ms']}ms). "
                    "Consider optimizing slow components or increasing cache TTL."
                )
        
        # Cache hit rate analysis
        cache_hits = sum(1 for m in recent_metrics if m.cache_hit)
        cache_hit_rate = cache_hits / len(recent_metrics)
        
        if cache_hit_rate < self.targets['cache_hit_rate_min']:
            self.recommendations.append(
                f"Cache hit rate ({cache_hit_rate:.1%}) below target ({self.targets['cache_hit_rate_min']:.1%}). "
                "Consider increasing cache TTL or improving cache key strategies."
            )
        
        # Component performance analysis
        for component, times in self.component_metrics.items():
            if times and len(times) >= 10:
                avg_time = statistics.mean(times)
                component_thresholds = {
                    'parsing': 150,
                    'program_analysis': 200,
                    'pattern_matching': 300,
                    'ml_detection': 500,
                    'account_analysis': 100,
                    'explanation_generation': 800
                }
                
                threshold = component_thresholds.get(component, 500)
                if avg_time > threshold:
                    self.recommendations.append(
                        f"{component.title()} component averaging {avg_time:.0f}ms (threshold: {threshold}ms). "
                        "Consider optimization or caching improvements."
                    )
        
        # Throughput analysis
        if self.current_rps < self.targets['throughput_min_rps']:
            self.recommendations.append(
                f"Current throughput ({self.current_rps:.1f} RPS) below target ({self.targets['throughput_min_rps']} RPS). "
                "Consider scaling workers or optimizing request processing."
            )
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        if not self.metrics:
            return {"error": "No performance data available"}
        
        current_time = time.time()
        
        # Recent metrics (last 5 minutes)
        recent_metrics = [
            m for m in self.metrics 
            if current_time - m.timestamp <= 300.0
        ]
        
        if not recent_metrics:
            return {"error": "No recent performance data"}
        
        # Response time statistics
        response_times = [m.response_time_ms for m in recent_metrics]
        success_count = sum(1 for m in recent_metrics if m.success)
        cache_hits = sum(1 for m in recent_metrics if m.cache_hit)
        
        # Component performance
        component_stats = {}
        for component, times in self.component_metrics.items():
            if times:
                recent_times = [t for t in times if t > 0]  # Filter valid times
                if recent_times:
                    component_stats[component] = {
                        'avg_ms': statistics.mean(recent_times),
                        'p95_ms': statistics.quantiles(recent_times, n=20)[18] if len(recent_times) >= 20 else max(recent_times),
                        'min_ms': min(recent_times),
                        'max_ms': max(recent_times)
                    }
        
        # Calculate percentiles
        p50 = statistics.median(response_times) if response_times else 0
        p95 = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else (max(response_times) if response_times else 0)
        p99 = statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else (max(response_times) if response_times else 0)
        
        # Get external service stats
        cache_stats = await cache_service.get_stats() if cache_service else {}
        queue_stats = await request_queue.get_stats() if request_queue else {}
        
        return {
            "timestamp": current_time,
            "window_size": len(recent_metrics),
            "time_range_minutes": 5,
            
            # Response time metrics
            "response_time": {
                "avg_ms": statistics.mean(response_times) if response_times else 0,
                "median_ms": p50,
                "p95_ms": p95,
                "p99_ms": p99,
                "min_ms": min(response_times) if response_times else 0,
                "max_ms": max(response_times) if response_times else 0
            },
            
            # Success metrics
            "success_rate": success_count / len(recent_metrics),
            "total_requests": len(recent_metrics),
            "successful_requests": success_count,
            "failed_requests": len(recent_metrics) - success_count,
            
            # Throughput metrics
            "current_rps": self.current_rps,
            "avg_rps": len(recent_metrics) / 5.0,  # 5 minute window
            
            # Cache metrics
            "cache_hit_rate": cache_hits / len(recent_metrics) if recent_metrics else 0,
            "cache_stats": cache_stats,
            
            # Component performance
            "component_performance": component_stats,
            
            # Queue metrics
            "queue_stats": queue_stats,
            
            # Target compliance
            "target_compliance": {
                "response_time_p95_target_ms": self.targets['response_time_p95_ms'],
                "response_time_p95_actual_ms": p95,
                "response_time_meets_target": p95 <= self.targets['response_time_p95_ms'],
                "success_rate_target": self.targets['success_rate_min'],
                "success_rate_actual": success_count / len(recent_metrics),
                "success_rate_meets_target": (success_count / len(recent_metrics)) >= self.targets['success_rate_min']
            },
            
            # Alerts and recommendations
            "active_alerts": [a for a in self.alerts if current_time - a['timestamp'] <= 300],
            "recommendations": self.recommendations,
            
            # System health
            "health_status": self._calculate_health_status(p95, success_count / len(recent_metrics))
        }
    
    def _calculate_health_status(self, p95_response_time: float, success_rate: float) -> str:
        """Calculate overall system health status"""
        if success_rate < 0.95:
            return "critical"
        elif p95_response_time > self.targets['response_time_p95_ms'] * 2:
            return "critical"
        elif success_rate < 0.98 or p95_response_time > self.targets['response_time_p95_ms']:
            return "degraded"
        elif success_rate < 0.995 or p95_response_time > self.targets['response_time_p95_ms'] * 0.8:
            return "warning"
        else:
            return "healthy"
    
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time performance metrics"""
        current_time = time.time()
        
        # Last 30 seconds of metrics
        recent_metrics = [
            m for m in self.metrics 
            if current_time - m.timestamp <= 30.0
        ]
        
        if not recent_metrics:
            return {
                "current_rps": 0,
                "avg_response_time_ms": 0,
                "success_rate": 1.0,
                "active_requests": 0
            }
        
        response_times = [m.response_time_ms for m in recent_metrics]
        success_count = sum(1 for m in recent_metrics if m.success)
        
        # Get queue stats for active requests
        try:
            queue_stats = await request_queue.get_stats()
            active_requests = queue_stats.get('active_requests', 0)
        except Exception:
            active_requests = 0
        
        return {
            "timestamp": current_time,
            "current_rps": self.current_rps,
            "avg_response_time_ms": statistics.mean(response_times) if response_times else 0,
            "success_rate": success_count / len(recent_metrics),
            "active_requests": active_requests,
            "queue_size": queue_stats.get('current_queue_size', 0) if 'queue_stats' in locals() else 0,
            "recent_request_count": len(recent_metrics)
        }
    
    def reset_metrics(self):
        """Reset all performance metrics"""
        self.metrics.clear()
        for component_queue in self.component_metrics.values():
            component_queue.clear()
        self.alerts.clear()
        self.recommendations.clear()
        self.request_count_window.clear()
        
        logger.info("✅ Performance metrics reset")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()