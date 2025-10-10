"""Runner script for integration tests with optimizations."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# Coverage options
COV_REPORT_TERM_MISSING = "--cov-report=term-missing"
COV_LIBS = "--cov=libs"

# Test options
TB_SHORT = "--tb=short"


def run_integration_tests(args):
    """Run integration tests with optimizations."""
    # Set environment variables for optimization
    env = os.environ.copy()
    env["USE_MOCK_SERVER"] = "true"
    env["MOCK_OPTIMIZE_MODE"] = "true"

    # Build pytest command
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/integration/",
        "-v",
        TB_SHORT,
        "--use-mock",  # Always use mock for integration tests
    ]

    # Add parallel execution if requested
    if args.parallel:
        cmd.extend(["-n", str(args.workers)])

    # Add specific test file if provided
    if args.test_file:
        cmd[-1] = f"tests/integration/{args.test_file}"

    # Add specific test function if provided
    if args.test_function:
        cmd.append(f"-k {args.test_function}")

    # Add coverage if requested
    if args.coverage:
        cmd.extend([COV_LIBS, "--cov-report=html", COV_REPORT_TERM_MISSING])

    # Add markers
    if not args.slow:
        cmd.extend(["-m", "not slow"])

    print(f"Running command: {' '.join(cmd)}")

    # Run tests
    result = subprocess.run(cmd, env=env, check=False)
    return result.returncode


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run integration tests with optimizations"
    )

    parser.add_argument(
        "--parallel", "-n", action="store_true", help="Run tests in parallel"
    )

    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=2,
        help="Number of parallel workers (default: 2, reduced from 4 for stability)",
    )

    parser.add_argument(
        "--test-file",
        "-f",
        help="Specific test file to run (e.g., test_billing_workflows.py)",
    )

    parser.add_argument("--test-function", "-k", help="Specific test function to run")

    parser.add_argument(
        "--coverage", "-c", action="store_true", help="Run with coverage report"
    )

    parser.add_argument("--slow", action="store_false", help="Skip slow tests")

    args = parser.parse_args()

    # Run tests
    exit_code = run_integration_tests(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
