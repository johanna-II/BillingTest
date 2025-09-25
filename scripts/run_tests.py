#!/usr/bin/env python3
"""Unified test runner for both local and CI environments.
Supports both Docker and non-Docker execution.
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


class TestRunner:
    """Simple test runner that works in both Docker and local environments."""

    def __init__(self, use_docker=False):
        self.use_docker = use_docker
        self.project_root = Path(__file__).parent.parent
        self.docker_compose_cmd = (
            self._find_docker_compose_cmd() if use_docker else None
        )

    def _find_docker_compose_cmd(self):
        """Find the appropriate docker compose command."""
        # Try 'docker compose' first (newer)
        try:
            subprocess.run(
                ["docker", "compose", "version"], capture_output=True, check=True
            )
            return ["docker", "compose"]
        except:
            pass

        # Try 'docker-compose' (legacy)
        try:
            subprocess.run(
                ["docker-compose", "--version"], capture_output=True, check=True
            )
            return ["docker-compose"]
        except:
            pass

        print("❌ Docker Compose not found. Please install Docker.")
        sys.exit(1)

    def _wait_for_mock_server(self, timeout=30):
        """Wait for mock server to be ready."""
        import urllib.error
        import urllib.request

        print("Waiting for mock server...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = urllib.request.urlopen(
                    "http://localhost:5000/health", timeout=1
                )
                if response.status == 200:
                    print("✓ Mock server is ready!")
                    return True
            except:
                time.sleep(1)

        print("❌ Mock server failed to start")
        return False

    def run_docker_tests(self, test_type="all", coverage=False):
        """Run tests using Docker Compose."""
        os.chdir(self.project_root)

        try:
            # Build mock server if requested (CI environments should set this)
            if os.environ.get("DOCKER_BUILD_NO_CACHE", "").lower() == "true":
                print("Building mock server image (no cache)...")
                subprocess.run(
                    [
                        *self.docker_compose_cmd,
                        "-f",
                        "docker-compose.test.yml",
                        "build",
                        "--no-cache",
                        "mock-server",
                    ],
                    check=True,
                )

            # Start mock server
            print("Starting mock server...")
            subprocess.run(
                [
                    *self.docker_compose_cmd,
                    "-f",
                    "docker-compose.test.yml",
                    "up",
                    "-d",
                    "mock-server",
                ],
                check=True,
            )

            # Wait for mock server
            if not self._wait_for_mock_server():
                print("\n❌ Mock server failed to start")
                print("\nContainer status:")
                subprocess.run(
                    [
                        *self.docker_compose_cmd,
                        "-f",
                        "docker-compose.test.yml",
                        "ps",
                    ],
                    check=False,
                )
                print("\nContainer logs:")
                subprocess.run(
                    [
                        *self.docker_compose_cmd,
                        "-f",
                        "docker-compose.test.yml",
                        "logs",
                        "mock-server",
                    ],
                    check=False,
                )
                return False

            # Run tests
            if test_type == "all":
                test_types = ["unit", "integration", "contracts"]
            else:
                test_types = [test_type]

            success = True
            for test in test_types:
                print(f"\n{'=' * 60}")
                print(f"Running {test} tests...")
                print("=" * 60)

                if test == "unit":
                    cmd = [
                        "run",
                        "--rm",
                        "test-full",
                        "python",
                        "-m",
                        "pytest",
                        "tests/unit/",
                        "-v",
                    ]
                    if coverage:
                        cmd.extend(
                            [
                                "--cov=libs",
                                "--cov-report=term-missing",
                                "--cov-report=xml",
                                "--cov-omit=libs/observability/*,libs/dependency_injection.py",
                            ]
                        )
                elif test == "integration":
                    cmd = ["run", "--rm", "test-integration"]
                elif test == "contracts":
                    cmd = ["run", "--rm", "test-contracts"]

                result = subprocess.run(
                    [*self.docker_compose_cmd, "-f", "docker-compose.test.yml", *cmd],
                    capture_output=False,
                    check=False,
                )

                if result.returncode != 0:
                    success = False
                    print(f"❌ {test} tests failed!")

            return success

        finally:
            # Clean up
            print("\nCleaning up...")
            subprocess.run(
                [
                    *self.docker_compose_cmd,
                    "-f",
                    "docker-compose.test.yml",
                    "down",
                    "-v",
                ],
                capture_output=True,
                check=False,
            )

    def run_local_tests(self, test_type="all", coverage=False):
        """Run tests locally without Docker."""
        os.chdir(self.project_root)

        # Set environment for mock server
        env = os.environ.copy()
        env["USE_MOCK_SERVER"] = "true"
        env["MOCK_SERVER_URL"] = "http://localhost:5000/api/v1"
        env["MOCK_SERVER_PORT"] = "5000"

        # Start mock server
        print("Starting mock server...")
        mock_server = subprocess.Popen(
            [sys.executable, "-m", "mock_server.run_server"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            # Wait for mock server
            if not self._wait_for_mock_server():
                stdout, stderr = mock_server.communicate(timeout=5)
                print(f"STDOUT: {stdout.decode()}")
                print(f"STDERR: {stderr.decode()}")
                return False

            # Run tests
            if test_type == "all":
                test_commands = {
                    "unit": ["pytest", "tests/unit/", "-v"],
                    "integration": ["pytest", "tests/integration/", "-v", "--use-mock"],
                    "contracts": ["pytest", "tests/contracts/", "-v", "--use-mock"],
                }
                if coverage and "unit" in test_commands:
                    test_commands["unit"].extend(
                        [
                            "--cov=libs",
                            "--cov-report=term-missing",
                            "--cov-report=xml",
                            "--cov-omit=libs/observability/*,libs/dependency_injection.py",
                        ]
                    )
            else:
                test_commands = {
                    test_type: ["pytest", f"tests/{test_type}/", "-v", "--use-mock"]
                }
                if coverage and test_type == "unit":
                    test_commands[test_type].extend(
                        [
                            "--cov=libs",
                            "--cov-report=term-missing",
                            "--cov-report=xml",
                            "--cov-omit=libs/observability/*,libs/dependency_injection.py",
                        ]
                    )

            success = True
            for test_name, cmd in test_commands.items():
                print(f"\n{'=' * 60}")
                print(f"Running {test_name} tests...")
                print("=" * 60)

                result = subprocess.run(
                    [sys.executable, "-m", *cmd], env=env, check=False
                )

                if result.returncode != 0:
                    success = False
                    print(f"❌ {test_name} tests failed!")

            return success

        finally:
            # Stop mock server
            print("\nStopping mock server...")
            mock_server.terminate()
            try:
                mock_server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                mock_server.kill()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run billing tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests with Docker
  python scripts/run_tests.py

  # Run specific tests with Docker
  python scripts/run_tests.py unit

  # Run tests locally (no Docker)
  python scripts/run_tests.py --local

  # Run specific tests locally
  python scripts/run_tests.py unit --local
        """,
    )

    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=["all", "unit", "integration", "contracts"],
        help="Type of tests to run (default: all)",
    )

    parser.add_argument(
        "--local", action="store_true", help="Run tests locally without Docker"
    )

    parser.add_argument(
        "--coverage", action="store_true", help="Run with coverage report"
    )

    args = parser.parse_args()

    # Create test runner
    runner = TestRunner(use_docker=not args.local)

    # Run tests
    try:
        if args.local:
            success = runner.run_local_tests(args.test_type, coverage=args.coverage)
        else:
            success = runner.run_docker_tests(args.test_type, coverage=args.coverage)

        if success:
            print("\n✅ All tests passed!")
            return 0
        print("\n❌ Some tests failed!")
        return 1

    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
