.PHONY: help install test lint format clean docker-build test-docker test-local

# Default target
help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies with Poetry"
	@echo "  make test          - Run all tests (Docker)"
	@echo "  make test-unit     - Run unit tests only"
	@echo "  make test-local    - Run tests locally (no Docker)"
	@echo "  make lint          - Run linting and auto-fix"
	@echo "  make format        - Format code with Black"
	@echo "  make clean         - Clean up temporary files"
	@echo "  make docker-build  - Build Docker images"

# Installation
install:
	poetry install
	pre-commit install

# Testing - Docker (default)
test:
	python scripts/run_tests.py

test-unit:
	python scripts/run_tests.py unit

test-integration:
	python scripts/run_tests.py integration

test-contracts:
	python scripts/run_tests.py contracts

# Testing - Local (no Docker)
test-local:
	python scripts/run_tests.py --local

test-local-unit:
	python scripts/run_tests.py unit --local

test-local-integration:
	python scripts/run_tests.py integration --local

# Testing with coverage
test-coverage:
	python scripts/run_tests.py unit --coverage

# Docker management
docker-build:
	docker compose -f docker-compose.test.yml build

docker-build-no-cache:
	docker compose -f docker-compose.test.yml build --no-cache

docker-clean:
	docker compose -f docker-compose.test.yml down -v

# Linting and formatting
lint:
	@echo "Running Ruff linter with auto-fix..."
	ruff check . --fix --show-fixes

lint-check:
	@echo "Running Ruff check only (no auto-fix)..."
	ruff check .

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

# Cleaning
clean:
	@echo "Cleaning up temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete

# CI/CD helpers
ci-setup:
	@echo "Setting up CI environment..."
	pip install requests

ci-test:
	@echo "Running CI tests..."
	python scripts/run_tests.py unit
