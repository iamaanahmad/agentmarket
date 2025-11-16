"""
TLS/HTTPS Configuration Service
Handles SSL/TLS certificate management and secure connection configuration
"""

import os
import ssl
import socket
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger
import uvicorn

try:
    from ..core.config import get_settings
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from core.config import get_settings


class TLSConfigurationService:
    """Service for managing TLS/HTTPS configuration"""
    
    def __init__(self):
        self.settings = get_settings()
        self.ssl_context: Optional[ssl.SSLContext] = None
        
    def create_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Create SSL context with secure configuration"""
        try:
            if not self.settings.use_https:
                logger.info("🔓 HTTPS disabled in configuration")
                return None
            
            # Check for certificate files
            cert_path = self.settings.ssl_cert_path
            key_path = self.settings.ssl_key_path
            
            if not cert_path or not key_path:
                logger.warning("⚠️ SSL certificate paths not configured")
                return self._create_development_ssl_context()
            
            if not os.path.exists(cert_path) or not os.path.exists(key_path):
                logger.warning(f"⚠️ SSL certificate files not found: {cert_path}, {key_path}")
                return self._create_development_ssl_context()
            
            # Create SSL context
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            
            # Load certificate and key
            context.load_cert_chain(cert_path, key_path)
            
            # Configure secure settings
            self._configure_secure_ssl_context(context)
            
            # Validate certificate
            if self._validate_certificate(cert_path):
                logger.info("✅ SSL certificate loaded and validated")
                self.ssl_context = context
                return context
            else:
                logger.error("❌ SSL certificate validation failed")
                return None
                
        except Exception as e:
            logger.error(f"❌ SSL context creation failed: {e}")
            return None
    
    def _create_development_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Create self-signed certificate for development"""
        try:
            if not self.settings.debug:
                logger.error("❌ Cannot use self-signed certificates in production")
                return None
            
            logger.warning("⚠️ Creating self-signed certificate for development")
            
            # Generate self-signed certificate
            cert_path, key_path = self._generate_self_signed_cert()
            
            if cert_path and key_path:
                context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                context.load_cert_chain(cert_path, key_path)
                self._configure_secure_ssl_context(context)
                
                logger.info("✅ Development SSL context created with self-signed certificate")
                self.ssl_context = context
                return context
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Development SSL context creation failed: {e}")
            return None
    
    def _configure_secure_ssl_context(self, context: ssl.SSLContext):
        """Configure SSL context with secure settings"""
        try:
            # Set minimum TLS version
            if hasattr(ssl, 'TLSVersion'):
                if self.settings.tls_version_min == "1.3":
                    context.minimum_version = ssl.TLSVersion.TLSv1_3
                elif self.settings.tls_version_min == "1.2":
                    context.minimum_version = ssl.TLSVersion.TLSv1_2
                
                if self.settings.tls_version_max == "1.3":
                    context.maximum_version = ssl.TLSVersion.TLSv1_3
            
            # Set cipher suites
            if self.settings.ssl_ciphers:
                context.set_ciphers(self.settings.ssl_ciphers)
            
            # Security options
            context.options |= ssl.OP_NO_SSLv2
            context.options |= ssl.OP_NO_SSLv3
            context.options |= ssl.OP_NO_TLSv1
            context.options |= ssl.OP_NO_TLSv1_1
            context.options |= ssl.OP_SINGLE_DH_USE
            context.options |= ssl.OP_SINGLE_ECDH_USE
            
            # Disable compression to prevent CRIME attacks
            context.options |= ssl.OP_NO_COMPRESSION
            
            # Set security level (if available)
            if hasattr(context, 'security_level'):
                context.security_level = 2  # High security level
            
            logger.debug("🔒 SSL context configured with secure settings")
            
        except Exception as e:
            logger.error(f"❌ SSL context configuration failed: {e}")
    
    def _generate_self_signed_cert(self) -> Tuple[Optional[str], Optional[str]]:
        """Generate self-signed certificate for development"""
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Create certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Development"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SecurityGuard AI Dev"),
                x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.DNSName("127.0.0.1"),
                    x509.DNSName("0.0.0.0"),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256())
            
            # Create certificates directory
            cert_dir = Path("./certificates")
            cert_dir.mkdir(exist_ok=True)
            
            # Write certificate and key files
            cert_path = cert_dir / "dev_cert.pem"
            key_path = cert_dir / "dev_key.pem"
            
            with open(cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            with open(key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            logger.info(f"📜 Self-signed certificate generated: {cert_path}")
            return str(cert_path), str(key_path)
            
        except ImportError:
            logger.error("❌ cryptography library not available for certificate generation")
            return None, None
        except Exception as e:
            logger.error(f"❌ Self-signed certificate generation failed: {e}")
            return None, None
    
    def _validate_certificate(self, cert_path: str) -> bool:
        """Validate SSL certificate"""
        try:
            from cryptography import x509
            from cryptography.hazmat.primitives import serialization
            
            with open(cert_path, "rb") as cert_file:
                cert_data = cert_file.read()
                cert = x509.load_pem_x509_certificate(cert_data)
            
            # Check expiration
            now = datetime.utcnow()
            if cert.not_valid_after < now:
                logger.error("❌ SSL certificate has expired")
                return False
            
            if cert.not_valid_before > now:
                logger.error("❌ SSL certificate is not yet valid")
                return False
            
            # Check if certificate expires soon (30 days)
            expires_soon = now + timedelta(days=30)
            if cert.not_valid_after < expires_soon:
                logger.warning(f"⚠️ SSL certificate expires soon: {cert.not_valid_after}")
            
            logger.debug(f"✅ SSL certificate valid until: {cert.not_valid_after}")
            return True
            
        except ImportError:
            logger.warning("⚠️ cryptography library not available for certificate validation")
            return True  # Assume valid if we can't validate
        except Exception as e:
            logger.error(f"❌ Certificate validation failed: {e}")
            return False
    
    def get_uvicorn_ssl_config(self) -> Dict:
        """Get SSL configuration for Uvicorn server"""
        try:
            if not self.settings.use_https:
                return {}
            
            ssl_config = {}
            
            if self.settings.ssl_cert_path and self.settings.ssl_key_path:
                if os.path.exists(self.settings.ssl_cert_path) and os.path.exists(self.settings.ssl_key_path):
                    ssl_config = {
                        "ssl_certfile": self.settings.ssl_cert_path,
                        "ssl_keyfile": self.settings.ssl_key_path,
                        "ssl_version": ssl.PROTOCOL_TLS_SERVER,
                        "ssl_cert_reqs": ssl.CERT_NONE,
                        "ssl_ca_certs": None,
                        "ssl_ciphers": self.settings.ssl_ciphers if self.settings.ssl_ciphers else "TLSv1.2:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP:!CAMELLIA"
                    }
                    
                    logger.info("🔒 Uvicorn SSL configuration prepared")
                else:
                    logger.error("❌ SSL certificate files not found for Uvicorn")
            else:
                logger.warning("⚠️ SSL certificate paths not configured")
            
            return ssl_config
            
        except Exception as e:
            logger.error(f"❌ Uvicorn SSL configuration failed: {e}")
            return {}
    
    def check_tls_security(self, hostname: str = "localhost", port: int = 8000) -> Dict:
        """Check TLS security configuration"""
        try:
            security_info = {
                "tls_enabled": False,
                "tls_version": None,
                "cipher_suite": None,
                "certificate_valid": False,
                "certificate_expires": None,
                "security_score": 0,
                "recommendations": []
            }
            
            try:
                # Create SSL context for testing
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                # Connect and get SSL info
                with socket.create_connection((hostname, port), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        security_info["tls_enabled"] = True
                        security_info["tls_version"] = ssock.version()
                        security_info["cipher_suite"] = ssock.cipher()
                        
                        # Get certificate info
                        cert = ssock.getpeercert()
                        if cert:
                            security_info["certificate_valid"] = True
                            # Parse expiration date
                            not_after = cert.get("notAfter")
                            if not_after:
                                security_info["certificate_expires"] = not_after
                        
                        # Calculate security score
                        score = 0
                        if security_info["tls_version"] in ["TLSv1.3"]:
                            score += 40
                        elif security_info["tls_version"] in ["TLSv1.2"]:
                            score += 30
                        else:
                            score += 10
                        
                        if security_info["certificate_valid"]:
                            score += 30
                        
                        if security_info["cipher_suite"]:
                            cipher_name = security_info["cipher_suite"][0] if security_info["cipher_suite"] else ""
                            if "ECDHE" in cipher_name and "AES" in cipher_name:
                                score += 30
                            elif "AES" in cipher_name:
                                score += 20
                            else:
                                score += 10
                        
                        security_info["security_score"] = min(100, score)
                        
                        # Generate recommendations
                        recommendations = []
                        if security_info["tls_version"] not in ["TLSv1.3", "TLSv1.2"]:
                            recommendations.append("Upgrade to TLS 1.2 or 1.3")
                        
                        if not security_info["certificate_valid"]:
                            recommendations.append("Install valid SSL certificate")
                        
                        if security_info["security_score"] < 80:
                            recommendations.append("Review cipher suite configuration")
                        
                        security_info["recommendations"] = recommendations
                        
            except (socket.error, ssl.SSLError, ConnectionRefusedError):
                security_info["recommendations"] = ["Enable HTTPS/TLS encryption"]
            
            return security_info
            
        except Exception as e:
            logger.error(f"❌ TLS security check failed: {e}")
            return {"error": str(e)}
    
    def generate_security_report(self) -> Dict:
        """Generate comprehensive TLS security report"""
        try:
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "tls_configuration": {
                    "https_enabled": self.settings.use_https,
                    "min_tls_version": self.settings.tls_version_min,
                    "max_tls_version": self.settings.tls_version_max,
                    "cipher_suites": self.settings.ssl_ciphers,
                    "certificate_configured": bool(self.settings.ssl_cert_path and self.settings.ssl_key_path)
                },
                "security_headers": {
                    "hsts_enabled": self.settings.enable_security_headers,
                    "hsts_max_age": self.settings.hsts_max_age,
                    "security_headers_enabled": self.settings.enable_security_headers
                },
                "compliance": {
                    "pci_dss_compliant": self.settings.use_https and self.settings.tls_version_min in ["1.2", "1.3"],
                    "hipaa_compliant": self.settings.use_https and self.settings.tls_version_min == "1.2",
                    "gdpr_compliant": self.settings.use_https
                }
            }
            
            # Add runtime security check
            if self.settings.use_https:
                runtime_check = self.check_tls_security()
                report["runtime_security"] = runtime_check
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Security report generation failed: {e}")
            return {"error": str(e)}


# Global TLS service instance
tls_service = TLSConfigurationService()


# Export for use in other modules
__all__ = [
    "TLSConfigurationService",
    "tls_service"
]