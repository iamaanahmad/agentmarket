"""
Configuration management for SecurityGuard AI
"""

import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "SecurityGuard AI"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    allowed_origins: List[str] = ["http://localhost:3000", "https://agentmarket.app"]
    allowed_hosts: List[str] = ["localhost", "127.0.0.1", "agentmarket.app"]
    
    # HTTPS/TLS Configuration
    use_https: bool = True
    ssl_cert_path: str = ""
    ssl_key_path: str = ""
    
    # Rate Limiting & Security
    enable_rate_limiting: bool = True
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    max_requests_per_day: int = 10000
    
    # Input Validation & Sanitization
    max_request_size_mb: int = 10
    max_transaction_size_kb: int = 100
    enable_input_sanitization: bool = True
    
    # Privacy & Compliance
    data_retention_hours: int = 0  # No data retention beyond session
    enable_audit_logging: bool = True
    audit_log_path: str = "./logs/audit.log"
    privacy_policy_url: str = "https://agentmarket.app/privacy"
    
    # Security Headers
    enable_security_headers: bool = True
    hsts_max_age: int = 31536000  # 1 year
    
    # Session Management
    session_timeout_minutes: int = 30
    max_concurrent_sessions_per_user: int = 5
    
    # Enhanced Security Settings
    enable_csrf_protection: bool = True
    csrf_secret_key: str = "csrf-secret-key-change-in-production"
    
    # Content Security Policy
    csp_default_src: str = "'self'"
    csp_script_src: str = "'self' 'unsafe-inline'"
    csp_style_src: str = "'self' 'unsafe-inline'"
    csp_img_src: str = "'self' data: https:"
    csp_connect_src: str = "'self' https:"
    
    # Additional Security Headers
    x_frame_options: str = "DENY"
    x_content_type_options: str = "nosniff"
    x_xss_protection: str = "1; mode=block"
    referrer_policy: str = "strict-origin-when-cross-origin"
    
    # Permissions Policy
    permissions_policy: str = "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), speaker=()"
    
    # Rate Limiting Enhancement
    rate_limit_storage_url: str = ""  # Redis URL for distributed rate limiting
    rate_limit_key_func: str = "ip"  # ip, user, or custom
    
    # Abuse Prevention
    enable_abuse_detection: bool = True
    max_failed_requests_per_minute: int = 10
    temporary_ban_duration_minutes: int = 15
    permanent_ban_threshold: int = 100
    
    # Data Privacy Controls
    enable_data_anonymization: bool = True
    anonymization_salt: str = "anonymization-salt-change-in-production"
    enable_right_to_deletion: bool = True
    enable_data_portability: bool = True
    
    # Compliance Reporting
    enable_compliance_reporting: bool = True
    compliance_report_retention_days: int = 90
    gdpr_compliance_mode: bool = True
    ccpa_compliance_mode: bool = True
    
    # Security Monitoring
    enable_security_monitoring: bool = True
    security_alert_webhook_url: str = ""
    security_log_retention_days: int = 90
    
    # Encryption Settings
    encryption_algorithm: str = "AES-256-GCM"
    key_derivation_iterations: int = 100000
    
    # TLS/SSL Configuration
    tls_version_min: str = "1.2"
    tls_version_max: str = "1.3"
    ssl_ciphers: str = "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
    
    # Input Validation Enhancement
    max_json_payload_size: int = 1048576  # 1MB
    max_form_data_size: int = 10485760   # 10MB
    max_file_upload_size: int = 52428800  # 50MB
    allowed_file_types: List[str] = [".txt", ".json", ".csv"]
    
    # API Security
    api_key_header_name: str = "X-API-Key"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    refresh_token_expiration_days: int = 30
    
    # Logging Enhancement
    log_sensitive_data: bool = False
    log_request_bodies: bool = False
    log_response_bodies: bool = False
    structured_logging: bool = True
    
    # Solana
    solana_rpc_url: str = "https://api.devnet.solana.com"
    solana_network: str = "devnet"
    
    # AI Services
    gemini_api_key: str = ""
    openai_api_key: str = ""
    
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost/agentmarket"
    redis_url: str = "redis://localhost:6379"
    
    # ML Model
    model_path: str = "./models/anomaly_detector.pkl"
    model_update_interval: int = 3600  # 1 hour
    
    # Exploit Database
    exploit_db_update_interval: int = 86400  # 24 hours
    exploit_sources: List[str] = [
        "https://api.github.com/repos/solana-labs/security-advisories",
        "https://api.certik.com/v1/solana/exploits",
    ]
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    
    # Monitoring
    sentry_dsn: str = ""
    log_level: str = "INFO"
    
    # Cache
    cache_ttl: int = 300  # 5 minutes
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()