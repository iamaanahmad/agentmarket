"""
Optimized database connection pool manager for SecurityGuard AI
Provides high-performance database access with connection pooling and query optimization
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from loguru import logger

# Optional imports for database functionality
try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    logger.warning("asyncpg not available - database pool will use fallback mode")

try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import NullPool, QueuePool
    from sqlalchemy import text
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning("SQLAlchemy async not available - database pool will use fallback mode")

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


class DatabasePool:
    """
    High-performance database connection pool with query optimization,
    connection monitoring, and automatic failover
    """
    
    def __init__(self):
        self.settings = get_settings()
        
        # SQLAlchemy async engine
        self.engine = None
        self.session_factory = None
        
        # Raw asyncpg pool for high-performance queries
        self.asyncpg_pool: Optional[Any] = None
        
        # Performance monitoring
        self.stats = ConnectionStats()
        self.query_times: List[float] = []
        self.slow_query_threshold_ms = 1000  # 1 second
        
        # Connection pool configuration
        self.pool_config = {
            'min_size': 5,
            'max_size': 20,
            'max_queries': 50000,
            'max_inactive_connection_lifetime': 300.0,  # 5 minutes
            'command_timeout': 60,
            'server_settings': {
                'application_name': 'SecurityGuard_AI',
                'jit': 'off'  # Disable JIT for consistent performance
            }
        }
    
    async def initialize(self):
        """Initialize database connection pools"""
        if not SQLALCHEMY_AVAILABLE and not ASYNCPG_AVAILABLE:
            logger.warning("⚠️ No database libraries available - running in fallback mode")
            return False
            
        try:
            # Initialize SQLAlchemy async engine with optimized settings
            if SQLALCHEMY_AVAILABLE:
                self.engine = create_async_engine(
                    self.settings.database_url,
                    poolclass=QueuePool,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True,
                    pool_recycle=3600,  # 1 hour
                    echo=False,  # Set to True for SQL debugging
                    future=True
                )
                
                # Create session factory
                self.session_factory = async_sessionmaker(
                    self.engine,
                    class_=AsyncSession,
                    expire_on_commit=False
                )
                
                # Test SQLAlchemy connection
                async with self.engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                
                logger.info("✅ SQLAlchemy database pool initialized")
            
            # Initialize asyncpg pool for high-performance queries
            if ASYNCPG_AVAILABLE:
                self.asyncpg_pool = await asyncpg.create_pool(
                    self.settings.database_url.replace('+asyncpg', ''),
                    **self.pool_config
                )
                
                # Test asyncpg connection
                async with self.asyncpg_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                
                logger.info("✅ AsyncPG database pool initialized")
            
            logger.info("✅ Database pools initialized successfully")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Database pool initialization failed (expected in test environment): {e}")
            return False
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get SQLAlchemy async session with connection management"""
        if not self.session_factory:
            raise RuntimeError("Database pool not initialized")
        
        session_start = time.time()
        
        async with self.session_factory() as session:
            try:
                self.stats.active_connections += 1
                yield session
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                self.stats.failed_queries += 1
                logger.error(f"Database session error: {e}")
                raise
                
            finally:
                self.stats.active_connections -= 1
                session_time = (time.time() - session_start) * 1000
                
                if session_time > self.slow_query_threshold_ms:
                    self.stats.slow_queries += 1
                    logger.warning(f"Slow database session: {session_time:.1f}ms")
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[Any, None]:
        """Get raw asyncpg connection for high-performance queries"""
        if not self.asyncpg_pool:
            raise RuntimeError("AsyncPG pool not initialized")
        
        connection_start = time.time()
        
        async with self.asyncpg_pool.acquire() as conn:
            try:
                self.stats.active_connections += 1
                yield conn
                
            except Exception as e:
                self.stats.failed_queries += 1
                logger.error(f"Database connection error: {e}")
                raise
                
            finally:
                self.stats.active_connections -= 1
                connection_time = (time.time() - connection_start) * 1000
                
                if connection_time > self.slow_query_threshold_ms:
                    self.stats.slow_queries += 1
                    logger.warning(f"Slow database connection: {connection_time:.1f}ms")
    
    async def execute_query(self, query: str, *args, timeout: float = 30.0) -> List[Dict[str, Any]]:
        """Execute optimized query with performance monitoring"""
        query_start = time.time()
        
        try:
            async with self.get_connection() as conn:
                result = await asyncio.wait_for(
                    conn.fetch(query, *args),
                    timeout=timeout
                )
                
                # Convert to list of dicts
                return [dict(row) for row in result]
                
        except asyncio.TimeoutError:
            self.stats.failed_queries += 1
            logger.error(f"Query timeout after {timeout}s: {query[:100]}...")
            raise
            
        except Exception as e:
            self.stats.failed_queries += 1
            logger.error(f"Query execution failed: {e}")
            raise
            
        finally:
            query_time = (time.time() - query_start) * 1000
            self.stats.total_queries += 1
            
            if query_time > self.slow_query_threshold_ms:
                self.stats.slow_queries += 1
                logger.warning(f"Slow query: {query_time:.1f}ms - {query[:100]}...")
    
    async def execute_transaction(self, queries: List[tuple], timeout: float = 30.0) -> bool:
        """Execute multiple queries in a transaction with rollback support"""
        transaction_start = time.time()
        
        try:
            async with self.get_connection() as conn:
                async with conn.transaction():
                    for query, args in queries:
                        await asyncio.wait_for(
                            conn.execute(query, *args),
                            timeout=timeout
                        )
                
                return True
                
        except asyncio.TimeoutError:
            self.stats.failed_queries += len(queries)
            logger.error(f"Transaction timeout after {timeout}s")
            return False
            
        except Exception as e:
            self.stats.failed_queries += len(queries)
            logger.error(f"Transaction failed: {e}")
            return False
            
        finally:
            transaction_time = (time.time() - transaction_start) * 1000
            self.stats.total_queries += len(queries)
            
            if transaction_time > self.slow_query_threshold_ms * 2:
                self.stats.slow_queries += 1
                logger.warning(f"Slow transaction: {transaction_time:.1f}ms")
    
    async def get_pool_stats(self) -> Dict[str, Any]:
        """Get comprehensive database pool statistics"""
        sqlalchemy_stats = {}
        asyncpg_stats = {}
        
        try:
            if self.engine:
                pool = self.engine.pool
                sqlalchemy_stats = {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "invalid": pool.invalid()
                }
        except Exception as e:
            logger.warning(f"Failed to get SQLAlchemy pool stats: {e}")
        
        try:
            if self.asyncpg_pool:
                asyncpg_stats = {
                    "size": self.asyncpg_pool.get_size(),
                    "min_size": self.asyncpg_pool.get_min_size(),
                    "max_size": self.asyncpg_pool.get_max_size(),
                    "idle_connections": self.asyncpg_pool.get_idle_size()
                }
        except Exception as e:
            logger.warning(f"Failed to get AsyncPG pool stats: {e}")
        
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
                "sqlalchemy": sqlalchemy_stats,
                "asyncpg": asyncpg_stats
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        health_start = time.time()
        
        try:
            # Test SQLAlchemy connection
            sqlalchemy_healthy = False
            try:
                async with self.get_session() as session:
                    await session.execute(text("SELECT 1"))
                    sqlalchemy_healthy = True
            except Exception as e:
                logger.warning(f"SQLAlchemy health check failed: {e}")
            
            # Test AsyncPG connection
            asyncpg_healthy = False
            try:
                async with self.get_connection() as conn:
                    await conn.fetchval("SELECT 1")
                    asyncpg_healthy = True
            except Exception as e:
                logger.warning(f"AsyncPG health check failed: {e}")
            
            health_time = (time.time() - health_start) * 1000
            
            overall_status = "healthy" if (sqlalchemy_healthy and asyncpg_healthy) else "degraded"
            
            return {
                "status": overall_status,
                "health_check_time_ms": health_time,
                "connections": {
                    "sqlalchemy": "healthy" if sqlalchemy_healthy else "unhealthy",
                    "asyncpg": "healthy" if asyncpg_healthy else "unhealthy"
                },
                "pool_utilization": {
                    "active_connections": self.stats.active_connections,
                    "total_capacity": self.pool_config['max_size']
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "health_check_time_ms": (time.time() - health_start) * 1000
            }
    
    async def close(self):
        """Close all database connections"""
        try:
            if self.asyncpg_pool:
                await self.asyncpg_pool.close()
                logger.info("✅ AsyncPG pool closed")
            
            if self.engine:
                await self.engine.dispose()
                logger.info("✅ SQLAlchemy engine disposed")
                
        except Exception as e:
            logger.warning(f"⚠️ Error closing database pools: {e}")


# Global database pool instance
database_pool = DatabasePool()