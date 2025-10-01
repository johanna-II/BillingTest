"""Configuration for integration tests."""

import logging
import os
import sys
import time

import pytest

from libs.http_client import BillingAPIClient

# Add project root to sys.path for imports
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def use_mock(request) -> bool:
    """Override global use_mock fixture for integration tests.

    In CI environment, automatically enable mock mode.
    Otherwise, use the command-line option.
    """
    is_ci = (
        os.environ.get("CI", "false").lower() == "true"
        or os.environ.get("GITHUB_ACTIONS", "false").lower() == "true"
    )

    if is_ci:
        # Always use mock in CI
        logger.info("CI environment detected - forcing use_mock=True")
        return True

    # Use command-line option
    return request.config.getoption("--use-mock", default=False)


@pytest.fixture(scope="session")
def integration_test_config():
    """Configuration specific to integration tests."""
    from tests.fixtures.mock_server import find_free_port

    # Use dynamic port for mock server to avoid conflicts in parallel execution
    default_port = (
        find_free_port()
        if not os.environ.get("MOCK_SERVER_PORT")
        else os.environ.get("MOCK_SERVER_PORT")
    )

    # In CI or when mock server is not available, use mock client instead
    # Check if we're in CI environment
    is_ci = (
        os.environ.get("CI", "false").lower() == "true"
        or os.environ.get("GITHUB_ACTIONS", "false").lower() == "true"
    )

    # Use real API only if explicitly requested AND not in CI
    use_real_api = (
        os.environ.get("USE_REAL_API", "false").lower() == "true" and not is_ci
    )

    return {
        "mock_server_port": int(default_port),
        "mock_server_url": os.environ.get(
            "MOCK_SERVER_URL", f"http://localhost:{default_port}"
        ),
        "use_real_api": use_real_api,
        "use_mock_client": is_ci,  # Use mock client in CI instead of mock server
        "test_timeout": int(os.environ.get("INTEGRATION_TEST_TIMEOUT", "300")),
        "parallel_workers": int(os.environ.get("INTEGRATION_WORKERS", "4")),
    }


@pytest.fixture(scope="session")
def mock_server(integration_test_config):
    """Start mock server for integration tests if needed."""
    if integration_test_config["use_real_api"]:
        # Using real API, no mock server needed
        yield None
        return

    # Use optimized mock server for better performance
    from tests.fixtures.optimized_mock_server import OptimizedMockServerManager

    # Use the configured port
    port = integration_test_config["mock_server_port"]

    # Get or create optimized server (reuses existing if available)
    manager = OptimizedMockServerManager.get_or_create(port=port)

    try:
        manager.start()
        logger.info(f"Mock server ready at {manager.url}")
        yield manager.url
    except Exception:
        logger.exception("Failed to start mock server")
        raise
    finally:
        # Note: Shared servers are not stopped to improve performance
        pass


@pytest.fixture(scope="class")
def api_client(mock_server, integration_test_config):
    """Create API client for integration tests."""
    if integration_test_config["use_real_api"]:
        # Use real API client with environment configuration
        return BillingAPIClient()

    if integration_test_config.get("use_mock_client", False):
        # Use mock client in CI to avoid server dependencies
        from unittest.mock import Mock

        mock_client = Mock(spec=BillingAPIClient)
        # Setup standard mock responses
        mock_client.post.return_value = {
            "header": {
                "isSuccessful": True,
                "resultCode": "0",
                "resultMessage": "SUCCESS",
            },
            "status": "SUCCESS",
            "id": "MOCK-ID-001",
        }
        mock_client.get.return_value = {
            "header": {
                "isSuccessful": True,
                "resultCode": "0",
                "resultMessage": "SUCCESS",
            },
            "status": "SUCCESS",
            "data": [],
        }
        mock_client.put.return_value = {
            "header": {
                "isSuccessful": True,
                "resultCode": "0",
                "resultMessage": "SUCCESS",
            },
            "status": "SUCCESS",
        }
        mock_client.delete.return_value = {
            "header": {
                "isSuccessful": True,
                "resultCode": "0",
                "resultMessage": "SUCCESS",
            },
            "status": "SUCCESS",
        }
        return mock_client

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


def _cleanup_test_data(client) -> None:
    """Helper to clean test data."""
    # This would call appropriate cleanup endpoints
    # For now, it's a placeholder


@pytest.fixture(scope="class")
def test_billing_group() -> str:
    """Test billing group ID - unique per test worker in parallel mode."""
    # Include worker ID for parallel test isolation
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
    base_id = os.environ.get("TEST_BILLING_GROUP", "bg-integration-test")
    return f"{base_id}-{worker_id}"


@pytest.fixture(scope="class")
def test_app_keys():
    """Test application keys - unique per test worker in parallel mode."""
    # Include worker ID for parallel test isolation
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
    return [
        f"app-integration-001-{worker_id}",
        f"app-integration-002-{worker_id}",
        f"app-integration-003-{worker_id}",
    ]


@pytest.fixture
def wait_for_calculation():
    """Helper fixture to wait for calculations to complete."""

    def _wait(timeout=60) -> None:
        """Wait for calculation to complete."""
        time.sleep(2)  # Simple wait for now
        # In real implementation, would poll calculation status

    return _wait


# Markers for integration tests
def pytest_configure(config) -> None:
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line(
        "markers", "requires_mock: mark test as requiring mock server"
    )
    config.addinivalue_line(
        "markers", "requires_real_api: mark test as requiring real API"
    )
