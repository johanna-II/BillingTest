# Testing Guide

## Quick Reference

```bash
# All tests
python run_tests.py --mode safe

# Fast feedback
python run_tests.py --mode fast tests -m "unit"

# Specific feature
python run_tests.py --mode default tests -m "credit"
```

## Test Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `default` | Sequential | Debugging |
| `parallel` | CPU/2 workers | General testing |
| `safe` | Mixed strategy | Recommended |
| `fast` | No coverage | Quick check |

## Test Markers

| Marker | Description | Example |
|--------|-------------|---------|
| `unit` | Fast unit tests | `-m unit` |
| `core` | Business logic | `-m core` |
| `api` | API tests | `-m api` |
| `contract` | Pact tests | `-m contract` |
| `serial` | No parallel | `-m serial` |
| `slow` | >5 seconds | `-m "not slow"` |

## Common Workflows

### Local Development
```bash
# After code changes
pytest tests/test_file.py -v

# Before commit
python run_tests.py --mode fast tests -m "unit"
```

### PR Testing
```bash
# Core functionality
python run_tests.py --mode default tests -m "core"

# Full suite
python run_tests.py --mode parallel
```

### CI/CD
```bash
# Quick check
pytest -m "unit and not slow"

# Integration
python run_tests.py --mode safe
```

## Mock Server

### Start Options
```bash
# With run_tests.py (auto-start)
python run_tests.py --mode default

# Docker Compose
docker-compose up -d

# Manual
cd mock_server && python run_server.py
```

### Endpoints
- `/health` - Health check
- `/api/v1/*` - Mock APIs
- `/openapi.json` - API spec
- `/test/reset` - Reset data

## Advanced Features

### Contract Testing
```bash
# Generate contracts
pytest tests/contracts/test_billing_consumer.py

# Verify provider
pytest tests/contracts/test_billing_provider.py
```

### Observability
```bash
# Enable telemetry
pytest --enable-telemetry

# With Jaeger
export JAEGER_ENABLED=true
pytest --enable-telemetry
```

### OpenAPI Validation
```bash
# Validate request
curl -X POST http://localhost:5000/openapi/validate \
  -H "Content-Type: application/json" \
  -d '{"method": "POST", "path": "/api/v1/credits", "body": {...}}'
```

## Troubleshooting

### Import Errors
```bash
export PYTHONPATH=$PWD
python run_tests.py --mode default
```

### Flaky Tests
- Use `@pytest.mark.serial` for state-dependent tests
- Check `/test/reset` endpoint functionality
- Verify unique UUID generation

### Mock Server Issues
```bash
# Check port
netstat -an | grep 5000

# Kill process (Windows)
taskkill /F /IM python.exe

# Kill process (Unix)
lsof -ti:5000 | xargs kill -9
```

## Performance Tips

- Use markers to run subsets: `-m "unit and not slow"`
- Enable parallel execution: `--mode parallel`
- Disable coverage for speed: `--no-coverage`
- Run failed tests first: `pytest --lf`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `USE_MOCK_SERVER` | Enable mock | `true` |
| `PYTHONPATH` | Module path | Current dir |
| `JAEGER_ENABLED` | Tracing | `false` |
| `JAEGER_HOST` | Jaeger host | `localhost` |
