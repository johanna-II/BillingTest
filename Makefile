.PHONY: test test-mock test-coverage test-contracts test-unit test-integration test-all clean

# Default test command
test:
	pytest -v

# Test with mock server
test-mock:
	@echo "Starting mock server..."
	python start_mock_server_simple.py &
	@sleep 5
	@echo "Running tests with mock..."
	USE_MOCK_SERVER=true pytest --use-mock -v
	@echo "Stopping mock server..."
	@pkill -f "start_mock_server_simple.py" || true

# Test with coverage
test-coverage:
	pytest --cov=libs --cov-report=term-missing --cov-report=html

# Contract tests only
test-contracts:
	pytest tests/contracts -v

# Unit tests only
test-unit:
	pytest tests/unit -v

# Integration tests only
test-integration:
	pytest tests/integration -v --use-mock

# Run all tests with coverage
test-all:
	USE_MOCK_SERVER=true pytest --use-mock --cov=libs --cov-report=term-missing --cov-fail-under=80

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf report/
