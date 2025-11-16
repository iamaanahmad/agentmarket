"""
Async request queue and load balancer for SecurityGuard AI
Handles 100+ concurrent requests with performance optimization
"""

import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from loguru import logger

try:
    from ..core.config import get_settings
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from core.config import get_settings


class RequestPriority(Enum):
    """Request priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class QueuedRequest:
    """Queued request data structure"""
    request_id: str
    handler: Callable[..., Awaitable[Any]]
    args: tuple
    kwargs: dict
    priority: RequestPriority = RequestPriority.NORMAL
    created_at: float = field(default_factory=time.time)
    timeout: float = 30.0
    retries: int = 0
    max_retries: int = 2
    
    def __lt__(self, other):
        """Priority queue comparison"""
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value
        return self.created_at < other.created_at


@dataclass
class QueueStats:
    """Queue performance statistics"""
    total_requests: int = 0
    completed_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    retry_requests: int = 0
    current_queue_size: int = 0
    max_queue_size: int = 0
    avg_processing_time_ms: float = 0.0
    avg_wait_time_ms: float = 0.0
    
    @property
    def success_rate(self) -> float:
        return self.completed_requests / max(1, self.total_requests)
    
    @property
    def failure_rate(self) -> float:
        return self.failed_requests / max(1, self.total_requests)


class RequestQueue:
    """
    High-performance async request queue with load balancing,
    priority handling, and circuit breaker pattern
    """
    
    def __init__(self, max_concurrent: int = 100, max_queue_size: int = 1000):
        self.settings = get_settings()
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        
        # Queue management
        self.request_queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self.active_requests: Dict[str, asyncio.Task] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Performance tracking
        self.stats = QueueStats()
        self.processing_times: List[float] = []
        self.wait_times: List[float] = []
        
        # Worker management
        self.workers: List[asyncio.Task] = []
        self.worker_count = min(max_concurrent, 20)  # Optimal worker count
        self.running = False
        
        # Circuit breaker for overload protection
        self.circuit_breaker_failures = 0
        self.circuit_breaker_threshold = 10
        self.circuit_breaker_reset_time = 60
        self.circuit_breaker_last_failure = 0
    
    async def start(self):
        """Start the request queue workers"""
        if self.running:
            return
        
        self.running = True
        
        # Start worker tasks
        for i in range(self.worker_count):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        
        logger.info(f"✅ Request queue started with {self.worker_count} workers")
    
    async def stop(self):
        """Stop the request queue workers"""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        # Cancel active requests
        for task in self.active_requests.values():
            task.cancel()
        
        self.workers.clear()
        self.active_requests.clear()
        
        logger.info("✅ Request queue stopped")
    
    async def submit(self, handler: Callable[..., Awaitable[Any]], *args, 
                    priority: RequestPriority = RequestPriority.NORMAL,
                    timeout: float = 30.0, max_retries: int = 2, **kwargs) -> str:
        """
        Submit a request to the queue
        
        Args:
            handler: Async function to execute
            *args: Positional arguments for handler
            priority: Request priority
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            **kwargs: Keyword arguments for handler
            
        Returns:
            Request ID for tracking
        """
        # Check circuit breaker
        if self._is_circuit_breaker_open():
            raise RuntimeError("Request queue overloaded - circuit breaker open")
        
        # Check queue capacity
        if self.request_queue.qsize() >= self.max_queue_size:
            self._record_failure()
            raise RuntimeError(f"Request queue full (max: {self.max_queue_size})")
        
        # Create request
        request_id = str(uuid.uuid4())
        request = QueuedRequest(
            request_id=request_id,
            handler=handler,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout,
            max_retries=max_retries
        )
        
        # Add to queue
        try:
            await self.request_queue.put(request)
            self.stats.total_requests += 1
            self.stats.current_queue_size = self.request_queue.qsize()
            self.stats.max_queue_size = max(self.stats.max_queue_size, self.stats.current_queue_size)
            
            logger.debug(f"📥 Request queued: {request_id} (priority: {priority.name})")
            return request_id
            
        except asyncio.QueueFull:
            self._record_failure()
            raise RuntimeError("Request queue full")
    
    async def get_result(self, request_id: str, timeout: float = 30.0) -> Any:
        """
        Get result for a submitted request
        
        Args:
            request_id: Request ID from submit()
            timeout: Maximum time to wait for result
            
        Returns:
            Request result
        """
        if request_id not in self.active_requests:
            raise ValueError(f"Request {request_id} not found")
        
        try:
            task = self.active_requests[request_id]
            result = await asyncio.wait_for(task, timeout=timeout)
            return result
            
        except asyncio.TimeoutError:
            self.stats.timeout_requests += 1
            raise TimeoutError(f"Request {request_id} timed out")
        
        finally:
            # Clean up completed request
            if request_id in self.active_requests:
                del self.active_requests[request_id]
    
    async def submit_and_wait(self, handler: Callable[..., Awaitable[Any]], *args,
                             priority: RequestPriority = RequestPriority.NORMAL,
                             timeout: float = 30.0, max_retries: int = 2, **kwargs) -> Any:
        """
        Submit request and wait for result (convenience method)
        
        Args:
            handler: Async function to execute
            *args: Positional arguments
            priority: Request priority
            timeout: Request timeout
            max_retries: Maximum retries
            **kwargs: Keyword arguments
            
        Returns:
            Request result
        """
        request_id = await self.submit(
            handler, *args, 
            priority=priority, 
            timeout=timeout, 
            max_retries=max_retries, 
            **kwargs
        )
        
        return await self.get_result(request_id, timeout)
    
    async def _worker(self, worker_name: str):
        """Worker coroutine to process requests"""
        logger.debug(f"🔧 Worker {worker_name} started")
        
        while self.running:
            try:
                # Get request from queue with timeout
                try:
                    request = await asyncio.wait_for(
                        self.request_queue.get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue  # Check if still running
                
                # Update queue size
                self.stats.current_queue_size = self.request_queue.qsize()
                
                # Calculate wait time
                wait_time = (time.time() - request.created_at) * 1000
                self.wait_times.append(wait_time)
                
                # Keep only recent wait times
                if len(self.wait_times) > 1000:
                    self.wait_times = self.wait_times[-500:]
                
                # Process request
                await self._process_request(request, worker_name)
                
            except Exception as e:
                logger.error(f"❌ Worker {worker_name} error: {e}")
                await asyncio.sleep(0.1)  # Brief pause on error
        
        logger.debug(f"🔧 Worker {worker_name} stopped")
    
    async def _process_request(self, request: QueuedRequest, worker_name: str):
        """Process a single request with error handling and retries"""
        start_time = time.time()
        
        try:
            # Acquire semaphore for concurrency control
            async with self.semaphore:
                # Create task for the request
                task = asyncio.create_task(
                    self._execute_request(request)
                )
                
                # Track active request
                self.active_requests[request.request_id] = task
                
                logger.debug(f"🔄 Processing request {request.request_id} on {worker_name}")
                
                # Wait for completion or timeout
                try:
                    result = await asyncio.wait_for(task, timeout=request.timeout)
                    
                    # Record success
                    processing_time = (time.time() - start_time) * 1000
                    self.processing_times.append(processing_time)
                    
                    # Keep only recent processing times
                    if len(self.processing_times) > 1000:
                        self.processing_times = self.processing_times[-500:]
                    
                    self.stats.completed_requests += 1
                    self._record_success()
                    
                    logger.debug(f"✅ Request {request.request_id} completed in {processing_time:.1f}ms")
                    
                except asyncio.TimeoutError:
                    # Handle timeout
                    task.cancel()
                    self.stats.timeout_requests += 1
                    
                    # Retry if possible
                    if request.retries < request.max_retries:
                        request.retries += 1
                        self.stats.retry_requests += 1
                        await self.request_queue.put(request)
                        logger.warning(f"⚠️ Request {request.request_id} timeout, retrying ({request.retries}/{request.max_retries})")
                    else:
                        self.stats.failed_requests += 1
                        self._record_failure()
                        logger.error(f"❌ Request {request.request_id} failed after {request.max_retries} retries")
                
                except Exception as e:
                    # Handle execution error
                    self.stats.failed_requests += 1
                    self._record_failure()
                    logger.error(f"❌ Request {request.request_id} failed: {e}")
                
                finally:
                    # Clean up
                    if request.request_id in self.active_requests:
                        del self.active_requests[request.request_id]
        
        except Exception as e:
            logger.error(f"❌ Request processing error: {e}")
            self.stats.failed_requests += 1
            self._record_failure()
    
    async def _execute_request(self, request: QueuedRequest) -> Any:
        """Execute the actual request handler"""
        try:
            return await request.handler(*request.args, **request.kwargs)
        except Exception as e:
            logger.error(f"❌ Request handler error: {e}")
            raise
    
    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.circuit_breaker_failures < self.circuit_breaker_threshold:
            return False
        
        # Check if reset time has passed
        if time.time() - self.circuit_breaker_last_failure > self.circuit_breaker_reset_time:
            self.circuit_breaker_failures = 0
            return False
        
        return True
    
    def _record_failure(self):
        """Record a failure for circuit breaker"""
        self.circuit_breaker_failures += 1
        self.circuit_breaker_last_failure = time.time()
    
    def _record_success(self):
        """Record a success for circuit breaker"""
        if self.circuit_breaker_failures > 0:
            self.circuit_breaker_failures = max(0, self.circuit_breaker_failures - 1)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get queue performance statistics"""
        # Calculate averages
        if self.processing_times:
            self.stats.avg_processing_time_ms = sum(self.processing_times) / len(self.processing_times)
        
        if self.wait_times:
            self.stats.avg_wait_time_ms = sum(self.wait_times) / len(self.wait_times)
        
        return {
            "total_requests": self.stats.total_requests,
            "completed_requests": self.stats.completed_requests,
            "failed_requests": self.stats.failed_requests,
            "timeout_requests": self.stats.timeout_requests,
            "retry_requests": self.stats.retry_requests,
            "success_rate": self.stats.success_rate,
            "failure_rate": self.stats.failure_rate,
            "current_queue_size": self.stats.current_queue_size,
            "max_queue_size": self.stats.max_queue_size,
            "active_requests": len(self.active_requests),
            "avg_processing_time_ms": self.stats.avg_processing_time_ms,
            "avg_wait_time_ms": self.stats.avg_wait_time_ms,
            "circuit_breaker_failures": self.circuit_breaker_failures,
            "circuit_breaker_open": self._is_circuit_breaker_open(),
            "worker_count": len(self.workers),
            "running": self.running
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform queue health check"""
        stats = await self.get_stats()
        
        # Determine health status
        if not self.running:
            status = "stopped"
        elif self._is_circuit_breaker_open():
            status = "overloaded"
        elif stats["current_queue_size"] > self.max_queue_size * 0.8:
            status = "high_load"
        elif stats["failure_rate"] > 0.1:  # 10% failure rate
            status = "degraded"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "queue_utilization": stats["current_queue_size"] / self.max_queue_size,
            "worker_utilization": len(self.active_requests) / self.max_concurrent,
            **stats
        }


# Global request queue instance
request_queue = RequestQueue()