# Test Execution Guide

## Overview

All tests are designed to run with a mock server to ensure consistency and isolation. The test infrastructure automatically manages mock server lifecycle.

## Test Categories

1. **Unit Tests** - Fast, isolated tests without external dependencies
2. **Integration Tests** - Tests with mock API interactions
3. **Contract Tests** - API contract verification tests
4. **Performance Tests** - Benchmark and load tests
5. **Security Tests** - Security vulnerability scans

## Running Tests

### Quick Start (Docker - Recommended)

```bash
# Run all tests
make test

# Run specific test category
make test-unit
make test-integration
make test-contracts

# Run with coverage
make test-coverage
```

### Local Execution

```bash
# Run locally (mock server starts automatically)
make test-local
make test-local-unit
make test-local-integration
```

### Direct Script Usage

```bash
# Docker execution
python scripts/run_tests.py            # All tests
python scripts/run_tests.py unit       # Unit tests only
python scripts/run_tests.py integration # Integration tests
python scripts/run_tests.py contracts  # Contract tests

# Local execution
python scripts/run_tests.py --local
python scripts/run_tests.py unit --local

# With coverage
python scripts/run_tests.py unit --coverage
```

## Mock Server

### Automatic Management

- **Docker**: Mock server starts automatically as a service dependency
- **Local**: Test runner starts/stops mock server automatically
- **Port**: 5000 (default)
- **Health Check**: http://localhost:5000/health

### Manual Control (Development)

```bash
# Start mock server manually
python -m mock_server.run_server

# Or with Docker
docker compose -f docker-compose.test.yml up mock-server
```

## Test Configuration

### Environment Variables

```bash
# Mock server configuration
USE_MOCK_SERVER=true
MOCK_SERVER_URL=http://localhost:5000
MOCK_SERVER_PORT=5000

# Force Docker rebuild (CI)
DOCKER_BUILD_NO_CACHE=true
```

### pytest Options

Tests automatically receive these flags:
- `--use-mock`: Enable mock server usage
- `-v`: Verbose output
- `--cov`: Coverage for unit tests

## Troubleshooting

### Mock Server Not Starting

1. Check port availability:
   ```bash
   lsof -i :5000  # Linux/Mac
   netstat -ano | findstr :5000  # Windows
   ```

2. Check Docker logs:
   ```bash
   docker compose -f docker-compose.test.yml logs mock-server
   ```

3. Rebuild images:
   ```bash
   make docker-build-no-cache
   ```

### Tests Skipped

If you see "Test requires mock server (use --use-mock to enable)":
- The test runner should automatically add `--use-mock`
- Check if mock server is healthy
- Verify environment variables are set

### Integration Test Failures

Common causes:
1. Mock server not responding
2. Network connectivity issues in Docker
3. Incorrect API endpoints

Debug steps:
```bash
# Check container network
docker compose -f docker-compose.test.yml ps

# Test mock server directly
curl http://localhost:5000/health

# View detailed logs
docker compose -f docker-compose.test.yml logs -f
```

## CI/CD Integration

GitHub Actions automatically:
1. Builds Docker images
2. Starts mock server
3. Runs test matrix (unit, integration, contracts)
4. Generates coverage reports
5. Uploads artifacts

See `.github/workflows/ci.yml` for details.

## Pact Python v3 Migration

The project uses Pact Python v3 (beta) for contract testing. Key points:

1. **New test files**:
   - `test_billing_consumer_v3.py` - Consumer contract tests
   - `test_billing_provider_v3.py` - Provider verification tests

2. **Legacy v2 files** (automatically skipped):
   - `test_billing_consumer.py`
   - `test_billing_provider.py`

3. **Running contract tests**:
   ```bash
   # All contract tests
   make test-contracts

   # Consumer tests only
   pytest tests/contracts/test_billing_consumer_v3.py -m consumer

   # Provider tests only
   pytest tests/contracts/test_billing_provider_v3.py -m provider
   ```

## Best Practices

1. **Always use mock server** for consistent results
2. **Run tests in Docker** for environment consistency
3. **Check coverage** to ensure code quality
4. **Fix failures immediately** to maintain CI health
5. **Add new tests** when fixing bugs or adding features
