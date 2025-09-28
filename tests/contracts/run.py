#!/usr/bin/env python
"""Run contract tests."""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from test.mock_server import mock_server_context
from test.test_runner import TestRunner, create_argument_parser


def main():
    """Run contract tests."""
    parser = create_argument_parser("contracts")
    parser.add_argument(
        "--provider", action="store_true", help="Run provider tests only"
    )
    parser.add_argument(
        "--consumer", action="store_true", help="Run consumer tests only"
    )

    args = parser.parse_args()

    # Contract tests configuration
    runner = TestRunner("contracts", Path(__file__).parent)

    # Build command
    extra_args = ["--tb=" + args.tb]

    if args.timeout:
        extra_args.extend(["--timeout", str(args.timeout)])
    else:
        extra_args.extend(["--timeout", "120"])

    if args.keyword:
        extra_args.extend(["-k", args.keyword])

    # Handle provider/consumer selection
    markers = args.markers
    if args.provider and not args.consumer:
        provider_marker = "provider"
        markers = f"({markers}) and {provider_marker}" if markers else provider_marker
    elif args.consumer and not args.provider:
        consumer_marker = "consumer"
        markers = f"({markers}) and {consumer_marker}" if markers else consumer_marker

    # Get test path
    test_path = None
    if args.tests:
        test_path = " ".join(args.tests)

    # Contract tests run serially
    cmd = runner.build_pytest_command(
        test_path=test_path,
        markers=markers,
        parallel=0,  # Always serial
        verbose=args.verbose,
        coverage=not args.no_coverage,
        extra_args=extra_args,
    )

    # Run tests with mock server
    with mock_server_context():
        return runner.run_command(cmd)


if __name__ == "__main__":
    sys.exit(main())
