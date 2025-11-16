"""
Security Audit Logging Service
Comprehensive audit trail for security events and compliance reporting
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

import redis.asyncio as redis
from loguru import logger
from fastapi import Request

try:
    from ..core.config import get_settings
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from core.config import get_settings


class SecurityEventType(Enum):
    """Types of security events to audit"""
    AUTHENTICATION_SUCCESS = "authentication_success"
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_FAILURE = "authorization_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    MALICIOUS_INPUT_DETECTED = "malicious_input_detected"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    PRIVACY_REQUEST = "privacy_request"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SECURITY_SCAN = "security_scan"
    PAYMENT_TRANSACTION = "payment_transaction"
    SYSTEM_ERROR = "system_error"
    ADMIN_ACTION = "admin_action"


class RiskLevel(Enum):
    """Risk levels for security events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityAuditEvent:
    """Security audit event structure"""
    event_id: str
    timestamp: str
    event_type: SecurityEventType
    risk_level: RiskLevel
    user_id: Optional[str]
    session_id: Optional[str]
    client_ip: str
    user_agent: str
    endpoint: str
    method: str
    status_code: Optional[int]
    details: Dict[str, Any]
    geolocation: Optional[Dict[str, str]]
    threat_indicators: List[str]
    compliance_tags: List[str]


@dataclass
class ComplianceReport:
    """Compliance report structure"""
    report_id: str
    generated_at: str
    period_start: str
    period_end: str
    total_events: int
    events_by_type: Dict[str, int]
    events_by_risk: Dict[str, int]
    privacy_requests: int
    data_breaches: int
    compliance_violations: int
    recommendations: List[str]


