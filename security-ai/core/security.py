"""
Security utilities for SecurityGuard AI
"""

import time
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

try:
    from ..models.schemas import UserProfile
    from ..services.auth_service import auth_service, UserService
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from models.schemas import UserProfile
    from services.auth_service import auth_service, UserService


security = HTTPBearer(auto_error=False)
user_service = UserService(None)  # Will be initialized with proper db session in production


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UserProfile]:
    """
    Get current user from JWT token (optional authentication)
    Returns None for anonymous users
    """
    if not credentials:
        # Allow anonymous access
        return None
    
    try:
        # Verify JWT token
        token_payload = auth_service.verify_jwt_token(credentials.credentials)
        
        if not token_payload:
            logger.warning("❌ Invalid JWT token provided")
            return None
        
        # Get user profile from token
        wallet_address = token_payload.get("wallet_address")
        username = token_payload.get("username")
        
        if not wallet_address:
            logger.warning("❌ JWT token missing wallet address")
            return None
        
        # Get or create user profile
        user_profile = await user_service.get_or_create_user(wallet_address, username)
        
        logger.debug(f"✅ User authenticated: {wallet_address[:8]}...")
        return user_profile
        
    except Exception as e:
        logger.warning(f"❌ Authentication error: {e}")
        # Don't fail on auth errors, just return None for anonymous access
        return None


async def require_authentication(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserProfile:
    """
    Require valid authentication (raises exception if not authenticated)
    """
    user = await get_current_user(credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def verify_api_key(api_key: str) -> bool:
    """Verify API key for service access"""
    # In production, validate against database
    return len(api_key) > 10


def rate_limit_check(user_id: str, endpoint: str) -> bool:
    """Check rate limits for user/endpoint"""
    # In production, implement Redis-based rate limiting
    return True


def validate_solana_address(address: str) -> bool:
    """Validate Solana address format"""
    if not address or len(address) != 44:
        return False
    
    # Basic base58 character check
    valid_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    return all(c in valid_chars for c in address)


def sanitize_input(data: str) -> str:
    """Enhanced sanitize user input to prevent injection attacks"""
    if not data:
        return ""
    
    # Remove null bytes and control characters (except allowed whitespace)
    sanitized = ''.join(char for char in data if ord(char) >= 32 or char in '\t\n\r')
    
    # HTML encode dangerous characters
    sanitized = (sanitized
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;')
                .replace('/', '&#x2F;'))
    
    # Remove potentially dangerous patterns
    import re
    dangerous_patterns = [
        r'javascript:',
        r'vbscript:',
        r'data:',
        r'on\w+\s*=',  # Event handlers
        r'eval\s*\(',
        r'exec\s*\(',
        r'system\s*\(',
        r'__import__',
        r'subprocess',
        r'\.\./',
        r'\\.\\.\\',
    ]
    
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    return sanitized.strip()[:1000]  # Limit length


class SecurityMiddleware:
    """Security middleware for request validation"""
    
    def __init__(self):
        self.request_counts = {}
        self.last_reset = time.time()
    
    async def __call__(self, request, call_next):
        """Process request with security checks"""
        
        # Basic rate limiting (in-memory for demo)
        client_ip = request.client.host
        current_time = time.time()
        
        # Reset counters every minute
        if current_time - self.last_reset > 60:
            self.request_counts.clear()
            self.last_reset = current_time
        
        # Check rate limit
        if client_ip in self.request_counts:
            self.request_counts[client_ip] += 1
        else:
            self.request_counts[client_ip] = 1
        
        if self.request_counts[client_ip] > 100:  # 100 requests per minute
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        response = await call_next(request)
        return response