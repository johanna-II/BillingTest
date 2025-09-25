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


def pytest_collection_modifyitems(config, items):
    """Skip v2 tests when running v3 tests."""
    for item in items:
        # Skip deprecated v2 tests
        if "test_billing_consumer.py" in str(
            item.fspath
        ) or "test_billing_provider.py" in str(item.fspath):
            skip_marker = pytest.mark.skip(
                reason="Pact v2 tests are deprecated, use v3 tests"
            )
            item.add_marker(skip_marker)
