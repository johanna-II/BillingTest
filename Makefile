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
	@echo "Formatting code with Ruff..."
	ruff format .

format-check:
	@echo "Checking code formatting with Black..."
	black --check --diff .
	@echo "Checking code formatting with Ruff..."
	ruff format --check --diff .

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
