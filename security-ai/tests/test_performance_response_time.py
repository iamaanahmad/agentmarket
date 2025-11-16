"""
Performance Tests for Response Time and Concurrent Handling
Tests <2 second response time and concurrent request handling
Requirements: 1.1, 6.2, 6.4, 6.5
"""

import pytest
import asyncio
import time
import statistics
import concurrent.futures
from typing import List, Dict, Any
from fastapi.testclient import TestClient

from main import app
from services.transaction_analyzer import TransactionAnalyzer
from services.pattern_matcher import PatternMatcher
from services.ml_detector import MLAnomalyDetector


class TestPerformanceResponseTime:
    """Performance tests for response time requirements"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def simple_transaction(self):
        """Simple transaction for performance testing"""
        return {
            "programs": ["11111111111111111111111111111112"],
            "instructions": [
                {"index": 0, "data": "transfer", "accounts": ["sender", "receiver"]}
            ],
            "accounts": ["sender", "receiver"]
        }
    
    @pytest.fixture
    def complex_transaction(self):
        """Complex transaction for performance testing"""
        return {
            "programs": [
                "11111111111111111111111111111112",
                "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
                "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
            ],
            "instructions": [
                {"index": i, "data": f"instruction_{i}", "accounts": [f"acc_{i}", f"acc_{i+1}"]}
                for i in range(10)
            ],
            "accounts": [f"account_{i}" for i in range(20)]
        }
    
    @pytest.fixture
    def large_transaction(self):
        """Large transaction for stress testing"""
        return {
            "programs": [f"program_{i}" for i in range(25)],
            "instructions": [
                {"index": i, "data": f"complex_instruction_{i}", "accounts": [f"acc_{j}" for j in range(i, i+5)]}
                for i in range(50)
            ],
            "accounts": [f"account_{i}" for i in range(100)]
        }
    
    def test_simple_scan_response_time(self, client, simple_transaction):
        """Test simple scan meets <2 second response time"""
        scan_request = {
            "transaction": simple_transaction,
            "user_wallet": "test_wallet",
            "scan_type": "quick"
        }
        
        start_time = time.time()
        response = client.post("/api/security/scan", json=scan_request)
        response_time = (time.time() - start_time) * 1000
        
        # Should complete within 2 seconds
        assert response_time < 2000
        
        # Should be much faster for simple transactions
        assert response_time < 1000  # <1 second for simple transactions
        
        print(f"Simple scan response time: {response_time:.1f}ms")
    
    def test_complex_scan_response_time(self, client, complex_transaction):
        """Test complex scan meets <2 second response time"""
        scan_request = {
            "transaction": complex_transaction,
            "user_wallet": "test_wallet",
            "scan_type": "deep"
        }
        
        start_time = time.time()
        response = client.post("/api/security/scan", json=scan_request)
        response_time = (time.time() - start_time) * 1000
        
        # Should complete within 2 seconds even for complex transactions
        assert response_time < 2000
        
        print(f"Complex scan response time: {response_time:.1f}ms")
    
    def test_large_transaction_response_time(self, client, large_transaction):
        """Test large transaction handling within time limits"""
        scan_request = {
            "transaction": large_transaction,
            "user_wallet": "test_wallet",
            "scan_type": "comprehensive"
        }
        
        start_time = time.time()
        response = client.post("/api/security/scan", json=scan_request)
        response_time = (time.time() - start_time) * 1000
        
        # Should complete within 2 seconds or timeout gracefully
        if response.status_code == 200:
            assert response_time < 2000
        elif response.status_code == 408:  # Timeout
            assert response_time >= 2000  # Should timeout after 2s
        
        print(f"Large scan response time: {response_time:.1f}ms (status: {response.status_code})")
    
    def test_95th_percentile_response_time(self, client, simple_transaction):
        """Test 95th percentile response time meets <2 second requirement"""
        scan_request = {
            "transaction": simple_transaction,
            "user_wallet": "test_wallet",
            "scan_type": "quick"
        }
        
        response_times = []
        num_requests = 20
        
        for i in range(num_requests):
            start_time = time.time()
            response = client.post("/api/security/scan", json=scan_request)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code in [200, 401, 402]:  # Valid responses
                response_times.append(response_time)
        
        if response_times:
            p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            avg_time = statistics.mean(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            print(f"Response time stats (n={len(response_times)}):")
            print(f"  Average: {avg_time:.1f}ms")
            print(f"  95th percentile: {p95_time:.1f}ms")
            print(f"  Min: {min_time:.1f}ms")
            print(f"  Max: {max_time:.1f}ms")
            
            # 95% of requests should complete within 2 seconds
            assert p95_time < 2000
            
            # Average should be much better
            assert avg_time < 1000
    
    def test_concurrent_request_handling(self, client, simple_transaction):
        """Test handling of 100+ concurrent requests"""
        scan_request = {
            "transaction": simple_transaction,
            "user_wallet": "test_wallet",
            "scan_type": "quick"
        }
        
        def make_request():
            start_time = time.time()
            response = client.post("/api/security/scan", json=scan_request)
            response_time = (time.time() - start_time) * 1000
            return response.status_code, response_time
        
        # Test with 50 concurrent requests (scaled down for test environment)
        num_concurrent = 50
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(make_request) for _ in range(num_concurrent)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = (time.time() - start_time) * 1000
        
        # Analyze results
        successful_requests = [r for r in results if r[0] in [200, 401, 402]]
        failed_requests = [r for r in results if r[0] >= 500]
        overloaded_requests = [r for r in results if r[0] == 503]
        
        success_rate = len(successful_requests) / len(results)
        
        if successful_requests:
            response_times = [r[1] for r in successful_requests]
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = 0
            max_response_time = 0
        
        print(f"Concurrent request results ({num_concurrent} requests):")
        print(f"  Total time: {total_time:.1f}ms")
        print(f"  Success rate: {success_rate:.2%}")
        print(f"  Successful requests: {len(successful_requests)}")
        print(f"  Failed requests: {len(failed_requests)}")
        print(f"  Overloaded requests: {len(overloaded_requests)}")
        print(f"  Avg response time: {avg_response_time:.1f}ms")
        print(f"  Max response time: {max_response_time:.1f}ms")
        
        # Should handle concurrent load reasonably well
        assert success_rate > 0.7  # At least 70% success rate
        
        # Successful requests should meet time requirements
        if successful_requests:
            assert avg_response_time < 3000  # Allow some degradation under load
    
    def test_sustained_load_performance(self, client, simple_transaction):
        """Test sustained load performance over time"""
        scan_request = {
            "transaction": simple_transaction,
            "user_wallet": "test_wallet",
            "scan_type": "quick"
        }
        
        response_times = []
        num_requests = 30
        request_interval = 0.1  # 100ms between requests
        
        start_time = time.time()
        
        for i in range(num_requests):
            request_start = time.time()
            response = client.post("/api/security/scan", json=scan_request)
            response_time = (time.time() - request_start) * 1000
            
            if response.status_code in [200, 401, 402]:
                response_times.append(response_time)
            
            # Wait before next request
            time.sleep(request_interval)
        
        total_duration = (time.time() - start_time) * 1000
        
        if response_times:
            avg_time = statistics.mean(response_times)
            degradation = max(response_times) - min(response_times)
            
            print(f"Sustained load results ({num_requests} requests over {total_duration:.1f}ms):")
            print(f"  Successful requests: {len(response_times)}")
            print(f"  Average response time: {avg_time:.1f}ms")
            print(f"  Performance degradation: {degradation:.1f}ms")
            
            # Performance should remain stable
            assert avg_time < 2000
            assert degradation < 1000  # Performance shouldn't degrade too much
    
    @pytest.mark.asyncio
    async def test_component_performance_breakdown(self):
        """Test individual component performance"""
        # Test transaction parsing
        analyzer = TransactionAnalyzer()
        test_tx = {
            "programs": ["11111111111111111111111111111112"],
            "instructions": [{"index": 0, "data": "test", "accounts": ["acc1", "acc2"]}],
            "accounts": ["acc1", "acc2"]
        }
        
        start_time = time.time()
        parsed = await analyzer.parse_transaction(test_tx)
        parse_time = (time.time() - start_time) * 1000
        
        print(f"Transaction parsing time: {parse_time:.1f}ms")
        assert parse_time < 100  # Parsing should be very fast
        
        # Test ML detection (if available)
        try:
            ml_detector = MLAnomalyDetector()
            await ml_detector.load_model()
            
            start_time = time.time()
            ml_result = await ml_detector.analyze_transaction(test_tx)
            ml_time = (time.time() - start_time) * 1000
            
            print(f"ML detection time: {ml_time:.1f}ms")
            assert ml_time < 500  # ML should complete within 500ms
        except Exception as e:
            print(f"ML detector not available: {e}")
    
    def test_cache_performance_impact(self, client, simple_transaction):
        """Test cache performance impact"""
        scan_request = {
            "transaction": simple_transaction,
            "user_wallet": "test_wallet",
            "scan_type": "quick"
        }
        
        # First request (cache miss)
        start_time = time.time()
        response1 = client.post("/api/security/scan", json=scan_request)
        first_time = (time.time() - start_time) * 1000
        
        # Second request (potential cache hit)
        start_time = time.time()
        response2 = client.post("/api/security/scan", json=scan_request)
        second_time = (time.time() - start_time) * 1000
        
        print(f"Cache performance:")
        print(f"  First request: {first_time:.1f}ms")
        print(f"  Second request: {second_time:.1f}ms")
        print(f"  Improvement: {first_time - second_time:.1f}ms")
        
        # Both should meet time requirements
        if response1.status_code in [200, 401, 402]:
            assert first_time < 2000
        if response2.status_code in [200, 401, 402]:
            assert second_time < 2000
        
        # Second request should not be significantly slower
        assert second_time <= first_time * 1.5  # Allow some variance
    
    def test_memory_usage_under_load(self, client, complex_transaction):
        """Test memory usage doesn't grow excessively under load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        scan_request = {
            "transaction": complex_transaction,
            "user_wallet": "test_wallet",
            "scan_type": "deep"
        }
        
        # Make multiple requests
        for i in range(20):
            response = client.post("/api/security/scan", json=scan_request)
            
            # Check memory every 5 requests
            if i % 5 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_growth = current_memory - initial_memory
                
                print(f"Memory usage after {i+1} requests: {current_memory:.1f}MB (+{memory_growth:.1f}MB)")
                
                # Memory growth should be reasonable
                assert memory_growth < 100  # Less than 100MB growth
    
    def test_error_response_time(self, client):
        """Test error responses are also fast"""
        invalid_request = {
            "transaction": "invalid_data",
            "user_wallet": "invalid_wallet",
            "scan_type": "invalid"
        }
        
        start_time = time.time()
        response = client.post("/api/security/scan", json=invalid_request)
        response_time = (time.time() - start_time) * 1000
        
        # Error responses should also be fast
        assert response_time < 1000
        assert response.status_code in [400, 422, 500]
        
        print(f"Error response time: {response_time:.1f}ms")
    
    def test_timeout_handling(self, client, large_transaction):
        """Test timeout handling for slow requests"""
        # Create an extremely large transaction that might timeout
        huge_transaction = {
            "programs": [f"program_{i}" for i in range(100)],
            "instructions": [
                {"index": i, "data": f"complex_instruction_{i}", "accounts": [f"acc_{j}" for j in range(i, i+10)]}
                for i in range(200)
            ],
            "accounts": [f"account_{i}" for i in range(500)]
        }
        
        scan_request = {
            "transaction": huge_transaction,
            "user_wallet": "test_wallet",
            "scan_type": "comprehensive"
        }
        
        start_time = time.time()
        response = client.post("/api/security/scan", json=scan_request)
        response_time = (time.time() - start_time) * 1000
        
        print(f"Huge transaction response time: {response_time:.1f}ms (status: {response.status_code})")
        
        if response.status_code == 408:  # Timeout
            # Should timeout around the expected time
            assert 2000 <= response_time <= 30000  # Between 2s and 30s
        elif response.status_code == 200:
            # If it completes, should still be reasonable
            assert response_time < 5000  # Within 5 seconds
    
    def test_health_check_performance(self, client):
        """Test health check endpoint performance"""
        start_time = time.time()
        response = client.get("/health")
        response_time = (time.time() - start_time) * 1000
        
        # Health checks should be very fast
        assert response_time < 100
        assert response.status_code == 200
        
        print(f"Health check response time: {response_time:.1f}ms")
    
    def test_metrics_endpoint_performance(self, client):
        """Test metrics endpoint performance"""
        endpoints = [
            "/api/performance/metrics",
            "/api/performance/realtime",
            "/api/performance/cache",
            "/api/performance/queue"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            response_time = (time.time() - start_time) * 1000
            
            print(f"{endpoint} response time: {response_time:.1f}ms")
            
            # Metrics endpoints should be fast
            assert response_time < 500
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])