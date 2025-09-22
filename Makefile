# Makefile for BillingTest project
# Cross-platform support for Windows (with make), macOS, and Linux

.PHONY: help install test test-unit test-integration test-coverage test-docker \
        test-all clean lint format security-check docker-build docker-test \
        docker-test-all coverage-report

# Default Python command
PYTHON := python3
ifeq ($(OS),Windows_NT)
    PYTHON := python
endif

# Project directories
SRC_DIR := libs
TEST_DIR := tests
UNIT_TEST_DIR := tests/unit

# Coverage settings
COV_OMIT := --cov-omit=libs/observability/*,libs/dependency_injection.py

help: ## Show this help message
	@echo "BillingTest - Makefile Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install project dependencies
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt
	@echo "✅ Dependencies installed"

test: test-unit ## Run unit tests (alias for test-unit)

test-unit: ## Run unit tests with basic coverage
	$(PYTHON) -m pytest $(UNIT_TEST_DIR) --cov=$(SRC_DIR) $(COV_OMIT) --cov-report=term-missing -q

test-integration: ## Run integration tests
	$(PYTHON) -m pytest $(TEST_DIR) -m "integration or mock_required" -v

test-coverage: ## Run tests with full coverage report
	$(PYTHON) -m pytest $(UNIT_TEST_DIR) \
		--cov=$(SRC_DIR) $(COV_OMIT) \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-report=xml \
		--junit-xml=report/junit.xml \
		-v

test-parallel: ## Run tests in parallel (requires pytest-xdist)
	$(PYTHON) -m pytest $(UNIT_TEST_DIR) --cov=$(SRC_DIR) $(COV_OMIT) -n auto -q

test-all: ## Run all tests (unit, integration, performance, security)
	$(PYTHON) -m pytest $(TEST_DIR) --cov=$(SRC_DIR) $(COV_OMIT) --cov-report=term-missing -v

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf htmlcov/ .pytest_cache/ .coverage.* 2>/dev/null || true
	rm -rf report/*.xml report/*.json 2>/dev/null || true
	@echo "✅ Cleaned up generated files"

lint: ## Run code quality checks
	$(PYTHON) -m ruff check $(SRC_DIR) $(TEST_DIR)
	$(PYTHON) -m mypy $(SRC_DIR) --strict

format: ## Format code with Black and Ruff
	$(PYTHON) -m black $(SRC_DIR) $(TEST_DIR)
	$(PYTHON) -m ruff check --fix $(SRC_DIR) $(TEST_DIR)
	@echo "✅ Code formatted"

security-check: ## Run security vulnerability scan
	$(PYTHON) -m bandit -r $(SRC_DIR) -f json -o report/security_scan.json
	@echo "✅ Security scan complete. Check report/security_scan.json"

# Docker commands
docker-build: ## Build Docker test image
	docker build -f Dockerfile.test -t billingtest:latest .
	@echo "✅ Docker image built"

docker-test: ## Run tests in Docker container
	docker-compose -f docker-compose.test.yml run --rm test-full

docker-test-quick: ## Run quick tests in Docker
	docker-compose -f docker-compose.test.yml run --rm test-quick

docker-test-all: ## Run all test configurations in Docker
	docker-compose -f docker-compose.test.yml up --abort-on-container-exit

docker-clean: ## Clean up Docker containers and images
	docker-compose -f docker-compose.test.yml down -v
	docker-compose -f docker-compose.yml down -v
	@echo "✅ Docker cleanup complete"

# Coverage report
coverage-report: test-coverage ## Generate and open coverage report
	@echo "✅ Coverage report generated in htmlcov/"
ifeq ($(OS),Windows_NT)
	@start htmlcov/index.html 2>/dev/null || echo "Open htmlcov/index.html in your browser"
else ifeq ($(shell uname),Darwin)
	@open htmlcov/index.html 2>/dev/null || echo "Open htmlcov/index.html in your browser"
else
	@xdg-open htmlcov/index.html 2>/dev/null || echo "Open htmlcov/index.html in your browser"
endif

# Development workflow shortcuts
dev-test: clean test-unit ## Clean and run unit tests (development workflow)

dev-check: clean lint test-coverage ## Full check: clean, lint, and test with coverage

ci: clean lint security-check test-coverage ## CI pipeline: all checks

# Platform-specific test runners
test-windows: ## Run tests using Windows PowerShell script
ifeq ($(OS),Windows_NT)
	powershell -ExecutionPolicy Bypass -File run_tests_windows.ps1 -Coverage
else
	@echo "This command is for Windows only"
endif

test-unix: ## Run tests using Unix shell script
ifneq ($(OS),Windows_NT)
	./run_tests_unix.sh -c
else
	@echo "This command is for Unix/Linux/macOS only"
endif

test-cross-platform: ## Run tests using cross-platform Python script
	$(PYTHON) run_tests_cross_platform.py --coverage --verbose

# Environment setup
setup-dev: install ## Set up development environment
	$(PYTHON) -m pip install -r requirements.txt
	@echo "✅ Development environment ready"

# Performance testing
test-performance: ## Run performance tests
	$(PYTHON) -m pytest tests/performance/ -v

# Contract testing
test-contracts: ## Run contract tests
	$(PYTHON) -m pytest tests/contracts/ -v
