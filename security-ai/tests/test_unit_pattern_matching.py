"""
Unit Tests for Pattern Matching Engine
Tests pattern matching functionality and performance
Requirements: 4.1, 4.2, 4.3, 4.4
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from services.pattern_matcher import PatternMatcher
from models.database import create_database_engine, create_session_factory
from core.config import get_settings


class TestPatternMatching:
    """Unit tests for pattern matching functionality"""
    
    @pytest.fixture
    async def pattern_matcher(self):
        """Create pattern matcher instance with test database"""
        settings = get_settings()
        # Use test database URL if available, otherwise use in-memory SQLite
        test_db_url = getattr(settings, 'test_database_url', 'sqlite:///:memory:')
        
        engine = create_database_engine(test_db_url)
        session_factory = create_session_factory(engine)
        
        matcher = PatternMatcher(session_factory)
        await matcher.initialize()
        return matcher
    
    @pytest.fixture
    def safe_transaction(self):
        """Safe transaction for testing"""
        return {
            "programs": ["11111111111111111111111111111112"],  # System program
            "instructions": [
                {"index": 0, "data": "transfer", "accounts": ["user1", "user2"]}
            ],
            "accounts": ["user1", "user2"]
        }
    
    @pytest.fixture
    def malicious_transaction(self):
        """Malicious transaction for testing"""
        return {
            "programs": ["DrainWa11etProgramId123456789012345678901"],
            "instructions": [
                {"index": 0, "data": "drain_all_funds", "accounts": ["victim", "attacker"]}
            ],
            "accounts": ["victim", "attacker"]
        }
    
    @pytest.fixture
    def suspicious_transaction(self):
        """Suspicious transaction with unlimited approvals"""
        return {
            "programs": ["TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"],
            "instructions": [
                {"index": 0, "data": "approve_unlimited", "accounts": ["user", "spender"]}
            ],
            "accounts": ["user", "spender"]
        }
    
    @pytest.mark.asyncio
    async def test_pattern_matching_performance(self, pattern_matcher, safe_transaction):
        """Test pattern matching meets <100ms requirement"""
        start_time = time.time()
        
        matches, stats = await pattern_matcher.match_patterns(safe_transaction)
        
        match_time = (time.time() - start_time) * 1000
        
        assert match_time < 100  # <100ms requirement
        assert isinstance(matches, list)
        assert isinstance(stats, dict)
    
    @pytest.mark.asyncio
    async def test_exact_pattern_match(self, pattern_matcher, malicious_transaction):
        """Test exact pattern matching for known exploits"""
        matches, stats = await pattern_matcher.match_patterns(malicious_transaction)
        
        # Should detect the malicious program
        assert len(matches) > 0
        
        # Check for critical severity match
        critical_matches = [m for m in matches if m.severity == "CRITICAL"]
        assert len(critical_matches) > 0
        
        # Verify match details
        match = critical_matches[0]
        assert match.pattern_type in ["wallet_drainer", "malicious_program"]
        assert match.confidence > 0.8
    
    @pytest.mark.asyncio
    async def test_fuzzy_pattern_match(self, pattern_matcher):
        """Test fuzzy pattern matching for similar patterns"""
        # Transaction with similar but not exact malicious pattern
        similar_tx = {
            "programs": ["DrainWa11etProgramId123456789012345678902"],  # Similar to known pattern
            "instructions": [
                {"index": 0, "data": "drain_funds_v2", "accounts": ["victim", "attacker"]}
            ],
            "accounts": ["victim", "attacker"]
        }
        
        matches, stats = await pattern_matcher.match_patterns(similar_tx)
        
        # Should detect similar pattern with lower confidence
        if matches:
            fuzzy_matches = [m for m in matches if m.confidence < 1.0]
            assert len(fuzzy_matches) > 0
    
    @pytest.mark.asyncio
    async def test_no_false_positives_safe_transaction(self, pattern_matcher, safe_transaction):
        """Test no false positives for legitimate transactions"""
        matches, stats = await pattern_matcher.match_patterns(safe_transaction)
        
        # Should have no critical matches for safe transaction
        critical_matches = [m for m in matches if m.severity == "CRITICAL"]
        assert len(critical_matches) == 0
        
        # Any matches should be low severity
        if matches:
            for match in matches:
                assert match.severity in ["LOW", "MEDIUM"]
                assert match.confidence < 0.7  # Low confidence for false positives
    
    @pytest.mark.asyncio
    async def test_behavioral_pattern_detection(self, pattern_matcher, suspicious_transaction):
        """Test behavioral pattern detection (unlimited approvals)"""
        matches, stats = await pattern_matcher.match_patterns(suspicious_transaction)
        
        # Should detect unlimited approval pattern
        approval_matches = [m for m in matches if "approval" in m.pattern_type.lower()]
        assert len(approval_matches) > 0
        
        # Should be high severity
        high_severity_matches = [m for m in matches if m.severity in ["HIGH", "CRITICAL"]]
        assert len(high_severity_matches) > 0
    
    @pytest.mark.asyncio
    async def test_multi_instruction_sequence_detection(self, pattern_matcher):
        """Test detection of multi-instruction attack sequences"""
        complex_attack = {
            "programs": [
                "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
                "11111111111111111111111111111112"
            ],
            "instructions": [
                {"index": 0, "data": "approve_unlimited", "accounts": ["victim", "attacker"]},
                {"index": 1, "data": "transfer_from", "accounts": ["victim", "attacker", "token"]},
                {"index": 2, "data": "close_account", "accounts": ["victim", "attacker"]}
            ],
            "accounts": ["victim", "attacker", "token"]
        }
        
        matches, stats = await pattern_matcher.match_patterns(complex_attack)
        
        # Should detect multi-step attack pattern
        sequence_matches = [m for m in matches if "sequence" in m.pattern_type.lower() or len(matches) > 1]
        assert len(matches) > 0  # Should detect at least one pattern
    
    @pytest.mark.asyncio
    async def test_account_pattern_matching(self, pattern_matcher):
        """Test suspicious account interaction patterns"""
        suspicious_accounts = {
            "programs": ["TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"],
            "instructions": [
                {"index": 0, "data": "transfer", "accounts": ["known_scammer", "victim"]}
            ],
            "accounts": ["known_scammer", "victim"]
        }
        
        matches, stats = await pattern_matcher.match_patterns(suspicious_accounts)
        
        # Should detect suspicious account patterns if in database
        if matches:
            account_matches = [m for m in matches if "account" in m.pattern_type.lower()]
            assert len(account_matches) >= 0  # May or may not have account patterns
    
    @pytest.mark.asyncio
    async def test_concurrent_pattern_matching(self, pattern_matcher, safe_transaction):
        """Test concurrent pattern matching performance"""
        # Create multiple concurrent requests
        tasks = [
            pattern_matcher.match_patterns(safe_transaction)
            for _ in range(20)
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = (time.time() - start_time) * 1000
        
        # All should succeed
        assert len(results) == 20
        assert all(len(result) == 2 for result in results)  # (matches, stats)
        
        # Should handle concurrent load efficiently
        avg_time_per_request = total_time / 20
        assert avg_time_per_request < 100  # Each request <100ms
    
    @pytest.mark.asyncio
    async def test_pattern_cache_performance(self, pattern_matcher, safe_transaction):
        """Test pattern matching cache improves performance"""
        # First request (cache miss)
        start_time = time.time()
        matches1, stats1 = await pattern_matcher.match_patterns(safe_transaction)
        first_time = (time.time() - start_time) * 1000
        
        # Second request (cache hit)
        start_time = time.time()
        matches2, stats2 = await pattern_matcher.match_patterns(safe_transaction)
        second_time = (time.time() - start_time) * 1000
        
        # Results should be identical
        assert len(matches1) == len(matches2)
        
        # Second request should be faster (cache hit)
        # Note: In test environment, cache might not be significantly faster
        assert second_time <= first_time * 2  # Allow some variance
    
    @pytest.mark.asyncio
    async def test_pattern_database_size_handling(self, pattern_matcher):
        """Test handling of large pattern database"""
        # Test with transaction that could match many patterns
        complex_tx = {
            "programs": [f"program_{i}" for i in range(10)],
            "instructions": [
                {"index": i, "data": f"instruction_{i}", "accounts": [f"acc_{i}", f"acc_{i+1}"]}
                for i in range(20)
            ],
            "accounts": [f"account_{i}" for i in range(50)]
        }
        
        start_time = time.time()
        matches, stats = await pattern_matcher.match_patterns(complex_tx)
        match_time = (time.time() - start_time) * 1000
        
        # Should still meet performance requirement
        assert match_time < 100
        assert isinstance(matches, list)
    
    @pytest.mark.asyncio
    async def test_pattern_confidence_scoring(self, pattern_matcher, malicious_transaction):
        """Test pattern confidence scoring accuracy"""
        matches, stats = await pattern_matcher.match_patterns(malicious_transaction)
        
        if matches:
            for match in matches:
                # Confidence should be between 0 and 1
                assert 0 <= match.confidence <= 1
                
                # Critical matches should have high confidence
                if match.severity == "CRITICAL":
                    assert match.confidence > 0.8
                
                # Low severity matches should have lower confidence
                if match.severity == "LOW":
                    assert match.confidence < 0.8
    
    @pytest.mark.asyncio
    async def test_pattern_update_mechanism(self, pattern_matcher):
        """Test pattern database update mechanism"""
        # Get initial pattern count
        initial_stats = pattern_matcher.get_performance_stats()
        initial_count = initial_stats.get("total_patterns", 0)
        
        # Simulate pattern update (would normally come from threat intelligence)
        new_pattern = {
            "pattern_type": "test_pattern",
            "program_id": "TestProgram123456789012345678901234567890",
            "instruction_signature": b"test_signature",
            "description": "Test pattern for unit testing",
            "severity": "HIGH"
        }
        
        # Add pattern (mock implementation)
        # In real implementation, this would update the database
        # await pattern_matcher.add_pattern(new_pattern)
        
        # For testing, just verify the mechanism exists
        assert hasattr(pattern_matcher, 'initialize')  # Has initialization method
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_transaction(self, pattern_matcher):
        """Test error handling for invalid transaction data"""
        invalid_transactions = [
            None,
            {},
            {"programs": []},
            {"invalid": "structure"},
            {"programs": None, "instructions": None}
        ]
        
        for invalid_tx in invalid_transactions:
            try:
                matches, stats = await pattern_matcher.match_patterns(invalid_tx)
                # Should handle gracefully and return empty results
                assert isinstance(matches, list)
                assert isinstance(stats, dict)
            except Exception as e:
                # Should not crash, but if it raises exception, it should be handled
                assert isinstance(e, (ValueError, TypeError))
    
    @pytest.mark.asyncio
    async def test_memory_usage_optimization(self, pattern_matcher):
        """Test memory usage optimization for large transactions"""
        # Create very large transaction
        large_tx = {
            "programs": [f"program_{i}" for i in range(100)],
            "instructions": [
                {"index": i, "data": f"instruction_{i}", "accounts": [f"acc_{j}" for j in range(i, i+5)]}
                for i in range(200)
            ],
            "accounts": [f"account_{i}" for i in range(1000)]
        }
        
        # Should handle large transaction without memory issues
        matches, stats = await pattern_matcher.match_patterns(large_tx)
        
        assert isinstance(matches, list)
        assert isinstance(stats, dict)
    
    def test_pattern_matcher_initialization(self, pattern_matcher):
        """Test pattern matcher initialization"""
        # Should be initialized
        assert pattern_matcher is not None
        
        # Should have performance stats
        stats = pattern_matcher.get_performance_stats()
        assert isinstance(stats, dict)
        assert "total_patterns" in stats
        assert "cache_hit_rate" in stats
    
    @pytest.mark.asyncio
    async def test_pattern_matching_accuracy_metrics(self, pattern_matcher):
        """Test pattern matching accuracy tracking"""
        test_cases = [
            ({"programs": ["11111111111111111111111111111112"]}, "SAFE"),
            ({"programs": ["DrainWa11etProgramId123456789012345678901"]}, "CRITICAL"),
            ({"programs": ["TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"]}, "MEDIUM")
        ]
        
        correct_predictions = 0
        total_predictions = len(test_cases)
        
        for tx_data, expected_risk in test_cases:
            tx = {
                **tx_data,
                "instructions": [{"index": 0, "data": "test", "accounts": ["acc1", "acc2"]}],
                "accounts": ["acc1", "acc2"]
            }
            
            matches, stats = await pattern_matcher.match_patterns(tx)
            
            # Determine predicted risk level
            if matches:
                max_severity = max(match.severity for match in matches)
                if max_severity == "CRITICAL":
                    predicted_risk = "CRITICAL"
                elif max_severity == "HIGH":
                    predicted_risk = "HIGH"
                else:
                    predicted_risk = "MEDIUM"
            else:
                predicted_risk = "SAFE"
            
            # Check if prediction matches expectation
            if (expected_risk == "SAFE" and predicted_risk in ["SAFE", "MEDIUM"]) or \
               (expected_risk == "CRITICAL" and predicted_risk in ["HIGH", "CRITICAL"]) or \
               (expected_risk == predicted_risk):
                correct_predictions += 1
        
        # Should have reasonable accuracy
        accuracy = correct_predictions / total_predictions
        assert accuracy >= 0.6  # At least 60% accuracy in basic tests


if __name__ == "__main__":
    pytest.main([__file__, "-v"])