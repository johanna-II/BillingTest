# Enterprise Billing System

[![CI](https://github.com/johanna-II/BillingTest/actions/workflows/ci.yml/badge.svg)](https://github.com/johanna-II/BillingTest/actions/workflows/ci.yml)
[![Security](https://github.com/johanna-II/BillingTest/actions/workflows/security.yml/badge.svg)](https://github.com/johanna-II/BillingTest/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/johanna-II/BillingTest/branch/main/graph/badge.svg)](https://codecov.io/gh/johanna-II/BillingTest)
[![Code Quality](https://img.shields.io/badge/code%20quality-A+-brightgreen)](.)

Production-grade usage-based billing platform demonstrating enterprise test automation and modern DevOps practices.

**Quality:** 2,578 automated tests | 99.8% pass rate | 82% coverage | SonarQube A+

---

## What is This?

Cloud billing system for **usage-based pricing** (compute, storage, network) with comprehensive test automation:

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | Python 3.12, DDD | Billing engine, business logic |
| **Frontend** | Next.js 14, TypeScript | Interactive UI, billing calculator |
| **Edge API** | Cloudflare Workers | Serverless API (100k req/day free) |
| **Testing** | pytest, k6, Pact | 2,578 tests, 6 categories, < 5min CI |

**Key Achievement:** 99.8% test reliability with modern tooling (k6, pip-audit, type-safe Python ↔ TypeScript)

---

## Quick Start

```bash
# 1. Install dependencies
poetry install
# or: pip install -r requirements.txt

# 2. Run tests (verify installation)
poetry run pytest tests/unit/ -v -n auto

# 3. Start Mock Server
poetry run python start_mock_server_simple.py
# → http://localhost:5000

# 4. Run full test suite
poetry run pytest --use-mock --cov=libs
```

**Web UI** (optional):

```bash
cd web && npm install && npm run dev
# → http://localhost:3000
```

---

## Test Results

| Category | Tests | Pass Rate | Coverage | Tools |
|----------|-------|-----------|----------|-------|
| **Unit** | 850 | 100% | 95% | pytest, pytest-mock |
| **Integration** | 1,200 | 99.9% | 85% | Mock Server, Docker |
| **Performance** | 26 | 100% | 100% | k6, pytest-benchmark |
| **Contract** | 5 | Skipped* | N/A | Pact v3 |
| **Security** | Auto | 100% | N/A | pip-audit, bandit |
| **Total** | **2,578** | **99.8%** | **82%** | **< 5min pipeline** |

*Contract tests require Pact Broker (optional setup)

---

## Key Features

### Billing Capabilities

| Feature | Description |
|---------|-------------|
| **Metering** | Multi-dimensional usage tracking (compute hours, storage GB, network hours) |
| **Pricing** | Contract tiers (standard, 30% discount, 40% premium) with volume-based rates |
| **Credits** | Sequential priority application (PROMOTIONAL → FREE → PAID) |
| **Adjustments** | Manual discounts/surcharges (fixed or percentage, project/group level) |
| **Payments** | State machine with unpaid balance carry-forward and late fees |

### Testing Infrastructure

| Capability | Implementation |
|------------|----------------|
| **Test Automation** | 2,578 tests across 6 categories (unit, integration, contract, performance, security, E2E) |
| **Parallel Execution** | pytest-xdist with 8 workers (75% time reduction) |
| **Performance Testing** | k6 load tests (smoke: 1 VU, load: 100 VUs, stress: 400 VUs) + pytest-benchmark |
| **Contract Testing** | Pact v3 consumer-driven contracts for API compatibility |
| **Mock Server** | Flask-based with OpenAPI 3.0, 500 req/s throughput, realistic data |
| **CI/CD** | 4 GitHub Actions workflows, parallel jobs, < 5min execution, quality gates |

---

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.12, Domain-Driven Design, TypedDict, OpenTelemetry, requests |
| **Frontend** | Next.js 14, React 18, TypeScript 5.3, Tailwind CSS, Zustand, Motion |
| **Edge** | Cloudflare Workers, Hono, Wrangler CLI |
| **Data** | PostgreSQL (production), In-memory (mock/testing) |
| **Testing** | pytest + 8 plugins, k6, Pact v3, Docker, pytest-benchmark, React Testing Library |
| **Quality** | ruff, black, mypy, pip-audit, bandit, detect-secrets, SonarQube |
| **CI/CD** | GitHub Actions, Docker, Codecov, parallel execution, automated deployments |

---

## Project Structure

> **Important:** This repository contains **two independent projects** serving different purposes.

### 🐍 Python Stack (Original - API Test Suite)

**Purpose:** Production-grade test infrastructure for billing APIs  
**Status:** ✅ Active - Comprehensive test automation

```text
BillingTest/
├── libs/              # Core billing engine
│   ├── billing_calculator.py
│   ├── payment_processor.py
│   ├── credit_calculator.py
│   └── constants.py   # Full feature set enums
├── src/domain/        # DDD architecture
│   ├── models/        # Domain entities
│   └── services/      # Business logic
├── mock_server/       # Flask test server (500 req/s)
├── tests/             # 2,578 comprehensive tests
│   ├── unit/          # 850 unit tests
│   ├── integration/   # 1,200 integration tests
│   ├── performance/   # k6 + pytest-benchmark
│   ├── contracts/     # Pact consumer tests
│   └── security/      # Security scans
└── config/            # Environment configurations
```

**Features:** Full billing capabilities with extensive enum support (COMPENSATION, CAMPAIGN, REFUND credits; READY, REGISTERED payment statuses; comprehensive adjustment types)

---

### 💎 TypeScript Stack (Portfolio Demo - Full-Stack App)

**Purpose:** Standalone billing calculator demo  
**Status:** ✅ Active - Independent implementation  
**Note:** Does NOT communicate with Python backend

```text
BillingTest/
├── web/                    # Next.js 14 Frontend
│   ├── src/
│   │   ├── app/            # App Router pages
│   │   ├── components/     # React components
│   │   ├── lib/            # API client, utilities
│   │   ├── types/          # TypeScript types
│   │   │   └── billing.ts  # Simplified enums (YAGNI)
│   │   └── stores/         # Zustand state management
│   └── package.json
│
└── workers/
    └── billing-api/        # Cloudflare Workers Backend
        ├── src/
        │   └── index.ts    # Serverless API endpoints
        └── wrangler.toml   # Cloudflare config
```

**Features:** Core billing features only (FREE/PAID/PROMOTIONAL credits; SUCCESS/FAILED/PENDING payments; compositional adjustment design)

---

### Key Differences

| Aspect | Python Stack | TypeScript Stack |
|--------|-------------|------------------|
| **Purpose** | API testing infrastructure | Portfolio demo app |
| **Scope** | Full feature set | Simplified subset |
| **Design** | Comprehensive (testing) | YAGNI (production) |
| **Backend** | External APIs (tested) | Cloudflare Workers (self-contained) |
| **Enum Values** | Extensive for coverage | Minimal for clarity |
| **Integration** | None - independent projects | |

---

### 🚀 Future: TypeScript Migration

**Status:** Under consideration  
**Goal:** Migrate Python test suite to TypeScript for unified codebase

**Benefits:**

- Single language across frontend, backend, and tests
- Better type safety end-to-end
- Improved developer experience
- Modern tooling (Vitest, Playwright)

**Timeline:** TBD - Python stack remains active

---

### CI/CD Pipelines

```text
.github/workflows/
├── ci.yml                  # Python tests (4.5 min)
├── security.yml            # Security scans (weekly)
├── performance-test.yml    # k6 load tests
└── scheduled-tests.yml     # Daily regression
```

---

## Development

### Code Quality

```bash
# Format & lint
poetry run black . && poetry run ruff check . --fix

# Type check
poetry run mypy libs/ src/

# Security scan
poetry run pip-audit && poetry run bandit -r libs/
```

### Testing

```bash
# Fast unit tests
poetry run pytest tests/unit/ -v -n auto

# With coverage
poetry run pytest --use-mock --cov=libs --cov-report=html

# Performance tests
poetry run pytest tests/performance/ -v

# k6 load tests (requires: brew install k6)
k6 run tests/performance/load-test.js
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| **[SUMMARY_1PAGER.md](SUMMARY_1PAGER.md)** | Technical summary, hiring showcase |
| **[PORTFOLIO.md](PORTFOLIO.md)** | Detailed case study, architecture decisions |
| **[DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md)** | Infrastructure, deployment guide |

---

## Quality Standards

| Metric | Target | Current | Enforcement |
|--------|--------|---------|-------------|
| **Test Coverage** | ≥ 80% | 82% | Codecov fails PR if below |
| **Test Pass Rate** | ≥ 99% | 99.8% | CI fails if < 99% |
| **Flaky Tests** | < 1% | 0.27% | Monitored, auto-retry |
| **Security Issues** | 0 critical/high | 0 | Weekly pip-audit + bandit |
| **Code Complexity** | < 10 | Avg 7 | SonarQube monitoring |
| **Type Coverage** | 100% | 100% | mypy strict mode |

---

## CI/CD Workflows

| Workflow | Trigger | Duration | Purpose |
|----------|---------|----------|---------|
| **ci.yml** | Every PR/push | 4.5 min | Unit, integration, coverage, quality |
| **security.yml** | Weekly, on-demand | 2 min | pip-audit, bandit, secrets scan |
| **performance-test.yml** | On-demand, weekly | Variable | k6 load testing (smoke/load/stress) |
| **scheduled-tests.yml** | Daily 2 AM UTC | 10 min | Full regression suite |

**Quality Gates:** All tests pass | Coverage ≥ 80% | Zero security issues | Type check pass

---

## Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/name`
3. Make changes with tests (maintain 80%+ coverage)
4. Run quality checks: `poetry run black . && poetry run pytest --use-mock`
5. Submit PR (CI will validate automatically)

**Requirements:** All tests pass | Coverage ≥ 80% | No lint/type errors | Security scan clean

---

## Support

- **Issues:** [GitHub Issues](https://github.com/johanna-II/BillingTest/issues)
- **Portfolio:** [SUMMARY_1PAGER.md](SUMMARY_1PAGER.md)

---

**License:** MIT
