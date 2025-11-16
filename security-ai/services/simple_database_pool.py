"""
Simple database connection pool for SecurityGuard AI
Fallback implementation without external dependencies
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from loguru import logger

try:
    from ..core.config import get_settings
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from core.config import get_settings


@dataclass
class ConnectionStats:
    """Database connection statistics"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    total_queries: int = 0
    slow_queries: int = 0
    failed_queries: int = 0
    avg_query_time_ms: float = 0.0
    connection_errors: int = 0


class SimpleDatabasePool:
    """
    Simple database connection pool fallback
    Provides interface compatibility without external dependencies
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.stats = ConnectionStats()
        self.initialized = False
        
        # Performance monitoring
        self.query_times: List[float] = []
        self.slow_query_threshold_ms = 1000  # 1 second
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            logger.info("✅ Simple database pool initialized (fallback mode)")
            self.initialized = True
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Database pool initialization failed: {e}")
            return False
    
    async def execute_query(self, query: str, *args, timeout: float = 30.0) -> List[Dict[str, Any]]:
        """Execute query (fallback implementation)"""
        query_start = time.time()
        
        try:
            # Simulate query execution
            await asyncio.sleep(0.001)  # 1ms simulated query time
            
            query_time = (time.time() - query_start) * 1000
            self.stats.total_queries += 1
            
            if query_time > self.slow_query_threshold_ms:
                self.stats.slow_queries += 1
            
            # Return empty result for fallback
            return []
            
        except Exception as e:
            self.stats.failed_queries += 1
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def execute_transaction(self, queries: List[tuple], timeout: float = 30.0) -> bool:
        """Execute transaction (fallback implementation)"""
        try:
            # Simulate transaction execution
            await asyncio.sleep(0.005)  # 5ms simulated transaction time
            
            self.stats.total_queries += len(queries)
            return True
            
        except Exception as e:
            self.stats.failed_queries += len(queries)
            logger.error(f"Transaction failed: {e}")
            return False
    
    async def get_pool_stats(self) -> Dict[str, Any]:
        """Get database pool statistics"""
        return {
            "connection_stats": {
                "total_connections": self.stats.total_connections,
                "active_connections": self.stats.active_connections,
                "idle_connections": self.stats.idle_connections,
                "connection_errors": self.stats.connection_errors
            },
            "query_stats": {
                "total_queries": self.stats.total_queries,
                "slow_queries": self.stats.slow_queries,
                "failed_queries": self.stats.failed_queries,
                "avg_query_time_ms": self.stats.avg_query_time_ms
            },
            "pool_stats": {
                "fallback_mode": True,
                "initialized": self.initialized
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        health_start = time.time()
        
        try:
            # Simulate health check
            await asyncio.sleep(0.001)
            
            health_time = (time.time() - health_start) * 1000
            
            return {
                "status": "healthy" if self.initialized else "unhealthy",
                "health_check_time_ms": health_time,
                "connections": {
                    "fallback_mode": True,
                    "initialized": self.initialized
                },
                "pool_utilization": {
                    "active_connections": 0,
                    "total_capacity": 0
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "health_check_time_ms": (time.time() - health_start) * 1000
            }
    
    async def close(self):
        """Close database connections"""
        try:
            self.initialized = False
            logger.info("✅ Simple database pool closed")
        except Exception as e:
            logger.warning(f"⚠️ Error closing database pool: {e}")


# Global database pool instance
database_pool = SimpleDatabasePool()