#!/usr/bin/env python3
"""
Unified cross-platform test runner for Windows, macOS, and Linux
Supports multiple execution modes with mock server management
"""

import argparse
import os
import platform
import subprocess
import sys
import time
import signal
from typing import List, Optional
import requests
from pathlib import Path


class TestRunner:
    """Cross-platform test runner with mock server support"""
    
    def __init__(self):
        self.mock_process = None
        self.system = platform.system()
        self.cpu_count = os.cpu_count() or 1
        
    def start_mock_server(self) -> bool:
        """Start the mock server in the background"""
        print("Starting mock server...")
        
        # Set environment variable
        os.environ["USE_MOCK_SERVER"] = "true"
        
        # Start mock server
        if self.system == "Windows":
            # Windows: Use CREATE_NEW_PROCESS_GROUP for proper termination
            self.mock_process = subprocess.Popen(
                [sys.executable, "-m", "mock_server.run_server"],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            # Unix-like: Use preexec_fn to ensure proper signal handling
            self.mock_process = subprocess.Popen(
                [sys.executable, "-m", "mock_server.run_server"],
                preexec_fn=os.setsid if self.system != "Windows" else None
            )
        
        return True
    
    def wait_for_mock_server(self, skip_health_check: bool = False) -> bool:
        """Wait for mock server to be ready"""
        if skip_health_check:
            print("Skipping health check...")
            time.sleep(2)
            return True
            
        print("Waiting for mock server to be ready...")
        for i in range(30):
            try:
                response = requests.get("http://localhost:5000/health", timeout=1)
                if response.status_code == 200:
                    print("Mock server is ready!")
                    return True
            except (requests.ConnectionError, requests.Timeout):
                pass
            time.sleep(1)
        
        print("Mock server failed to start!")
        return False
    
    def stop_mock_server(self):
        """Stop the mock server"""
        if self.mock_process:
            print("Stopping mock server...")
            if self.system == "Windows":
                # Windows: Use taskkill for clean termination
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(self.mock_process.pid)],
                    capture_output=True
                )
            else:
                # Unix-like: Send SIGTERM to process group
                try:
                    os.killpg(os.getpgid(self.mock_process.pid), signal.SIGTERM)
                except ProcessLookupError:
                    pass
            
            self.mock_process.wait(timeout=5)
            self.mock_process = None
    
    def build_pytest_command(self, mode: str, no_coverage: bool, 
                           pytest_args: List[str]) -> List[str]:
        """Build pytest command based on execution mode"""
        cmd = ["pytest", "--use-mock"]
        
        if mode == "default":
            # Basic sequential execution
            cmd.extend(["-v"])
            
        elif mode == "parallel":
            # Moderate parallelization
            workers = max(2, self.cpu_count // 2)
            print(f"Using {workers} parallel workers")
            cmd.extend(["-v", "-n", str(workers), "--dist", "loadscope"])
            
        elif mode == "safe":
            # This mode requires special handling (see run_tests method)
            workers = max(2, self.cpu_count // 2)
            cmd.extend(["-v", "-n", str(workers), "--dist", "loadscope",
                       "--ignore", "tests/test_credit_all.py",
                       "--ignore", "tests/test_unpaid_and_credit.py"])
            
        elif mode == "fast":
            # Fast parallel execution without coverage
            cmd.extend(["-v", "-x", "-n", "auto", "--tb=no", "-q", "--no-cov"])
            no_coverage = True
            
        elif mode == "ultra":
            # Aggressive parallelization
            workers = min(self.cpu_count - 1, 5)
            print(f"Using {workers} parallel workers")
            cmd.extend(["-v", "-n", str(workers), "--dist", "worksteal",
                       "--maxfail", "5", "--tb=short", "--durations=10",
                       "--no-header", "-p", "no:warnings"])
            
        elif mode == "super":
            # Maximum optimization
            print("Running with maximum optimization...")
            cmd = [sys.executable, "-m", "pytest", "tests",
                   "--use-mock", "-n", "auto", "--dist", "worksteal",
                   "-x", "--tb=line", "--no-header", "--quiet",
                   "--override-ini=addopts=",
                   "--override-ini=testpaths=tests"]
            no_coverage = True
        
        # Add coverage flag if needed
        if no_coverage and mode not in ["fast", "super"]:
            cmd.append("--no-cov")
        
        # Add user-provided arguments
        cmd.extend(pytest_args)
        
        return cmd
    
    def run_tests(self, mode: str, no_coverage: bool, skip_health_check: bool,
                  pytest_args: List[str]) -> int:
        """Run tests with the specified configuration"""
        print(f"Starting tests with mock server (Mode: {mode})...")
        print(f"Detected {self.cpu_count} CPU cores on {self.system}")
        
        # Set optimization environment variables for certain modes
        if mode in ["super", "ultra"]:
            os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
            os.environ["PYTEST_CURRENT_TEST"] = "1"
        
        # Start mock server
        if not self.start_mock_server():
            return 1
        
        try:
            # Wait for mock server
            if not self.wait_for_mock_server(skip_health_check):
                return 1
            
            # Special handling for safe mode
            if mode == "safe":
                print("Running credit tests sequentially...")
                credit_cmd = ["pytest", "--use-mock", "-v", 
                             "tests/test_credit_all.py", 
                             "tests/test_unpaid_and_credit.py"]
                result = subprocess.run(credit_cmd)
                
                if result.returncode != 0:
                    print("Credit tests failed!")
                    return result.returncode
                
                print("Running remaining tests in parallel...")
            
            # Build and run main pytest command
            cmd = self.build_pytest_command(mode, no_coverage, pytest_args)
            print(f"Running tests: {' '.join(cmd)}")
            
            result = subprocess.run(cmd)
            
            # Show summary
            if result.returncode == 0:
                print("\033[92mAll tests passed!\033[0m")  # Green text
            else:
                print("\033[91mSome tests failed!\033[0m")  # Red text
            
            return result.returncode
            
        finally:
            # Always stop mock server
            self.stop_mock_server()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Unified cross-platform test runner",
        epilog="Any additional arguments are passed directly to pytest"
    )
    
    parser.add_argument(
        "--mode",
        choices=["default", "parallel", "safe", "fast", "ultra", "super"],
        default="default",
        help="Test execution mode (default: %(default)s)"
    )
    
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Disable coverage reporting"
    )
    
    parser.add_argument(
        "--skip-health-check",
        action="store_true",
        help="Skip mock server health check"
    )
    
    # Parse known args and collect remaining for pytest
    args, pytest_args = parser.parse_known_args()
    
    # Run tests
    runner = TestRunner()
    sys.exit(runner.run_tests(
        args.mode,
        args.no_coverage,
        args.skip_health_check,
        pytest_args
    ))


if __name__ == "__main__":
    main()
