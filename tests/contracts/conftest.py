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
    """Modify test collection based on configuration."""
    # Check if we should use v3 tests (opt-in via environment variable)
    use_v3_tests = os.environ.get("USE_PACT_V3", "false").lower() == "true"

    for item in items:
        if use_v3_tests:
            # If v3 is requested, skip v2 tests
            if "test_billing_consumer.py" in str(
                item.fspath
            ) or "test_billing_provider.py" in str(item.fspath):
                skip_marker = pytest.mark.skip(
                    reason="Using Pact v3 tests (USE_PACT_V3=true)"
                )
                item.add_marker(skip_marker)
        # If v3 is NOT requested (default), skip v3 tests
        elif "_v3.py" in str(item.fspath):
            skip_marker = pytest.mark.skip(
                reason="Pact v3 is beta - use USE_PACT_V3=true to enable v3 tests"
            )
            item.add_marker(skip_marker)
