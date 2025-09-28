#!/usr/bin/env python
"""Run security tests."""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from test.mock_server import mock_server_context
from test.test_runner import TestRunner, create_argument_parser, get_default_workers


def main():
    """Run security tests."""
    parser = create_argument_parser("security")
    parser.add_argument(
        "--vulnerability-scan",
        action="store_true",
        help="Run vulnerability scanning tests",
    )

    args = parser.parse_args()

    # Security tests configuration
    runner = TestRunner("security", Path(__file__).parent)

    # Build command
    extra_args = ["--tb=" + args.tb]

    if args.timeout:
        extra_args.extend(["--timeout", str(args.timeout)])
    else:
        extra_args.extend(["--timeout", "180"])

    if args.keyword:
        extra_args.extend(["-k", args.keyword])

    # Handle vulnerability scan option
    markers = args.markers
    if args.vulnerability_scan:
        vuln_marker = "vulnerability"
        markers = f"({markers}) and {vuln_marker}" if markers else vuln_marker

    # Get test path
    test_path = None
    if args.tests:
        test_path = " ".join(args.tests)

    # Security tests can have limited parallelism
    parallel = args.parallel or get_default_workers("security")

    cmd = runner.build_pytest_command(
        test_path=test_path,
        markers=markers,
        parallel=parallel,
        verbose=args.verbose,
        coverage=not args.no_coverage,
        extra_args=extra_args,
    )

    # Run tests with mock server
    with mock_server_context():
        return runner.run_command(cmd)


if __name__ == "__main__":
    sys.exit(main())
