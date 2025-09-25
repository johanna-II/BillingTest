# Makefile for Billing Test Project

.PHONY: help install test lint lint-check format format-check mypy type-check pre-commit clean

help:
	@echo "Available commands:"
	@echo "  install       - Install dependencies"
	@echo "  test          - Run all tests"
	@echo "  lint          - Run linter with auto-fix for safe issues"
	@echo "  lint-check    - Run linter check only (no auto-fix)"
	@echo "  format        - Format code with black"
	@echo "  format-check  - Check code formatting without changing files"
	@echo "  mypy          - Run type checking"
	@echo "  type-check    - Alias for mypy"
	@echo "  pre-commit    - Run pre-commit hooks"
	@echo "  clean         - Clean up cache files"

install:
	pip install -r requirements.txt
	pre-commit install

test:
	pytest

# Docker-based tests
test-docker:
	python scripts/run_tests.py

test-docker-unit:
	python scripts/run_tests.py unit

test-docker-integration:
	python scripts/run_tests.py integration

test-docker-contracts:
	python scripts/run_tests.py contracts

# Build Docker images
docker-build:
	docker compose -f docker-compose.test.yml build

docker-build-no-cache:
	docker compose -f docker-compose.test.yml build --no-cache

# Local tests (no Docker)
test-local:
	python scripts/run_tests.py --local

test-local-unit:
	python scripts/run_tests.py unit --local

test-local-integration:
	python scripts/run_tests.py integration --local

# Linting commands
lint:
	@echo "Running Ruff with auto-fix for safe issues..."
	ruff check . --fix --show-fixes

lint-check:
	@echo "Running Ruff check only (no auto-fix)..."
	ruff check .

# Formatting commands
format:
	@echo "Formatting code with Black..."
	black .

format-check:
	@echo "Checking code formatting with Black..."
	black --check --diff .

# Type checking
mypy type-check:
	@echo "Running MyPy type checking..."
	mypy libs/ --strict

# Pre-commit
pre-commit:
	pre-commit run --all-files

# Clean up
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .mypy_cache .pytest_cache .ruff_cache
	rm -rf htmlcov coverage.xml .coverage
