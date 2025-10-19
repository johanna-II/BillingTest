"""Configuration for contract tests."""

import os

import pytest


def pytest_configure(config):
    """Configure pytest for contract tests."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "consumer: marks tests as consumer contract tests"
    )
    config.addinivalue_line(
        "markers", "provider: marks tests as provider contract tests"
    )

    # Set environment for contract tests
    os.environ["PACT_DO_NOT_TRACK"] = "true"

    # Create necessary directories
    pact_dir = os.path.join(os.path.dirname(__file__), "pacts")
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(pact_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)


@pytest.fixture(scope="class")
def pact_dir():
    """Get pact directory."""
    return os.path.join(os.path.dirname(__file__), "pacts")
