"""
Application Performance Monitoring (APM) service for SecurityGuard AI
Tracks performance metrics, errors, and business metrics
"""
import time
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading
from contextlib import asynccontextmanager

@dataclass
class RequestMetric:
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    timestamp: datetime
    user_id: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class BusinessMetric:
    metric_name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None

@dataclass
class ErrorEvent:
    error_type: str
    error_message: str
    stack_trace: Optional[str]
    endpoint: str
    timestamp: datetime
    user_id: Optional[str] = None
    context: Dict[str, Any] = None

class MetricsCollector:
    def __init__(self, max_metrics_in_memory: int = 10000):
        self.max_metrics_in_memory = max_metrics_in_memory
        
        # In-memory storage for recent metrics
        self.request_metrics = deque(maxlen=max_metrics_in_memory)
        self.business_metrics = deque(maxlen=max_metrics_in_memory)
        self.error_events = deque(maxlen=max_metrics_in_memory)
        
        # Real-time aggregations
        self.response_times = defaultdict(list)  # endpoint -> [response_times]
        self.error_counts = defaultdict(int)     # endpoint -> error_count
        self.request_counts = defaultdict(int)   # endpoint -> request_count
        
        # Thread lock for thread-safe operations
        self.lock = threading.Lock()
        
        # Start background cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task to clean up old metrics"""
        async def cleanup_old_metrics():
            while True:
                await asyncio.sleep(300)  # Clean up every 5 minutes
                self._cleanup_old_metrics()
        
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(cleanup_old_metrics())
    
    def _cleanup_old_metrics(self):
        """Remove metrics older than 1 hour from real-time aggregations"""
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        
        with self.lock:
            # Clean up response times
            for endpoint in list(self.response_times.keys()):
                self.response_times[endpoint] = [
                    (rt, ts) for rt, ts in self.response_times[endpoint]
                    if ts > cutoff_time
                ]
                if not self.response_times[endpoint]:
                    del self.response_times[endpoint]
    
    def record_request(self, metric: RequestMetric):
        """Record a request metric"""
        with self.lock:
            self.request_metrics.append(metric)
            
            # Update real-time aggregations
            self.request_counts[metric.endpoint] += 1
            
            if metric.status_code >= 400:
                self.error_counts[metric.endpoint] += 1
            
            # Store response time with timestamp for cleanup
            self.response_times[metric.endpoint].append(
                (metric.response_time_ms, metric.timestamp)
            )
    
    def record_business_metric(self, metric: BusinessMetric):
        """Record a business metric"""
        with self.lock:
            self.business_metrics.append(metric)
    
    def record_error(self, error: ErrorEvent):
        """Record an error event"""
        with self.lock:
            self.error_events.append(error)
            self.error_counts[error.endpoint] += 1
    
    def get_endpoint_stats(self, endpoint: str, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get statistics for a specific endpoint"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        with self.lock:
            # Filter metrics within time window
            recent_requests = [
                m for m in self.request_metrics
                if m.endpoint == endpoint and m.timestamp > cutoff_time
            ]
            
            if not recent_requests:
                return {
                    "endpoint": endpoint,
                    "request_count": 0,
                    "error_count": 0,
                    "error_rate": 0.0,
                    "avg_response_time_ms": 0.0,
                    "p95_response_time_ms": 0.0,
                    "p99_response_time_ms": 0.0
                }
            
            # Calculate statistics
            response_times = [m.response_time_ms for m in recent_requests]
            error_count = sum(1 for m in recent_requests if m.status_code >= 400)
            
            response_times.sort()
            p95_index = int(0.95 * len(response_times))
            p99_index = int(0.99 * len(response_times))
            
            return {
                "endpoint": endpoint,
                "request_count": len(recent_requests),
                "error_count": error_count,
                "error_rate": error_count / len(recent_requests) if recent_requests else 0.0,
                "avg_response_time_ms": sum(response_times) / len(response_times),
                "p95_response_time_ms": response_times[p95_index] if response_times else 0.0,
                "p99_response_time_ms": response_times[p99_index] if response_times else 0.0
            }
    
    def get_overall_stats(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get overall system statistics"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        with self.lock:
            recent_requests = [
                m for m in self.request_metrics
                if m.timestamp > cutoff_time
            ]
            
            recent_errors = [
                e for e in self.error_events
                if e.timestamp > cutoff_time
            ]
            
            if not recent_requests:
                return {
                    "total_requests": 0,
                    "total_errors": 0,
                    "overall_error_rate": 0.0,
                    "avg_response_time_ms": 0.0,
                    "requests_per_minute": 0.0
                }
            
            # Calculate overall statistics
            total_requests = len(recent_requests)
            total_errors = len(recent_errors)
            avg_response_time = sum(m.response_time_ms for m in recent_requests) / total_requests
            requests_per_minute = total_requests / time_window_minutes
            
            return {
                "total_requests": total_requests,
                "total_errors": total_errors,
                "overall_error_rate": total_errors / total_requests if total_requests > 0 else 0.0,
                "avg_response_time_ms": avg_response_time,
                "requests_per_minute": requests_per_minute
            }
    
    def get_business_metrics(self, time_window_minutes: int = 60) -> Dict[str, List[Dict]]:
        """Get business metrics grouped by metric name"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        with self.lock:
            recent_metrics = [
                m for m in self.business_metrics
                if m.timestamp > cutoff_time
            ]
            
            # Group by metric name
            grouped_metrics = defaultdict(list)
            for metric in recent_metrics:
                grouped_metrics[metric.metric_name].append(asdict(metric))
            
            return dict(grouped_metrics)

class APMService:
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.start_time = datetime.utcnow()
    
    @asynccontextmanager
    async def track_request(self, endpoint: str, method: str, user_id: Optional[str] = None):
        """Context manager to track request performance"""
        start_time = time.time()
        error_message = None
        status_code = 200
        
        try:
            yield
        except Exception as e:
            error_message = str(e)
            status_code = 500
            
            # Record error event
            self.record_error(
                endpoint=endpoint,
                error_type=type(e).__name__,
                error_message=str(e),
                user_id=user_id
            )
            raise
        finally:
            # Record request metric
            response_time_ms = (time.time() - start_time) * 1000
            
            self.metrics_collector.record_request(RequestMetric(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                error_message=error_message
            ))
    
    def record_business_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a business metric"""
        self.metrics_collector.record_business_metric(BusinessMetric(
            metric_name=name,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags or {}
        ))
    
    def record_error(self, endpoint: str, error_type: str, error_message: str, 
                    user_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """Record an error event"""
        self.metrics_collector.record_error(ErrorEvent(
            error_type=error_type,
            error_message=error_message,
            stack_trace=None,  # Could be enhanced to capture stack traces
            endpoint=endpoint,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            context=context or {}
        ))
    
    def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data"""
        overall_stats = self.metrics_collector.get_overall_stats()
        business_metrics = self.metrics_collector.get_business_metrics()
        
        # Get stats for key endpoints
        key_endpoints = ["/api/scan", "/api/chat", "/api/history", "/health"]
        endpoint_stats = {}
        
        for endpoint in key_endpoints:
            endpoint_stats[endpoint] = self.metrics_collector.get_endpoint_stats(endpoint)
        
        return {
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "overall_stats": overall_stats,
            "endpoint_stats": endpoint_stats,
            "business_metrics": business_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_prometheus_metrics(self) -> str:
        """Generate Prometheus-compatible metrics"""
        overall_stats = self.metrics_collector.get_overall_stats()
        
        metrics = []
        
        # HTTP request metrics
        metrics.append(f'http_requests_total {overall_stats["total_requests"]}')
        metrics.append(f'http_request_duration_seconds {overall_stats["avg_response_time_ms"] / 1000}')
        metrics.append(f'http_requests_per_minute {overall_stats["requests_per_minute"]}')
        
        # Error metrics
        metrics.append(f'http_errors_total {overall_stats["total_errors"]}')
        metrics.append(f'http_error_rate {overall_stats["overall_error_rate"]}')
        
        # Business metrics
        business_metrics = self.metrics_collector.get_business_metrics(time_window_minutes=5)
        
        for metric_name, metric_list in business_metrics.items():
            if metric_list:
                latest_value = metric_list[-1]["value"]
                safe_name = metric_name.replace("-", "_").replace(" ", "_").lower()
                metrics.append(f'{safe_name} {latest_value}')
        
        # System uptime
        uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
        metrics.append(f'system_uptime_seconds {uptime_seconds}')
        
        return '\n'.join(metrics)

# Global APM service instance
apm_service = APMService()

def get_apm_service() -> APMService:
    """Get the global APM service instance"""
    return apm_service