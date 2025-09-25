#!/usr/bin/env python
"""Run integration tests."""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from test.mock_server import mock_server_context
from test.test_runner import (
    TestRunner,
    create_argument_parser,
    get_default_workers,
)


def main():
    """Run integration tests."""
    parser = create_argument_parser("integration")
    parser.add_argument(
        "--no-mock", action="store_true", help="Run without mock server"
    )
    parser.add_argument(
        "--mock-verbose", action="store_true", help="Show mock server output"
    )

    args = parser.parse_args()

    # Integration tests configuration
    runner = TestRunner("integration", Path(__file__).parent)

    # Build command
    extra_args = ["--tb=" + args.tb]

    if args.timeout:
        extra_args.extend(["--timeout", str(args.timeout)])
    else:
        # Default timeout for integration tests
        extra_args.extend(["--timeout", "60"])

    if args.keyword:
        extra_args.extend(["-k", args.keyword])

    # Get test path
    test_path = None
    if args.tests:
        test_path = " ".join(args.tests)

    # Integration tests typically run serially
    parallel = args.parallel or get_default_workers("integration")

    cmd = runner.build_pytest_command(
        test_path=test_path,
        markers=args.markers,
        parallel=parallel,
        verbose=args.verbose,
        coverage=not args.no_coverage,
        extra_args=extra_args,
    )

    # Run tests with or without mock server
    if args.no_mock:
        return runner.run_command(cmd)
    with mock_server_context(verbose=args.mock_verbose):
        return runner.run_command(cmd)


if __name__ == "__main__":
    sys.exit(main())
