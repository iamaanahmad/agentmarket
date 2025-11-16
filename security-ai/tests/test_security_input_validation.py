"""
Security Tests for Input Validation and Privacy Compliance
Tests input validation, sanitization, and privacy compliance
Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

import pytest
import json
import base64
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from main import app
from core.security_middleware import InputValidator
from services.privacy_service import privacy_service


class TestSecurityInputValidation:
    """Security tests for input validation and privacy compliance"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def input_validator(self):
        """Create input validator instance"""
        return InputValidator()
    
    # Input Validation Tests
    
    def test_solana_address_validation(self, input_validator):
        """Test Solana address validation"""
        valid_addresses = [
            "11111111111111111111111111111112",  # System program
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",  # Token program
            "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",  # Serum program
        ]
        
        invalid_addresses = [
            "",  # Empty
            "invalid_address",  # Too short
            "this_is_way_too_long_to_be_a_valid_solana_address_123456789012345678901234567890",  # Too long
            "contains_invalid_chars_!@#$%^&*()",  # Invalid characters
            "0x1234567890123456789012345678901234567890",  # Ethereum format
            None,  # Null
        ]
        
        # Test valid addresses
        for addr in valid_addresses:
            assert input_validator.validate_solana_address(addr), f"Valid address failed: {addr}"
        
        # Test invalid addresses
        for addr in invalid_addresses:
            assert not input_validator.validate_solana_address(addr), f"Invalid address passed: {addr}"
    
    def test_string_sanitization(self, input_validator):
        """Test string sanitization against XSS and injection"""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "../../../etc/passwd",
            "eval(malicious_code)",
            "<iframe src='javascript:alert(1)'></iframe>",
            "onload=alert('xss')",
            "{{7*7}}",  # Template injection
        ]
        
        for malicious_input in malicious_inputs:
            sanitized = input_validator.sanitize_string(malicious_input)
            
            # Should remove or escape dangerous content
            assert "<script>" not in sanitized.lower()
            assert "javascript:" not in sanitized.lower()
            assert "onerror=" not in sanitized.lower()
            assert "onload=" not in sanitized.lower()
            assert "drop table" not in sanitized.lower()
            assert "../" not in sanitized
            
            print(f"Sanitized '{malicious_input[:30]}...' -> '{sanitized[:30]}...'")
    
    def test_transaction_data_validation(self, client):
        """Test transaction data validation"""
        # Valid transaction structure
        valid_transaction = {
            "programs": ["11111111111111111111111111111112"],
            "instructions": [
                {"index": 0, "data": "transfer", "accounts": ["sender", "receiver"]}
            ],
            "accounts": ["sender", "receiver"]
        }
        
        scan_request = {
            "transaction": valid_transaction,
            "user_wallet": "11111111111111111111111111111112",
            "scan_type": "quick"
        }
        
        response = client.post("/api/security/scan", json=scan_request)
        
        # Should accept valid transaction
        assert response.status_code in [200, 401, 402]  # Valid structure
    
    def test_invalid_transaction_structures(self, client):
        """Test rejection of invalid transaction structures"""
        invalid_transactions = [
            # Missing required fields
            {"programs": []},
            {"instructions": []},
            {"accounts": []},
            
            # Wrong data types
            {"programs": "not_a_list", "instructions": [], "accounts": []},
            {"programs": [], "instructions": "not_a_list", "accounts": []},
            {"programs": [], "instructions": [], "accounts": "not_a_list"},
            
            # Null values
            {"programs": None, "instructions": None, "accounts": None},
            
            # Nested injection attempts
            {
                "programs": ["<script>alert('xss')</script>"],
                "instructions": [{"index": 0, "data": "'; DROP TABLE users; --", "accounts": []}],
                "accounts": ["../../../etc/passwd"]
            },
        ]
        
        for invalid_tx in invalid_transactions:
            scan_request = {
                "transaction": invalid_tx,
                "user_wallet": "test_wallet",
                "scan_type": "quick"
            }
            
            response = client.post("/api/security/scan", json=scan_request)
            
            # Should reject invalid structures
            assert response.status_code in [400, 422, 500]
    
    def test_request_size_limits(self, client):
        """Test request size limits"""
        # Create extremely large transaction
        huge_transaction = {
            "programs": [f"program_{i}" * 100 for i in range(1000)],  # Very long program names
            "instructions": [
                {
                    "index": i,
                    "data": "x" * 10000,  # Very long instruction data
                    "accounts": [f"account_{j}" * 50 for j in range(100)]
                }
                for i in range(500)
            ],
            "accounts": [f"account_{i}" * 100 for i in range(2000)]
        }
        
        scan_request = {
            "transaction": huge_transaction,
            "user_wallet": "test_wallet",
            "scan_type": "quick"
        }
        
        response = client.post("/api/security/scan", json=scan_request)
        
        # Should handle large requests appropriately
        assert response.status_code in [200, 401, 402, 413, 422, 500]  # 413 = Payload Too Large
    
    def test_base64_injection_protection(self, client):
        """Test protection against base64 injection attacks"""
        # Malicious payload encoded in base64
        malicious_payload = {
            "programs": ["<script>alert('xss')</script>"],
            "instructions": [{"index": 0, "data": "'; DROP TABLE users; --", "accounts": []}],
            "accounts": ["malicious_account"]
        }
        
        # Encode as base64
        json_str = json.dumps(malicious_payload)
        base64_payload = base64.b64encode(json_str.encode()).decode()
        
        scan_request = {
            "transaction": base64_payload,
            "user_wallet": "test_wallet",
            "scan_type": "quick"
        }
        
        response = client.post("/api/security/scan", json=scan_request)
        
        # Should handle base64 data safely
        if response.status_code == 200:
            data = response.json()
            response_text = json.dumps(data)
            
            # Should not contain unescaped malicious content
            assert "<script>" not in response_text
            assert "DROP TABLE" not in response_text
    
    def test_unicode_and_encoding_attacks(self, client):
        """Test protection against Unicode and encoding attacks"""
        unicode_attacks = [
            "\\u003cscript\\u003ealert('xss')\\u003c/script\\u003e",  # Unicode encoded script
            "%3Cscript%3Ealert('xss')%3C/script%3E",  # URL encoded script
            "\\x3cscript\\x3ealert('xss')\\x3c/script\\x3e",  # Hex encoded script
            "＜script＞alert('xss')＜/script＞",  # Full-width characters
            "scr\u0000ipt",  # Null byte injection
        ]
        
        for attack in unicode_attacks:
            chat_request = {
                "message": attack,
                "context": {},
                "conversation_history": []
            }
            
            response = client.post("/api/security/chat", json=chat_request)
            
            if response.status_code == 200:
                data = response.json()
                response_text = json.dumps(data)
                
                # Should not contain dangerous content
                assert "script" not in response_text.lower() or "sanitized" in response_text.lower()
    
    # Privacy Compliance Tests
    
    @pytest.mark.asyncio
    async def test_data_anonymization(self):
        """Test data anonymization for privacy compliance"""
        # Initialize privacy service
        await privacy_service.initialize()
        
        test_session_id = "test_session_privacy"
        sensitive_data = {
            "wallet_address": "11111111111111111111111111111112",
            "transaction_hash": "5j7s8K9mN2pQ3rT4uV5wX6yZ7a8B9c0D1e2F3g4H5i6J",
            "user_ip": "192.168.1.100",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        # Process data with privacy compliance
        result = await privacy_service.process_transaction_data(
            test_session_id,
            json.dumps(sensitive_data),
            sensitive_data["wallet_address"]
        )
        
        assert "anonymized" in result or "processed" in result
        
        # Verify sensitive data is not stored in plain text
        if "processed_data" in result:
            processed = result["processed_data"]
            
            # Should not contain full wallet address
            assert sensitive_data["wallet_address"] not in str(processed)
            
            # Should not contain full transaction hash
            assert sensitive_data["transaction_hash"] not in str(processed)
    
    @pytest.mark.asyncio
    async def test_session_data_isolation(self):
        """Test session data isolation"""
        await privacy_service.initialize()
        
        session1_id = "session_1_privacy_test"
        session2_id = "session_2_privacy_test"
        
        # Process data for different sessions
        data1 = {"user": "user1", "transaction": "tx1"}
        data2 = {"user": "user2", "transaction": "tx2"}
        
        result1 = await privacy_service.process_transaction_data(
            session1_id, json.dumps(data1), "wallet1"
        )
        
        result2 = await privacy_service.process_transaction_data(
            session2_id, json.dumps(data2), "wallet2"
        )
        
        # Sessions should be isolated
        assert result1 != result2
        
        # Get session summaries
        summary1 = await privacy_service.get_user_data_summary(session1_id)
        summary2 = await privacy_service.get_user_data_summary(session2_id)
        
        # Should not contain data from other sessions
        if "data_summary" in summary1 and "data_summary" in summary2:
            assert summary1["data_summary"] != summary2["data_summary"]
    
    @pytest.mark.asyncio
    async def test_data_retention_compliance(self):
        """Test data retention compliance"""
        await privacy_service.initialize()
        
        test_session_id = "retention_test_session"
        test_data = {"test": "data", "timestamp": "2024-01-01T00:00:00Z"}
        
        # Process data
        await privacy_service.process_transaction_data(
            test_session_id, json.dumps(test_data), "test_wallet"
        )
        
        # Verify data exists
        summary = await privacy_service.get_user_data_summary(test_session_id)
        assert "session_id" in summary
        
        # Test data deletion (right to be forgotten)
        deletion_result = await privacy_service.delete_user_session_data(test_session_id)
        assert deletion_result.get("success", False)
        
        # Verify data is deleted
        post_deletion_summary = await privacy_service.get_user_data_summary(test_session_id)
        assert "error" in post_deletion_summary or post_deletion_summary.get("data_found", True) is False
    
    def test_privacy_policy_endpoint(self, client):
        """Test privacy policy endpoint"""
        response = client.get("/api/privacy/policy")
        
        if response.status_code == 200:
            data = response.json()
            
            # Should have privacy policy sections
            required_sections = ["privacy_policy", "data_handling", "compliance"]
            present_sections = [s for s in required_sections if s in data]
            
            assert len(present_sections) > 0
            
            # Should mention GDPR/CCPA compliance
            policy_text = json.dumps(data).lower()
            assert "gdpr" in policy_text or "privacy" in policy_text
    
    def test_data_export_functionality(self, client):
        """Test data export for privacy compliance"""
        # Test without authentication (should fail)
        response = client.get("/api/analytics/export")
        assert response.status_code == 401
        
        # Test with invalid format
        response = client.get("/api/analytics/export?format=invalid")
        assert response.status_code in [400, 401, 422]
    
    def test_right_to_deletion(self, client):
        """Test right to deletion (GDPR Article 17)"""
        # Test without authentication (should fail)
        response = client.delete("/api/analytics/user")
        assert response.status_code == 401
    
    # Security Middleware Tests
    
    def test_sql_injection_prevention(self, client):
        """Test SQL injection prevention"""
        sql_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'/*",
            "' UNION SELECT * FROM users --",
            "1; DELETE FROM users WHERE 1=1 --",
        ]
        
        for payload in sql_payloads:
            # Test in various endpoints
            response = client.get(f"/api/payment/balance/{payload}")
            
            # Should not cause SQL errors
            assert response.status_code in [200, 400, 422]
            
            if response.status_code == 200:
                data = response.json()
                response_text = json.dumps(data).lower()
                
                # Should not contain SQL error messages
                sql_error_indicators = ["sql", "syntax error", "mysql", "postgresql", "sqlite"]
                assert not any(indicator in response_text for indicator in sql_error_indicators)
    
    def test_xss_prevention(self, client):
        """Test XSS prevention"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "';alert('xss');//",
            "<iframe src='javascript:alert(1)'></iframe>",
        ]
        
        for payload in xss_payloads:
            chat_request = {
                "message": payload,
                "context": {"test": payload},
                "conversation_history": []
            }
            
            response = client.post("/api/security/chat", json=chat_request)
            
            if response.status_code == 200:
                data = response.json()
                response_text = json.dumps(data)
                
                # Should not contain unescaped script content
                dangerous_patterns = ["<script>", "javascript:", "onerror=", "onload="]
                assert not any(pattern in response_text for pattern in dangerous_patterns)
    
    def test_csrf_protection(self, client):
        """Test CSRF protection measures"""
        # Test that state-changing operations require proper authentication
        state_changing_endpoints = [
            ("/api/payment/create", "POST"),
            ("/api/payment/confirm", "POST"),
            ("/api/analytics/user", "DELETE"),
        ]
        
        for endpoint, method in state_changing_endpoints:
            if method == "POST":
                response = client.post(endpoint, json={})
            elif method == "DELETE":
                response = client.delete(endpoint)
            
            # Should require authentication (CSRF protection)
            assert response.status_code in [401, 403, 422]
    
    def test_directory_traversal_prevention(self, client):
        """Test directory traversal prevention"""
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd",
        ]
        
        for payload in traversal_payloads:
            # Test in wallet address parameter
            response = client.get(f"/api/payment/balance/{payload}")
            
            # Should not access file system
            assert response.status_code in [200, 400, 422]
            
            if response.status_code == 200:
                data = response.json()
                response_text = json.dumps(data).lower()
                
                # Should not contain file system content
                file_indicators = ["root:", "administrator", "system32", "/etc/", "/bin/"]
                assert not any(indicator in response_text for indicator in file_indicators)
    
    def test_command_injection_prevention(self, client):
        """Test command injection prevention"""
        command_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /",
            "`whoami`",
            "$(id)",
            "; ping google.com",
        ]
        
        for payload in command_payloads:
            chat_request = {
                "message": f"Test message {payload}",
                "context": {},
                "conversation_history": []
            }
            
            response = client.post("/api/security/chat", json=chat_request)
            
            if response.status_code == 200:
                data = response.json()
                response_text = json.dumps(data).lower()
                
                # Should not contain command execution results
                command_indicators = ["uid=", "gid=", "total ", "drwx", "ping statistics"]
                assert not any(indicator in response_text for indicator in command_indicators)
    
    def test_header_injection_prevention(self, client):
        """Test HTTP header injection prevention"""
        # Test with malicious headers
        malicious_headers = {
            "X-Forwarded-For": "127.0.0.1\r\nX-Injected-Header: malicious",
            "User-Agent": "Mozilla/5.0\r\nX-Injected: attack",
            "Referer": "http://example.com\r\nSet-Cookie: malicious=true",
        }
        
        response = client.get("/health", headers=malicious_headers)
        
        # Should handle malicious headers safely
        assert response.status_code == 200
        
        # Response should not contain injected headers
        response_headers = dict(response.headers)
        assert "X-Injected-Header" not in response_headers
        assert "X-Injected" not in response_headers
    
    def test_content_type_validation(self, client):
        """Test content type validation"""
        # Test with various content types
        test_data = '{"transaction": {}, "user_wallet": "test", "scan_type": "quick"}'
        
        content_types = [
            "application/json",  # Valid
            "text/plain",  # Invalid
            "application/xml",  # Invalid
            "multipart/form-data",  # Invalid
            "application/javascript",  # Potentially dangerous
        ]
        
        for content_type in content_types:
            response = client.post(
                "/api/security/scan",
                data=test_data,
                headers={"Content-Type": content_type}
            )
            
            if content_type == "application/json":
                # Should accept valid JSON content type
                assert response.status_code in [200, 401, 402, 422]
            else:
                # Should reject invalid content types
                assert response.status_code in [415, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])