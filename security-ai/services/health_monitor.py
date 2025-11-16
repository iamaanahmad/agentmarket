"""
Health monitoring and system status checks for SecurityGuard AI
"""
import asyncio
import time
import psutil
import redis
import asyncpg
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class ComponentHealth:
    name: str
    status: HealthStatus
    response_time_ms: float
    error_message: Optional[str] = None
    last_check: datetime = None
    
    def __post_init__(self):
        if self.last_check is None:
            self.last_check = datetime.utcnow()

@dataclass
class SystemHealth:
    overall_status: HealthStatus
    components: Dict[str, ComponentHealth]
    system_metrics: Dict[str, Any]
    timestamp: datetime
    
class HealthMonitor:
    def __init__(self, database_url: str, redis_url: str):
        self.database_url = database_url
        self.redis_url = redis_url
        self.redis_client = None
        self.db_pool = None
        
    async def initialize(self):
        """Initialize connections for health checks"""
        try:
            # Initialize Redis connection
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            
            # Initialize database pool
            self.db_pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=2)
            
        except Exception as e:
            print(f"Failed to initialize health monitor: {e}")
    
    async def check_database_health(self) -> ComponentHealth:
        """Check PostgreSQL database connectivity and performance"""
        start_time = time.time()
        
        try:
            if not self.db_pool:
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0,
                    error_message="Database pool not initialized"
                )
            
            async with self.db_pool.acquire() as conn:
                # Simple query to test connectivity
                result = await conn.fetchval("SELECT 1")
                
                if result == 1:
                    response_time = (time.time() - start_time) * 1000
                    
                    # Check if response time is acceptable
                    if response_time > 1000:  # 1 second threshold
                        status = HealthStatus.DEGRADED
                    else:
                        status = HealthStatus.HEALTHY
                    
                    return ComponentHealth(
                        name="database",
                        status=status,
                        response_time_ms=response_time
                    )
                else:
                    return ComponentHealth(
                        name="database",
                        status=HealthStatus.UNHEALTHY,
                        response_time_ms=(time.time() - start_time) * 1000,
                        error_message="Database query returned unexpected result"
                    )
                    
        except Exception as e:
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e)
            )
    
    async def check_redis_health(self) -> ComponentHealth:
        """Check Redis cache connectivity and performance"""
        start_time = time.time()
        
        try:
            if not self.redis_client:
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0,
                    error_message="Redis client not initialized"
                )
            
            # Test Redis connectivity with ping
            result = self.redis_client.ping()
            
            if result:
                response_time = (time.time() - start_time) * 1000
                
                # Check if response time is acceptable
                if response_time > 500:  # 500ms threshold
                    status = HealthStatus.DEGRADED
                else:
                    status = HealthStatus.HEALTHY
                
                return ComponentHealth(
                    name="redis",
                    status=status,
                    response_time_ms=response_time
                )
            else:
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=(time.time() - start_time) * 1000,
                    error_message="Redis ping failed"
                )
                
        except Exception as e:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e)
            )
    
    async def check_ml_model_health(self) -> ComponentHealth:
        """Check ML model availability and performance"""
        start_time = time.time()
        
        try:
            # Import here to avoid circular imports
            from core.security import SecurityAnalyzer
            
            analyzer = SecurityAnalyzer()
            
            # Test with a simple dummy transaction
            test_features = [0.1] * 50  # Dummy feature vector
            
            # This should complete quickly for a healthy model
            prediction = analyzer.ml_detector.predict_risk(test_features)
            
            response_time = (time.time() - start_time) * 1000
            
            if prediction is not None and 0 <= prediction <= 1:
                if response_time > 200:  # 200ms threshold for ML prediction
                    status = HealthStatus.DEGRADED
                else:
                    status = HealthStatus.HEALTHY
                
                return ComponentHealth(
                    name="ml_model",
                    status=status,
                    response_time_ms=response_time
                )
            else:
                return ComponentHealth(
                    name="ml_model",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    error_message="ML model returned invalid prediction"
                )
                
        except Exception as e:
            return ComponentHealth(
                name="ml_model",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e)
            )
    
    async def check_pattern_matcher_health(self) -> ComponentHealth:
        """Check pattern matcher performance"""
        start_time = time.time()
        
        try:
            from services.pattern_matcher import PatternMatcher
            
            matcher = PatternMatcher()
            
            # Test with a dummy program ID
            test_program_id = "11111111111111111111111111111112"  # System program
            
            matches = await matcher.find_matches(test_program_id, [])
            
            response_time = (time.time() - start_time) * 1000
            
            if matches is not None:
                if response_time > 100:  # 100ms threshold for pattern matching
                    status = HealthStatus.DEGRADED
                else:
                    status = HealthStatus.HEALTHY
                
                return ComponentHealth(
                    name="pattern_matcher",
                    status=status,
                    response_time_ms=response_time
                )
            else:
                return ComponentHealth(
                    name="pattern_matcher",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    error_message="Pattern matcher returned None"
                )
                
        except Exception as e:
            return ComponentHealth(
                name="pattern_matcher",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e)
            )
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_free_gb = disk.free / (1024**3)
            
            # Network I/O
            network = psutil.net_io_counters()
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_available_gb": round(memory_available_gb, 2),
                "disk_percent": round(disk_percent, 2),
                "disk_free_gb": round(disk_free_gb, 2),
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def get_comprehensive_health(self) -> SystemHealth:
        """Get comprehensive system health status"""
        # Run all health checks concurrently
        health_checks = await asyncio.gather(
            self.check_database_health(),
            self.check_redis_health(),
            self.check_ml_model_health(),
            self.check_pattern_matcher_health(),
            return_exceptions=True
        )
        
        components = {}
        
        # Process health check results
        for check in health_checks:
            if isinstance(check, ComponentHealth):
                components[check.name] = check
            else:
                # Handle exceptions
                components["unknown"] = ComponentHealth(
                    name="unknown",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0,
                    error_message=str(check)
                )
        
        # Determine overall status
        statuses = [comp.status for comp in components.values()]
        
        if all(status == HealthStatus.HEALTHY for status in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(status == HealthStatus.UNHEALTHY for status in statuses):
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED
        
        # Get system metrics
        system_metrics = self.get_system_metrics()
        
        return SystemHealth(
            overall_status=overall_status,
            components=components,
            system_metrics=system_metrics,
            timestamp=datetime.utcnow()
        )
    
    async def get_readiness_status(self) -> bool:
        """Check if the service is ready to handle requests"""
        try:
            # Check critical components only
            db_health = await self.check_database_health()
            redis_health = await self.check_redis_health()
            
            return (db_health.status != HealthStatus.UNHEALTHY and 
                   redis_health.status != HealthStatus.UNHEALTHY)
        except:
            return False
    
    async def get_liveness_status(self) -> bool:
        """Check if the service is alive (basic functionality)"""
        try:
            # Simple check - can we access basic system resources?
            psutil.cpu_percent()
            return True
        except:
            return False

# Global health monitor instance
health_monitor = None

async def get_health_monitor() -> HealthMonitor:
    """Get or create health monitor instance"""
    global health_monitor
    
    if health_monitor is None:
        import os
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/securityguard")
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        health_monitor = HealthMonitor(database_url, redis_url)
        await health_monitor.initialize()
    
    return health_monitor