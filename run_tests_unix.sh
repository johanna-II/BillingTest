#!/bin/bash
# Unix/Linux/macOS shell script for running billing tests
# Supports bash 3.2+ (macOS default) and modern Linux distributions

# Default values
TEST_DIR="tests/unit"
COVERAGE=false
NO_OBSERVABILITY=false
VERBOSE=false
MARKERS=""
PATTERN=""
PARALLEL=0
INSTALL_DEPS=false
DOCKER=false
PYTEST_ARGS=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

# Function to show help
show_help() {
    cat << EOF
BillingTest - Unix/Linux/macOS Test Runner

Usage: ./run_tests_unix.sh [options] [test_directory]

Options:
    -c, --coverage          Run with coverage report
    -n, --no-observability  Exclude observability from coverage
    -v, --verbose           Verbose output
    -m, --markers EXPR      Run tests matching mark expression
    -k, --pattern PATTERN   Run tests matching pattern
    -p, --parallel N        Number of parallel workers
    -i, --install-deps      Install dependencies first
    -d, --docker            Run tests in Docker container
    -a, --pytest-args ARGS  Additional pytest arguments
    -h, --help              Show this help message

Examples:
    # Run unit tests with coverage
    ./run_tests_unix.sh -c

    # Run specific tests in parallel
    ./run_tests_unix.sh -k "test_payment" -p 4

    # Run tests in Docker
    ./run_tests_unix.sh -d -c

EOF
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -n|--no-observability)
            NO_OBSERVABILITY=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -m|--markers)
            MARKERS="$2"
            shift 2
            ;;
        -k|--pattern)
            PATTERN="$2"
            shift 2
            ;;
        -p|--parallel)
            PARALLEL="$2"
            shift 2
            ;;
        -i|--install-deps)
            INSTALL_DEPS=true
            shift
            ;;
        -d|--docker)
            DOCKER=true
            shift
            ;;
        -a|--pytest-args)
            PYTEST_ARGS="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        *)
            # Assume it's the test directory
            TEST_DIR="$1"
            shift
            ;;
    esac
done

# Get script directory (works on macOS and Linux)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

# Function to check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Find Python command
PYTHON_CMD=""
for cmd in python3 python py; do
    if command_exists "$cmd"; then
        PYTHON_CMD="$cmd"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    print_color "$RED" "Error: Python not found. Please install Python 3.8+ and add it to PATH."
    exit 1
fi

# Show Python version
print_color "$GREEN" "Using Python: $PYTHON_CMD"
$PYTHON_CMD --version

# Detect OS
OS_TYPE="Unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="Linux"
elif [[ "$OSTYPE" == "freebsd"* ]]; then
    OS_TYPE="FreeBSD"
fi
print_color "$CYAN" "Operating System: $OS_TYPE"

# Install dependencies if requested
if [ "$INSTALL_DEPS" = true ]; then
    print_color "$YELLOW" "\nInstalling dependencies..."
    
    if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        $PYTHON_CMD -m pip install -r "$PROJECT_ROOT/requirements.txt"
        if [ $? -ne 0 ]; then
            print_color "$RED" "Failed to install dependencies"
            exit 1
        fi
        print_color "$GREEN" "Dependencies installed successfully"
    else
        print_color "$YELLOW" "Warning: requirements.txt not found"
    fi
fi

# Run tests in Docker if requested
if [ "$DOCKER" = true ]; then
    print_color "$YELLOW" "\nRunning tests in Docker..."
    
    if ! command_exists docker; then
        print_color "$RED" "Error: Docker not found. Please install Docker."
        exit 1
    fi
    
    # Build Docker command
    DOCKER_CMD="docker run --rm -v $PROJECT_ROOT:/app -w /app python:3.12-slim bash -c"
    
    # Build inner command
    INNER_CMD="pip install -r requirements.txt && python -m pytest"
    
    if [ "$COVERAGE" = true ]; then
        INNER_CMD="$INNER_CMD --cov=libs --cov-report=term-missing --cov-report=html --cov-report=xml"
        if [ "$NO_OBSERVABILITY" = true ]; then
            INNER_CMD="$INNER_CMD --cov-omit=libs/observability/* --cov-omit=libs/dependency_injection.py"
        fi
    fi
    
    INNER_CMD="$INNER_CMD $TEST_DIR"
    
    if [ "$VERBOSE" = true ]; then
        INNER_CMD="$INNER_CMD -v"
    else
        INNER_CMD="$INNER_CMD -q"
    fi
    
    [ -n "$MARKERS" ] && INNER_CMD="$INNER_CMD -m \"$MARKERS\""
    [ -n "$PATTERN" ] && INNER_CMD="$INNER_CMD -k \"$PATTERN\""
    [ "$PARALLEL" -gt 0 ] && INNER_CMD="$INNER_CMD -n $PARALLEL"
    [ -n "$PYTEST_ARGS" ] && INNER_CMD="$INNER_CMD $PYTEST_ARGS"
    
    eval "$DOCKER_CMD \"$INNER_CMD\""
    exit $?
fi

# Build pytest command
CMD="$PYTHON_CMD -m pytest"

# Add coverage options
if [ "$COVERAGE" = true ]; then
    CMD="$CMD --cov=libs --cov-report=term-missing --cov-report=html --cov-report=xml"
    
    if [ "$NO_OBSERVABILITY" = true ]; then
        CMD="$CMD --cov-omit=libs/observability/*,libs/dependency_injection.py"
    fi
fi

# Add test directory
CMD="$CMD $TEST_DIR"

# Add verbosity
if [ "$VERBOSE" = true ]; then
    CMD="$CMD -v"
else
    CMD="$CMD -q"
fi

# Add markers
[ -n "$MARKERS" ] && CMD="$CMD -m \"$MARKERS\""

# Add pattern
[ -n "$PATTERN" ] && CMD="$CMD -k \"$PATTERN\""

# Add parallel execution
[ "$PARALLEL" -gt 0 ] && CMD="$CMD -n $PARALLEL"

# Add additional pytest args
[ -n "$PYTEST_ARGS" ] && CMD="$CMD $PYTEST_ARGS"

# Set environment variables
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Show command if verbose
if [ "$VERBOSE" = true ]; then
    print_color "$CYAN" "\nRunning command: $CMD"
    print_color "$CYAN" "Working directory: $PROJECT_ROOT"
fi

# Change to project directory
cd "$PROJECT_ROOT" || exit 1

# Run tests
print_color "$YELLOW" "\nRunning tests..."
eval "$CMD"
EXIT_CODE=$?

# Show results
if [ $EXIT_CODE -eq 0 ]; then
    print_color "$GREEN" "\nTests passed successfully!"
else
    print_color "$RED" "\nTests failed with exit code: $EXIT_CODE"
fi

# Show coverage report location if generated
if [ "$COVERAGE" = true ]; then
    HTML_REPORT="$PROJECT_ROOT/htmlcov/index.html"
    if [ -f "$HTML_REPORT" ]; then
        print_color "$CYAN" "\nCoverage report generated: $HTML_REPORT"
        
        # Try to open in browser based on OS
        if [[ "$OSTYPE" == "darwin"* ]]; then
            print_color "$CYAN" "Open in browser: open $HTML_REPORT"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            print_color "$CYAN" "Open in browser: xdg-open $HTML_REPORT"
        fi
    fi
fi

exit $EXIT_CODE
