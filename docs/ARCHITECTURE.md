# System Architecture

## Overview

The Billing Test System is a comprehensive testing framework for a
usage-based billing platform, consisting of backend services, frontend UI,
edge API, and supporting infrastructure.

## High-Level Architecture

```mermaid
graph TB
    subgraph "User Layer"
        U[User/Developer]
    end

    subgraph "Frontend"
        WEB[Web UI<br/>Next.js 14]
    end

    subgraph "Edge Layer"
        CF[Cloudflare Workers<br/>Hono Framework]
    end

    subgraph "Backend Services"
        API[Billing API<br/>Internal Service]
    end

    subgraph "Core Engine"
        CALC[Calculation Engine<br/>Python]
        METER[Metering Service]
        CONTRACT[Contract Service]
        PAYMENT[Payment Service]
        CREDIT[Credit Service]
        ADJ[Adjustment Service]
    end

    U -->|Browse| WEB
    WEB -->|API Call| CF
    CF -->|Route| API
    API --> CALC
    CALC --> METER
    CALC --> CONTRACT
    CALC --> PAYMENT
    CALC --> CREDIT
    CALC --> ADJ
```

## Test Infrastructure Architecture

```mermaid
graph LR
    subgraph "Test Execution"
        DEV[Developer]
        CI[CI/CD Pipeline]
    end

    subgraph "Test Framework"
        PYTEST[pytest]
        XDIST[pytest-xdist<br/>Parallel Execution]
        HYPOTHESIS[Hypothesis<br/>Property Testing]
        BENCH[pytest-benchmark]
    end

    subgraph "Test Categories"
        UNIT[Unit Tests]
        INT[Integration Tests]
        CONT[Contract Tests]
        PERF[Performance Tests]
        SEC[Security Tests]
    end

    subgraph "Mock Infrastructure"
        MOCK[Mock Server<br/>Flask]
        DOCKER[Docker Container]
        OPENAPI[OpenAPI Spec]
    end

    DEV --> PYTEST
    CI --> PYTEST
    PYTEST --> XDIST
    PYTEST --> HYPOTHESIS
    PYTEST --> BENCH

    XDIST --> UNIT
    XDIST --> INT
    PYTEST --> CONT
    PYTEST --> PERF
    PYTEST --> SEC

    INT --> MOCK
    CONT --> MOCK
    PERF --> MOCK
    MOCK --> DOCKER
    MOCK --> OPENAPI
```

## CI/CD Pipeline Architecture

```mermaid
graph TB
    subgraph "Triggers"
        PR[Pull Request]
        PUSH[Push to main/develop]
        SCHED[Scheduled<br/>Daily 2AM UTC]
        MANUAL[Manual Trigger]
    end

    subgraph "Workflows"
        CI[ci.yml<br/>Main CI/CD]
        INT_TEST[integration-tests-service.yml<br/>Integration Tests]
        SCHEDULED[scheduled-tests.yml<br/>Regression]
        SECURITY[security.yml<br/>Security Scan]
    end

    subgraph "Jobs"
        LINT[Lint & Type Check]
        UNIT_J[Unit Tests]
        CONTRACT_J[Contract Tests]
        COMP[Comprehensive Tests<br/>main branch only]
        INT_J[Integration Tests<br/>Docker]
        PERF_J[Performance Tests]
        SEC_J[Security Scan]
        COV[Coverage Check<br/>80% threshold]
    end

    subgraph "Reports"
        CODECOV[Codecov]
        ARTIFACTS[GitHub Artifacts]
        SUMMARY[Job Summary]
    end

    PR --> CI
    PR --> INT_TEST
    PUSH --> CI
    PUSH --> INT_TEST
    SCHED --> SCHEDULED
    MANUAL --> SECURITY

    CI --> LINT
    CI --> UNIT_J
    CI --> CONTRACT_J
    CI --> COMP
    CI --> PERF_J
    CI --> SEC_J
    CI --> COV

    INT_TEST --> INT_J

    UNIT_J --> CODECOV
    INT_J --> CODECOV
    CONTRACT_J --> CODECOV

    COV --> ARTIFACTS
    PERF_J --> ARTIFACTS
    INT_J --> SUMMARY
```

## Domain Model Architecture (DDD)

