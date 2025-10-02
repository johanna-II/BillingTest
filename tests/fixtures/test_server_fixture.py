"""Common mock server fixture for performance and security tests."""

import logging
import os
from collections.abc import Generator

import pytest

logger = logging.getLogger(__name__)


def create_mock_server_fixture(
    test_type: str, rate_limit: int | None = None, skip_message: str | None = None
) -> Generator[str, None, None]:
    """Create mock server fixture with configurable settings.

    Args:
        test_type: Type of test (e.g., "performance", "security")
        rate_limit: Optional rate limit to set (req/sec)
        skip_message: Custom skip message if mock server is not available

    Yields:
        Mock server URL
    """
    # Set rate limit if specified
    if rate_limit is not None:
        os.environ["MOCK_SERVER_RATE_LIMIT"] = str(rate_limit)
        logger.info(f"Set rate limit to {rate_limit} req/sec for {test_type} tests")

    # Check if in CI environment
    is_ci = (
        os.environ.get("CI", "false").lower() == "true"
        or os.environ.get("GITHUB_ACTIONS", "false").lower() == "true"
    )

    # In CI, mock server should be started by workflow
    if is_ci:
        mock_url = f"http://localhost:{os.environ.get('MOCK_SERVER_PORT', '5000')}"
        rate_info = f" with rate limit {rate_limit} req/sec" if rate_limit else ""
        logger.info(f"Using CI mock server at {mock_url}{rate_info}")
        yield mock_url
        return

    # For local development, check if USE_MOCK_SERVER is set
    use_mock = os.environ.get("USE_MOCK_SERVER", "false").lower() == "true"

    if not use_mock:
        # Skip if mock server is not explicitly enabled
        default_message = (
            f"{test_type.capitalize()} tests require mock server - "
            "use --use-mock or set USE_MOCK_SERVER=true"
        )
        pytest.skip(skip_message or default_message)

    # Start local mock server
    from tests.fixtures.mock_server import MockServerManager, find_free_port

    port = int(os.environ.get("MOCK_SERVER_PORT", "0"))
    if port == 0:
        port = find_free_port()

    manager = MockServerManager(port=port)

    try:
        manager.start()
        logger.info(f"Mock server started on {manager.url} for {test_type} tests")
        yield manager.url
    finally:
        manager.stop()
        logger.info(f"Mock server stopped for {test_type} tests")
