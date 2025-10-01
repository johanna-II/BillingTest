"""Configuration for security tests."""

import logging
import os

import pytest

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def mock_server():
    """Start mock server for security tests if needed."""
    # Check if in CI environment
    is_ci = (
        os.environ.get("CI", "false").lower() == "true"
        or os.environ.get("GITHUB_ACTIONS", "false").lower() == "true"
    )

    # In CI, mock server should be started by workflow
    if is_ci:
        mock_url = f"http://localhost:{os.environ.get('MOCK_SERVER_PORT', '5000')}"
        logger.info(f"Using CI mock server at {mock_url}")
        yield mock_url
        return

    # For local development, check if USE_MOCK_SERVER is set
    use_mock = os.environ.get("USE_MOCK_SERVER", "false").lower() == "true"

    if not use_mock:
        # Skip if mock server is not explicitly enabled
        pytest.skip(
            "Security tests require mock server - use --use-mock or set USE_MOCK_SERVER=true"
        )

    # Start local mock server
    from tests.fixtures.mock_server import MockServerManager, find_free_port

    port = int(os.environ.get("MOCK_SERVER_PORT", "0"))
    if port == 0:
        port = find_free_port()

    manager = MockServerManager(port=port)

    try:
        manager.start()
        logger.info(f"Mock server started on {manager.url}")
        yield manager.url
    finally:
        manager.stop()
        logger.info("Mock server stopped")


@pytest.fixture(scope="session")
def mock_server_url(mock_server) -> str:
    """Provide mock server URL for tests."""
    return mock_server