```mermaid
classDiagram
    class BillingStatement {
        +String id
        +String user_id
        +String billing_group_id
        +BillingPeriod period
        +UsageAggregation usage
        +Decimal base_amount
        +UnpaidAmount unpaid
        +List~Adjustment~ adjustments
        +List~Credit~ credits
        +Decimal final_amount
        +calculate()
    }

    class BillingPeriod {
        +int year
        +int month
        +datetime start_date
        +datetime end_date
        +from_month_string()
    }

    class UsageAggregation {
        +String billing_group_id
        +BillingPeriod period
        +List~MeteringData~ metering_data
        +Decimal total_amount
        +aggregate()
    }

    class Adjustment {
        +String id
        +AdjustmentType type
        +Decimal amount
        +AdjustmentTarget target
        +apply()
    }

    class Credit {
        +String id
        +CreditType type
        +Decimal amount
        +CreditPriority priority
        +datetime expire_date
        +apply()
    }

    class UnpaidAmount {
        +Decimal amount
        +BillingPeriod period
        +List~String~ invoice_ids
    }

    BillingStatement --> BillingPeriod
    BillingStatement --> UsageAggregation
    BillingStatement --> UnpaidAmount
    BillingStatement --> Adjustment
    BillingStatement --> Credit
```

## Test Execution Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Git as Git Hook
    participant CI as GitHub Actions
    participant Pytest as pytest
    participant Mock as Mock Server
    participant Worker as pytest-xdist Worker

    Dev->>Git: git commit
    Git->>Git: Pre-commit hooks<br/>(lint, format, secrets)

    alt Hooks Pass
        Git->>Dev: Commit accepted
        Dev->>CI: git push
    else Hooks Fail
        Git->>Dev: ❌ Fix issues
    end

    CI->>Pytest: Run test suite
    Pytest->>Mock: Start Mock Server
    Mock-->>Pytest: Server ready

    Pytest->>Worker: Spawn workers (n=2)

    par Worker 1
        Worker->>Mock: Test requests
        Mock-->>Worker: Responses
    and Worker 2
        Worker->>Mock: Test requests
        Mock-->>Worker: Responses
    end

    Worker-->>Pytest: Results
    Pytest->>Pytest: Aggregate results
    Pytest->>CI: Report (Pass/Fail)

    alt Tests Pass
        CI->>Dev: ✅ Success
    else Tests Fail
        CI->>Dev: ❌ Fix tests
    end
```

## Mock Server Architecture

```mermaid
graph TB
    subgraph "Mock Server"
        FLASK[Flask Application]
        ROUTES[Route Handlers]
        DATA[Test Data Manager]
        OPENAPI_H[OpenAPI Handler]
        SWAGGER[Swagger UI]
        SECURITY[Security Validation]
    end

    subgraph "Features"
        RATE[Rate Limiting<br/>500 req/s]
        HEALTH[Health Check]
        STATE[Stateful Sessions]
        SPEC[OpenAPI 3.0 Spec]
    end

    subgraph "Integration"
        DOCKER[Docker Container]
        COMPOSE[Docker Compose]
        NETWORK[Host Network]
    end

    FLASK --> ROUTES
    ROUTES --> DATA
    ROUTES --> OPENAPI_H
    ROUTES --> SWAGGER
    ROUTES --> SECURITY

    FLASK --> RATE
    FLASK --> HEALTH
    FLASK --> STATE
    FLASK --> SPEC

    FLASK --> DOCKER
    DOCKER --> COMPOSE
    DOCKER --> NETWORK
```

## Parallel Execution Strategy

```mermaid
graph TB
    subgraph "Test Execution"
        MAIN[pytest Main Process]
    end

    subgraph "Worker Isolation"
        W1[Worker gw0<br/>UUID: uuid-kr-gw0]
        W2[Worker gw1<br/>UUID: uuid-kr-gw1]
        W3[Worker gw2<br/>UUID: uuid-kr-gw2]
    end

    subgraph "Mock Server"
        MOCK[Mock Server<br/>Shared Resource]
    end

    subgraph "Test Data"
        D1[Test Data 1<br/>Isolated]
        D2[Test Data 2<br/>Isolated]
        D3[Test Data 3<br/>Isolated]
    end

    MAIN -->|Spawn| W1
    MAIN -->|Spawn| W2
    MAIN -->|Spawn| W3

    W1 --> D1
    W2 --> D2
    W3 --> D3

    W1 -->|HTTP| MOCK
    W2 -->|HTTP| MOCK
    W3 -->|HTTP| MOCK

    W1 -->|Results| MAIN
    W2 -->|Results| MAIN
    W3 -->|Results| MAIN
