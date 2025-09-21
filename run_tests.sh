#!/bin/bash

# Unified test runner for Linux/macOS (Bash)

# Default values
MODE="default"
NO_COVERAGE=false
SKIP_HEALTH_CHECK=false
PYTEST_ARGS=()

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --no-coverage)
            NO_COVERAGE=true
            shift
            ;;
        --skip-health-check)
            SKIP_HEALTH_CHECK=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS] [PYTEST_ARGS...]"
            echo ""
            echo "Options:"
            echo "  --mode MODE           Test execution mode (default|parallel|safe|fast|ultra|super)"
            echo "  --no-coverage         Disable coverage reporting"
            echo "  --skip-health-check   Skip mock server health check"
            echo "  -h, --help           Show this help message"
            echo ""
            echo "Any additional arguments are passed directly to pytest"
            exit 0
            ;;
        *)
            PYTEST_ARGS+=("$1")
            shift
            ;;
    esac
done

# Validate mode
if [[ ! "$MODE" =~ ^(default|parallel|safe|fast|ultra|super)$ ]]; then
    echo "Error: Invalid mode '$MODE'. Valid modes are: default, parallel, safe, fast, ultra, super"
    exit 1
fi

echo "Starting tests with mock server (Mode: $MODE)..."

# Set environment variables
export USE_MOCK_SERVER=true

# Additional environment variables for optimization modes
if [[ "$MODE" == "super" || "$MODE" == "ultra" ]]; then
    export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
    export PYTEST_CURRENT_TEST=1
fi

# Start mock server in background
echo "Starting mock server..."
python -m mock_server.run_server &
MOCK_PID=$!

# Function to stop mock server
cleanup() {
    echo "Stopping mock server..."
    kill $MOCK_PID 2>/dev/null
}

# Ensure cleanup on exit
trap cleanup EXIT

# Health check for mock server (unless skipped)
if [[ "$SKIP_HEALTH_CHECK" != "true" ]]; then
    echo "Waiting for mock server to be ready..."
    ready=false
    for i in {1..30}; do
        if curl -f http://localhost:5000/health >/dev/null 2>&1; then
            echo "Mock server is ready!"
            ready=true
            break
        fi
        sleep 1
    done
    
    if [[ "$ready" != "true" ]]; then
        echo "Mock server failed to start!"
        exit 1
    fi
else
    # Simple wait when health check is skipped
    sleep 2
fi

# Get CPU count
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CPU_COUNT=$(sysctl -n hw.ncpu)
else
    # Linux
    CPU_COUNT=$(nproc)
fi
echo "Detected $CPU_COUNT CPU cores"

# Build pytest command based on mode
PYTEST_CMD=(pytest --use-mock)

case "$MODE" in
    "default")
        # Basic sequential execution
        PYTEST_CMD+=(-v)
        ;;
    
    "parallel")
        # Moderate parallelization
        WORKERS=$((CPU_COUNT / 2))
        [[ $WORKERS -lt 2 ]] && WORKERS=2
        echo "Using $WORKERS parallel workers"
        PYTEST_CMD+=(-v -n $WORKERS --dist loadscope)
        ;;
    
    "safe")
        # Run credit tests sequentially first
        echo "Running credit tests sequentially..."
        pytest --use-mock -v tests/test_credit_all.py tests/test_unpaid_and_credit.py
        
        if [[ $? -ne 0 ]]; then
            echo "Credit tests failed!"
            exit 1
        fi
        
        # Run remaining tests in parallel
        WORKERS=$((CPU_COUNT / 2))
        [[ $WORKERS -lt 2 ]] && WORKERS=2
        echo "Running remaining tests with $WORKERS workers..."
        PYTEST_CMD+=(-v -n $WORKERS --dist loadscope 
                     --ignore tests/test_credit_all.py 
                     --ignore tests/test_unpaid_and_credit.py)
        ;;
    
    "fast")
        # Fast parallel execution without coverage
        PYTEST_CMD+=(-v -x -n auto --tb=no -q --no-cov)
        NO_COVERAGE=true
        ;;
    
    "ultra")
        # Aggressive parallelization
        WORKERS=$((CPU_COUNT - 1))
        [[ $WORKERS -gt 5 ]] && WORKERS=5
        echo "Using $WORKERS parallel workers"
        PYTEST_CMD+=(-v -n $WORKERS --dist worksteal 
                     --maxfail 5 --tb=short --durations=10 
                     --no-header -p no:warnings)
        ;;
    
    "super")
        # Maximum optimization
        echo "Running with maximum optimization..."
        PYTEST_CMD=(python -m pytest tests 
                    --use-mock -n auto --dist worksteal 
                    -x --tb=line --no-header --quiet
                    --override-ini="addopts="
                    --override-ini="testpaths=tests")
        NO_COVERAGE=true
        ;;
esac

# Add coverage flag if needed
if [[ "$NO_COVERAGE" == "true" && "$MODE" != "fast" && "$MODE" != "super" ]]; then
    PYTEST_CMD+=(--no-cov)
fi

# Add user-provided arguments
PYTEST_CMD+=("${PYTEST_ARGS[@]}")

# Run tests
echo "Running tests: ${PYTEST_CMD[@]}"
"${PYTEST_CMD[@]}"

# Store test exit code
TEST_EXIT_CODE=$?

# Show summary
if [[ $TEST_EXIT_CODE -eq 0 ]]; then
    echo "All tests passed!"
else
    echo "Some tests failed!"
fi

# Exit with test exit code
exit $TEST_EXIT_CODE
