#!/usr/bin/env python
"""Run performance tests."""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from test.mock_server import mock_server_context
from test.test_runner import TestRunner, create_argument_parser


def main():
    """Run performance tests."""
    parser = create_argument_parser("performance")
    parser.add_argument(
        "--mock-verbose", action="store_true", help="Show mock server output"
    )

    args = parser.parse_args()

    # Performance tests configuration
    runner = TestRunner("performance", Path(__file__).parent)

    # Build command
    extra_args = ["--tb=" + args.tb]

    # Performance tests need longer timeout
    if args.timeout:
        extra_args.extend(["--timeout", str(args.timeout)])
    else:
        extra_args.extend(["--timeout", "300"])

    if args.keyword:
        extra_args.extend(["-k", args.keyword])

    # Get test path
    test_path = None
    if args.tests:
        test_path = " ".join(args.tests)

    # Performance tests MUST run serially
    if args.parallel > 0:
        print(
            "⚠️  Warning: Performance tests should run serially. Ignoring parallel option."
        )

    cmd = runner.build_pytest_command(
        test_path=test_path,
        markers=args.markers,
        parallel=0,  # Always serial
        verbose=args.verbose,
        coverage=not args.no_coverage,
        extra_args=extra_args,
    )

    # Run tests with mock server
    with mock_server_context(verbose=args.mock_verbose) as mock_url:
        print(f"Mock server available at: {mock_url}")
        return runner.run_command(cmd)


if __name__ == "__main__":
    sys.exit(main())
