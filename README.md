# Billing System

[![CI](https://github.com/johanna-II/BillingTest/actions/workflows/ci.yml/badge.svg)](https://github.com/johanna-II/BillingTest/actions/workflows/ci.yml)
[![Integration Tests](https://github.com/johanna-II/BillingTest/actions/workflows/integration-tests-service.yml/badge.svg)](https://github.com/johanna-II/BillingTest/actions/workflows/integration-tests-service.yml)
[![codecov](https://codecov.io/gh/johanna-II/BillingTest/branch/main/graph/badge.svg)](https://codecov.io/gh/johanna-II/BillingTest)
[![Security](https://github.com/johanna-II/BillingTest/actions/workflows/security.yml/badge.svg)](https://github.com/johanna-II/BillingTest/actions/workflows/security.yml)

Production-grade usage-based billing system with comprehensive testing infrastructure. Handles metering, pricing, adjustments, credits, and payment processing with 80%+ test coverage.

## What is This?

A complete billing platform consisting of:
- **Backend Services** (Python): Core billing engine with metering, contracts, adjustments, and payment processing
- **Web UI** (Next.js): Interactive billing calculator and history management
- **Edge API** (Cloudflare Workers): Serverless billing API
- **Mock Server** (Flask): High-fidelity API mocking for testing (500 req/s)

Built with enterprise-grade testing: unit, integration, contract, performance, and security tests with automated CI/CD.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Core Logic** | Python 3.12, Domain-Driven Design |
| **Frontend** | Next.js 14, React 18, TypeScript, Tailwind CSS, Zustand |
| **Edge API** | Cloudflare Workers, Hono |
| **Testing** | pytest, Docker, GitHub Actions |
| **Observability** | OpenTelemetry, Prometheus |
| **Mocking** | Flask-based Mock Server with OpenAPI spec |

---

## Architecture

```
┌─────────────┐       ┌──────────────────┐      ┌─────────────────┐
│   Web UI    │──────>│  Cloudflare      │─────>│   Billing API   │
│  (Next.js)  │       │   Workers        │      │   (Internal)    │
└─────────────┘       └──────────────────┘      └─────────────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │  Core Billing    │
                     │     Engine       │
                     │   (Python libs)  │
                     └──────────────────┘
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
         ┌──────────┐  ┌──────────┐  ┌──────────┐
         │ Metering │  │ Contracts│  │ Payments │
         └──────────┘  └──────────┘  └──────────┘
```

**Test Infrastructure:**
```
┌───────────────────────────────────────────────────────────────────────────┐
│                              CI/CD Pipelines                              │
├────────────────┬───────────────────────────────┬──────────────────────────┤
│   ci.yml       │ integration-tests-service     │  scheduled-tests.yml     │
│                │                               │                          │
│ • Unit         │ • Real Mock                   │ • Daily regression       │
│ • Contracts    │   Server                      │ • Performance benchmarks │
│ • Comprehensive│ • Component                   │ • Security scans         │
└────────────────┴───────────────────────────────┴──────────────────────────┘
```

---

## Quick Start

### Prerequisites
- **Python**: 3.11 or 3.12
- **Node.js**: 18+ (for frontend)
- **Docker**: For integration tests

### Installation

```bash
# Clone repository
git clone https://github.com/johanna-II/BillingTest.git
cd BillingTest

# Backend setup
pip install -r requirements.txt

# Frontend setup (optional)
cd web && npm install
```

### Run Tests

```bash
# Unit tests (fast, no dependencies)
pytest tests/unit/ -v

# Integration tests with Mock Server
pytest tests/integration/ --use-mock -v

# All tests
pytest --use-mock
```

### Run Web UI

```bash
cd web
npm run dev
# Open http://localhost:3000
```

---

## Project Structure

```
BillingTest/
├── libs/                      # Core billing engine
│   ├── Calculation.py         # Billing calculations
│   ├── Metering.py           # Usage aggregation
│   ├── Contract.py           # Pricing & contracts
│   ├── Credit.py             # Credit management
│   ├── Adjustment.py         # Billing adjustments
│   ├── Payments.py           # Payment processing
│   └── observability/        # Telemetry (OpenTelemetry)
│
├── src/domain/               # Domain-Driven Design models
│   ├── models/               # Domain entities
│   ├── services/             # Domain services
│   └── repositories/         # Repository interfaces
│
├── web/                      # Next.js frontend
│   ├── src/components/       # React components
│   ├── src/stores/          # Zustand state management
│   └── src/types/           # TypeScript types
│
├── workers/billing-api/      # Cloudflare Workers edge API
│
├── mock_server/              # Flask-based Mock Server
│   ├── app.py               # Flask application
│   ├── mock_data.py         # Test data generation
│   └── openapi_handler.py   # OpenAPI spec serving
│
├── tests/
│   ├── unit/                # Unit tests (fast)
│   ├── integration/         # Integration tests (Mock Server)
│   ├── contracts/           # Contract tests (API contracts)
│   ├── performance/         # Performance benchmarks
│   └── security/            # Security vulnerability tests
│
└── .github/workflows/        # CI/CD pipelines
    ├── ci.yml               # Main CI (unit, contracts, comprehensive)
    ├── integration-tests-service.yml  # Integration tests
    ├── scheduled-tests.yml  # Daily regression tests
    └── security.yml         # Security scans
```

---

## Test Categories

| Type | Description | Runs On | Mock Server |
|------|-------------|---------|-------------|
| **Unit** | Isolated component tests | Every PR/push | No |
| **Integration** | End-to-end with real Mock Server | Every PR/push | Docker container |
| **Contracts** | API contract validation | Every PR/push | Local process |
| **Comprehensive** | Heavy business logic combinations | main branch only | Docker container |
| **Performance** | Benchmarking & profiling | Every PR/push | Yes |
| **Security** | Vulnerability scanning | Every PR/push | Yes |

### Running Specific Test Types

```bash
# Unit tests only (no Mock Server needed)
pytest tests/unit/ -v -n auto

# Integration tests (Docker Mock Server)
pytest tests/integration/ --use-mock -v -n 2

# Contract tests
pytest tests/contracts/ --use-mock -v

# Performance tests
pytest tests/performance/ -v

# Security tests
pytest tests/security/ -v

# Comprehensive tests (slow)
pytest tests/integration/test_all_business_combinations.py \
       tests/integration/test_comprehensive_business_logic.py \
       --use-mock -v
```

---

## CI/CD Pipelines

### 1. **Main CI** (`ci.yml`)
- **Triggers**: All PRs, pushes to `main`/`develop`
- **Jobs**:
  - Lint (ruff, mypy)
  - Unit tests
  - Contract tests
  - Comprehensive tests (main branch only)
  - Coverage check (80% threshold)
  - Performance benchmarks
  - Security tests

### 2. **Integration Tests** (`integration-tests-service.yml`)
- **Triggers**: All PRs, pushes
- **Jobs**:
  - Real Mock Server in Docker
  - Component tests with `responses` library
  - Parallel execution (2 workers)

### 3. **Scheduled Tests** (`scheduled-tests.yml`)
- **Triggers**: Daily at 2 AM UTC
- **Jobs**:
  - Full regression test matrix (members × months)
  - Performance benchmarking
  - Security scans

### 4. **Security** (`security.yml`)
- **Triggers**: Weekly, on security updates
- **Jobs**:
  - Dependency vulnerability checks
  - Bandit security scanning
  - License compliance

---

## Development

### Code Quality Standards

```bash
# Format code
ruff check . --fix
black .

# Type check
mypy libs --ignore-missing-imports

# Security scan
bandit -r libs/
```

### Mock Server

The Mock Server provides high-fidelity API mocking for testing:

```bash
# Start Mock Server locally
python -m mock_server.run_server

# With custom rate limit
MOCK_SERVER_RATE_LIMIT=500 python -m mock_server.run_server

# Access Swagger UI
open http://localhost:5000/docs
```

**Features:**
- OpenAPI 3.0 spec serving
- Configurable rate limiting (default: 500 req/s)
- Realistic response data
- Health check endpoint

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=libs --cov-report=html

# View in browser
open htmlcov/index.html

# Current coverage target: 80%
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_MOCK_SERVER` | `true` | Enable Mock Server for tests |
| `MOCK_SERVER_URL` | `http://localhost:5000` | Mock Server URL |
| `MOCK_SERVER_RATE_LIMIT` | `500` | Rate limit (req/s) |
| `PYTHON_VERSION` | `3.12` | Python version for CI |
| `MIN_COVERAGE` | `80` | Minimum coverage threshold |

---

## Key Features

### Billing Engine
- ✅ **Usage-based metering**: Aggregate and calculate usage charges
- ✅ **Tiered pricing**: Support for volume-based pricing tiers
- ✅ **Credits system**: Apply credits with priority rules
- ✅ **Adjustments**: Manual billing adjustments (discounts, corrections)
- ✅ **Unpaid balance**: Carry forward unpaid amounts
- ✅ **Payment processing**: Multi-step payment state machine

### Testing Infrastructure
- ✅ **80%+ coverage**: Comprehensive test suite with high coverage
- ✅ **Parallel execution**: pytest-xdist with optimal worker counts
- ✅ **Retry logic**: Auto-retry flaky tests (3 attempts)
- ✅ **Isolation**: Docker containers for consistent environments
- ✅ **Performance**: Benchmark tracking and regression detection
- ✅ **Security**: Automated vulnerability scanning

### Observability
- ✅ **OpenTelemetry**: Distributed tracing support
- ✅ **Prometheus metrics**: Performance monitoring
- ✅ **Structured logging**: JSON logs for production
- ✅ **Health checks**: Liveness and readiness probes

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Ensure tests pass: `pytest --use-mock`
5. Check code quality: `ruff check . && mypy libs`
6. Commit: `git commit -m 'feat: add feature'`
7. Push: `git push origin feature/my-feature`
8. Open a Pull Request

**PR Requirements:**
- ✅ All tests passing
- ✅ Coverage ≥ 80%
- ✅ No linter errors
- ✅ Type checking passes

---

## License

MIT License - see [LICENSE.md](LICENSE.md)

---

## Support

- **Issues**: [GitHub Issues](https://github.com/johanna-II/BillingTest/issues)
- **Discussions**: [GitHub Discussions](https://github.com/johanna-II/BillingTest/discussions)
