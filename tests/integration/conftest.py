"""Configuration for integration tests."""

import pytest
import os
import sys
import time
import subprocess
from contextlib import contextmanager

from libs.http_client import BillingAPIClient

# Add project root to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.fixture(scope="session")
def integration_test_config():
    """Configuration specific to integration tests."""
    from tests.fixtures.mock_server import find_free_port
    
    # Use dynamic port for mock server to avoid conflicts in parallel execution
    default_port = find_free_port() if not os.environ.get('MOCK_SERVER_PORT') else os.environ.get('MOCK_SERVER_PORT')
    
    return {
        'mock_server_port': int(default_port),
        'mock_server_url': os.environ.get('MOCK_SERVER_URL', f'http://localhost:{default_port}'),
        'use_real_api': os.environ.get('USE_REAL_API', 'false').lower() == 'true',
        'test_timeout': int(os.environ.get('INTEGRATION_TEST_TIMEOUT', '300')),
        'parallel_workers': int(os.environ.get('INTEGRATION_WORKERS', '4'))
    }


@pytest.fixture(scope="session")
def mock_server(integration_test_config):
    """Start mock server for integration tests if needed."""
    if integration_test_config['use_real_api']:
        # Using real API, no mock server needed
        yield None
        return
    
    from tests.fixtures.mock_server import MockServerManager
    
    # Use the configured port
    port = integration_test_config['mock_server_port']
    mock_url = f"http://localhost:{port}"
    
    # Check if mock server is already running (e.g., manually started)
    try:
        import requests
        response = requests.get(f"{mock_url}/health", timeout=2)
        if response.status_code == 200:
            # Mock server already running
            yield mock_url
            return
    except:
        pass
    
    # Start mock server with manager
    manager = MockServerManager(port=port)
    manager.start()
    
    yield mock_url
    
    # Cleanup
    manager.stop()


@pytest.fixture(scope="class")
def api_client(mock_server, integration_test_config):
    """Create API client for integration tests."""
    if integration_test_config['use_real_api']:
        # Use real API client with environment configuration
        return BillingAPIClient()
    else:
        # Use mock server
        base_url = f"{mock_server}/api/v1"
        return BillingAPIClient(base_url=base_url)


@pytest.fixture
def clean_test_data(api_client):
    """Clean up test data before and after tests."""
    # Clean before test
    _cleanup_test_data(api_client)
    
    yield
    
    # Clean after test
    _cleanup_test_data(api_client)


def _cleanup_test_data(client):
    """Helper to clean test data."""
    # This would call appropriate cleanup endpoints
    # For now, it's a placeholder
    pass


@pytest.fixture(scope="class")
def test_billing_group():
    """Test billing group ID - unique per test worker in parallel mode."""
    # Include worker ID for parallel test isolation
    worker_id = os.environ.get('PYTEST_XDIST_WORKER', 'master')
    base_id = os.environ.get('TEST_BILLING_GROUP', 'bg-integration-test')
    return f"{base_id}-{worker_id}"


@pytest.fixture(scope="class") 
def test_app_keys():
    """Test application keys - unique per test worker in parallel mode."""
    # Include worker ID for parallel test isolation
    worker_id = os.environ.get('PYTEST_XDIST_WORKER', 'master')
    return [
        f'app-integration-001-{worker_id}',
        f'app-integration-002-{worker_id}',
        f'app-integration-003-{worker_id}'
    ]


@pytest.fixture
def wait_for_calculation():
    """Helper fixture to wait for calculations to complete."""
    def _wait(timeout=60):
        """Wait for calculation to complete."""
        time.sleep(2)  # Simple wait for now
        # In real implementation, would poll calculation status
    return _wait


# Markers for integration tests
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_mock: mark test as requiring mock server"
    )
    config.addinivalue_line(
        "markers", "requires_real_api: mark test as requiring real API"
    )
