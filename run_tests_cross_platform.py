#!/usr/bin/env python3
"""Cross-platform test runner for BillingTest project."""

import os
import sys
import platform
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional, Tuple


class CrossPlatformTestRunner:
    """Handles cross-platform test execution."""
    
    def __init__(self):
        self.system = platform.system()
        self.python_cmd = self._get_python_command()
        self.project_root = Path(__file__).parent.absolute()
        
    def _get_python_command(self) -> str:
        """Get the appropriate Python command for the current platform."""
        if self.system == "Windows":
            # Try python first, then python3
            for cmd in ["python", "python3"]:
                if self._command_exists(cmd):
                    return cmd
        else:
            # Unix-like systems prefer python3
            for cmd in ["python3", "python"]:
                if self._command_exists(cmd):
                    return cmd
        
        raise RuntimeError("Python interpreter not found")
    
    def _command_exists(self, cmd: str) -> bool:
        """Check if a command exists on the system."""
        try:
            if self.system == "Windows":
                subprocess.run(["where", cmd], capture_output=True, check=True)
            else:
                subprocess.run(["which", cmd], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _setup_environment(self) -> dict:
        """Set up environment variables for test execution."""
        env = os.environ.copy()
        
        # Add project root to PYTHONPATH
        pythonpath = env.get("PYTHONPATH", "")
        if pythonpath:
            env["PYTHONPATH"] = f"{self.project_root}{os.pathsep}{pythonpath}"
        else:
            env["PYTHONPATH"] = str(self.project_root)
        
        return env
    
    def _get_test_command(self, args: argparse.Namespace) -> List[str]:
        """Build the pytest command based on arguments."""
        cmd = [self.python_cmd, "-m", "pytest"]
        
        # Add coverage options
        if args.coverage:
            cmd.extend([
                "--cov=libs",
                "--cov-report=term-missing",
                "--cov-report=html",
                "--cov-report=xml"
            ])
            
            # Exclude specified files from coverage
            if args.no_observability:
                cmd.extend([
                    "--cov-omit=libs/observability/*",
                    "--cov-omit=libs/dependency_injection.py"
                ])
        
        # Add test directory
        cmd.append(args.test_dir)
        
        # Add verbose output
        if args.verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
        
        # Add markers
        if args.markers:
            cmd.extend(["-m", args.markers])
        
        # Add specific test pattern
        if args.pattern:
            cmd.extend(["-k", args.pattern])
        
        # Add parallel execution
        if args.parallel:
            cmd.extend(["-n", str(args.parallel)])
        
        # Add other pytest options
        if args.pytest_args:
            cmd.extend(args.pytest_args.split())
        
        return cmd
    
    def _install_dependencies(self) -> bool:
        """Install required dependencies."""
        print(f"Installing dependencies on {self.system}...")
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            print("Warning: requirements.txt not found")
            return False
        
        try:
            cmd = [self.python_cmd, "-m", "pip", "install", "-r", str(requirements_file)]
            subprocess.run(cmd, check=True, cwd=self.project_root)
            print("Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to install dependencies: {e}")
            return False
    
    def run_tests(self, args: argparse.Namespace) -> int:
        """Run the tests with the specified configuration."""
        # Install dependencies if requested
        if args.install_deps:
            if not self._install_dependencies():
                return 1
        
        # Set up environment
        env = self._setup_environment()
        
        # Build command
        cmd = self._get_test_command(args)
        
        # Print command for debugging
        if args.verbose:
            print(f"Running command: {' '.join(cmd)}")
            print(f"Working directory: {self.project_root}")
            print(f"Python version: {sys.version}")
            print(f"Platform: {self.system} {platform.release()}")
        
        # Run tests
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                env=env,
                check=False
            )
            return result.returncode
        except Exception as e:
            print(f"Error running tests: {e}")
            return 1
    
    def run_in_docker(self, args: argparse.Namespace) -> int:
        """Run tests inside Docker container."""
        print("Running tests in Docker...")
        
        # Check if Docker is available
        if not self._command_exists("docker"):
            print("Docker is not installed or not in PATH")
            return 1
        
        # Build Docker command
        docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{self.project_root}:/app",
            "-w", "/app",
            "python:3.12-slim",
            "bash", "-c",
            f"pip install -r requirements.txt && python run_tests_cross_platform.py {' '.join(sys.argv[1:])}"
        ]
        
        try:
            result = subprocess.run(docker_cmd, check=False)
            return result.returncode
        except Exception as e:
            print(f"Error running Docker: {e}")
            return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Cross-platform test runner for BillingTest project"
    )
    
    parser.add_argument(
        "test_dir",
        nargs="?",
        default="tests/unit",
        help="Test directory to run (default: tests/unit)"
    )
    
    parser.add_argument(
        "-c", "--coverage",
        action="store_true",
        help="Run with coverage report"
    )
    
    parser.add_argument(
        "--no-observability",
        action="store_true",
        help="Exclude observability and dependency_injection from coverage"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "-m", "--markers",
        help="Run tests matching given mark expression"
    )
    
    parser.add_argument(
        "-k", "--pattern",
        help="Run tests matching given pattern"
    )
    
    parser.add_argument(
        "-n", "--parallel",
        type=int,
        help="Number of parallel workers"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install dependencies before running tests"
    )
    
    parser.add_argument(
        "--docker",
        action="store_true",
        help="Run tests inside Docker container"
    )
    
    parser.add_argument(
        "--pytest-args",
        help="Additional pytest arguments"
    )
    
    args = parser.parse_args()
    
    runner = CrossPlatformTestRunner()
    
    if args.docker:
        return runner.run_in_docker(args)
    else:
        return runner.run_tests(args)


if __name__ == "__main__":
    sys.exit(main())
