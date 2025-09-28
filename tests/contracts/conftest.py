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

    # Additional safety check for CI environments
    is_ci = any(
        os.environ.get(var, "false").lower() == "true"
        for var in ["CI", "CONTINUOUS_INTEGRATION", "JENKINS", "GITHUB_ACTIONS"]
    )

    # Check if we should skip all Pact tests
    skip_pact_tests = os.environ.get("SKIP_PACT_TESTS", "false").lower() == "true"

    # In CI, force disable v3 tests unless explicitly enabled
    if is_ci and not use_v3_tests:
        use_v3_tests = False
        print("CI environment detected: Pact v3 tests will be skipped")
        print(
            f"CI environment variables: CI={os.environ.get('CI')}, GITHUB_ACTIONS={os.environ.get('GITHUB_ACTIONS')}"
        )

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
