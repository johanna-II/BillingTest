"""Common test runner functionality."""

import argparse
import os
import subprocess
import sys
from pathlib import Path


class TestRunner:
    """Base class for running tests with common functionality."""

    def __init__(self, category: str, base_path: Path) -> None:
        self.category = category
        self.base_path = base_path
        self.project_root = base_path.parent.parent
        self.python = sys.executable

    def run_command(self, cmd: list[str], env: dict[str, str] | None = None) -> int:
        """Run a command and return exit code."""
        # Merge environment variables
        run_env = os.environ.copy()
        if env:
            run_env.update(env)

        # Run command
        result = subprocess.run(cmd, env=run_env, cwd=self.project_root, check=False)

        # Print result
        if result.returncode == 0:
            pass
        else:
            pass

        return result.returncode

    def build_pytest_command(
        self,
        test_path: str | None = None,
        markers: str | None = None,
        parallel: int = 0,
        verbose: bool = True,
        coverage: bool = True,
        extra_args: list[str] | None = None,
    ) -> list[str]:
        """Build pytest command with common options."""
        cmd = [self.python, "-m", "pytest"]

        # Test path
        if test_path:
            cmd.append(test_path)
        else:
            cmd.append(str(self.base_path))

        # Verbosity
        if verbose:
            cmd.append("-v")

        # Markers
        if markers:
            cmd.extend(["-m", markers])

        # Parallel execution
        if parallel > 0:
            cmd.extend(["-n", str(parallel)])

        # Coverage
        if coverage:
            cmd.extend(
                [
                    "--cov=libs",
                    "--cov-report=term-missing:skip-covered",
                    "--cov-report=html",
                ]
            )

        # Extra arguments
        if extra_args:
            cmd.extend(extra_args)

        return cmd


def create_argument_parser(category: str) -> argparse.ArgumentParser:
    """Create common argument parser for test runners."""
    parser = argparse.ArgumentParser(
        description=f"Run {category} tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "tests", nargs="*", help="Specific test files or directories to run"
    )

    parser.add_argument(
        "-p",
        "--parallel",
        type=int,
        default=0,
        help="Number of parallel workers (0 for serial execution)",
    )

    parser.add_argument("-m", "--markers", help="Pytest markers to filter tests")

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=True,
        help="Verbose output (default: True)",
    )

    parser.add_argument(
        "--no-coverage", action="store_true", help="Disable coverage reporting"
    )

    parser.add_argument("--timeout", type=int, help="Test timeout in seconds")

    parser.add_argument(
        "-k", "--keyword", help="Only run tests matching the given substring expression"
    )

    parser.add_argument(
        "--tb",
        choices=["short", "long", "native", "no", "line"],
        default="short",
        help="Traceback print mode",
    )

    return parser


def get_default_workers(category: str) -> int:
    """Get default number of workers for a test category."""
    import multiprocessing

    cpu_count = multiprocessing.cpu_count()

    # Different defaults for different categories
    defaults = {
        "unit": min(cpu_count - 1, 4),  # Unit tests can run in parallel
        "integration": 0,  # Integration tests run serially by default
        "performance": 0,  # Performance tests must run serially
        "contracts": 0,  # Contract tests run serially
        "security": 2,  # Security tests can have some parallelism
    }

    return defaults.get(category, 0)
