"""
Pytest configuration and shared fixtures for SecurityGuard AI tests
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_database():
    """Mock database for testing"""
    return Mock()

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.exists.return_value = False
    return mock_redis

@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    from core.config import Settings
    
    settings = Settings()
    settings.database_url = "sqlite:///:memory:"
    settings.redis_url = "redis://localhost:6379/1"
    settings.debug = True
    settings.max_request_size_mb = 10
    settings.data_retention_hours = 0
    settings.session_timeout_minutes = 30
    
    return settings

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, mock_settings):
    """Setup test environment with mocked dependencies"""
    # Mock settings
    monkeypatch.setattr("core.config.get_settings", lambda: mock_settings)
    
    # Mock external services that might not be available in test environment
    monkeypatch.setattr("services.claude_explainer.ClaudeExplainer.initialize", AsyncMock())
    monkeypatch.setattr("services.ml_detector.MLAnomalyDetector.load_model", AsyncMock())
    
    # Mock Redis operations
    mock_redis_client = AsyncMock()
    mock_redis_client.get.return_value = None
    mock_redis_client.set.return_value = True
    monkeypatch.setattr("redis.asyncio.Redis", lambda **kwargs: mock_redis_client)

# Test markers
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "frontend: mark test as a frontend/user acceptance test"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file names"""
    for item in items:
        # Add markers based on test file names
        if "test_unit_" in item.fspath.basename:
            item.add_marker(pytest.mark.unit)
        elif "test_integration_" in item.fspath.basename:
            item.add_marker(pytest.mark.integration)
        elif "test_performance_" in item.fspath.basename:
            item.add_marker(pytest.mark.performance)
        elif "test_security_" in item.fspath.basename:
            item.add_marker(pytest.mark.security)
        elif "test_user_acceptance_" in item.fspath.basename:
            item.add_marker(pytest.mark.frontend)