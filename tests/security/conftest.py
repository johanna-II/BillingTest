"""Configuration for security tests."""

import pytest

from tests.fixtures.test_server_fixture import create_mock_server_fixture


@pytest.fixture(scope="session")
def mock_server():
    """Start mock server for security tests if needed.

    Uses low rate limit (50 req/sec) for rate limiting tests.
    """
    yield from create_mock_server_fixture(test_type="security", rate_limit=50)


@pytest.fixture(scope="session")
def mock_server_url(mock_server) -> str:
    """Provide mock server URL for tests."""
    return mock_server
