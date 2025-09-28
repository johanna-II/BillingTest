# Makefile for BillingTest project
# Optimized for test-driven development

.PHONY: help install test unit integration contract clean lint format type-check coverage monitor ci-test

# Default target
help:
	@echo "BillingTest - Test Automation Commands"
	@echo "====================================="
	@echo "Setup:"
	@echo "  make install       - Install all dependencies"
	@echo "  make install-dev   - Install with dev tools"
	@echo ""
	@echo "Testing (Optimized Order):"
	@echo "  make test          - Run all tests (unit->integration->contract)"
	@echo "  make unit          - Run unit tests only (fastest)"
	@echo "  make integration   - Run integration tests"
	@echo "  make contract      - Run contract tests"
	@echo "  make test-fast     - Run tests in parallel"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          - Run all linters"
	@echo "  make format        - Format code with black"
	@echo "  make type-check    - Run mypy type checking"
	@echo "  make static        - Run all static analysis"
	@echo ""
	@echo "Monitoring:"
	@echo "  make coverage      - Generate coverage report"
	@echo "  make monitor       - Monitor test performance"
	@echo "  make benchmark     - Run performance benchmarks"
	@echo ""
	@echo "CI/CD:"
	@echo "  make ci-test       - Run CI test pipeline"
	@echo "  make pre-commit    - Install pre-commit hooks"
	@echo "  make validate      - Validate everything (for PR)"

# Python interpreter
PYTHON := python
PIP := $(PYTHON) -m pip

# Directories
LIBS_DIR := libs
TESTS_DIR := tests
UNIT_DIR := $(TESTS_DIR)/unit
INT_DIR := $(TESTS_DIR)/integration
CONTRACT_DIR := $(TESTS_DIR)/contracts

# Coverage settings
COV_MIN := 80

# Installation targets
install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-test.txt

install-dev: install
	$(PIP) install pre-commit
	pre-commit install

# Test targets - Optimized execution order
test: static unit
	@echo "✅ All static checks passed, running tests..."
	@$(PYTHON) tests/run_all_tests.py --suite all

test-fast:
	@$(PYTHON) tests/run_all_tests.py --suite all --no-parallel

# Individual test suites
unit:
	@echo "🧪 Running unit tests..."
	@$(PYTHON) -m pytest $(UNIT_DIR) -v --tb=short \
		--cov=$(LIBS_DIR) --cov-report=term-missing \
		-n auto

integration:
	@echo "🔗 Running integration tests..."
	@$(PYTHON) -m pytest $(INT_DIR) -v --tb=short \
		--cov=$(LIBS_DIR) --cov-report=term-missing \
		-n 4

contract:
	@echo "📜 Running contract tests..."
	@$(PYTHON) -m pytest $(CONTRACT_DIR) -v --tb=short \
		--cov=$(LIBS_DIR) --cov-report=term-missing

# Static analysis
static: lint type-check

lint:
	@echo "🔍 Running linters..."
	@black --check .
	@ruff check .

format:
	@echo "🎨 Formatting code..."
	@black .
	@ruff check --fix .

type-check:
	@echo "🔤 Type checking..."
	@mypy $(LIBS_DIR) --ignore-missing-imports

# Coverage and monitoring
coverage:
	@echo "📊 Generating coverage report..."
	@coverage report
	@coverage html
	@echo "Coverage report: file://$$(pwd)/htmlcov/index.html"

monitor:
	@echo "📈 Monitoring test performance..."
	@$(PYTHON) tests/test_monitor.py --save-baseline

benchmark:
	@echo "⚡ Running benchmarks..."
	@$(PYTHON) -m pytest $(UNIT_DIR) --benchmark-only -v

# CI/CD targets
ci-test: clean
	@echo "🚀 Running CI test pipeline..."
	@make static
	@$(PYTHON) tests/run_all_tests.py --suite all --use-mock

pre-commit:
	@pre-commit run --all-files

validate: clean static test coverage
	@echo "✅ All validations passed!"

# Utility targets
clean:
	@echo "🧹 Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name ".coverage" -delete
	@rm -rf htmlcov/
	@rm -rf test-results/
	@rm -f coverage*.xml

# Quick test commands for development
qt: unit  # Quick test - unit only
ft: test-fast  # Full test - all suites fast
st: static  # Static analysis only

# Watch for changes and run tests
watch:
	@echo "👀 Watching for changes..."
	@watchmedo shell-command \
		--patterns="*.py" \
		--recursive \
		--command='make unit' \
		.