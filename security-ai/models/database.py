"""
SQLAlchemy database models for SecurityGuard AI
PostgreSQL schema for exploit patterns and scan history
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, JSON,
    Index, ForeignKey, create_engine, MetaData
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID, BYTEA
import uuid

Base = declarative_base()
metadata = MetaData()


class ExploitPatternDB(Base):
    """
    Exploit pattern database model
    Optimized for <100ms pattern matching with proper indexing
    """
    __tablename__ = 'exploit_patterns'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pattern_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Pattern classification
    pattern_type = Column(String(50), nullable=False, index=True)  # program, instruction, behavioral
    severity = Column(String(20), nullable=False, index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    confidence = Column(Float, default=0.8, nullable=False)
    
    # Pattern matching data
    program_id = Column(String(44), nullable=True, index=True)  # Solana program ID
    instruction_signature = Column(BYTEA, nullable=True)  # Binary instruction pattern
    instruction_pattern = Column(String(500), nullable=True)  # Text pattern for instructions
    account_pattern = Column(String(500), nullable=True)  # Account interaction pattern
    
    # Behavioral patterns (JSON for flexibility)
    behavioral_rules = Column(JSON, nullable=True)  # Complex behavioral rules
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Performance tracking
    match_count = Column(Integer, default=0, nullable=False)  # How many times this pattern matched
    false_positive_count = Column(Integer, default=0, nullable=False)
    
    # Source information
    source = Column(String(100), nullable=True)  # threat_intelligence, manual, community
    threat_actor = Column(String(255), nullable=True)  # Associated threat actor
    
    # Relationships
    scan_matches = relationship("ScanPatternMatch", back_populates="pattern")
    
    # Composite indexes for performance
    __table_args__ = (
        Index('idx_pattern_lookup', 'pattern_type', 'severity', 'is_active'),
        Index('idx_program_severity', 'program_id', 'severity', 'is_active'),
        Index('idx_pattern_performance', 'pattern_type', 'match_count', 'severity'),
        Index('idx_updated_active', 'updated_at', 'is_active'),
    )


class ScanHistoryDB(Base):
    """
    Scan history database model
    Stores user scan results with privacy compliance
    """
    __tablename__ = 'scan_history'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # User information (optional for anonymous scans)
    user_wallet = Column(String(44), nullable=True, index=True)
    
    # Transaction information (limited for privacy)
    transaction_hash = Column(String(88), nullable=True, index=True)
    transaction_signature = Column(String(88), nullable=True)  # First signature only
    
    # Scan results
    risk_level = Column(String(10), nullable=False, index=True)  # SAFE, CAUTION, DANGER
    risk_score = Column(Integer, nullable=False, index=True)  # 0-100
    confidence = Column(Float, nullable=False)
    
    # Analysis summary (no sensitive transaction data)
    program_count = Column(Integer, nullable=False)
    instruction_count = Column(Integer, nullable=False)
    pattern_matches_count = Column(Integer, nullable=False)
    
    # Performance metrics
    scan_time_ms = Column(Integer, nullable=False)
    ml_analysis_time_ms = Column(Integer, nullable=True)
    pattern_match_time_ms = Column(Integer, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    scan_type = Column(String(20), default='quick', nullable=False)  # quick, deep, comprehensive
    
    # Privacy compliance - auto-delete after retention period
    expires_at = Column(DateTime, nullable=True, index=True)
    
    # Relationships
    pattern_matches = relationship("ScanPatternMatch", back_populates="scan")
    
    # Partitioning and performance indexes
    __table_args__ = (
        Index('idx_user_scans', 'user_wallet', 'created_at'),
        Index('idx_risk_analysis', 'risk_level', 'risk_score', 'created_at'),
        Index('idx_performance_tracking', 'scan_time_ms', 'created_at'),
        Index('idx_cleanup', 'expires_at', 'created_at'),
    )


class ScanPatternMatch(Base):
    """
    Junction table for scan results and matched patterns
    Enables pattern effectiveness analysis
    """
    __tablename__ = 'scan_pattern_matches'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    scan_id = Column(UUID(as_uuid=True), ForeignKey('scan_history.id'), nullable=False, index=True)
    pattern_id = Column(Integer, ForeignKey('exploit_patterns.id'), nullable=False, index=True)
    
    # Match details
    match_confidence = Column(Float, nullable=False)
    match_evidence = Column(JSON, nullable=True)  # Evidence that triggered the match
    
    # Performance tracking
    match_time_ms = Column(Integer, nullable=True)
    
    # Feedback (for pattern improvement)
    is_false_positive = Column(Boolean, nullable=True)  # User feedback
    feedback_timestamp = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    scan = relationship("ScanHistoryDB", back_populates="pattern_matches")
    pattern = relationship("ExploitPatternDB", back_populates="scan_matches")
    
    # Composite indexes
    __table_args__ = (
        Index('idx_scan_patterns', 'scan_id', 'pattern_id'),
        Index('idx_pattern_effectiveness', 'pattern_id', 'match_confidence', 'is_false_positive'),
    )


class ThreatIntelligenceFeed(Base):
    """
    Threat intelligence feed tracking
    Manages daily pattern updates from external sources
    """
    __tablename__ = 'threat_intelligence_feeds'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Feed information
    feed_name = Column(String(100), nullable=False, index=True)
    feed_url = Column(String(500), nullable=True)
    feed_type = Column(String(50), nullable=False)  # api, rss, manual
    
    # Update tracking
    last_update = Column(DateTime, nullable=True, index=True)
    last_successful_update = Column(DateTime, nullable=True)
    update_frequency_hours = Column(Integer, default=24, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    error_count = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    
    # Statistics
    patterns_added = Column(Integer, default=0, nullable=False)
    patterns_updated = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_feed_updates', 'feed_name', 'last_update', 'is_active'),
    )


class PatternCache(Base):
    """
    Pattern matching cache for performance optimization
    Redis backup in database for persistence
    """
    __tablename__ = 'pattern_cache'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Cache key (hash of transaction components)
    cache_key = Column(String(64), unique=True, nullable=False, index=True)
    
    # Cached data
    transaction_hash = Column(String(64), nullable=False, index=True)  # Hash of transaction
    matched_patterns = Column(JSON, nullable=False)  # Serialized pattern matches
    
    # Cache metadata
    hit_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_cache_lookup', 'cache_key', 'expires_at'),
        Index('idx_cache_cleanup', 'expires_at'),
    )


class UserProfileDB(Base):
    """
    User profile database model
    Stores user information and statistics
    """
    __tablename__ = 'user_profiles'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User identification
    wallet_address = Column(String(44), unique=True, nullable=False, index=True)
    username = Column(String(50), nullable=True, index=True)
    
    # User statistics
    total_scans = Column(Integer, default=0, nullable=False)
    threats_detected = Column(Integer, default=0, nullable=False)
    total_payments_sol = Column(Float, default=0.0, nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    last_active = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    last_payment = Column(DateTime, nullable=True, index=True)
    
    # Relationships
    payments = relationship("PaymentRecordDB", back_populates="user")
    
    __table_args__ = (
        Index('idx_user_activity', 'wallet_address', 'last_active'),
        Index('idx_user_stats', 'total_scans', 'threats_detected'),
    )


class PaymentRecordDB(Base):
    """
    Payment record database model
    Tracks all payments for audit and access control
    """
    __tablename__ = 'payment_records'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Payment identification
    payment_id = Column(String(100), unique=True, nullable=False, index=True)
    transaction_signature = Column(String(88), nullable=True, index=True)
    
    # User and service information
    user_wallet = Column(String(44), ForeignKey('user_profiles.wallet_address'), nullable=False, index=True)
    service_type = Column(String(50), nullable=False, index=True)
    
    # Payment details
    amount_sol = Column(Float, nullable=False)
    amount_lamports = Column(Integer, nullable=False)
    
    # Payment status
    status = Column(String(20), nullable=False, index=True)  # pending, completed, failed, expired
    
    # Blockchain information
    escrow_account = Column(String(44), nullable=True)
    block_time = Column(DateTime, nullable=True)
    confirmation_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    processed_at = Column(DateTime, nullable=True, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    
    # Service access tracking
    services_used = Column(Integer, default=0, nullable=False)  # How many services this payment covered
    last_service_used = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("UserProfileDB", back_populates="payments")
    
    __table_args__ = (
        Index('idx_payment_lookup', 'user_wallet', 'status', 'created_at'),
        Index('idx_payment_access', 'user_wallet', 'service_type', 'processed_at'),
        Index('idx_payment_cleanup', 'expires_at', 'status'),
    )


class ServiceAccessLog(Base):
    """
    Service access log for tracking usage and billing
    """
    __tablename__ = 'service_access_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Access information
    user_wallet = Column(String(44), nullable=False, index=True)
    service_type = Column(String(50), nullable=False, index=True)
    payment_id = Column(String(100), ForeignKey('payment_records.payment_id'), nullable=True, index=True)
    
    # Service details
    scan_id = Column(String(100), nullable=True, index=True)
    risk_level = Column(String(10), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    
    # Access metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    
    # Timestamps
    accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_access_tracking', 'user_wallet', 'service_type', 'accessed_at'),
        Index('idx_payment_usage', 'payment_id', 'accessed_at'),
    )


# Database utility functions
def create_database_engine(database_url: str):
    """Create SQLAlchemy engine with optimized settings"""
    return create_engine(
        database_url,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False  # Set to True for SQL debugging
    )


def create_session_factory(engine):
    """Create session factory"""
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def create_tables(engine):
    """Create all database tables"""
    Base.metadata.create_all(engine)


def create_indexes(engine):
    """Create additional performance indexes"""
    with engine.connect() as conn:
        # Additional indexes for performance
        conn.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_exploit_patterns_composite 
            ON exploit_patterns(pattern_type, severity DESC, program_id) 
            WHERE is_active = true;
        """)
        
        conn.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scan_history_performance 
            ON scan_history(created_at DESC, risk_level, scan_time_ms) 
            WHERE user_wallet IS NOT NULL;
        """)
        
        conn.execute("""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pattern_effectiveness 
            ON scan_pattern_matches(pattern_id, match_confidence DESC, is_false_positive) 
            WHERE is_false_positive IS NOT TRUE;
        """)
        
        conn.commit()


# Database initialization script
def initialize_database(database_url: str):
    """Initialize database with tables and indexes"""
    engine = create_database_engine(database_url)
    
    # Create tables
    create_tables(engine)
    
    # Create performance indexes
    try:
        create_indexes(engine)
    except Exception as e:
        print(f"Warning: Could not create some indexes: {e}")
    
    return engine