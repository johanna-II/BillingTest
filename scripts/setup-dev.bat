@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   Billing Test Development Setup
echo ========================================
echo.

:: Check Python
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    exit /b 1
)
python --version
echo [OK] Python found
echo.

:: Check pip
echo [2/6] Checking pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not installed
    exit /b 1
)
echo [OK] pip found
echo.

:: Install dependencies
echo [3/6] Installing dependencies...
pip install -r requirements.txt
pip install -r requirements-mock.txt
echo [OK] Dependencies installed
echo.

:: Install dev tools
echo [4/6] Installing development tools...
pip install pre-commit ruff mypy black bandit vulture pytest-cov pytest-html pytest-benchmark
echo [OK] Development tools installed
echo.

:: Setup pre-commit
echo [5/6] Setting up pre-commit hooks...
pre-commit install >nul 2>&1
if errorlevel 1 (
    echo [WARN] pre-commit not available, skipping hooks
) else (
    echo [OK] Pre-commit hooks installed
)
echo.

:: Create directories
echo [6/6] Creating directories...
if not exist "logs" mkdir logs
if not exist "htmlcov" mkdir htmlcov
if not exist ".coverage_data" mkdir .coverage_data
if not exist "benchmarks" mkdir benchmarks
echo [OK] Directories created
echo.

:: Run quick test
echo ========================================
echo   Running validation tests...
echo ========================================
echo.
pytest tests/unit/ -v -n auto --maxfail=5 -q

if errorlevel 1 (
    echo.
    echo [WARN] Some tests failed, but setup is complete
) else (
    echo.
    echo [OK] Validation passed!
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Quick Start Guide:
echo.
echo   Run tests:
echo     pytest tests/unit/ -v
echo     pytest tests/integration/ --use-mock -v
echo     pytest --use-mock
echo.
echo   Code quality:
echo     ruff check .
echo     black .
echo     mypy libs --ignore-missing-imports
echo.
echo   Coverage:
echo     pytest --cov=libs --cov-report=html
echo     start htmlcov\index.html
echo.
echo   Mock Server:
echo     python -m mock_server.run_server
echo.
echo   Frontend (if Node.js installed):
echo     cd web
echo     npm install
echo     npm run dev
echo.
echo Documentation:
echo   - README.md         - Quick start
echo   - PORTFOLIO.md      - Technical details
echo   - IMPROVEMENTS_KR.md - Improvements (Korean)
echo.
echo Happy coding! ^_^
echo.

endlocal
