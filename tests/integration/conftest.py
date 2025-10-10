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

    # In CI or when mock server is not available, use mock server
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
        "use_mock_client": False,  # Always use actual mock server for better integration testing
        "test_timeout": int(os.environ.get("INTEGRATION_TEST_TIMEOUT", "300")),
        "parallel_workers": int(os.environ.get("INTEGRATION_WORKERS", "4")),
        "is_ci": is_ci,
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
    is_ci = integration_test_config.get("is_ci", False)

    # Get or create optimized server (reuses existing if available)
    manager = OptimizedMockServerManager.get_or_create(port=port)

    # Increase timeout for CI environment
    if is_ci:
        manager._startup_timeout = 60  # 60 seconds for CI
        manager._health_check_interval = 0.5
        logger.info("CI environment detected - using extended startup timeout")

    try:
        manager.start()
        logger.info(f"Mock server ready at {manager.url}")

        # Additional verification in CI
        if is_ci:
            import time

            time.sleep(2)  # Give extra time for server to stabilize
            if not manager._is_server_running():
                raise RuntimeError("Mock server health check failed after startup")

        yield manager.url
    except Exception as e:
        logger.exception(f"Failed to start mock server: {e}")
        # In CI, provide more debug info
        if is_ci and manager.process:
            if manager.process.stdout:
                stdout = manager.process.stdout.read()
                logger.error(f"Mock server stdout: {stdout.decode()}")
            if manager.process.stderr:
                stderr = manager.process.stderr.read()
                logger.error(f"Mock server stderr: {stderr.decode()}")
        raise
    finally:
        # Note: Shared servers are not stopped to improve performance
        # But in CI, we may want to clean up
        if not is_ci:
            pass  # Keep server running for reuse
        else:
            # In CI, consider cleanup based on environment variable
            if os.environ.get("CLEANUP_MOCK_SERVER", "false").lower() == "true":
                manager.stop()


@pytest.fixture(scope="function")
def api_client(mock_server, integration_test_config):
    """Create API client for integration tests.

    Function-scoped to ensure proper cleanup and isolation in parallel execution.
    """
    if integration_test_config["use_real_api"]:
        # Use real API client with environment configuration
        client = BillingAPIClient()
    else:
        # Use mock server - removed mock client logic for better integration testing
        if not mock_server:
            raise RuntimeError(
                "Mock server not available. Check if mock server started successfully."
            )

        base_url = mock_server
        if not base_url.endswith("/api/v1"):
            base_url = f"{base_url}"

        logger.info(f"Creating API client with base URL: {base_url}")
        client = BillingAPIClient(base_url=base_url)

    yield client

    # Cleanup: close client session safely
    try:
        if hasattr(client, "close"):
            client.close()
    except Exception as e:
        # Ignore cleanup errors to prevent worker crash
        logger.warning(f"Error during client cleanup: {e}")


@pytest.fixture
def clean_test_data(api_client):
    """Clean up test data before and after tests - Safely."""
    # Clean before test (with error handling)
    try:
        _cleanup_test_data(api_client)
    except Exception as e:
        logger.warning(f"Pre-test cleanup failed: {e}")

    yield

    # Clean after test (with error handling)
    try:
        _cleanup_test_data(api_client)
    except Exception as e:
        logger.warning(f"Post-test cleanup failed: {e}")


def _cleanup_test_data(client) -> None:
    """Helper to clean test data - Safe implementation."""
    # Skip cleanup if client is not available
    if client is None or not hasattr(client, "session"):
        return
    # Minimal cleanup to prevent worker crashes
    # In parallel mode, cleanup can cause conflicts


@pytest.fixture(scope="function")
def test_billing_group(worker_id) -> str:
    """Test billing group ID - unique per test worker in parallel mode.

    Function-scoped for better isolation in parallel execution.

    Args:
        worker_id: Unique worker identifier from pytest-xdist

    Returns:
        Unique billing group ID for this worker
    """
    import time

    # Add timestamp to ensure uniqueness even within same worker
    timestamp = int(time.time() * 1000) % 100000  # Last 5 digits
    base_id = os.environ.get("TEST_BILLING_GROUP", "bg-integration-test")
    return f"{base_id}-{worker_id}-{timestamp}"


@pytest.fixture(scope="function")
def test_app_keys(worker_id):
    """Test application keys - unique per test worker in parallel mode.

    Function-scoped for better isolation in parallel execution.

    Args:
        worker_id: Unique worker identifier from pytest-xdist

    Returns:
        List of unique app keys for this worker
    """
    import time

    timestamp = int(time.time() * 1000) % 100000
    return [
        f"app-integration-001-{worker_id}-{timestamp}",
        f"app-integration-002-{worker_id}-{timestamp}",
        f"app-integration-003-{worker_id}-{timestamp}",
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
