"""
Comprehensive Security and Privacy Compliance Middleware
Implements HTTPS/TLS, rate limiting, input validation, and audit logging
"""

import time
import json
import hashlib
import asyncio
from typing import Dict, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
import redis.asyncio as redis

from .config import get_settings


class SecurityHeaders:
    """Security headers for HTTPS/TLS and privacy protection"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get comprehensive security headers"""
        settings = get_settings()
        
        headers = {
            # HTTPS/TLS Security
            "Strict-Transport-Security": f"max-age={settings.hsts_max_age}; includeSubDomains; preload",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https:; "
                "font-src 'self'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
            
            # Privacy Headers
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "speaker=()"
            ),
            
            # Cache Control for sensitive data
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
            "Pragma": "no-cache",
            "Expires": "0",
            
            # Custom Security Headers
            "X-Privacy-Policy": settings.privacy_policy_url,
            "X-Data-Retention": "session-only",
            "X-Security-Contact": "security@agentmarket.app"
        }
        
        return headers


class RateLimiter:
    """Advanced rate limiting with Redis backend and multiple time windows"""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client: Optional[redis.Redis] = None
        self.local_cache: Dict[str, deque] = defaultdict(deque)
        self.cache_cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
        
    async def initialize(self):
        """Initialize Redis connection for distributed rate limiting"""
        try:
            self.redis_client = redis.from_url(
                self.settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1
            )
            await self.redis_client.ping()
            logger.info("✅ Rate limiter Redis connection established")
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable for rate limiting, using local cache: {e}")
            self.redis_client = None
    
    async def check_rate_limit(self, identifier: str, endpoint: str = "default") -> tuple[bool, Dict[str, int]]:
        """
        Check rate limits for identifier across multiple time windows
        Returns (is_allowed, rate_info)
        """
        current_time = time.time()
        
        # Define time windows (seconds)
        windows = {
            "minute": 60,
            "hour": 3600,
            "day": 86400
        }
        
        # Define limits per window
        limits = {
            "minute": self.settings.max_requests_per_minute,
            "hour": self.settings.max_requests_per_hour,
            "day": self.settings.max_requests_per_day
        }
        
        # Adjust limits for specific endpoints
        if endpoint == "scan":
            limits["minute"] = min(limits["minute"], 30)  # More restrictive for expensive operations
        elif endpoint == "chat":
            limits["minute"] = min(limits["minute"], 20)
        
        rate_info = {}
        
        try:
            if self.redis_client:
                # Use Redis for distributed rate limiting
                for window_name, window_seconds in windows.items():
                    key = f"rate_limit:{identifier}:{endpoint}:{window_name}"
                    
                    # Use Redis sliding window counter
                    pipe = self.redis_client.pipeline()
                    pipe.zremrangebyscore(key, 0, current_time - window_seconds)
                    pipe.zcard(key)
                    pipe.zadd(key, {str(current_time): current_time})
                    pipe.expire(key, window_seconds)
                    
                    results = await pipe.execute()
                    current_count = results[1]
                    
                    rate_info[f"{window_name}_count"] = current_count
                    rate_info[f"{window_name}_limit"] = limits[window_name]
                    rate_info[f"{window_name}_remaining"] = max(0, limits[window_name] - current_count)
                    
                    if current_count > limits[window_name]:
                        rate_info["blocked_by"] = window_name
                        return False, rate_info
            else:
                # Fallback to local cache
                await self._cleanup_local_cache()
                
                for window_name, window_seconds in windows.items():
                    cache_key = f"{identifier}:{endpoint}:{window_name}"
                    
                    # Clean old entries
                    cutoff_time = current_time - window_seconds
                    while (self.local_cache[cache_key] and 
                           self.local_cache[cache_key][0] < cutoff_time):
                        self.local_cache[cache_key].popleft()
                    
                    # Add current request
                    self.local_cache[cache_key].append(current_time)
                    current_count = len(self.local_cache[cache_key])
                    
                    rate_info[f"{window_name}_count"] = current_count
                    rate_info[f"{window_name}_limit"] = limits[window_name]
                    rate_info[f"{window_name}_remaining"] = max(0, limits[window_name] - current_count)
                    
                    if current_count > limits[window_name]:
                        rate_info["blocked_by"] = window_name
                        return False, rate_info
            
            return True, rate_info
            
        except Exception as e:
            logger.error(f"❌ Rate limiting error: {e}")
            # Fail open for availability
            return True, {"error": "rate_limit_check_failed"}
    
    async def _cleanup_local_cache(self):
        """Clean up old entries from local cache"""
        current_time = time.time()
        if current_time - self.last_cleanup > self.cache_cleanup_interval:
            for cache_key in list(self.local_cache.keys()):
                # Remove entries older than 1 day
                cutoff_time = current_time - 86400
                while (self.local_cache[cache_key] and 
                       self.local_cache[cache_key][0] < cutoff_time):
                    self.local_cache[cache_key].popleft()
                
                # Remove empty deques
                if not self.local_cache[cache_key]:
                    del self.local_cache[cache_key]
            
            self.last_cleanup = current_time


