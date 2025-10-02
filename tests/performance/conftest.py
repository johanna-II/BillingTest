"""Configuration for performance tests."""

import pytest

from tests.fixtures.test_server_fixture import create_mock_server_fixture


@pytest.fixture(scope="session")
def mock_server():
    """Start mock server for performance tests if needed.

    Uses high rate limit (500 req/sec) for performance testing.
    """
    yield from create_mock_server_fixture(test_type="performance", rate_limit=500)


@pytest.fixture(scope="session")
def mock_server_url(mock_server) -> str:
    """Provide mock server URL for tests."""
    return mock_server
