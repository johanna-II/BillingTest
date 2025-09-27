# Billing Test System

[![CI/CD Pipeline](https://github.com/johanna-II/BillingTest/actions/workflows/ci.yml/badge.svg)](https://github.com/johanna-II/BillingTest/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/johanna-II/BillingTest/branch/main/graph/badge.svg)](https://codecov.io/gh/johanna-II/BillingTest)
[![Security Scan](https://github.com/johanna-II/BillingTest/actions/workflows/security.yml/badge.svg)](https://github.com/johanna-II/BillingTest/actions/workflows/security.yml)

Production-ready billing system test suite with comprehensive coverage and automated CI/CD pipeline.

## Features

- 🧪 Comprehensive test coverage for billing operations
- 🔒 Security scanning and vulnerability detection
- 🚀 Automated CI/CD with GitHub Actions
- 📊 Code coverage reporting with minimum 80% threshold
- 🐳 Docker containerization for consistent environments
- 📝 Type-safe Python with strict mypy checking
- 🖥️ Full cross-platform support (Windows, macOS, Linux)
- 🔧 Multiple test runners for different environments
~~~~
## Quick Start

### Prerequisites

- Python 3.11 or 3.12
- Poetry 2.2.1 or higher
- Docker and Docker Compose

### Installation

```bash
# Clone the repository
git clone https://github.com/johanna-II/BillingTest.git
cd BillingTest

# Install dependencies with Poetry
poetry install

# Or use pip
pip install -r requirements.txt
```

### Running Tests

> ⚠️ **Important**: Always use `--use-mock` option when running tests to avoid SSL certificate errors with internal servers.

#### Organized Test Structure

Tests are organized by category, each with its own run script:

**📁 Test Categories:**
- `tests/unit/` - Unit tests (no external dependencies)
- `tests/integration/` - Integration tests (requires mock server & `--use-mock`)
- `tests/performance/` - Performance tests (benchmarking)
- `tests/contracts/` - Contract tests (API contracts, requires `--use-mock`)
- `tests/security/` - Security tests (vulnerability scanning)

**🚀 Run All Tests:**
```bash
# Run all test categories with mock server (RECOMMENDED)
USE_MOCK_SERVER=true pytest --use-mock

# Run all test categories with appropriate test runner
python tests/run_all_tests.py --use-mock
```

**🧪 Run Specific Category:**
```bash
# Run unit tests (no mock needed)
python tests/unit/run.py

# Run integration tests (MUST use mock server)
USE_MOCK_SERVER=true pytest tests/integration --use-mock
# Or using the runner script (handles mock automatically)
python tests/integration/run.py

# Run performance tests (with mock for stable results)
USE_MOCK_SERVER=true pytest tests/performance --use-mock

# Using the test runner for specific categories
python tests/unit/run.py
python tests/integration/run.py --parallel 2
```

**⚡ Common Options:**
```bash
# Run with specific parallel workers
python tests/unit/run.py --parallel 4

# Run specific test files
python tests/unit/run.py test_calculation_unit.py

# Filter by keyword
python tests/integration/run.py -k "test_payment"

# Disable coverage
python tests/unit/run.py --no-coverage

# Set custom timeout
python tests/performance/run.py --timeout 600
```

**🛠️ Make Commands (if make is available):**
```bash
# Run unit tests with coverage
make test-coverage

# Run all checks (lint, security, tests)
make ci

# Run tests in Docker
make docker-test

# Clean and test
make dev-test
```

**Available Modes:**
- `default`: Sequential test execution with full output
- `parallel`: Moderate parallelization (CPU/2 workers)
- `safe`: Runs credit tests sequentially, then parallel for others
- `fast`: Maximum speed without coverage
- `ultra`: Aggressive parallelization with optimizations
- `super`: Maximum optimization for CI environments

#### Docker Test Execution

```bash
# Run tests in Docker (all platforms)
docker-compose -f docker-compose.test.yml run test-full

# Quick tests without coverage
docker-compose -f docker-compose.test.yml run test-quick

# Test on different Python versions
docker-compose -f docker-compose.test.yml run test-py311
docker-compose -f docker-compose.test.yml run test-py310

# Run integration tests with mock server
docker-compose -f docker-compose.test.yml up test-integration

# Run all test configurations
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

#### Manual Test Execution

```bash
# Run all tests with coverage
poetry run pytest --cov=libs --cov-report=term-missing

# Run specific test categories
poetry run pytest -m unit          # Unit tests only
poetry run pytest -m integration   # Integration tests only
poetry run pytest -m performance   # Performance tests only

# Run with mock server
poetry run pytest --use-mock --env alpha --member kr
```

### Docker Usage

```bash
# Build and run with Docker Compose
docker-compose up -d
docker-compose run BillingTest pytest

# Run specific member tests
docker-compose run BillingTest pytest --env alpha --member kr --month 2024-01
```

## Project Structure

```
BillingTest/
├── libs/                    # Core library code (coverage target)
│   ├── adjustment.py       # Billing adjustments
│   ├── Batch.py           # Batch processing
│   ├── calculation.py     # Billing calculations
│   ├── Contract.py        # Contract management
│   ├── Credit.py          # Credit operations
│   ├── Metering.py        # Usage metering
│   ├── Payments.py        # Payment processing
│   └── observability/     # Telemetry and monitoring
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── performance/       # Performance tests
│   ├── contracts/         # Contract tests
│   └── security/          # Security tests
├── mock_server/           # Mock API server
├── config/                # Configuration files
└── .github/workflows/     # CI/CD pipelines
```

## Code Coverage

Current coverage target: **80%**

To view detailed coverage report:

```bash
# Generate HTML coverage report
poetry run pytest --cov=libs --cov-report=html

# Open htmlcov/index.html in browser
```

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment:

### Main Pipeline (`ci.yml`)
- **Linting & Type Checking**: Black, Ruff, mypy, Bandit
- **Test Coverage**: Multi-version Python testing with 80% coverage requirement
- **Integration Tests**: Matrix testing across members and environments
- **Security Scanning**: Trivy vulnerability scanning
- **Docker Build & Push**: Automated image building for main branch

### Security Pipeline (`security.yml`)
- Weekly security scans
- Dependency vulnerability checks
- License compliance verification
- Docker image security scanning

### Scheduled Tests (`scheduled-tests.yml`)
- Daily full test suite execution
- Performance benchmarking
- Contract testing

## Development

### Code Style

The project enforces strict code quality standards:

```bash
# Format code
poetry run black .

# Lint code
poetry run ruff check .

# Type check
poetry run mypy libs --strict

# Security check
poetry run bandit -r libs
```

### Pre-commit Hooks

Install pre-commit hooks for automatic code quality checks:

```bash
poetry run pre-commit install
```

## Environment Variables

- `USE_MOCK_SERVER`: Enable mock server for testing (default: true)
- `PYTHON_VERSION`: Python version for CI/CD (default: 3.12)
- `MIN_COVERAGE`: Minimum coverage threshold (default: 80)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/johanna-II/BillingTest/issues) page.
