#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Setting up Billing Test Development Environment${NC}\n"

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2 | cut -d '.' -f 1,2)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}❌ Python $REQUIRED_VERSION or higher is required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"

# Check Docker
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker installed${NC}"
    DOCKER_AVAILABLE=true
else
    echo -e "${YELLOW}⚠ Docker not found (optional, but recommended for integration tests)${NC}"
    DOCKER_AVAILABLE=false
fi

# Check Node.js (for frontend)
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js $NODE_VERSION${NC}"
    NODE_AVAILABLE=true
else
    echo -e "${YELLOW}⚠ Node.js not found (optional, needed for frontend development)${NC}"
    NODE_AVAILABLE=false
fi

echo ""

# Install Python dependencies
echo "📦 Installing Python dependencies..."

if command -v poetry &> /dev/null; then
    echo "Using Poetry..."
    poetry install --no-interaction
    PYTHON_CMD="poetry run python"
    PYTEST_CMD="poetry run pytest"
else
    echo "Using pip..."
    pip install -r requirements.txt
    pip install -r requirements-mock.txt
    PYTHON_CMD="python3"
    PYTEST_CMD="pytest"
fi

echo -e "${GREEN}✓ Python dependencies installed${NC}\n"

# Install development tools
echo "🔧 Installing development tools..."
pip install pre-commit ruff mypy black bandit vulture pytest-cov pytest-html pytest-benchmark

echo -e "${GREEN}✓ Development tools installed${NC}\n"

# Setup pre-commit hooks
echo "🎣 Setting up pre-commit hooks..."
if command -v pre-commit &> /dev/null; then
    pre-commit install
    echo -e "${GREEN}✓ Pre-commit hooks installed${NC}\n"
else
    echo -e "${YELLOW}⚠ pre-commit not found, skipping hook installation${NC}\n"
fi

# Setup frontend (if Node.js is available)
if [ "$NODE_AVAILABLE" = true ]; then
    echo "🎨 Setting up frontend..."
    if [ -d "web" ]; then
        cd web
        npm install
        cd ..
        echo -e "${GREEN}✓ Frontend dependencies installed${NC}\n"
    fi
fi

# Setup Docker (if available)
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo "🐳 Building Docker images..."
    docker-compose -f docker-compose.test.yml build --quiet
    echo -e "${GREEN}✓ Docker images built${NC}\n"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p htmlcov
mkdir -p .coverage_data
mkdir -p benchmarks
echo -e "${GREEN}✓ Directories created${NC}\n"

# Run quick validation
echo "✅ Running validation tests..."
$PYTEST_CMD tests/unit/ -v -n auto --maxfail=5 -q

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ Validation passed!${NC}\n"
else
    echo -e "\n${YELLOW}⚠ Some tests failed, but setup is complete${NC}\n"
fi

# Print next steps
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ Setup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo "📚 Quick Start Guide:"
echo ""
echo "  Run tests:"
echo "    $PYTEST_CMD tests/unit/ -v          # Unit tests"
echo "    $PYTEST_CMD tests/integration/ --use-mock -v  # Integration tests"
echo "    $PYTEST_CMD --use-mock              # All tests"
echo ""
echo "  Code quality:"
echo "    ruff check .                        # Lint code"
echo "    black .                             # Format code"
echo "    mypy libs --ignore-missing-imports  # Type check"
echo ""
echo "  Coverage:"
echo "    $PYTEST_CMD --cov=libs --cov-report=html"
echo "    open htmlcov/index.html"
echo ""

if [ "$DOCKER_AVAILABLE" = true ]; then
    echo "  Mock Server:"
    echo "    python -m mock_server.run_server   # Start locally"
    echo "    docker-compose -f docker-compose.test.yml up mock-server"
    echo ""
fi

if [ "$NODE_AVAILABLE" = true ]; then
    echo "  Frontend:"
    echo "    cd web && npm run dev              # Start dev server"
    echo "    cd web && npm run build            # Build for production"
    echo ""
fi

echo "  Useful commands:"
echo "    python tests/run_all_tests.py --suite=all  # Run all tests with runner"
echo "    python scripts/analyze_flaky_tests.py      # Analyze flaky tests"
echo ""

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo "📖 Documentation:"
echo "  - README.md         - Quick start and overview"
echo "  - PORTFOLIO.md      - Detailed technical breakdown"
echo "  - IMPROVEMENTS_KR.md - Improvement suggestions (Korean)"
echo ""

echo -e "${GREEN}Happy coding! 🎉${NC}\n"
