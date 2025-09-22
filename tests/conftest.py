"""
Pytest configuration and fixtures for billing test suite.

This module provides:
- Command-line options for test configuration
- Global fixtures for test setup
- Mock server integration
- Test environment configuration
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Optional

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.fixtures import SubRequest

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestConfig:
    """Test configuration container."""
    env: str
    member: str
    month: str
    use_mock: bool
    
    @property
    def is_production(self) -> bool:
        """Check if testing against production environment."""
        return self.env in {"prod", "production"}
    
    @property
    def should_skip_destructive(self) -> bool:
        """Check if destructive tests should be skipped."""
        return self.is_production and not self.use_mock


# Plugin configuration
pytest_plugins = [
    "tests.fixtures.test_data",
    # Uncomment to enable telemetry
    # "tests.pytest_telemetry",
]


def pytest_addoption(parser: Parser) -> None:
    """
    Add custom command-line options.
    
    Args:
        parser: Pytest argument parser
    """
    # Environment options
    parser.addoption(
        "--env",
        action="store",
        default="alpha",
        choices=["alpha", "beta", "staging", "prod"],
        help="Target environment (default: alpha)"
    )
    
    parser.addoption(
        "--member",
        action="store",
        default="kr",
        choices=["kr", "jp", "us", "eu", "etc"],
        help="Member country code (default: kr)"
    )
    
    parser.addoption(
        "--month",
        action="store",
        default="2021-05",
        help="Test target month in YYYY-MM format (default: 2021-05)"
    )
    
    # Mock options
    parser.addoption(
        "--use-mock",
        action="store_true",
        default=False,
        help="Use mock server instead of real APIs"
    )
    
    parser.addoption(
        "--mock-port",
        action="store",
        default="5000",
        help="Mock server port (default: 5000)"
    )
    
    # Test behavior options
    parser.addoption(
        "--skip-slow",
        action="store_true",
        default=False,
        help="Skip slow tests"
    )
    
    parser.addoption(
        "--run-destructive",
        action="store_true",
        default=False,
        help="Run destructive tests (use with caution)"
    )


def pytest_configure(config: Config) -> None:
    """
    Configure pytest with custom settings.
    
    Args:
        config: Pytest configuration object
    """
    # Register custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "destructive: marks tests that modify/delete data"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "mock_required: marks tests that require mock server"
    )
    config.addinivalue_line(
        "markers", "performance: marks performance tests"
    )
    
    # Set up environment
    if config.getoption("--use-mock"):
        os.environ["USE_MOCK_SERVER"] = "true"
        os.environ["MOCK_SERVER_PORT"] = config.getoption("--mock-port")
        logger.info(f"Mock server mode enabled on port {os.environ['MOCK_SERVER_PORT']}")
    
    # Log test configuration
    logger.info(
        f"Test configuration: "
        f"env={config.getoption('--env')}, "
        f"member={config.getoption('--member')}, "
        f"month={config.getoption('--month')}, "
        f"use_mock={config.getoption('--use-mock')}"
    )


def pytest_unconfigure(config: Config) -> None:
    """
    Clean up after pytest execution.
    
    Args:
        config: Pytest configuration object
    """
    # Clean up environment variables
    os.environ.pop("USE_MOCK_SERVER", None)
    os.environ.pop("MOCK_SERVER_PORT", None)
    
    logger.info("Test execution completed, environment cleaned up")


def pytest_collection_modifyitems(config: Config, items: list[pytest.Item]) -> None:
    """
    Modify test collection based on configuration.
    
    Args:
        config: Pytest configuration object
        items: List of collected test items
    """
    skip_slow = config.getoption("--skip-slow")
    skip_destructive = not config.getoption("--run-destructive")
    use_mock = config.getoption("--use-mock")
    
    for item in items:
        # Skip slow tests if requested
        if skip_slow and "slow" in item.keywords:
            skip_marker = pytest.mark.skip(reason="Skipping slow tests")
            item.add_marker(skip_marker)
        
        # Skip destructive tests unless explicitly allowed
        if skip_destructive and "destructive" in item.keywords:
            skip_marker = pytest.mark.skip(
                reason="Skipping destructive tests (use --run-destructive to enable)"
            )
            item.add_marker(skip_marker)
        
        # Skip tests requiring mock when not using mock
        if not use_mock and "mock_required" in item.keywords:
            skip_marker = pytest.mark.skip(
                reason="Test requires mock server (use --use-mock to enable)"
            )
            item.add_marker(skip_marker)


# Global fixtures
@pytest.fixture(scope="session")
def test_config(request: SubRequest) -> TestConfig:
    """
    Provide test configuration as a single object.
    
    Args:
        request: Pytest request object
        
    Returns:
        TestConfig instance with all configuration values
    """
    return TestConfig(
        env=request.config.getoption("--env"),
        member=request.config.getoption("--member"),
        month=request.config.getoption("--month"),
        use_mock=request.config.getoption("--use-mock")
    )


@pytest.fixture(scope="session")
def env(test_config: TestConfig) -> str:
    """
    Provide environment name.
    
    Args:
        test_config: Test configuration
        
    Returns:
        Environment name
    """
    return test_config.env


@pytest.fixture(scope="session")
def member(test_config: TestConfig) -> str:
    """
    Provide member country code.
    
    Args:
        test_config: Test configuration
        
    Returns:
        Member country code
    """
    return test_config.member


@pytest.fixture(scope="session")
def month(test_config: TestConfig) -> str:
    """
    Provide test target month.
    
    Args:
        test_config: Test configuration
        
    Returns:
        Target month in YYYY-MM format
    """
    return test_config.month


@pytest.fixture(scope="session")
def use_mock(test_config: TestConfig) -> bool:
    """
    Provide mock usage flag.
    
    Args:
        test_config: Test configuration
        
    Returns:
        True if using mock server
    """
    return test_config.use_mock


# Mock server fixture
@pytest.fixture(scope="session")
def mock_server(use_mock: bool) -> Optional[Generator[str, None, None]]:
    """
    Start and stop mock server for tests.
    
    Args:
        use_mock: Whether to use mock server
        
    Yields:
        Mock server URL if enabled, None otherwise
    """
    if not use_mock:
        yield None
        return
    
    # Import mock server management
    try:
        from tests.fixtures.mock_server import MockServerManager
        
        port = int(os.environ.get("MOCK_SERVER_PORT", "5000"))
        manager = MockServerManager(port=port)
        
        # Start server
        manager.start()
        logger.info(f"Mock server started on {manager.url}")
        
        yield manager.url
        
        # Stop server
        manager.stop()
        logger.info("Mock server stopped")
        
    except ImportError:
        logger.warning("Mock server fixtures not available")
        yield None


# Test data fixtures
@pytest.fixture(scope="session")
def sample_uuid() -> str:
    """Provide a sample UUID for testing."""
    return "123e4567-e89b-12d3-a456-426614174000"


@pytest.fixture(scope="session")
def sample_campaign_id() -> str:
    """Provide a sample campaign ID for testing."""
    return "CAMP-2021-TEST-001"


@pytest.fixture(scope="session")
def sample_payment_group_id() -> str:
    """Provide a sample payment group ID for testing."""
    return "PG-2021-05-001"


# Utility fixtures
@pytest.fixture
def temp_config_file(tmp_path: Path) -> Path:
    """
    Create a temporary configuration file.
    
    Args:
        tmp_path: Pytest temporary path fixture
        
    Returns:
        Path to temporary configuration file
    """
    config_file = tmp_path / "test_config.json"
    config_file.write_text("""{
        "uuid": "test-uuid",
        "billing_group_id": "test-bg-001",
        "project_id": ["proj-001"],
        "campaign_id": ["camp-001"]
    }""")
    return config_file


@pytest.fixture(autouse=True)
def reset_environment():
    """
    Reset environment variables before each test.
    
    This fixture automatically runs before each test to ensure
    a clean environment state.
    """
    # Store original environment
    original_env = os.environ.copy()
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# Performance monitoring fixture
@pytest.fixture
def performance_monitor():
    """
    Monitor test performance.
    
    Yields:
        Performance monitor instance
    """
    import time
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.measurements = {}
        
        def start(self, name: str):
            self.start_time = time.time()
            self.current_name = name
        
        def stop(self):
            if self.start_time:
                elapsed = time.time() - self.start_time
                self.measurements[self.current_name] = elapsed
                logger.info(f"Performance: {self.current_name} took {elapsed:.3f}s")
        
        def get_measurement(self, name: str) -> Optional[float]:
            return self.measurements.get(name)
    
    monitor = PerformanceMonitor()
    yield monitor
    
    # Log all measurements at the end
    if monitor.measurements:
        logger.info(f"Performance summary: {monitor.measurements}")


# Shared test utilities
@pytest.fixture
def assert_api_response():
    """
    Provide API response assertion helper.
    
    Returns:
        Assertion function
    """
    def _assert_response(response: dict, expected_status: str = "SUCCESS"):
        assert "header" in response, "Response missing header"
        assert response["header"].get("isSuccessful", False), \
            f"API request failed: {response['header'].get('resultMessage', 'Unknown error')}"
        
        if "status" in response:
            assert response["status"] == expected_status, \
                f"Expected status {expected_status}, got {response['status']}"
    
    return _assert_response