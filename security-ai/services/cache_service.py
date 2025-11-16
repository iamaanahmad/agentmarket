"""
High-performance caching service for SecurityGuard AI
Optimized for <2 second response times with Redis clustering support
"""

import asyncio
import json
import time
import hashlib
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta

import redis.asyncio as redis
from loguru import logger

try:
    from ..core.config import get_settings
    from ..models.schemas import TransactionScanResponse
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from core.config import get_settings
    from models.schemas import TransactionScanResponse


@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    errors: int = 0
    total_requests: int = 0
    avg_lookup_time_ms: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        return self.hits / max(1, self.total_requests)
    
    @property
    def miss_rate(self) -> float:
        return self.misses / max(1, self.total_requests)


class CacheService:
    """
    High-performance Redis caching service with connection pooling,
    circuit breaker pattern, and performance monitoring
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_pool: Optional[redis.ConnectionPool] = None
        self.redis_client: Optional[redis.Redis] = None
        
        # Performance monitoring
        self.stats = CacheStats()
        self.lookup_times: List[float] = []
        
        # Circuit breaker for Redis failures
        self.circuit_breaker_failures = 0
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_reset_time = 60  # seconds
        self.circuit_breaker_last_failure = 0
        
        # Cache configuration
        self.cache_config = {
            # Scan results cache
            'scan_results': {
                'ttl': 300,  # 5 minutes
                'prefix': 'scan:',
                'compress': True
            },
            
            # Pattern matches cache
            'pattern_matches': {
                'ttl': 1800,  # 30 minutes
                'prefix': 'patterns:',
                'compress': True
            },
            
            # ML predictions cache
            'ml_predictions': {
                'ttl': 600,  # 10 minutes
                'prefix': 'ml:',
                'compress': False
            },
            
            # Program analysis cache
            'program_analysis': {
                'ttl': 3600,  # 1 hour
                'prefix': 'programs:',
                'compress': False
            },
            
            # User sessions cache
            'user_sessions': {
                'ttl': 86400,  # 24 hours
                'prefix': 'session:',
                'compress': False
            },
            
            # Account analysis cache
            'account_analysis': {
                'ttl': 900,  # 15 minutes
                'prefix': 'accounts:',
                'compress': False
            }
        }
    
    async def initialize(self):
        """Initialize Redis connection pool with optimized settings"""
        try:
            # Create connection pool for better performance
            self.redis_pool = redis.ConnectionPool.from_url(
                self.settings.redis_url,
                max_connections=20,  # Pool size for concurrent requests
                retry_on_timeout=True,
                retry_on_error=[redis.ConnectionError, redis.TimeoutError],
                health_check_interval=30,
                socket_connect_timeout=2,
                socket_timeout=1,
                decode_responses=True
            )
            
            # Create Redis client from pool
            self.redis_client = redis.Redis(connection_pool=self.redis_pool)
            
            # Test connection
            await asyncio.wait_for(self.redis_client.ping(), timeout=2.0)
            
            # Set up Redis optimizations
            await self._setup_redis_optimizations()
            
            logger.info("✅ Cache service initialized with connection pool")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Cache service initialization failed: {e}")
            self.redis_client = None
            return False
    
    async def _setup_redis_optimizations(self):
        """Configure Redis for optimal performance"""
        try:
            # Enable keyspace notifications for cache invalidation
            await self.redis_client.config_set('notify-keyspace-events', 'Ex')
            
            # Set memory policy for cache eviction
            await self.redis_client.config_set('maxmemory-policy', 'allkeys-lru')
            
            logger.debug("✅ Redis optimizations configured")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis optimization setup failed: {e}")
    
    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open (Redis unavailable)"""
        if self.circuit_breaker_failures < self.circuit_breaker_threshold:
            return False
        
        # Check if reset time has passed
        if time.time() - self.circuit_breaker_last_failure > self.circuit_breaker_reset_time:
            self.circuit_breaker_failures = 0
            return False
        
        return True
    
    def _record_failure(self):
        """Record a cache failure for circuit breaker"""
        self.circuit_breaker_failures += 1
        self.circuit_breaker_last_failure = time.time()
        self.stats.errors += 1
    
    def _record_success(self):
        """Record a successful cache operation"""
        if self.circuit_breaker_failures > 0:
            self.circuit_breaker_failures = max(0, self.circuit_breaker_failures - 1)
    
    def _generate_cache_key(self, cache_type: str, identifier: str) -> str:
        """Generate optimized cache key with consistent hashing"""
        prefix = self.cache_config[cache_type]['prefix']
        
        # Use SHA256 hash for consistent key length and distribution
        if len(identifier) > 100:  # Hash long identifiers
            identifier = hashlib.sha256(identifier.encode()).hexdigest()[:32]
        
        return f"{prefix}{identifier}"
    
    async def get(self, cache_type: str, identifier: str, timeout: float = 0.05) -> Optional[Any]:
        """
        Get value from cache with performance monitoring
        
        Args:
            cache_type: Type of cache (scan_results, pattern_matches, etc.)
            identifier: Unique identifier for the cached item
            timeout: Maximum time to wait for cache lookup (default: 50ms)
        """
        if not self.redis_client or self._is_circuit_breaker_open():
            self.stats.misses += 1
            self.stats.total_requests += 1
            return None
        
        start_time = time.time()
        
        try:
            cache_key = self._generate_cache_key(cache_type, identifier)
            
            # Get value with timeout
            cached_data = await asyncio.wait_for(
                self.redis_client.get(cache_key),
                timeout=timeout
            )
            
            lookup_time = (time.time() - start_time) * 1000
            self.lookup_times.append(lookup_time)
            
            # Keep only recent lookup times for performance
            if len(self.lookup_times) > 1000:
                self.lookup_times = self.lookup_times[-500:]
            
            self.stats.total_requests += 1
            
            if cached_data:
                self.stats.hits += 1
                self._record_success()
                
                # Decompress if needed
                if self.cache_config[cache_type]['compress']:
                    cached_data = self._decompress_data(cached_data)
                
                # Parse JSON
                try:
                    return json.loads(cached_data)
                except json.JSONDecodeError:
                    return cached_data
            else:
                self.stats.misses += 1
                return None
                
        except asyncio.TimeoutError:
            self.stats.misses += 1
            self.stats.total_requests += 1
            logger.debug(f"Cache lookup timeout for {cache_type}:{identifier}")
            return None
            
        except Exception as e:
            self._record_failure()
            self.stats.total_requests += 1
            logger.debug(f"Cache lookup error: {e}")
            return None
    
    async def set(self, cache_type: str, identifier: str, value: Any, 
                  custom_ttl: Optional[int] = None) -> bool:
        """
        Set value in cache with compression and TTL
        
        Args:
            cache_type: Type of cache
            identifier: Unique identifier
            value: Value to cache
            custom_ttl: Custom TTL override
        """
        if not self.redis_client or self._is_circuit_breaker_open():
            return False
        
        try:
            cache_key = self._generate_cache_key(cache_type, identifier)
            ttl = custom_ttl or self.cache_config[cache_type]['ttl']
            
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            # Compress if configured
            if self.cache_config[cache_type]['compress']:
                serialized_value = self._compress_data(serialized_value)
            
            # Set with TTL (fire and forget for performance)
            asyncio.create_task(
                self.redis_client.setex(cache_key, ttl, serialized_value)
            )
            
            self._record_success()
            return True
            
        except Exception as e:
            self._record_failure()
            logger.debug(f"Cache set error: {e}")
            return False
    
    async def delete(self, cache_type: str, identifier: str) -> bool:
        """Delete value from cache"""
        if not self.redis_client or self._is_circuit_breaker_open():
            return False
        
        try:
            cache_key = self._generate_cache_key(cache_type, identifier)
            await self.redis_client.delete(cache_key)
            return True
            
        except Exception as e:
            self._record_failure()
            logger.debug(f"Cache delete error: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern"""
        if not self.redis_client or self._is_circuit_breaker_open():
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
            
        except Exception as e:
            self._record_failure()
            logger.debug(f"Cache pattern invalidation error: {e}")
            return 0
    
    def _compress_data(self, data: str) -> str:
        """Compress data for storage (simple implementation)"""
        # In production, use gzip or lz4 compression
        return data
    
    def _decompres_data(self, data: str) -> str:
        """Decompress data from storage"""
        return data
    
    def _decompress_data(self, data: str) -> str:
        """Decompress data from storage (fixed typo)"""
        return data
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        # Calculate average lookup time
        if self.lookup_times:
            self.stats.avg_lookup_time_ms = sum(self.lookup_times) / len(self.lookup_times)
        
        return {
            "hit_rate": self.stats.hit_rate,
            "miss_rate": self.stats.miss_rate,
            "total_requests": self.stats.total_requests,
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "errors": self.stats.errors,
            "avg_lookup_time_ms": self.stats.avg_lookup_time_ms,
            "circuit_breaker_failures": self.circuit_breaker_failures,
            "circuit_breaker_open": self._is_circuit_breaker_open(),
            "redis_connected": self.redis_client is not None
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform cache health check"""
        if not self.redis_client:
            return {"status": "disconnected", "error": "No Redis connection"}
        
        try:
            start_time = time.time()
            await asyncio.wait_for(self.redis_client.ping(), timeout=1.0)
            ping_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "ping_time_ms": ping_time,
                "circuit_breaker_open": self._is_circuit_breaker_open()
            }
            
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def close(self):
        """Close Redis connections"""
        try:
            if self.redis_client:
                await self.redis_client.close()
            if self.redis_pool:
                await self.redis_pool.disconnect()
            logger.info("✅ Cache service connections closed")
        except Exception as e:
            logger.warning(f"⚠️ Error closing cache connections: {e}")


# Global cache service instance
cache_service = CacheService()