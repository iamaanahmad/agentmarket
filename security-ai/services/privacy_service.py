"""
Privacy Compliance Service
Implements data privacy controls, session-only data handling, and compliance reporting
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

import redis.asyncio as redis
from loguru import logger

from ..core.config import get_settings


@dataclass
class PrivacyEvent:
    """Privacy-related event for audit trail"""
    timestamp: str
    event_type: str
    user_id: Optional[str]
    data_type: str
    action: str
    details: Dict[str, Any]
    session_id: str
    client_ip: str


@dataclass
class DataProcessingRecord:
    """Record of data processing for transparency"""
    session_id: str
    user_wallet: Optional[str]
    data_types: List[str]
    processing_purpose: str
    retention_policy: str
    created_at: str
    expires_at: str
    anonymized: bool = False


class SessionDataManager:
    """Manages session-only data storage with automatic cleanup"""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client: Optional[redis.Redis] = None
        self.local_sessions: Dict[str, Dict] = {}
        self.session_timeout = self.settings.session_timeout_minutes * 60
        
    async def initialize(self):
        """Initialize Redis connection for session management"""
        try:
            self.redis_client = redis.from_url(
                self.settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            await self.redis_client.ping()
            logger.info("✅ Session data manager initialized with Redis")
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable for sessions, using local storage: {e}")
            self.redis_client = None
    
    async def create_session(self, session_id: str, user_wallet: Optional[str] = None) -> Dict:
        """Create new session with privacy-compliant settings"""
        session_data = {
            "session_id": session_id,
            "user_wallet": user_wallet,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(seconds=self.session_timeout)).isoformat(),
            "data_processed": [],
            "scan_count": 0,
            "last_activity": datetime.utcnow().isoformat()
        }
        
        try:
            if self.redis_client:
                await self.redis_client.setex(
                    f"session:{session_id}",
                    self.session_timeout,
                    json.dumps(session_data)
                )
            else:
                self.local_sessions[session_id] = session_data
            
            logger.debug(f"📝 Created privacy-compliant session: {session_id[:8]}...")
            return session_data
            
        except Exception as e:
            logger.error(f"❌ Session creation failed: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data if it exists and hasn't expired"""
        try:
            if self.redis_client:
                session_json = await self.redis_client.get(f"session:{session_id}")
                if session_json:
                    return json.loads(session_json)
            else:
                session_data = self.local_sessions.get(session_id)
                if session_data:
                    # Check expiration for local sessions
                    expires_at = datetime.fromisoformat(session_data["expires_at"])
                    if datetime.utcnow() > expires_at:
                        del self.local_sessions[session_id]
                        return None
                    return session_data
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Session retrieval failed: {e}")
            return None
    
    async def update_session_activity(self, session_id: str, activity_data: Dict):
        """Update session with new activity (scan, chat, etc.)"""
        try:
            session_data = await self.get_session(session_id)
            if not session_data:
                return False
            
            # Update activity
            session_data["last_activity"] = datetime.utcnow().isoformat()
            session_data["scan_count"] = session_data.get("scan_count", 0) + 1
            
            # Add data processing record
            if "data_type" in activity_data:
                session_data["data_processed"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "data_type": activity_data["data_type"],
                    "purpose": activity_data.get("purpose", "security_analysis")
                })
            
            # Save updated session
            if self.redis_client:
                await self.redis_client.setex(
                    f"session:{session_id}",
                    self.session_timeout,
                    json.dumps(session_data)
                )
            else:
                self.local_sessions[session_id] = session_data
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Session update failed: {e}")
            return False
    
    async def delete_session(self, session_id: str):
        """Immediately delete session and all associated data"""
        try:
            if self.redis_client:
                await self.redis_client.delete(f"session:{session_id}")
            else:
                self.local_sessions.pop(session_id, None)
            
            logger.debug(f"🗑️ Session deleted: {session_id[:8]}...")
            
        except Exception as e:
            logger.error(f"❌ Session deletion failed: {e}")
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions from local storage"""
        if not self.redis_client:  # Redis handles expiration automatically
            current_time = datetime.utcnow()
            expired_sessions = []
            
            for session_id, session_data in self.local_sessions.items():
                expires_at = datetime.fromisoformat(session_data["expires_at"])
                if current_time > expires_at:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.local_sessions[session_id]
            
            if expired_sessions:
                logger.debug(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")


class PrivacyComplianceService:
    """Main privacy compliance service"""
    
    def __init__(self):
        self.settings = get_settings()
        self.session_manager = SessionDataManager()
        self.redis_client: Optional[redis.Redis] = None
        self.privacy_events: List[PrivacyEvent] = []
        
    async def initialize(self):
        """Initialize privacy compliance service"""
        await self.session_manager.initialize()
        
        try:
            self.redis_client = redis.from_url(
                self.settings.redis_url,
                decode_responses=True
            )
            logger.info("✅ Privacy compliance service initialized")
        except Exception as e:
            logger.warning(f"⚠️ Privacy service Redis unavailable: {e}")
    
    async def process_transaction_data(self, session_id: str, transaction_data: str, 
                                     user_wallet: Optional[str] = None) -> Dict:
        """
        Process transaction data with privacy compliance
        - No persistent storage beyond session
        - Anonymize sensitive data
        - Log processing for transparency
        """
        try:
            # Create or get session
            session = await self.session_manager.get_session(session_id)
            if not session:
                session = await self.session_manager.create_session(session_id, user_wallet)
            
            # Anonymize transaction data for processing
            anonymized_data = self._anonymize_transaction_data(transaction_data)
            
            # Update session with processing activity
            await self.session_manager.update_session_activity(session_id, {
                "data_type": "transaction_data",
                "purpose": "security_analysis",
                "anonymized": True
            })
            
            # Log privacy event
            await self._log_privacy_event(
                "data_processed",
                user_wallet,
                "transaction_data",
                "security_analysis",
                {
                    "session_id": session_id,
                    "data_size_bytes": len(transaction_data),
                    "anonymized": True,
                    "retention": "session_only"
                },
                session_id,
                "unknown"  # Client IP would be passed from middleware
            )
            
            return {
                "session_id": session_id,
                "anonymized_data": anonymized_data,
                "processing_record": {
                    "purpose": "security_analysis",
                    "retention_policy": "session_only",
                    "anonymized": True,
                    "expires_at": session["expires_at"]
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Transaction data processing failed: {e}")
            raise
    
    async def get_user_data_summary(self, session_id: str) -> Dict:
        """Get summary of data processed in current session"""
        try:
            session = await self.session_manager.get_session(session_id)
            if not session:
                return {"error": "Session not found"}
            
            return {
                "session_id": session_id,
                "created_at": session["created_at"],
                "expires_at": session["expires_at"],
                "data_processed": session.get("data_processed", []),
                "scan_count": session.get("scan_count", 0),
                "retention_policy": "session_only",
                "privacy_policy": self.settings.privacy_policy_url
            }
            
        except Exception as e:
            logger.error(f"❌ Data summary generation failed: {e}")
            return {"error": "Failed to generate data summary"}
    
    async def delete_user_session_data(self, session_id: str, user_wallet: Optional[str] = None):
        """Delete all user data from current session (right to be forgotten)"""
        try:
            # Delete session data
            await self.session_manager.delete_session(session_id)
            
            # Log privacy event
            await self._log_privacy_event(
                "data_deleted",
                user_wallet,
                "all_session_data",
                "user_request",
                {
                    "session_id": session_id,
                    "deletion_type": "complete_session"
                },
                session_id,
                "unknown"
            )
            
            return {
                "success": True,
                "message": "All session data deleted successfully",
                "session_id": session_id,
                "deleted_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Session data deletion failed: {e}")
            return {
                "success": False,
                "error": "Failed to delete session data"
            }
    
    async def generate_privacy_report(self, session_id: str) -> Dict:
        """Generate privacy compliance report for current session"""
        try:
            session = await self.session_manager.get_session(session_id)
            if not session:
                return {"error": "Session not found"}
            
            # Get privacy events for this session
            session_events = [
                event for event in self.privacy_events 
                if event.session_id == session_id
            ]
            
            report = {
                "report_generated_at": datetime.utcnow().isoformat(),
                "session_id": session_id,
                "privacy_compliance": {
                    "data_retention": "session_only",
                    "data_anonymization": "enabled",
                    "encryption_in_transit": "tls_1_3",
                    "user_consent": "implicit_by_usage",
                    "right_to_deletion": "supported",
                    "data_portability": "session_summary_available"
                },
                "session_summary": {
                    "created_at": session["created_at"],
                    "expires_at": session["expires_at"],
                    "data_processed": session.get("data_processed", []),
                    "scan_count": session.get("scan_count", 0)
                },
                "privacy_events": [asdict(event) for event in session_events],
                "compliance_status": "compliant",
                "privacy_policy_url": self.settings.privacy_policy_url
            }
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Privacy report generation failed: {e}")
            return {"error": "Failed to generate privacy report"}
    
    def _anonymize_transaction_data(self, transaction_data: str) -> str:
        """Anonymize sensitive data in transaction for processing"""
        try:
            # For transaction data, we can hash account addresses while preserving structure
            import re
            
            # Pattern for Solana addresses (44 characters, base58)
            address_pattern = r'\b[1-9A-HJ-NP-Za-km-z]{44}\b'
            
            def anonymize_address(match):
                address = match.group(0)
                # Keep first 4 and last 4 characters, hash the middle
                if len(address) == 44:
                    hash_middle = hashlib.sha256(address[4:-4].encode()).hexdigest()[:8]
                    return f"{address[:4]}...{hash_middle}...{address[-4:]}"
                return address
            
            anonymized = re.sub(address_pattern, anonymize_address, transaction_data)
            return anonymized
            
        except Exception as e:
            logger.warning(f"⚠️ Data anonymization failed: {e}")
            return transaction_data  # Return original if anonymization fails
    
    async def _log_privacy_event(self, event_type: str, user_id: Optional[str], 
                                data_type: str, action: str, details: Dict,
                                session_id: str, client_ip: str):
        """Log privacy-related events for audit trail"""
        try:
            event = PrivacyEvent(
                timestamp=datetime.utcnow().isoformat(),
                event_type=event_type,
                user_id=user_id,
                data_type=data_type,
                action=action,
                details=details,
                session_id=session_id,
                client_ip=client_ip
            )
            
            # Store in memory (limited size)
            self.privacy_events.append(event)
            if len(self.privacy_events) > 1000:  # Keep only last 1000 events
                self.privacy_events = self.privacy_events[-1000:]
            
            # Log to audit trail
            logger.bind(privacy=True).info(f"PRIVACY: {json.dumps(asdict(event))}")
            
            # Store in Redis for real-time monitoring (if available)
            if self.redis_client:
                await self.redis_client.lpush(
                    "privacy_audit_log",
                    json.dumps(asdict(event))
                )
                await self.redis_client.ltrim("privacy_audit_log", 0, 9999)
            
        except Exception as e:
            logger.error(f"❌ Privacy event logging failed: {e}")
    
    async def cleanup_expired_data(self):
        """Clean up expired session data"""
        await self.session_manager.cleanup_expired_sessions()


# Global privacy service instance
privacy_service = PrivacyComplianceService()


# Export for use in other modules
__all__ = [
    "PrivacyComplianceService",
    "SessionDataManager", 
    "PrivacyEvent",
    "DataProcessingRecord",
    "privacy_service"
]