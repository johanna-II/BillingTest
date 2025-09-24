#!/usr/bin/env python
"""Run unit tests."""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).resolve().parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from test.test_runner import TestRunner, create_argument_parser, get_default_workers


def main():
    """Run unit tests."""
    parser = create_argument_parser('unit')
    parser.add_argument(
        '--no-telemetry',
        action='store_true',
        default=True,
        help='Skip telemetry tests (default: True)'
    )
    
    args = parser.parse_args()
    
    # Unit tests configuration
    runner = TestRunner('unit', Path(__file__).parent)
    
    # Build command
    extra_args = ['--tb=' + args.tb]
    
    if args.timeout:
        extra_args.extend(['--timeout', str(args.timeout)])
        
    if args.keyword:
        extra_args.extend(['-k', args.keyword])
        
    # Skip telemetry tests by default
    markers = args.markers
    if args.no_telemetry:
        telemetry_exclusion = 'not telemetry'
        if markers:
            markers = f'({markers}) and {telemetry_exclusion}'
        else:
            markers = telemetry_exclusion
    
    # Get test path
    test_path = None
    if args.tests:
        # If specific tests provided, use them
        test_path = ' '.join(args.tests)
    
    # Set default parallel workers for unit tests
    parallel = args.parallel
    if parallel == 0 and not any(arg in sys.argv for arg in ['-p', '--parallel']):
        parallel = get_default_workers('unit')
    
    cmd = runner.build_pytest_command(
        test_path=test_path,
        markers=markers,
        parallel=parallel,
        verbose=args.verbose,
        coverage=not args.no_coverage,
        extra_args=extra_args
    )
    
    # Run tests
    return runner.run_command(cmd)


if __name__ == '__main__':
    sys.exit(main())