class InputValidator:
    """Comprehensive input validation and sanitization"""
    
    def __init__(self):
        self.settings = get_settings()
        self.max_request_size = self.settings.max_request_size_mb * 1024 * 1024
        self.max_transaction_size = self.settings.max_transaction_size_kb * 1024
        
        # Dangerous patterns to detect
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'onclick\s*=',
            r'eval\s*\(',
            r'exec\s*\(',
            r'system\s*\(',
            r'__import__',
            r'subprocess',
            r'os\.system',
            r'\.\./',
            r'\\.\\.\\',
        ]
    
    def validate_request_size(self, request: Request) -> bool:
        """Validate request size limits"""
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            return False
        return True
    
    def sanitize_string(self, value: str, max_length: int = 1000) -> str:
        """Sanitize string input to prevent injection attacks"""
        if not isinstance(value, str):
            return str(value)[:max_length]
        
        # Remove null bytes and control characters
        sanitized = ''.join(char for char in value if ord(char) >= 32 or char in '\t\n\r')
        
        # Limit length
        sanitized = sanitized[:max_length]
        
        # HTML encode dangerous characters
        sanitized = (sanitized
                    .replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                    .replace('"', '&quot;')
                    .replace("'", '&#x27;')
                    .replace('/', '&#x2F;'))
        
        return sanitized.strip()
    
    def validate_solana_address(self, address: str) -> bool:
        """Validate Solana address format"""
        if not address or not isinstance(address, str):
            return False
        
        if len(address) != 44:
            return False
        
        # Check base58 characters
        valid_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        return all(c in valid_chars for c in address)
    
    def validate_transaction_data(self, transaction_data: str) -> bool:
        """Validate transaction data format and size"""
        if not transaction_data or not isinstance(transaction_data, str):
            return False
        
        # Check size limit
        if len(transaction_data.encode('utf-8')) > self.max_transaction_size:
            return False
        
        # Check if it's valid base64 (for serialized transactions)
        try:
            import base64
            base64.b64decode(transaction_data, validate=True)
            return True
        except Exception:
            # Could be JSON transaction object
            try:
                json.loads(transaction_data)
                return True
            except Exception:
                return False
    
    async def validate_request_body(self, body: bytes) -> tuple[bool, Optional[str]]:
        """Validate request body for security threats"""
        if not body:
            return True, None
        
        try:
            # Check size
            if len(body) > self.max_request_size:
                return False, "Request body too large"
            
            # Decode and check for dangerous patterns
            body_str = body.decode('utf-8', errors='ignore')
            
            import re
            for pattern in self.dangerous_patterns:
                if re.search(pattern, body_str, re.IGNORECASE):
                    return False, f"Potentially dangerous content detected"
            
            return True, None
            
        except Exception as e:
            logger.warning(f"Request validation error: {e}")
            return False, "Request validation failed"


