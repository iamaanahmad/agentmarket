"""
Pydantic models for SecurityGuard AI API
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum

from pydantic import BaseModel, Field, validator


class RiskLevel(str, Enum):
    """Risk level enumeration"""
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    DANGER = "DANGER"


class ScanType(str, Enum):
    """Scan type enumeration"""
    QUICK = "quick"
    DEEP = "deep"
    COMPREHENSIVE = "comprehensive"


class TransactionScanRequest(BaseModel):
    """Request model for transaction scanning"""
    transaction: Union[str, Dict[str, Any]] = Field(
        ..., 
        description="Base64 encoded transaction or transaction object"
    )
    user_wallet: Optional[str] = Field(
        None, 
        description="User's wallet address for context"
    )
    scan_type: ScanType = Field(
        ScanType.QUICK, 
        description="Type of scan to perform"
    )
    
    @validator('transaction')
    def validate_transaction(cls, v):
        if isinstance(v, str) and len(v) == 0:
            raise ValueError("Transaction cannot be empty")
        return v


class SecurityAnalysisDetails(BaseModel):
    """Detailed security analysis results"""
    program_analysis: Dict[str, Any] = Field(
        default_factory=dict,
        description="Analysis of programs involved in transaction"
    )
    pattern_matches: List[str] = Field(
        default_factory=list,
        description="Matched exploit patterns"
    )
    ml_analysis: Dict[str, Any] = Field(
        default_factory=dict,
        description="ML model analysis results"
    )
    account_analysis: Dict[str, Any] = Field(
        default_factory=dict,
        description="Account risk assessment"
    )


class TransactionScanResponse(BaseModel):
    """Response model for transaction scanning"""
    scan_id: str = Field(..., description="Unique scan identifier")
    risk_level: RiskLevel = Field(..., description="Overall risk assessment")
    risk_score: int = Field(..., ge=0, le=100, description="Risk score (0-100)")
    explanation: str = Field(..., description="Human-readable explanation")
    recommendation: str = Field(..., description="Recommended action")
    details: SecurityAnalysisDetails = Field(..., description="Detailed analysis")
    scan_time_ms: int = Field(..., description="Scan duration in milliseconds")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SecurityChatMessage(BaseModel):
    """Chat message model"""
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SecurityChatRequest(BaseModel):
    """Request model for security chat"""
    message: str = Field(..., min_length=1, max_length=1000)
    context: Optional[Dict[str, Any]] = Field(
        None, 
        description="Optional context (transaction, address, etc.)"
    )
    conversation_history: List[SecurityChatMessage] = Field(
        default_factory=list,
        description="Previous conversation messages"
    )


class SecurityChatResponse(BaseModel):
    """Response model for security chat"""
    message: str = Field(..., description="AI response message")
    analysis: Optional[Dict[str, Any]] = Field(
        None, 
        description="Optional security analysis if applicable"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Security recommendations"
    )
    related_scans: List[str] = Field(
        default_factory=list,
        description="Related scan IDs if applicable"
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ScanHistoryResponse(BaseModel):
    """Response model for scan history"""
    scan_id: str
    risk_level: RiskLevel
    risk_score: int
    explanation: str
    scan_time_ms: int
    timestamp: datetime
    transaction_summary: Optional[str] = None


class UserProfile(BaseModel):
    """User profile model"""
    wallet_address: str = Field(..., description="User's wallet address")
    username: Optional[str] = None
    total_scans: int = Field(default=0)
    threats_detected: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)


class ExploitPattern(BaseModel):
    """Exploit pattern model"""
    pattern_id: str
    name: str
    description: str
    severity: str
    program_ids: List[str] = Field(default_factory=list)
    instruction_patterns: List[str] = Field(default_factory=list)
    account_patterns: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MLModelPrediction(BaseModel):
    """ML model prediction result"""
    anomaly_score: float = Field(..., ge=0.0, le=1.0)
    classification: str = Field(..., description="Normal/Suspicious/Malicious")
    confidence: float = Field(..., ge=0.0, le=1.0)
    feature_importance: Dict[str, float] = Field(default_factory=dict)


class ProgramAnalysis(BaseModel):
    """Program analysis result"""
    program_id: str
    is_verified: bool = False
    is_blacklisted: bool = False
    risk_score: int = Field(..., ge=0, le=100)
    deployment_date: Optional[datetime] = None
    interaction_count: int = 0
    reputation_score: float = Field(default=0.0, ge=0.0, le=1.0)


class AccountAnalysis(BaseModel):
    """Account analysis result"""
    address: str
    is_new_account: bool = False
    creation_date: Optional[datetime] = None
    transaction_history_length: int = 0
    suspicious_activity: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)
    reputation_score: float = Field(default=0.0, ge=0.0, le=1.0)


class SecurityStats(BaseModel):
    """Platform security statistics"""
    total_scans: int = 0
    threats_blocked: int = 0
    users_protected: int = 0
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_response_time_ms: int = 0
    top_threats: List[str] = Field(default_factory=list)
    daily_scans: Dict[str, int] = Field(default_factory=dict)


class WebhookPayload(BaseModel):
    """Webhook payload for notifications"""
    event_type: str
    scan_id: str
    user_wallet: str
    risk_level: RiskLevel
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)


class AuthenticationRequest(BaseModel):
    """Request model for wallet authentication"""
    wallet_address: str = Field(..., description="User's Solana wallet address")
    message: str = Field(..., description="Signed authentication message")
    signature: str = Field(..., description="Wallet signature of the message")
    timestamp: int = Field(..., description="Message timestamp")
    username: Optional[str] = Field(None, description="Optional username")
    
    @validator('wallet_address')
    def validate_wallet_address(cls, v):
        if not v or len(v) < 32 or len(v) > 44:
            raise ValueError("Invalid Solana wallet address format")
        try:
            import base58
            decoded = base58.b58decode(v)
            if len(decoded) != 32:
                raise ValueError("Invalid Solana wallet address format")
        except Exception:
            raise ValueError("Invalid Solana wallet address format")
        return v


class AuthenticationResponse(BaseModel):
    """Response model for wallet authentication"""
    success: bool = Field(..., description="Authentication success status")
    jwt_token: Optional[str] = Field(None, description="JWT authentication token")
    user_profile: Optional[UserProfile] = Field(None, description="User profile information")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")
    error: Optional[str] = Field(None, description="Error message if authentication failed")


class PaymentRequest(BaseModel):
    """Request model for payment processing"""
    service_type: str = Field(default="transaction_scan", description="Type of service")
    user_wallet: str = Field(..., description="User's wallet address")
    
    @validator('user_wallet')
    def validate_wallet_address(cls, v):
        if not v or len(v) < 32 or len(v) > 44:
            raise ValueError("Invalid Solana wallet address format")
        try:
            import base58
            decoded = base58.b58decode(v)
            if len(decoded) != 32:
                raise ValueError("Invalid Solana wallet address format")
        except Exception:
            raise ValueError("Invalid Solana wallet address format")
        return v


class PaymentResponse(BaseModel):
    """Response model for payment requests"""
    payment_id: str = Field(..., description="Unique payment identifier")
    amount_sol: float = Field(..., description="Payment amount in SOL")
    amount_lamports: int = Field(..., description="Payment amount in lamports")
    escrow_program_id: str = Field(..., description="Escrow program ID")
    platform_wallet: str = Field(..., description="Platform wallet address")
    expires_at: datetime = Field(..., description="Payment expiration time")
    has_sufficient_balance: bool = Field(..., description="Whether user has sufficient balance")
    current_balance_sol: float = Field(..., description="User's current balance in SOL")
    balance_message: str = Field(..., description="Balance status message")
    payment_instructions: Dict[str, Any] = Field(..., description="Payment instructions")


class PaymentConfirmationRequest(BaseModel):
    """Request model for payment confirmation"""
    payment_id: str = Field(..., description="Payment request ID")
    transaction_signature: str = Field(..., description="Solana transaction signature")
    
    @validator('transaction_signature')
    def validate_transaction_signature(cls, v):
        if not v or len(v) < 64:
            raise ValueError("Invalid transaction signature format")
        return v


class PaymentStatusResponse(BaseModel):
    """Response model for payment status"""
    payment_id: str = Field(..., description="Payment identifier")
    status: str = Field(..., description="Payment status (pending/completed/expired/not_found)")
    payment_details: Optional[Dict[str, Any]] = Field(None, description="Payment details")
    time_remaining_seconds: Optional[int] = Field(None, description="Time remaining for pending payments")
    error: Optional[str] = Field(None, description="Error message if applicable")


class AuthMessageRequest(BaseModel):
    """Request model for authentication message generation"""
    wallet_address: str = Field(..., description="User's wallet address")
    timestamp: int = Field(..., description="Current timestamp")
    
    @validator('wallet_address')
    def validate_wallet_address(cls, v):
        if not v or len(v) < 32 or len(v) > 44:
            raise ValueError("Invalid Solana wallet address format")
        try:
            import base58
            decoded = base58.b58decode(v)
            if len(decoded) != 32:
                raise ValueError("Invalid Solana wallet address format")
        except Exception:
            raise ValueError("Invalid Solana wallet address format")
        return v


class AuthMessageResponse(BaseModel):
    """Response model for authentication message"""
    message: str = Field(..., description="Message to be signed by wallet")
    timestamp: int = Field(..., description="Message timestamp")
    expires_in_seconds: int = Field(default=300, description="Message validity period")