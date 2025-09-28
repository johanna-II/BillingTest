"""Master test runner for all test suites.

This script provides a unified interface for running all tests with
appropriate configurations and reporting.
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Coverage options
COV_REPORT_TERM_MISSING = "--cov-report=term-missing"


class TestRunner:
    """Manages test execution across different test suites."""

    def __init__(self):
        self.test_root = Path(__file__).parent
        self.project_root = self.test_root.parent

    def run_command(self, cmd: list[str], env: dict | None = None) -> int:
        """Run a command and return exit code."""
        print(f"\n{'='*60}")
        print(f"Running: {' '.join(cmd)}")
        print(f"{'='*60}")

        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        # Ensure Python is in PATH for subprocess
        if "PATH" in process_env:
            python_dir = os.path.dirname(sys.executable)
            if python_dir not in process_env["PATH"]:
                process_env["PATH"] = f"{python_dir}{os.pathsep}{process_env['PATH']}"

        result = subprocess.run(
            cmd, env=process_env, check=False, cwd=str(self.project_root)
        )
        return result.returncode

    def run_unit_tests(self, parallel: bool = True) -> int:
        """Run unit tests."""
        cmd = ["pytest", "tests/unit/", "-v", "--tb=short"]

        if parallel:
            cmd.extend(["-n", "auto"])

        cmd.extend(
            [
                "--cov=libs",
                "--cov-config=.coveragerc",
                COV_REPORT_TERM_MISSING,
                "--cov-report=html:htmlcov/unit",
            ]
        )

        return self.run_command(cmd)

    def run_integration_tests(
        self, use_mock: bool = True, parallel: bool = True
    ) -> int:
        """Run integration tests."""
        cmd = ["pytest", "tests/integration/", "-v", "--tb=short"]

        if use_mock:
            cmd.append("--use-mock")

        if parallel:
            cmd.extend(["-n", "4"])  # Limited parallelism for integration

        cmd.extend(
            [
                "--cov=libs",
                "--cov-config=.coveragerc",
                "--cov-append",
                COV_REPORT_TERM_MISSING,
                "--cov-report=html:htmlcov/integration",
            ]
        )

        env = {"USE_MOCK_SERVER": "true"} if use_mock else {}

        return self.run_command(cmd, env)

    def run_450_combinations(self, sample_only: bool = False) -> int:
        """Run the 450 combination tests."""
        cmd = ["pytest", "tests/integration/test_complete_450_combinations.py", "-v"]

        if sample_only:
            # Run only critical combinations
            cmd.append("-k")
            cmd.append("test_combination[NO_UNPAID-BG_NONE-PROJ_NONE-NO_CREDIT]")
        else:
            # Run all combinations with aggressive parallelization
            cmd.extend(["-n", "auto"])

        return self.run_command(cmd)

    def run_contract_tests(self, use_mock: bool = False) -> int:
        """Run contract tests."""
        cmd = [
            "pytest",
            "tests/contracts/",
            "-v",
            "--tb=short",
            "--cov=libs",
            "--cov-config=.coveragerc",
            "--cov-append",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov/contracts",
        ]

        if use_mock:
            cmd.append("--use-mock")

        env = {"USE_MOCK_SERVER": "true"} if use_mock else {}

        return self.run_command(cmd, env)

    def run_performance_tests(self) -> int:
        """Run performance tests."""
        cmd = ["pytest", "tests/performance/", "-v", "--tb=short"]
        return self.run_command(cmd)

    def run_security_tests(self) -> int:
        """Run security tests."""
        cmd = ["pytest", "tests/security/", "-v", "--tb=short"]
        return self.run_command(cmd)

    def generate_report(self) -> None:
        """Generate final test report."""
        print("\n" + "=" * 60)
        print("TEST EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().isoformat()}")

        # Coverage report
        subprocess.run(["coverage", "report"], check=False)

        # Generate HTML report
        subprocess.run(["coverage", "html"], check=False)
        print(f"\nHTML coverage report: file://{self.project_root}/htmlcov/index.html")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run billing system tests")

    parser.add_argument(
        "--suite",
        choices=[
            "all",
            "unit",
            "integration",
            "contracts",
            "performance",
            "security",
            "450",
        ],
        default="all",
        help="Test suite to run",
    )

    parser.add_argument(
        "--no-parallel", action="store_true", help="Disable parallel test execution"
    )

    parser.add_argument(
        "--no-mock",
        action="store_true",
        help="Run integration tests against real services",
    )

    parser.add_argument(
        "--use-mock",
        action="store_true",
        help="Force use of mock server for all tests (including contracts)",
    )

    parser.add_argument(
        "--sample-450", action="store_true", help="Run only sample of 450 combinations"
    )

    parser.add_argument(
        "--coverage-only",
        action="store_true",
        help="Generate coverage report from existing data",
    )

    args = parser.parse_args()

    runner = TestRunner()

    if args.coverage_only:
        runner.generate_report()
        return 0

    # Start mock server for integration tests
    if args.suite in ["all", "integration"] and not args.no_mock:
        print("Starting mock server...")
        # Mock server should be started by conftest.py

    exit_codes = []

    # Determine mock usage
    use_mock_for_integration = not args.no_mock or args.use_mock
    use_mock_for_contracts = args.use_mock

    # Run selected test suites
    if args.suite == "all":
        exit_codes.append(runner.run_unit_tests(not args.no_parallel))
        exit_codes.append(
            runner.run_integration_tests(use_mock_for_integration, not args.no_parallel)
        )
        exit_codes.append(runner.run_contract_tests(use_mock_for_contracts))
        # Optionally run other suites
    elif args.suite == "unit":
        exit_codes.append(runner.run_unit_tests(not args.no_parallel))
    elif args.suite == "integration":
        exit_codes.append(
            runner.run_integration_tests(use_mock_for_integration, not args.no_parallel)
        )
    elif args.suite == "contracts":
        exit_codes.append(runner.run_contract_tests(use_mock_for_contracts))
    elif args.suite == "performance":
        exit_codes.append(runner.run_performance_tests())
    elif args.suite == "security":
        exit_codes.append(runner.run_security_tests())
    elif args.suite == "450":
        exit_codes.append(runner.run_450_combinations(args.sample_450))

    # Generate final report
    runner.generate_report()

    # Return non-zero if any test failed
    return 1 if any(code != 0 for code in exit_codes) else 0


if __name__ == "__main__":
    sys.exit(main())
