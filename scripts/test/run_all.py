#!/usr/bin/env python
"""Run all test categories in the correct order."""

import argparse
import subprocess
import sys
from pathlib import Path

# Test execution order and configuration
TEST_STAGES = [
    # (category, description, default_args)
    ("unit", "Unit Tests (No External Dependencies)", ["--parallel", "4"]),
    ("integration", "Integration Tests (With Mock Server)", []),
    ("contracts", "Contract Tests (API Contracts)", []),
    ("security", "Security Tests", ["--parallel", "2"]),
    ("performance", "Performance Tests (Serial Only)", []),
]


def run_category(
    category: str, args: list[str], project_root: Path
) -> tuple[bool, float]:
    """Run a test category and return success status and duration."""
    import time

    runner_script = project_root / "scripts" / "test" / "run_category.py"
    cmd = [sys.executable, str(runner_script), category] + args

    start_time = time.time()
    result = subprocess.run(cmd, check=False)
    duration = time.time() - start_time

    return result.returncode == 0, duration


def print_summary(results: list[tuple[str, bool, float]]):
    """Print test execution summary."""
    print("\n" + "=" * 70)
    print("TEST EXECUTION SUMMARY")
    print("=" * 70)

    total_duration = sum(duration for _, _, duration in results)
    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed

    print("\nResults:")
    for category, success, duration in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {category:15} {status:12} ({duration:.1f}s)")

    print(f"\nTotal: {passed} passed, {failed} failed in {total_duration:.1f}s")

    if failed == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n❌ {failed} test suite(s) failed")


def main():
    """Run all test categories."""
    parser = argparse.ArgumentParser(
        description="Run all test categories in order",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script runs all test categories in the following order:
1. Unit tests (parallel)
2. Integration tests (with mock server)
3. Contract tests
4. Security tests
5. Performance tests (serial)

You can skip categories or override their arguments.

Examples:
  python scripts/test/run_all.py
  python scripts/test/run_all.py --skip unit,performance
  python scripts/test/run_all.py --only unit,integration
  python scripts/test/run_all.py --unit-args "--parallel 2"
        """,
    )

    parser.add_argument("--skip", help="Comma-separated list of categories to skip")

    parser.add_argument(
        "--only", help="Comma-separated list of categories to run (skip all others)"
    )

    parser.add_argument(
        "--fail-fast", action="store_true", help="Stop on first test failure"
    )

    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Disable coverage reporting for all tests",
    )

    # Add category-specific argument overrides
    for category, _, _ in TEST_STAGES:
        parser.add_argument(
            f"--{category}-args", help=f"Override arguments for {category} tests"
        )

    args = parser.parse_args()

    # Determine which categories to run
    categories_to_run = [cat for cat, _, _ in TEST_STAGES]

    if args.only:
        only_cats = [c.strip() for c in args.only.split(",")]
        categories_to_run = [c for c in categories_to_run if c in only_cats]
    elif args.skip:
        skip_cats = [c.strip() for c in args.skip.split(",")]
        categories_to_run = [c for c in categories_to_run if c not in skip_cats]

    # Run tests
    project_root = Path(__file__).parent.parent.parent
    results = []

    print("=" * 70)
    print("RUNNING ALL TEST CATEGORIES")
    print("=" * 70)

    for category, description, default_args in TEST_STAGES:
        if category not in categories_to_run:
            continue

        # Get category-specific args
        category_args = default_args.copy()
        override_args = getattr(args, f"{category}_args", None)
        if override_args:
            category_args = override_args.split()

        # Add global options
        if args.no_coverage:
            category_args.append("--no-coverage")

        print(f"\n{'='*70}")
        print(f"Stage: {description}")
        print(f"{'='*70}")

        success, duration = run_category(category, category_args, project_root)
        results.append((category, success, duration))

        if not success and args.fail_fast:
            print("\n❌ Test failed. Stopping due to --fail-fast.")
            break

    # Print summary
    print_summary(results)

    # Exit with error if any tests failed
    return 0 if all(success for _, success, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