class AuditLogger:
    """Security audit logging for compliance"""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client: Optional[redis.Redis] = None
        
    async def initialize(self):
        """Initialize audit logger"""
        try:
            self.redis_client = redis.from_url(
                self.settings.redis_url,
                decode_responses=True
            )
            logger.info("✅ Audit logger initialized")
        except Exception as e:
            logger.warning(f"⚠️ Audit logger Redis unavailable: {e}")
    
    async def log_security_event(self, event_type: str, details: Dict, 
                                request: Request, user_id: Optional[str] = None):
        """Log security-related events for audit trail"""
        try:
            audit_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "user_id": user_id,
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent", ""),
                "endpoint": str(request.url.path),
                "method": request.method,
                "details": details,
                "session_id": self._generate_session_id(request)
            }
            
            # Log to file
            logger.bind(audit=True).info(f"AUDIT: {json.dumps(audit_entry)}")
            
            # Store in Redis for real-time monitoring (if available)
            if self.redis_client:
                await self.redis_client.lpush(
                    "security_audit_log",
                    json.dumps(audit_entry)
                )
                # Keep only last 10000 entries
                await self.redis_client.ltrim("security_audit_log", 0, 9999)
            
        except Exception as e:
            logger.error(f"❌ Audit logging failed: {e}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get real client IP considering proxies"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _generate_session_id(self, request: Request) -> str:
        """Generate session ID for tracking"""
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        session_data = f"{client_ip}:{user_agent}:{time.time()}"
        return hashlib.md5(session_data.encode()).hexdigest()[:16]


class SecurityComplianceMiddleware(BaseHTTPMiddleware):
    """Main security and privacy compliance middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        self.rate_limiter = RateLimiter()
        self.input_validator = InputValidator()
        self.audit_logger = AuditLogger()
        self.security_headers = SecurityHeaders()
        
        # Track initialization
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure all components are initialized"""
        if not self._initialized:
            await self.rate_limiter.initialize()
            await self.audit_logger.initialize()
            self._initialized = True
    
    async def dispatch(self, request: Request, call_next):
        """Main middleware dispatch with comprehensive security checks"""
        await self._ensure_initialized()
        
        start_time = time.time()
        client_ip = self.audit_logger._get_client_ip(request)
        
        try:
            # 1. Request size validation
            if not self.input_validator.validate_request_size(request):
                await self.audit_logger.log_security_event(
                    "request_size_exceeded",
                    {"max_size_mb": self.settings.max_request_size_mb},
                    request
                )
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request too large"},
                    headers=self.security_headers.get_security_headers()
                )
            
            # 2. Rate limiting (if enabled)
            if self.settings.enable_rate_limiting:
                endpoint_type = self._get_endpoint_type(request.url.path)
                is_allowed, rate_info = await self.rate_limiter.check_rate_limit(
                    client_ip, endpoint_type
                )
                
                if not is_allowed:
                    await self.audit_logger.log_security_event(
                        "rate_limit_exceeded",
                        {
                            "endpoint": endpoint_type,
                            "rate_info": rate_info
                        },
                        request
                    )
                    
                    headers = self.security_headers.get_security_headers()
                    headers.update({
                        "X-RateLimit-Limit": str(rate_info.get(f"{rate_info.get('blocked_by', 'minute')}_limit", 0)),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time() + 60)),
                        "Retry-After": "60"
                    })
                    
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "Rate limit exceeded",
                            "message": f"Too many requests in {rate_info.get('blocked_by', 'time window')}",
                            "rate_info": rate_info
                        },
                        headers=headers
                    )
            
            # 3. Input validation for request body
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                is_valid, error_msg = await self.input_validator.validate_request_body(body)
                
                if not is_valid:
                    await self.audit_logger.log_security_event(
                        "malicious_input_detected",
                        {"error": error_msg, "body_size": len(body)},
                        request
                    )
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid request content"},
                        headers=self.security_headers.get_security_headers()
                    )
                
                # Recreate request with validated body
                request._body = body
            
            # 4. Process request
            response = await call_next(request)
            
            # 5. Add security headers to response
            if self.settings.enable_security_headers:
                for header, value in self.security_headers.get_security_headers().items():
                    response.headers[header] = value
            
            # 6. Log successful request (for sensitive endpoints)
            if self._is_sensitive_endpoint(request.url.path):
                await self.audit_logger.log_security_event(
                    "sensitive_endpoint_access",
                    {
                        "endpoint": request.url.path,
                        "status_code": response.status_code,
                        "response_time_ms": int((time.time() - start_time) * 1000)
                    },
                    request
                )
            
            return response
            
        except Exception as e:
            # Log security-related errors
            await self.audit_logger.log_security_event(
                "middleware_error",
                {"error": str(e), "type": type(e).__name__},
                request
            )
            
            # Return secure error response
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"},
                headers=self.security_headers.get_security_headers()
            )
    
    def _get_endpoint_type(self, path: str) -> str:
        """Determine endpoint type for rate limiting"""
        if "/scan" in path:
            return "scan"
        elif "/chat" in path:
            return "chat"
        elif "/auth" in path:
            return "auth"
        elif "/payment" in path:
            return "payment"
        else:
            return "default"
    
    def _is_sensitive_endpoint(self, path: str) -> bool:
        """Check if endpoint handles sensitive data"""
        sensitive_patterns = [
            "/api/security/scan",
            "/api/security/chat",
            "/api/auth/",
            "/api/payment/",
            "/api/analytics/user",
            "/api/analytics/export"
        ]
        return any(pattern in path for pattern in sensitive_patterns)


# Export middleware for use in main application
__all__ = [
    "SecurityComplianceMiddleware",
    "SecurityHeaders", 
    "RateLimiter",
    "InputValidator",
    "AuditLogger"
]