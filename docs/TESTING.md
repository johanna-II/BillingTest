# Testing Guide

## Quick Start

### Run All Tests with Docker (Recommended)

```bash
python scripts/run_tests.py
# or
make test-docker
```

### Run Specific Tests with Docker

```bash
# Unit tests only
python scripts/run_tests.py unit

# Integration tests only
python scripts/run_tests.py integration

# Contract tests only
python scripts/run_tests.py contracts
```

### Run Tests Locally (Without Docker)

```bash
# All tests
python scripts/run_tests.py --local

# Specific tests
python scripts/run_tests.py unit --local
```

## Test Categories

- **Unit Tests**: Fast, isolated tests with no external dependencies
- **Integration Tests**: Tests with mock server for API integration
- **Contract Tests**: API contract validation tests

## CI/CD

Tests automatically run on:

- Push to `main` or `develop` branches
- Pull requests
- Manual workflow dispatch

The CI pipeline runs:

1. Linting and formatting checks
2. All test categories in parallel
3. Security scanning

## Make Targets

```bash
# Docker-based testing
make test-docker              # All tests
make test-docker-unit         # Unit tests only
make test-docker-integration  # Integration tests only
make test-docker-contracts    # Contract tests only

# Local testing (no Docker)
make test-local               # All tests locally
make test-local-unit          # Unit tests locally
make test-local-integration   # Integration tests locally

# Other commands
make lint                     # Run linter with auto-fix
make format                   # Format code
make clean                    # Clean cache files
```

## Mock Server

The mock server automatically starts when running integration or contract tests.
It provides API endpoints based on the OpenAPI specification in `docs/openapi/billing-api.yaml`.

## Troubleshooting

### Docker Issues

- Ensure Docker is installed and running
- The script automatically detects `docker compose` vs `docker-compose`

### Port Conflicts

- Mock server uses port 5000 by default
- Check if port is in use: `netstat -an | grep 5000`

### Test Failures

- Check mock server logs in Docker: `docker compose -f docker-compose.test.yml logs mock-server`
- Run with verbose output: Add `-v` flag to pytest commands
