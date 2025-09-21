import os
import pytest

# Import mock server fixture if mock mode is enabled
if os.environ.get("USE_MOCK_SERVER", "false").lower() == "true":
    try:
        from test_with_mock import mock_server
    except ImportError:
        from .test_with_mock import mock_server

# Load telemetry plugin - commented out for now as it's optional
# pytest_plugins = ["tests.pytest_telemetry"]

# Load standard test fixtures
pytest_plugins = ["tests.fixtures.test_data"]


def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="alpha", help="alpha, beta")
    parser.addoption("--member", action="store", default="kr", help="kr, jp and etc")
    parser.addoption(
        "--month", action="store", default="2021-05", help="test target month"
    )
    parser.addoption(
        "--use-mock", action="store_true", default=False, 
        help="Use mock server instead of real APIs"
    )


@pytest.fixture(scope="class")
def env(request):
    return request.config.getoption("--env")


@pytest.fixture(scope="class")
def member(request):
    return request.config.getoption("--member")


@pytest.fixture(scope="class")
def month(request):
    return request.config.getoption("--month")


def pytest_configure(config):
    """Set up mock server if --use-mock option is provided."""
    if config.getoption("--use-mock"):
        os.environ["USE_MOCK_SERVER"] = "true"
        print("Mock server mode enabled")


def pytest_unconfigure(config):
    """Clean up mock server environment."""
    os.environ.pop("USE_MOCK_SERVER", None)