class SecurityAuditService:
    """Main security audit logging service"""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client: Optional[redis.Redis] = None
        self.audit_events: List[SecurityAuditEvent] = []
        self.max_memory_events = 10000
        
    async def initialize(self):
        """Initialize audit service"""
        try:
            if self.settings.redis_url:
                self.redis_client = redis.from_url(
                    self.settings.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                await self.redis_client.ping()
                logger.info("✅ Security audit service initialized with Redis")
            else:
                logger.warning("⚠️ Redis not configured, using memory-only audit logging")
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable for audit logging: {e}")
            self.redis_client = None
    
    async def log_security_event(
        self,
        event_type: SecurityEventType,
        risk_level: RiskLevel,
        request: Request,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        status_code: Optional[int] = None
    ) -> str:
        """
        Log a security event with comprehensive details
        Returns event ID for tracking
        """
        try:
            # Generate unique event ID
            event_id = self._generate_event_id()
            
            # Extract request information
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "")
            endpoint = str(request.url.path)
            method = request.method
            
            # Detect threat indicators
            threat_indicators = self._detect_threat_indicators(request, details)
            
            # Determine compliance tags
            compliance_tags = self._get_compliance_tags(event_type, details)
            
            # Get geolocation (if available)
            geolocation = await self._get_geolocation(client_ip)
            
            # Create audit event
            audit_event = SecurityAuditEvent(
                event_id=event_id,
                timestamp=datetime.utcnow().isoformat(),
                event_type=event_type,
                risk_level=risk_level,
                user_id=user_id,
                session_id=session_id,
                client_ip=client_ip,
                user_agent=user_agent,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                details=self._sanitize_details(details),
                geolocation=geolocation,
                threat_indicators=threat_indicators,
                compliance_tags=compliance_tags
            )
            
            # Store audit event
            await self._store_audit_event(audit_event)
            
            # Log to structured logger
            logger.bind(
                audit=True,
                event_id=event_id,
                event_type=event_type.value,
                risk_level=risk_level.value,
                user_id=user_id,
                client_ip=client_ip
            ).info(f"SECURITY_AUDIT: {event_type.value}")
            
            # Trigger alerts for high-risk events
            if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                await self._trigger_security_alert(audit_event)
            
            return event_id
            
        except Exception as e:
            logger.error(f"❌ Security audit logging failed: {e}")
            # Fallback logging
            logger.bind(audit_error=True).error(
                f"AUDIT_FAILURE: {event_type.value} - {str(e)}"
            )
            return "audit_failed"
    
    async def get_audit_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[SecurityEventType]] = None,
        risk_levels: Optional[List[RiskLevel]] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[SecurityAuditEvent]:
        """Get audit events with filtering"""
        try:
            if self.redis_client:
                return await self._get_events_from_redis(
                    start_time, end_time, event_types, risk_levels, user_id, limit
                )
            else:
                return self._get_events_from_memory(
                    start_time, end_time, event_types, risk_levels, user_id, limit
                )
        except Exception as e:
            logger.error(f"❌ Audit event retrieval failed: {e}")
            return []
    
    async def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        report_type: str = "full"
    ) -> ComplianceReport:
        """Generate compliance report for specified period"""
        try:
            # Get events for period
            events = await self.get_audit_events(start_date, end_date, limit=10000)
            
            # Analyze events
            total_events = len(events)
            events_by_type = {}
            events_by_risk = {}
            privacy_requests = 0
            data_breaches = 0
            compliance_violations = 0
            
            for event in events:
                # Count by type
                event_type = event.event_type.value
                events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
                
                # Count by risk
                risk_level = event.risk_level.value
                events_by_risk[risk_level] = events_by_risk.get(risk_level, 0) + 1
                
                # Count specific compliance events
                if "privacy" in event.compliance_tags:
                    privacy_requests += 1
                if "data_breach" in event.compliance_tags:
                    data_breaches += 1
                if "compliance_violation" in event.compliance_tags:
                    compliance_violations += 1
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                events_by_type, events_by_risk, privacy_requests, 
                data_breaches, compliance_violations
            )
            
            # Create report
            report = ComplianceReport(
                report_id=self._generate_report_id(),
                generated_at=datetime.utcnow().isoformat(),
                period_start=start_date.isoformat(),
                period_end=end_date.isoformat(),
                total_events=total_events,
                events_by_type=events_by_type,
                events_by_risk=events_by_risk,
                privacy_requests=privacy_requests,
                data_breaches=data_breaches,
                compliance_violations=compliance_violations,
                recommendations=recommendations
            )
            
            # Store report
            await self._store_compliance_report(report)
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Compliance report generation failed: {e}")
            raise
    
    async def cleanup_old_events(self, retention_days: int = 90):
        """Clean up old audit events based on retention policy"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            if self.redis_client:
                # Clean up Redis events
                await self._cleanup_redis_events(cutoff_date)
            
            # Clean up memory events
            self.audit_events = [
                event for event in self.audit_events
                if datetime.fromisoformat(event.timestamp) > cutoff_date
            ]
            
            logger.info(f"🧹 Cleaned up audit events older than {retention_days} days")
            
        except Exception as e:
            logger.error(f"❌ Audit cleanup failed: {e}")
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        timestamp = str(time.time())
        random_data = str(hash(timestamp))
        return hashlib.md5(f"{timestamp}:{random_data}".encode()).hexdigest()[:16]
    
    def _generate_report_id(self) -> str:
        """Generate unique report ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"compliance_report_{timestamp}"
    
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
    
    def _detect_threat_indicators(self, request: Request, details: Dict) -> List[str]:
        """Detect threat indicators in request"""
        indicators = []
        
        # Check for suspicious patterns
        user_agent = request.headers.get("user-agent", "").lower()
        if any(bot in user_agent for bot in ["bot", "crawler", "spider", "scraper"]):
            indicators.append("automated_client")
        
        # Check for suspicious request patterns
        if len(request.headers.get("user-agent", "")) < 10:
            indicators.append("minimal_user_agent")
        
        # Check for rapid requests (would need rate limiting data)
        if "rate_limit" in details:
            indicators.append("high_request_rate")
        
        # Check for malicious input patterns
        if "malicious_input" in details:
            indicators.append("malicious_payload")
        
        return indicators
    
    def _get_compliance_tags(self, event_type: SecurityEventType, details: Dict) -> List[str]:
        """Determine compliance tags for event"""
        tags = []
        
        # GDPR tags
        if event_type in [SecurityEventType.DATA_ACCESS, SecurityEventType.DATA_MODIFICATION, SecurityEventType.DATA_DELETION]:
            tags.append("gdpr")
        
        if event_type == SecurityEventType.PRIVACY_REQUEST:
            tags.extend(["gdpr", "ccpa", "privacy"])
        
        # Security tags
        if event_type in [SecurityEventType.MALICIOUS_INPUT_DETECTED, SecurityEventType.SUSPICIOUS_ACTIVITY]:
            tags.append("security_incident")
        
        # Payment tags
        if event_type == SecurityEventType.PAYMENT_TRANSACTION:
            tags.extend(["pci_dss", "financial"])
        
        # Add custom tags from details
        if "compliance_tags" in details:
            tags.extend(details["compliance_tags"])
        
        return list(set(tags))  # Remove duplicates
    
    async def _get_geolocation(self, ip: str) -> Optional[Dict[str, str]]:
        """Get geolocation for IP (placeholder - would integrate with GeoIP service)"""
        # In production, integrate with MaxMind GeoIP or similar service
        if ip in ["127.0.0.1", "localhost", "unknown"]:
            return {"country": "Unknown", "city": "Unknown"}
        
        # Placeholder geolocation
        return {"country": "Unknown", "city": "Unknown", "ip": ip}
    
    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data from audit details"""
        sanitized = details.copy()
        
        # Remove sensitive keys
        sensitive_keys = [
            "password", "token", "secret", "key", "signature",
            "private_key", "api_key", "auth_token"
        ]
        
        for key in sensitive_keys:
            if key in sanitized:
                sanitized[key] = "[REDACTED]"
        
        # Truncate long values
        for key, value in sanitized.items():
            if isinstance(value, str) and len(value) > 1000:
                sanitized[key] = value[:1000] + "...[TRUNCATED]"
        
        return sanitized
    
    async def _store_audit_event(self, event: SecurityAuditEvent):
        """Store audit event in Redis and memory"""
        try:
            # Store in Redis if available
            if self.redis_client:
                event_key = f"audit_event:{event.event_id}"
                event_data = json.dumps(asdict(event))
                
                # Store event with TTL
                ttl_seconds = self.settings.security_log_retention_days * 24 * 3600
                await self.redis_client.setex(event_key, ttl_seconds, event_data)
                
                # Add to time-based index
                timestamp_key = f"audit_index:{event.timestamp[:10]}"  # YYYY-MM-DD
                await self.redis_client.sadd(timestamp_key, event.event_id)
                await self.redis_client.expire(timestamp_key, ttl_seconds)
            
            # Store in memory (limited size)
            self.audit_events.append(event)
            if len(self.audit_events) > self.max_memory_events:
                self.audit_events = self.audit_events[-self.max_memory_events:]
            
        except Exception as e:
            logger.error(f"❌ Audit event storage failed: {e}")
    
    async def _trigger_security_alert(self, event: SecurityAuditEvent):
        """Trigger security alert for high-risk events"""
        try:
            if self.settings.security_alert_webhook_url:
                # In production, send webhook notification
                logger.warning(
                    f"🚨 SECURITY ALERT: {event.event_type.value} "
                    f"(Risk: {event.risk_level.value}) from {event.client_ip}"
                )
            
            # Log critical events with special formatting
            if event.risk_level == RiskLevel.CRITICAL:
                logger.bind(critical_security_event=True).critical(
                    f"CRITICAL SECURITY EVENT: {event.event_type.value} - "
                    f"Event ID: {event.event_id}, IP: {event.client_ip}"
                )
        
        except Exception as e:
            logger.error(f"❌ Security alert failed: {e}")
    
    async def _get_events_from_redis(
        self, start_time, end_time, event_types, risk_levels, user_id, limit
    ) -> List[SecurityAuditEvent]:
        """Get events from Redis storage"""
        # Implementation would query Redis indexes
        # For now, return empty list
        return []
    
    def _get_events_from_memory(
        self, start_time, end_time, event_types, risk_levels, user_id, limit
    ) -> List[SecurityAuditEvent]:
        """Get events from memory storage"""
        filtered_events = self.audit_events
        
        # Apply filters
        if start_time:
            filtered_events = [
                e for e in filtered_events 
                if datetime.fromisoformat(e.timestamp) >= start_time
            ]
        
        if end_time:
            filtered_events = [
                e for e in filtered_events 
                if datetime.fromisoformat(e.timestamp) <= end_time
            ]
        
        if event_types:
            filtered_events = [
                e for e in filtered_events 
                if e.event_type in event_types
            ]
        
        if risk_levels:
            filtered_events = [
                e for e in filtered_events 
                if e.risk_level in risk_levels
            ]
        
        if user_id:
            filtered_events = [
                e for e in filtered_events 
                if e.user_id == user_id
            ]
        
        # Sort by timestamp (newest first) and limit
        filtered_events.sort(key=lambda x: x.timestamp, reverse=True)
        return filtered_events[:limit]
    
    def _generate_recommendations(
        self, events_by_type, events_by_risk, privacy_requests, 
        data_breaches, compliance_violations
    ) -> List[str]:
        """Generate security recommendations based on audit data"""
        recommendations = []
        
        # High-risk event recommendations
        if events_by_risk.get("critical", 0) > 0:
            recommendations.append(
                "Critical security events detected. Immediate investigation required."
            )
        
        if events_by_risk.get("high", 0) > 10:
            recommendations.append(
                "High number of high-risk events. Review security controls."
            )
        
        # Rate limiting recommendations
        if events_by_type.get("rate_limit_exceeded", 0) > 100:
            recommendations.append(
                "Consider implementing stricter rate limiting policies."
            )
        
        # Authentication recommendations
        auth_failures = events_by_type.get("authentication_failure", 0)
        if auth_failures > 50:
            recommendations.append(
                "High authentication failure rate. Consider implementing account lockout."
            )
        
        # Privacy recommendations
        if privacy_requests > 10:
            recommendations.append(
                "High volume of privacy requests. Review data handling procedures."
            )
        
        # Data breach recommendations
        if data_breaches > 0:
            recommendations.append(
                "Data breach incidents detected. Immediate compliance review required."
            )
        
        # Default recommendation
        if not recommendations:
            recommendations.append("Security posture appears normal. Continue monitoring.")
        
        return recommendations
    
    async def _store_compliance_report(self, report: ComplianceReport):
        """Store compliance report"""
        try:
            if self.redis_client:
                report_key = f"compliance_report:{report.report_id}"
                report_data = json.dumps(asdict(report))
                
                # Store with extended TTL for compliance reports
                ttl_seconds = self.settings.compliance_report_retention_days * 24 * 3600
                await self.redis_client.setex(report_key, ttl_seconds, report_data)
            
            logger.info(f"📊 Compliance report generated: {report.report_id}")
            
        except Exception as e:
            logger.error(f"❌ Compliance report storage failed: {e}")
    
    async def _cleanup_redis_events(self, cutoff_date: datetime):
        """Clean up old events from Redis"""
        try:
            if not self.redis_client:
                return
            
            # This would implement Redis cleanup logic
            # For now, just log the action
            logger.info(f"🧹 Redis audit cleanup for events before {cutoff_date}")
            
        except Exception as e:
            logger.error(f"❌ Redis audit cleanup failed: {e}")


# Global audit service instance
security_audit_service = SecurityAuditService()


# Export for use in other modules
__all__ = [
    "SecurityAuditService",
    "SecurityEventType",
    "RiskLevel",
    "SecurityAuditEvent",
    "ComplianceReport",
    "security_audit_service"
]