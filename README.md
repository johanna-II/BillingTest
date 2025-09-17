# BillingTest

<!-- CI/CD Badges -->
<!-- markdownlint-disable MD033 -->
<div align="center">

[![CI](https://img.shields.io/github/actions/workflow/status/johanna-II/BillingTest/ci.yml?branch=main&label=CI&logo=github&color=success&logoColor=white&labelColor=0d1117)](https://github.com/johanna-II/BillingTest/actions/workflows/ci.yml)
[![Security](https://img.shields.io/github/actions/workflow/status/johanna-II/BillingTest/security.yml?branch=main&label=Security&logo=github&color=success&logoColor=white&labelColor=0d1117)](https://github.com/johanna-II/BillingTest/actions/workflows/security.yml)
[![codecov](https://img.shields.io/codecov/c/github/johanna-II/BillingTest?logo=codecov&logoColor=white&labelColor=0d1117)](https://codecov.io/gh/johanna-II/BillingTest)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=BillingTest&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=johanna-II_BillingTest)

<!-- Language & Tools -->
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg?logo=python&logoColor=white&labelColor=0d1117)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/Poetry-1.7.1-blue.svg?logo=poetry&logoColor=white&labelColor=0d1117)](https://python-poetry.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?labelColor=0d1117)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/badge/linter-ruff-FCC21B.svg?logo=ruff&logoColor=white&labelColor=0d1117)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/type%20checker-mypy-blue.svg?logo=python&logoColor=white&labelColor=0d1117)](http://mypy-lang.org/)

<!-- Dependencies & Maintenance -->
[![Renovate](https://img.shields.io/badge/renovate-enabled-brightgreen.svg?logo=renovatebot&logoColor=white&labelColor=0d1117)](https://renovatebot.com)
[![Dependencies Status](https://img.shields.io/librariesio/github/johanna-II/BillingTest?logo=libraries.io&logoColor=white&labelColor=0d1117)](https://libraries.io/github/johanna-II/BillingTest)
[![License](https://img.shields.io/badge/license-MIT-green.svg?labelColor=0d1117)](LICENSE.md)

</div>
<!-- markdownlint-enable MD033 -->

Billing Automation Test Suite for payment module verification.

> [!IMPORTANT]
> **📌 Portfolio Project Notice**
>
> This is a portfolio demonstration project showcasing CI/CD implementation with GitHub Actions. The workflows are configured but will fail during execution due to:
>
> - Missing production API endpoints and credentials
> - Unavailable internal billing system dependencies
> - Required secrets that cannot be shared publicly
>
> The code structure, patterns, and CI/CD configuration demonstrate best practices for enterprise billing system automation.

## Requirements

- Python 3.12 or higher
- Poetry (recommended) or pip

## Features

- **Modern Python**: Fully updated to leverage Python 3.12 features
  - Type hints with union operator (`|`)
  - `match-case` pattern matching
  - `StrEnum` for better string enumerations
  - Enhanced type annotations throughout

- **Code Quality Tools**:
  - Black for code formatting
  - Ruff for linting
  - mypy for type checking
  - pytest for testing with coverage reports

## Installation

### Using Poetry (Recommended)

```bash
poetry install
```

### Using pip

```bash
pip install -r requirements.txt
```

## Project Structure

```text
BillingTest/
ㄴ config/          # Environment configurations
ㄴ libs/            # Core billing modules
ㄴㄴ adjustment.py      # Billing adjustments management
ㄴㄴ Batch.py          # Batch job operations
ㄴㄴ calculation.py    # Price calculations
ㄴㄴ Contract.py       # Contract management
ㄴㄴ Credit.py         # Credit operations
ㄴㄴ Metering.py       # Usage metering
ㄴㄴ Payments.py       # Payment processing
ㄴㄴ ...
ㄴ tests/           # Test suites
Dockerfile       # Container configuration (Python 3.12)
```

## Running Tests

```bash
# Run all tests with coverage
pytest --cov=libs --cov-report=html

# Run specific test file
pytest tests/test_credit_all.py

# Run tests in parallel
pytest -n auto
```

## Code Formatting

```bash
# Format all Python files
black .

# Check formatting without changes
black . --check

# Run linter
ruff check .

# Type checking
mypy libs/
```

## Docker Support

Build and run the test suite in a container:

```bash
docker build -t billing-test .
docker run billing-test pytest
```

## CI/CD with GitHub Actions

This project uses GitHub Actions for continuous integration and deployment.

### Available Workflows

1. **CI** (`ci.yml`) - Runs on every push and PR
   - Linting with Ruff and Black
   - Type checking with mypy
   - Unit tests for all regions

2. **Billing Test** (`billing-test.yml`) - Manual test execution
   - Replaces Jenkins pipeline
   - Supports all test parameters
   - Generates HTML reports

3. **Scheduled Tests** (`scheduled-tests.yml`) - Daily automated tests
   - Runs full test suite
   - Multi-region parallel execution
   - Slack notifications on failure

4. **Security Scan** (`security.yml`) - Security vulnerability scanning
   - Bandit for Python code
   - Trivy for dependencies
   - Automated dependency updates via Dependabot

### Running Tests via GitHub Actions

1. Go to the Actions tab in GitHub
2. Select "Billing Test" workflow
3. Click "Run workflow"
4. Fill in the parameters:
   - Environment: alpha
   - Member: kr/jp/etc
   - Month: YYYY-MM
   - Test case: (optional) specific test

### Migration from Jenkins

See [Migration Guide](docs/MIGRATION_TO_GITHUB_ACTIONS.md) for detailed instructions on migrating from Jenkins to GitHub Actions.

## Configuration

Place environment-specific configurations in the `config/` directory:

- `alpha_kr.py` - Korean alpha environment
- `alpha_jp.py` - Japanese alpha environment
- `alpha_etc.py` - Other regions alpha environment

## Development Guidelines

1. All code must be formatted with Black
2. Type hints are required for all functions
3. Use Python 3.12+ features where appropriate
4. Write tests for new functionality
5. Maintain test coverage above 80%

## 📚 Documentation

- **Technical Architecture**: [System Design & Diagrams](docs/TECHNICAL_DIAGRAMS.md) - Visual guide to how it all works

## License

See LICENSE.md for details.
