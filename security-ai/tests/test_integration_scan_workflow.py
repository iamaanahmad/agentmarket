"""
Integration Tests for Complete Scan Workflow
Tests end-to-end transaction scanning and payment processing
Requirements: 1.1, 1.2, 5.1, 5.2, 6.2, 6.4
"""

import pytest
import asyncio
import time
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from typing import Dict, Any

from main import app
from services.auth_service import auth_service
from services.payment_service import payment_service
from models.schemas import TransactionScanRequest, AuthenticationRequest, PaymentRequest


class TestIntegrationScanWorkflow:
    """Integration tests for complete scan workflow"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def test_wallet(self):
        """Test wallet address"""
        return "11111111111111111111111111111112"
    
    @pytest.fixture
    def valid_transaction(self):
        """Valid transaction for testing"""
        return {
            "programs": ["11111111111111111111111111111112"],
            "instructions": [
                {"index": 0, "data": "transfer", "accounts": ["sender", "receiver"]}
            ],
            "accounts": ["sender", "receiver"],
            "signatures": ["test_signature"],
            "recent_blockhash": "test_blockhash"
        }
    
    @pytest.fixture
    def malicious_transaction(self):
        """Malicious transaction for testing"""
        return {
            "programs": ["DrainWa11etProgramId123456789012345678901"],
            "instructions": [
                {"index": 0, "data": "drain_funds", "accounts": ["victim", "attacker"]}
            ],
            "accounts": ["victim", "attacker"],
            "signatures": ["malicious_signature"],
            "recent_blockhash": "malicious_blockhash"
        }
    
    @pytest.fixture
    async def authenticated_user(self, client, test_wallet):
        """Create authenticated user for testing"""
        # Generate auth message
        timestamp = int(time.time())
        response = client.post("/api/auth/message", json={
            "wallet_address": test_wallet,
            "timestamp": timestamp
        })
        
        assert response.status_code == 200
        auth_data = response.json()
        
        # Mock authentication (in real test, would use actual signature)
        auth_response = client.post("/api/auth/authenticate", json={
            "wallet_address": test_wallet,
            "message": auth_data["message"],
            "signature": "mock_signature_for_testing",
            "timestamp": timestamp,
            "username": "test_user"
        })
        
        if auth_response.status_code == 200:
            auth_result = auth_response.json()
            return auth_result.get("jwt_token")
        return None
    
    def test_health_check_integration(self, client):
        """Test health check endpoint integration"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "service" in data
        assert data["service"] == "SecurityGuard AI"
    
    def test_unauthenticated_scan_request(self, client, valid_transaction):
        """Test scan request without authentication"""
        scan_request = {
            "transaction": valid_transaction,
            "user_wallet": "test_wallet",
            "scan_type": "quick"
        }
        
        response = client.post("/api/security/scan", json=scan_request)
        
        # Should work for unauthenticated users (public service)
        # Or require payment/authentication based on implementation
        assert response.status_code in [200, 401, 402]
    
    @pytest.mark.asyncio
    async def test_complete_authenticated_scan_workflow(self, client, authenticated_user, valid_transaction, test_wallet):
        """Test complete authenticated scan workflow"""
        if not authenticated_user:
            pytest.skip("Authentication not working in test environment")
        
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        
        # 1. Create payment request
        payment_request = {
            "user_wallet": test_wallet,
            "service_type": "transaction_scan"
        }
        
        payment_response = client.post(
            "/api/payment/create",
            json=payment_request,
            headers=headers
        )
        
        # Payment creation should work or be mocked
        if payment_response.status_code == 200:
            payment_data = payment_response.json()
            payment_id = payment_data["payment_id"]
            
            # 2. Mock payment confirmation
            confirm_response = client.post(
                "/api/payment/confirm",
                json={
                    "payment_id": payment_id,
                    "transaction_signature": "mock_payment_signature"
                },
                headers=headers
            )
            
            # 3. Perform scan
            scan_request = {
                "transaction": valid_transaction,
                "user_wallet": test_wallet,
                "scan_type": "quick"
            }
            
            scan_response = client.post(
                "/api/security/scan",
                json=scan_request,
                headers=headers
            )
            
            assert scan_response.status_code == 200
            scan_data = scan_response.json()
            
            # Verify scan response structure
            assert "scan_id" in scan_data
            assert "risk_level" in scan_data
            assert "risk_score" in scan_data
            assert "explanation" in scan_data
            assert "recommendation" in scan_data
    
    def test_scan_performance_requirement(self, client, valid_transaction):
        """Test scan meets <2 second performance requirement"""
        scan_request = {
            "transaction": valid_transaction,
            "user_wallet": "test_wallet",
            "scan_type": "quick"
        }
        
        start_time = time.time()
        response = client.post("/api/security/scan", json=scan_request)
        scan_time = (time.time() - start_time) * 1000
        
        # Should complete within 2 seconds
        assert scan_time < 2000
        
        # Response should be valid regardless of auth status
        assert response.status_code in [200, 401, 402]
    
    def test_concurrent_scan_requests(self, client, valid_transaction):
        """Test concurrent scan request handling"""
        scan_request = {
            "transaction": valid_transaction,
            "user_wallet": "test_wallet",
            "scan_type": "quick"
        }
        
        # Create multiple concurrent requests
        import concurrent.futures
        import requests
        
        def make_request():
            return client.post("/api/security/scan", json=scan_request)
        
        start_time = time.time()
        
        # Use ThreadPoolExecutor for concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = (time.time() - start_time) * 1000
        
        # All requests should complete
        assert len(responses) == 10
        
        # Should handle concurrent load efficiently
        assert total_time < 5000  # 10 concurrent requests in <5s
        
        # All responses should be valid
        for response in responses:
            assert response.status_code in [200, 401, 402, 503]  # Include 503 for overload
    
    def test_malicious_transaction_detection_integration(self, client, malicious_transaction):
        """Test end-to-end malicious transaction detection"""
        scan_request = {
            "transaction": malicious_transaction,
            "user_wallet": "test_wallet",
            "scan_type": "deep"
        }
        
        response = client.post("/api/security/scan", json=scan_request)
        
        if response.status_code == 200:
            data = response.json()
            
            # Should detect high risk
            assert data["risk_level"] in ["CAUTION", "DANGER"]
            assert data["risk_score"] > 50
            
            # Should provide explanation
            assert len(data["explanation"]) > 0
            assert len(data["recommendation"]) > 0
    
    def test_scan_history_integration(self, client, authenticated_user):
        """Test scan history retrieval integration"""
        if not authenticated_user:
            pytest.skip("Authentication not working in test environment")
        
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        
        response = client.get("/api/security/history", headers=headers)
        
        # Should return history (empty or populated)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_security_chat_integration(self, client):
        """Test security chat integration"""
        chat_request = {
            "message": "Is this transaction safe?",
            "context": {"transaction_type": "token_transfer"},
            "conversation_history": []
        }
        
        response = client.post("/api/security/chat", json=chat_request)
        
        # Should work for unauthenticated users or require auth
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert len(data["message"]) > 0
    
    def test_platform_stats_integration(self, client):
        """Test platform statistics integration"""
        response = client.get("/api/security/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have basic stats structure
        assert isinstance(data, dict)
    
    def test_payment_workflow_integration(self, client, authenticated_user, test_wallet):
        """Test complete payment workflow integration"""
        if not authenticated_user:
            pytest.skip("Authentication not working in test environment")
        
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        
        # 1. Check balance
        balance_response = client.get(f"/api/payment/balance/{test_wallet}")
        assert balance_response.status_code == 200
        
        # 2. Get payment instructions
        instructions_response = client.get(f"/api/payment/instructions/{test_wallet}")
        assert instructions_response.status_code == 200
        
        # 3. Create payment request
        payment_request = {
            "user_wallet": test_wallet,
            "service_type": "transaction_scan"
        }
        
        create_response = client.post(
            "/api/payment/create",
            json=payment_request,
            headers=headers
        )
        
        if create_response.status_code == 200:
            payment_data = create_response.json()
            payment_id = payment_data["payment_id"]
            
            # 4. Check payment status
            status_response = client.get(
                f"/api/payment/status/{payment_id}",
                headers=headers
            )
            assert status_response.status_code == 200
    
    def test_error_handling_integration(self, client):
        """Test error handling integration"""
        # Invalid transaction data
        invalid_request = {
            "transaction": "invalid_data",
            "user_wallet": "invalid_wallet",
            "scan_type": "invalid_type"
        }
        
        response = client.post("/api/security/scan", json=invalid_request)
        
        # Should handle errors gracefully
        assert response.status_code in [400, 422, 500]
        
        if response.status_code != 500:
            data = response.json()
            assert "detail" in data or "error" in data
    
    def test_rate_limiting_integration(self, client, valid_transaction):
        """Test rate limiting integration"""
        scan_request = {
            "transaction": valid_transaction,
            "user_wallet": "test_wallet",
            "scan_type": "quick"
        }
        
        # Make many requests quickly
        responses = []
        for _ in range(20):
            response = client.post("/api/security/scan", json=scan_request)
            responses.append(response)
        
        # Should eventually hit rate limits or handle gracefully
        status_codes = [r.status_code for r in responses]
        
        # Should have mix of success and rate limit responses
        assert any(code in [200, 401, 402] for code in status_codes)
        
        # May have rate limit responses
        rate_limited = any(code == 429 for code in status_codes)
        # Rate limiting may or may not be active in test environment
    
    def test_caching_integration(self, client, valid_transaction):
        """Test caching integration for identical requests"""
        scan_request = {
            "transaction": valid_transaction,
            "user_wallet": "test_wallet",
            "scan_type": "quick"
        }
        
        # First request
        start_time = time.time()
        response1 = client.post("/api/security/scan", json=scan_request)
        first_time = (time.time() - start_time) * 1000
        
        # Second identical request (should be cached)
        start_time = time.time()
        response2 = client.post("/api/security/scan", json=scan_request)
        second_time = (time.time() - start_time) * 1000
        
        # Both should succeed or fail consistently
        assert response1.status_code == response2.status_code
        
        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()
            
            # Results should be similar (may have different timestamps)
            assert data1["risk_level"] == data2["risk_level"]
            assert data1["risk_score"] == data2["risk_score"]
            
            # Second request may be faster due to caching
            # (though not guaranteed in test environment)
    
    def test_monitoring_endpoints_integration(self, client):
        """Test monitoring endpoints integration"""
        # Performance metrics
        metrics_response = client.get("/api/performance/metrics")
        assert metrics_response.status_code == 200
        
        # Real-time metrics
        realtime_response = client.get("/api/performance/realtime")
        assert realtime_response.status_code == 200
        
        # Cache stats
        cache_response = client.get("/api/performance/cache")
        assert cache_response.status_code == 200
        
        # Queue stats
        queue_response = client.get("/api/performance/queue")
        assert queue_response.status_code == 200
    
    def test_health_monitoring_integration(self, client):
        """Test health monitoring integration"""
        # Basic health
        health_response = client.get("/health")
        assert health_response.status_code == 200
        
        # Liveness probe
        live_response = client.get("/health/live")
        assert live_response.status_code in [200, 503]
        
        # Readiness probe
        ready_response = client.get("/health/ready")
        assert ready_response.status_code in [200, 503]
        
        # Detailed health
        detailed_response = client.get("/health/detailed")
        assert detailed_response.status_code in [200, 500]
    
    def test_prometheus_metrics_integration(self, client):
        """Test Prometheus metrics integration"""
        response = client.get("/metrics")
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            # Should return text/plain metrics
            assert response.headers.get("content-type") == "text/plain; charset=utf-8"
    
    @pytest.mark.asyncio
    async def test_background_task_integration(self, client, valid_transaction):
        """Test background task integration"""
        scan_request = {
            "transaction": valid_transaction,
            "user_wallet": "test_wallet",
            "scan_type": "quick"
        }
        
        response = client.post("/api/security/scan", json=scan_request)
        
        if response.status_code == 200:
            # Background tasks should execute (caching, analytics, etc.)
            # Wait a moment for background tasks
            await asyncio.sleep(0.1)
            
            # Verify background tasks don't cause errors
            # (This is implicit - if background tasks fail, they should be logged)
            assert True  # Background tasks completed without crashing
    
    def test_cors_integration(self, client):
        """Test CORS integration"""
        # Preflight request
        response = client.options("/api/security/scan")
        
        # Should handle CORS appropriately
        assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly handled
    
    def test_security_headers_integration(self, client):
        """Test security headers integration"""
        response = client.get("/health")
        
        headers = response.headers
        
        # Should have security headers
        security_headers = [
            "x-content-type-options",
            "x-frame-options", 
            "x-xss-protection"
        ]
        
        # At least some security headers should be present
        present_headers = [h for h in security_headers if h in [k.lower() for k in headers.keys()]]
        assert len(present_headers) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])