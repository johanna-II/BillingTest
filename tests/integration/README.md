# Integration Tests

This directory contains integration tests for the billing system.

## Overview

Integration tests verify the interaction between different components of the billing system, including:

- Billing workflows (contracts, metering, calculations, payments)
- Adjustment management
- Credit management
- Payment processing
- Batch operations

## Running Integration Tests

### Quick Start

```bash
# Run all integration tests with mock server
python -m pytest tests/integration/ --use-mock -v

# Or use the optimized runner
python tests/integration/run_integration_tests.py
```

### Using the Integration Test Runner

The `run_integration_tests.py` script provides optimized test execution:

```bash
# Run tests in parallel (faster)
python tests/integration/run_integration_tests.py --parallel

# Run specific test file
python tests/integration/run_integration_tests.py -f test_billing_workflows.py

# Run specific test function
python tests/integration/run_integration_tests.py -k test_standard_billing_cycle

# Run with coverage report
python tests/integration/run_integration_tests.py --coverage

# Skip slow tests
python tests/integration/run_integration_tests.py --slow
```

### Manual Test Execution

```bash
# Basic execution
pytest tests/integration/ --use-mock

# Parallel execution (requires pytest-xdist)
pytest tests/integration/ --use-mock -n 4

# With coverage
pytest tests/integration/ --use-mock --cov=libs --cov-report=html

# Run specific test class
pytest tests/integration/test_billing_workflows.py::TestBillingWorkflows --use-mock

# Run with verbose output
pytest tests/integration/ --use-mock -v --tb=short
```

## Test Structure

### Base Integration Test Class

All integration tests inherit from `BaseIntegrationTest` which provides:

- Common fixtures for API clients and managers
- Test data cleanup
- Assertion helpers
- Consistent test context

Example:

```python
from tests.integration.base_integration import BaseIntegrationTest

class TestMyFeature(BaseIntegrationTest):
    def test_feature(self, test_context, test_app_keys):
        managers = test_context["managers"]
        # Your test logic here
```

### Available Fixtures

- `test_context`: Complete test context with managers and configuration
- `test_app_keys`: Unique application keys for testing
- `api_clients`: Billing and Payment API clients
- `month`: Test month (from command line or default)
- `member`: Test member/region (from command line or default)

## Mock Server Optimization

The integration tests use an optimized mock server that:

- Reuses server instances across tests
- Supports parallel test execution
- Provides faster startup times
- Uses connection pooling

## Writing New Integration Tests

1. Create a new test file in `tests/integration/`
2. Import and inherit from `BaseIntegrationTest`
3. Use the provided fixtures and managers
4. Follow the naming convention: `test_<feature>_<scenario>`

Example:

```python
import pytest
from tests.integration.base_integration import BaseIntegrationTest

@pytest.mark.integration
@pytest.mark.mock_required
class TestNewFeature(BaseIntegrationTest):

    def test_basic_scenario(self, test_context, test_app_keys):
        """Test description."""
        managers = test_context["managers"]

        # Setup
        result = managers["contract"].apply_contract(
            contract_id="test-001",
            name="Test Contract"
        )
        self.assert_api_success(result)

        # Test logic
        # ...

        # Assertions
        assert expected == actual
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Use Base Class**: Always inherit from `BaseIntegrationTest`
3. **Cleanup**: The base class handles cleanup automatically
4. **Assertions**: Use `self.assert_api_success()` for API responses
5. **Test Data**: Use fixtures for test data generation
6. **Parallel Safety**: Ensure tests can run in parallel

## Troubleshooting

### Tests are Skipped

- Make sure to use `--use-mock` flag
- Check if mock server is running

### Mock Server Issues

- Check port availability (default: 5000)
- Look for server logs in console output
- Try running with a different port: `--mock-port 5001`

### Slow Tests

- Use parallel execution: `-n auto`
- Skip slow tests: `-m "not slow"`
- Use the optimized runner script

### Test Failures

- Check mock server health: `curl http://localhost:5000/health`
- Verify test data setup
- Look for cleanup issues between tests