```

## Technology Stack

### Backend

- **Language**: Python 3.12
- **Architecture**: Domain-Driven Design (DDD)
- **Patterns**: Repository Pattern, Domain Services
- **Type Safety**: mypy strict mode

### Frontend

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5.x
- **State Management**: Zustand with persist middleware
- **Styling**: Tailwind CSS 3.x
- **Components**: React 18

### Edge

- **Platform**: Cloudflare Workers
- **Framework**: Hono
- **Runtime**: V8 Isolates

### Testing

- **Framework**: pytest 8.x
- **Parallel Execution**: pytest-xdist
- **Property Testing**: Hypothesis 6.x
- **Benchmarking**: pytest-benchmark
- **Contract Testing**: Pact
- **Mock Server**: Flask 3.x

### DevOps

- **CI/CD**: GitHub Actions
- **Containers**: Docker, Docker Compose
- **Observability**: OpenTelemetry, Prometheus
- **Security**: Bandit, Safety, Trivy

## Key Design Decisions

### 1. Mock Server Over Real API

- **Decision**: Build custom Flask-based Mock Server
- **Rationale**:
  - 10x faster execution
  - 99.9% reliability
  - Full control over responses
  - No rate limiting
- **Trade-off**: Maintenance overhead vs. test reliability

### 2. Parallel Execution with Worker Isolation

- **Decision**: Use pytest-xdist with unique worker IDs
- **Rationale**:
  - 3.5x speedup (30min → 9min)
  - Prevent data conflicts
  - Safe concurrent execution
- **Trade-off**: Complexity vs. speed

### 3. Conditional Comprehensive Tests

- **Decision**: Run heavy tests only on main branch
- **Rationale**:
  - Fast PR feedback (5-8 min)
  - Full regression on main
  - Developer opt-in with [full-test] tag
- **Trade-off**: Coverage on PR vs. speed

### 4. Multiple CI/CD Workflows

- **Decision**: 4 separate workflows vs. 1 monolithic
- **Rationale**:
  - Clear separation of concerns
  - Different triggers and purposes
  - Better resource utilization
- **Trade-off**: Configuration duplication vs. clarity

## Performance Characteristics

| Component | Metric | Value |
|-----------|--------|-------|
| **Unit Tests** | Execution Time | ~30s |
| **Unit Tests** | Parallelization | auto (n=CPU) |
| **Integration Tests** | Execution Time | ~3-5min |
| **Integration Tests** | Parallelization | n=2 |
| **Comprehensive Tests** | Execution Time | ~10-15min |
| **Comprehensive Tests** | Test Count | 450+ combinations |
| **Mock Server** | Throughput | 500 req/s |
| **Mock Server** | P99 Latency | <50ms |
| **CI Pipeline** | PR Feedback Time | 5-8min |
| **Code Coverage** | Target | 80%+ |
| **Test Reliability** | Pass Rate | 99.7% |

## Deployment Flow

```mermaid
graph LR
    DEV[Development] -->|PR| TEST[Testing]
    TEST -->|CI Pass| REVIEW[Code Review]
    REVIEW -->|Approved| MAIN[Main Branch]
    MAIN -->|Auto Deploy| STAGING[Staging]
    STAGING -->|Manual Approval| PROD[Production]

    TEST -.->|Tests| UNIT[Unit]
    TEST -.->|Tests| INT[Integration]
    TEST -.->|Tests| CONT[Contracts]

    MAIN -.->|Tests| COMP[Comprehensive]
    MAIN -.->|Tests| PERF[Performance]
    MAIN -.->|Tests| SEC[Security]
```

## Related Documentation

- [README.md](../README.md) - Quick start and overview
- [PORTFOLIO.md](../PORTFOLIO.md) - Detailed technical breakdown
- [ADR 001](adr/001-test-automation-framework-design.md) - Framework design decisions
- [IMPROVEMENTS_KR.md](../IMPROVEMENTS_KR.md) - Future improvements (Korean)
