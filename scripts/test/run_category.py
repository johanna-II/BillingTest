#!/usr/bin/env python
"""Run tests for a specific category."""

import sys
import subprocess
import argparse
from pathlib import Path


CATEGORIES = {
    'unit': 'tests/unit/run.py',
    'integration': 'tests/integration/run.py',
    'performance': 'tests/performance/run.py',
    'contracts': 'tests/contracts/run.py',
    'security': 'tests/security/run.py',
}


def main():
    """Run tests for a specific category."""
    parser = argparse.ArgumentParser(
        description='Run tests for a specific category',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available categories:
  unit         - Unit tests (fast, no external dependencies)
  integration  - Integration tests (with mock server)
  performance  - Performance tests (serial execution)
  contracts    - Contract tests (API contracts)
  security     - Security tests (vulnerability scanning)

Examples:
  python scripts/test/run_category.py unit
  python scripts/test/run_category.py integration --parallel 2
  python scripts/test/run_category.py unit tests/unit/test_calculation_unit.py
        """
    )
    
    parser.add_argument(
        'category',
        choices=list(CATEGORIES.keys()),
        help='Test category to run'
    )
    
    parser.add_argument(
        'args',
        nargs=argparse.REMAINDER,
        help='Additional arguments to pass to the category runner'
    )
    
    args = parser.parse_args()
    
    # Get the runner script
    runner_script = CATEGORIES[args.category]
    project_root = Path(__file__).parent.parent.parent
    runner_path = project_root / runner_script
    
    if not runner_path.exists():
        print(f"Error: Runner script not found: {runner_path}")
        return 1
    
    # Build command
    cmd = [sys.executable, str(runner_path)]
    if args.args:
        # Remove leading '--' if present
        extra_args = args.args
        if extra_args and extra_args[0] == '--':
            extra_args = extra_args[1:]
        cmd.extend(extra_args)
    
    # Execute
    print(f"Running {args.category} tests...")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    return subprocess.run(cmd).returncode


if __name__ == '__main__':
    sys.exit(main())
