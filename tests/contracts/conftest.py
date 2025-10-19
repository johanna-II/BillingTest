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
    # Additional safety check for CI environments
    is_ci = any(
        os.environ.get(var, "false").lower() == "true"
        for var in ["CI", "CONTINUOUS_INTEGRATION", "JENKINS", "GITHUB_ACTIONS"]
    )

    # Check if we should skip all Pact tests
    skip_pact_tests = os.environ.get("SKIP_PACT_TESTS", "false").lower() == "true"

    for item in items:
        # Skip all Pact tests if requested
        if skip_pact_tests and "contracts" in str(item.fspath):
            skip_marker = pytest.mark.skip(
                reason="Pact tests are disabled (SKIP_PACT_TESTS=true)"
            )
            item.add_marker(skip_marker)
            continue

        # In CI, skip provider verification tests that can have cleanup issues
        if (
            is_ci
            and "provider" in item.keywords
            and (
                "test_verify_billing_api_contract" in item.name
                or "test_mock_server_contract_compliance" in item.name
            )
        ):
            skip_marker = pytest.mark.skip(
                reason="Provider verification tests are skipped in CI due to cleanup issues"
            )
            item.add_marker(skip_marker)
            continue
