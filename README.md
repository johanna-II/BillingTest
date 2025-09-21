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

<!-- Technology Stack -->
### Powered by

[![Flask](https://img.shields.io/badge/Flask-3.0-000000.svg?logo=flask&logoColor=white&labelColor=0d1117)](https://flask.palletsprojects.com/)
[![Pytest](https://img.shields.io/badge/Pytest-8.4-0A9EDC.svg?logo=pytest&logoColor=white&labelColor=0d1117)](https://pytest.org/)
[![Pact](https://img.shields.io/badge/Pact-Consumer_Driven-00D4AA.svg?logo=pact&logoColor=white&labelColor=0d1117)](https://pact.io/)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-Observability-242450.svg?logo=opentelemetry&logoColor=white&labelColor=0d1117)](https://opentelemetry.io/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg?logo=docker&logoColor=white&labelColor=0d1117)](https://www.docker.com/)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI/CD-2088FF.svg?logo=github-actions&logoColor=white&labelColor=0d1117)](https://github.com/features/actions)

</div>
<!-- markdownlint-enable MD033 -->

Enterprise billing system test automation framework with modern Python architecture.

> **Mock Server Available**: Complete mock API server included for local testing without external dependencies!

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
python run_tests.py --mode safe

# Run specific tests
python run_tests.py --mode fast tests -m "unit"
```

## Features

- **Mock Server**: Automatic API mocking with OpenAPI support
- **Contract Testing**: Consumer-driven contracts with Pact
- **Observability**: OpenTelemetry integration for tracing
- **Multi-region**: Support for KR, JP, and other regions
- **CI/CD Optimized**: 67% faster pipeline execution

## Test Execution

### Modes
- `default`: Sequential execution
- `parallel`: Parallel with CPU/2 workers
- `safe`: Credit tests sequential, others parallel
- `fast`: No coverage, quick feedback

### Markers
- `unit`: Unit tests (<3s)
- `core`: Core business logic
- `api`: API integration tests
- `contract`: Contract tests
- `serial`: Must run sequentially

### Examples
```bash
# Quick validation
pytest -m "unit and not slow"

# Core business logic
python run_tests.py --mode default tests -m "core"

# With mock server
export USE_MOCK_SERVER=true
python run_tests.py --mode parallel
```

## Technical Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    BillingTest Framework                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │   Tests     │  │ Mock Server  │  │  Observability  │   │
│  │             │  │              │  │                 │   │
│  │ • Unit      │  │ • OpenAPI    │  │ • OpenTelemetry │   │
│  │ • Integration│ │ • Pact       │  │ • Metrics       │   │
│  │ • Contract  │  │ • In-Memory  │  │ • Traces        │   │
│  └──────┬──────┘  └──────┬───────┘  └────────┬────────┘   │
│         │                 │                    │            │
│  ┌──────┴─────────────────┴────────────────────┴────────┐  │
│  │                  Core Libraries                       │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │                                                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ │  │
│  │  │Configuration│  │  Metering   │  │   Contract   │ │  │
│  │  │  Manager    │  │  Manager    │  │   Manager    │ │  │
│  │  └─────────────┘  └─────────────┘  └──────────────┘ │  │
│  │                                                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ │  │
│  │  │  Payment    │  │   Credit    │  │ Calculation  │ │  │
│  │  │  Manager    │  │  Manager    │  │   Manager    │ │  │
│  │  └─────────────┘  └─────────────┘  └──────────────┘ │  │
│  │                                                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ │  │
│  │  │ Adjustment  │  │   Batch     │  │ HTTP Client  │ │  │
│  │  │  Manager    │  │  Manager    │  │              │ │  │
│  │  └─────────────┘  └─────────────┘  └──────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│                              │                              │
│  ┌───────────────────────────┴───────────────────────────┐ │
│  │                  External APIs                         │ │
│  │  • Billing API  • Metering API  • Payment Gateway     │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Manager Pattern
All operations follow a consistent Manager pattern for clean separation of concerns:

```python
# Example: Payment processing flow
payment_manager = PaymentManager(month="2024-01", uuid="user123")
payment_manager.get_payment_status()
payment_manager.process_payment(amount=100000)
payment_manager.verify_payment()
```

#### 2. Mock Server Architecture
- **Flask-based** with thread-safe in-memory storage
- **OpenAPI integration** for automatic response generation
- **Test isolation** with UUID-based data separation
- **Provider states** for contract testing

#### 3. Test Framework
- **Fixture-based** setup with automatic teardown
- **Parallel execution** with intelligent grouping
- **Retry mechanisms** for flaky test mitigation
- **Coverage tracking** with 60%+ enforcement

#### 4. Data Flow

```
Test Case → Metering Data → Calculation → Billing → Payment
    ↓            ↓              ↓           ↓         ↓
Mock Server ← API Calls ← Verification ← Credits ← Results
```

### Key Design Decisions

1. **Manager Pattern**: Each domain has a dedicated manager class
2. **Immutable Test Data**: Tests use unique UUIDs for isolation
3. **Graceful Degradation**: Fallbacks for API failures
4. **Type Safety**: Full type hints with mypy strict mode
5. **Async-Ready**: HTTP client supports async operations

### File Structure

```
BillingTest/
├── libs/                    # Core library modules
│   ├── __init__.py         # Public API exports
│   ├── InitializeConfig.py # Configuration management
│   ├── Metering.py         # Usage data handling
│   ├── Contract.py         # Contract operations
│   ├── Credit.py           # Credit management
│   ├── Payment.py          # Payment processing
│   ├── calculation.py      # Billing calculations
│   ├── adjustment.py       # Adjustment handling
│   ├── http_client.py      # API communication
│   └── observability/      # Telemetry integration
├── tests/                   # Test suites
│   ├── fixtures/           # Reusable test fixtures
│   ├── contracts/          # Pact contract tests
│   └── test_*.py          # Test modules
├── mock_server/            # Mock API server
│   ├── app.py             # Flask application
│   └── openapi_handler.py # OpenAPI integration
├── config/                 # Environment configs
├── docs/                   # Additional documentation
└── run_tests.py           # Test runner
```

## CI/CD Pipeline

Optimized GitHub Actions workflow with:
- **Stage 1**: Quick validation (<2 min)
- **Stage 2**: Parallel quality checks
- **Stage 3**: Smart test execution
- **Stage 4**: Coverage analysis
- **Stage 5**: Integration tests (main/develop only)

## Development

### Setup
```bash
# Clone repository
git clone <repo-url>
cd BillingTest

# Install dependencies
pip install -r requirements.txt

# Run tests
python run_tests.py --mode fast
```

### Contributing
1. Follow PEP 8 and use type hints
2. Add tests for new features
3. Maintain >60% coverage
4. Update documentation

## Documentation

- [Testing Guide](TESTING_GUIDE.md) - Detailed testing instructions
- [Technical Architecture](TECHNICAL_ARCHITECTURE.md) - Deep dive with flow & sequence diagrams
- [Advanced Features](docs/ADVANCED_FEATURES.md) - Mock server, contracts, observability

## License

See LICENSE.md for details.
