# Quick Start Guide

Get started with the project and run tests in 5 minutes!

## Fast Start (3 Steps)

### Step 1: Clone & Setup

```bash
git clone https://github.com/johanna-II/BillingTest.git
cd BillingTest

# Auto setup (Linux/Mac)
./scripts/setup-dev.sh

# Windows
scripts\setup-dev.bat
```

### Step 2: Run Tests

```bash
# Run all tests
pytest --use-mock

# Or use CLI
python -m tests.cli run --type=all
```

### Step 3: View Coverage

```bash
# Generate and open coverage report
python -m tests.cli coverage
```

Done!

---

## Commonly Used Commands

### Running Tests

```bash
# Unit tests (fast, 30 seconds)
pytest tests/unit/ -v -n auto

# Integration tests (uses Mock Server)
pytest tests/integration/ --use-mock -v

# Contract tests (API validation)
pytest tests/contracts/ --use-mock -v

# Performance tests
pytest tests/performance/ -v

# All tests with coverage
pytest --use-mock --cov=libs --cov-report=html
```

### Mock Server

```bash
# Start mock server
python -m mock_server.run_server

# Server will run at http://localhost:5001
# Swagger UI: http://localhost:5001/docs
```

### Using CLI

```bash
# Show help
python -m tests.cli --help

# Run specific test type
python -m tests.cli run --type=unit
python -m tests.cli run --type=integration
python -m tests.cli run --type=contracts

# Coverage report
python -m tests.cli coverage
```

---

## Test Categories

| Type | Command | Time | Description |
|------|--------|------|------|
| **Unit** | `pytest tests/unit/ -v -n auto` | ~30s | Unit tests |
| **Integration** | `pytest tests/integration/ --use-mock -v` | ~3-5min | Mock |
| **Contracts** | `pytest tests/contracts/ --use-mock -v` | ~2min | Contracts |
| **Performance** | `pytest tests/performance/ -v` | ~1-2min | Performance |
| **Property** | `pytest tests/unit/test_billing_*.py` | ~1min | Property |

---

## Frontend (Optional)

```bash
cd web
npm install
npm run dev
# Open http://localhost:3000
```

**Features:**

- Interactive billing calculator
- Real-time calculation
- Payment processing
- Statement history

---

## Troubleshooting

### Mock Server Connection Failed

```bash
# Check if server is running
curl http://localhost:5001/health

# Start server if not running
python -m mock_server.run_server
```

### Test Timeout

```bash
# Increase timeout
pytest --use-mock --timeout=300

# Or run sequentially
pytest tests/integration/ --use-mock -n 0
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or use Poetry
poetry install
```

### Coverage Not Generated

```bash
# Generate HTML coverage report
pytest --use-mock --cov=libs --cov-report=html

# Open report
open htmlcov/index.html  # Mac
start htmlcov/index.html  # Windows
```

---

## Environment Setup

### Python Version

- Requires Python 3.12+
- Use pyenv or conda for version management

### Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Or with Poetry
poetry install
```

### Docker (Optional)

```bash
# Run tests in Docker
docker-compose -f docker-compose.test.yml up

# With observability
docker-compose -f docker-compose.observability.yml up
```

---

## CI/CD

### GitHub Actions

- **ci.yml**: Runs on every PR/push
- **integration-tests-service.yml**: Full integration tests
- **scheduled-tests.yml**: Daily regression tests
- **security.yml**: Security scans

### Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Project Structure

```text
BillingTest/
├── libs/              # Core billing engine
├── tests/             # All test suites
│   ├── unit/         # Unit tests
│   ├── integration/  # Integration tests
│   ├── contracts/    # Contract tests
│   ├── performance/  # Performance tests
│   └── security/     # Security tests
├── mock_server/       # Mock API server
├── web/              # Next.js frontend
└── workers/          # Cloudflare Workers API
```

---

## Next Steps

1. Read [README.md](README.md) for full documentation
2. Check [PORTFOLIO.md](PORTFOLIO.md) for technical deep dive
3. Review [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design
4. Explore test files to understand coverage

---

## Need Help?

1. **README.md** - Full guide
2. **IMPROVEMENTS_KR.md** - Improvements & troubleshooting
3. **GitHub Issues** - Bug reports
4. **tests/cli.py** - CLI help: `python -m tests.cli --help`

---

Happy Testing!
