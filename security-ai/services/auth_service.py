"""
Authentication service for SecurityGuard AI
JWT-based authentication with Solana wallet signature verification
"""

import jwt
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
import base58
from loguru import logger

try:
    from ..core.config import get_settings
    from ..models.schemas import UserProfile
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from core.config import get_settings
    from models.schemas import UserProfile


class AuthenticationService:
    """
    Handles JWT token generation and Solana wallet signature verification
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.secret_key = self.settings.secret_key
        self.algorithm = "HS256"
        self.token_expiry_hours = 24
        
    def verify_solana_signature(
        self, 
        wallet_address: str, 
        message: str, 
        signature: str
    ) -> bool:
        """
        Verify Solana wallet signature for authentication
        
        Args:
            wallet_address: Base58 encoded Solana public key
            message: Original message that was signed
            signature: Base58 encoded signature
            
        Returns:
            bool: True if signature is valid
        """
        try:
            # Decode the public key and signature from base58
            public_key_bytes = base58.b58decode(wallet_address)
            signature_bytes = base58.b58decode(signature)
            
            # Create verify key from public key
            verify_key = VerifyKey(public_key_bytes)
            
            # Verify the signature
            verify_key.verify(message.encode('utf-8'), signature_bytes)
            
            logger.info(f"✅ Signature verified for wallet: {wallet_address[:8]}...")
            return True
            
        except (BadSignatureError, ValueError, Exception) as e:
            logger.warning(f"❌ Signature verification failed for {wallet_address[:8]}...: {e}")
            return False
    
    def generate_auth_message(self, wallet_address: str, timestamp: int) -> str:
        """
        Generate authentication message for wallet signing
        
        Args:
            wallet_address: User's wallet address
            timestamp: Current timestamp
            
        Returns:
            str: Message to be signed by wallet
        """
        return f"SecurityGuard AI Authentication\nWallet: {wallet_address}\nTimestamp: {timestamp}\nNonce: {hashlib.md5(f'{wallet_address}{timestamp}'.encode()).hexdigest()[:8]}"
    
    def create_jwt_token(self, wallet_address: str, user_data: Dict[str, Any]) -> str:
        """
        Create JWT token for authenticated user
        
        Args:
            wallet_address: User's wallet address
            user_data: Additional user data to include in token
            
        Returns:
            str: JWT token
        """
        now = datetime.utcnow()
        payload = {
            "wallet_address": wallet_address,
            "username": user_data.get("username"),
            "iat": now,
            "exp": now + timedelta(hours=self.token_expiry_hours),
            "iss": "SecurityGuard AI",
            "sub": wallet_address
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info(f"🔑 JWT token created for wallet: {wallet_address[:8]}...")
        return token
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Optional[Dict]: Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": True}
            )
            
            logger.debug(f"✅ JWT token verified for wallet: {payload.get('wallet_address', 'unknown')[:8]}...")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("❌ JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"❌ Invalid JWT token: {e}")
            return None
    
    def validate_auth_request(
        self, 
        wallet_address: str, 
        message: str, 
        signature: str, 
        timestamp: int
    ) -> bool:
        """
        Validate complete authentication request
        
        Args:
            wallet_address: User's wallet address
            message: Signed message
            signature: Wallet signature
            timestamp: Message timestamp
            
        Returns:
            bool: True if authentication is valid
        """
        # Check timestamp (must be within 5 minutes)
        current_time = int(time.time())
        if abs(current_time - timestamp) > 300:  # 5 minutes
            logger.warning(f"❌ Authentication timestamp too old: {current_time - timestamp}s")
            return False
        
        # Validate wallet address format
        if not self._is_valid_solana_address(wallet_address):
            logger.warning(f"❌ Invalid wallet address format: {wallet_address}")
            return False
        
        # Generate expected message
        expected_message = self.generate_auth_message(wallet_address, timestamp)
        if message != expected_message:
            logger.warning("❌ Authentication message mismatch")
            return False
        
        # Verify signature
        return self.verify_solana_signature(wallet_address, message, signature)
    
    def _is_valid_solana_address(self, address: str) -> bool:
        """
        Validate Solana address format
        
        Args:
            address: Solana address string
            
        Returns:
            bool: True if valid format
        """
        if not address or len(address) < 32 or len(address) > 44:
            return False
        
        try:
            decoded = base58.b58decode(address)
            return len(decoded) == 32
        except Exception:
            return False


class UserService:
    """
    User profile management service
    """
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        
    async def get_or_create_user(self, wallet_address: str, username: Optional[str] = None) -> UserProfile:
        """
        Get existing user or create new user profile
        
        Args:
            wallet_address: User's wallet address
            username: Optional username
            
        Returns:
            UserProfile: User profile object
        """
        try:
            # For demo purposes, create in-memory user profile
            # In production, this would query/create in database using UserProfileDB
            
            user_profile = UserProfile(
                wallet_address=wallet_address,
                username=username or f"user_{wallet_address[:8]}",
                total_scans=0,
                threats_detected=0,
                created_at=datetime.utcnow(),
                last_active=datetime.utcnow()
            )
            
            logger.info(f"👤 User profile created/retrieved for: {wallet_address[:8]}...")
            return user_profile
            
        except Exception as e:
            logger.error(f"❌ Failed to get/create user profile: {e}")
            raise
    
    async def update_user_stats(self, wallet_address: str, scan_completed: bool, threat_detected: bool):
        """
        Update user statistics after scan
        
        Args:
            wallet_address: User's wallet address
            scan_completed: Whether scan was completed successfully
            threat_detected: Whether threat was detected in scan
        """
        try:
            # In production, update UserProfileDB in database
            logger.info(f"📊 Updated stats for {wallet_address[:8]}... - Scan: {scan_completed}, Threat: {threat_detected}")
            
        except Exception as e:
            logger.error(f"❌ Failed to update user stats: {e}")
    
    async def log_service_access(
        self, 
        wallet_address: str, 
        service_type: str, 
        payment_id: Optional[str] = None,
        scan_id: Optional[str] = None,
        risk_level: Optional[str] = None,
        processing_time_ms: Optional[int] = None
    ):
        """
        Log service access for tracking and billing
        
        Args:
            wallet_address: User's wallet address
            service_type: Type of service accessed
            payment_id: Associated payment ID
            scan_id: Scan ID if applicable
            risk_level: Risk level if applicable
            processing_time_ms: Processing time in milliseconds
        """
        try:
            # In production, create ServiceAccessLog record in database
            logger.info(f"📝 Service access logged: {wallet_address[:8]}... - {service_type}")
            
        except Exception as e:
            logger.error(f"❌ Failed to log service access: {e}")


# Global authentication service instance
auth_service = AuthenticationService()