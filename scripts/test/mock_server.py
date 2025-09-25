"""Mock server management utilities."""

import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager

import requests


def find_free_port() -> int:
    """Find a free port on the system."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def wait_for_server(url: str, timeout: int = 30) -> bool:
    """Wait for mock server to be ready."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/health", timeout=1)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(0.5)

    return False


@contextmanager
def mock_server_context(port: int | None = None, verbose: bool = False):
    """Context manager to start and stop mock server."""
    if port is None:
        port = find_free_port()

    # Set environment variables
    env = os.environ.copy()
    env["MOCK_SERVER_PORT"] = str(port)
    env["MOCK_SERVER_URL"] = f"http://localhost:{port}"
    env["USE_MOCK_SERVER"] = "true"

    # Update current process environment
    os.environ.update(
        {
            "MOCK_SERVER_PORT": str(port),
            "MOCK_SERVER_URL": f"http://localhost:{port}",
            "USE_MOCK_SERVER": "true",
        }
    )

    # Start mock server
    server_process = subprocess.Popen(
        [sys.executable, "-m", "mock_server.run_server"],
        env=env,
        stdout=None if verbose else subprocess.PIPE,
        stderr=None if verbose else subprocess.PIPE,
    )

    try:
        # Wait for server to be ready
        server_url = f"http://localhost:{port}"
        if not wait_for_server(server_url, timeout=30):
            msg = "Mock server failed to start within 30 seconds"
            raise RuntimeError(msg)

        yield server_url

    finally:
        # Stop mock server
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
            server_process.wait()


class MockServerManager:
    """Manager for mock server lifecycle during tests."""

    def __init__(self, port: int | None = None) -> None:
        self.port = port or find_free_port()
        self.process = None
        self.url = f"http://localhost:{self.port}"

    def start(self, verbose: bool = False) -> str:
        """Start the mock server."""
        if self.process:
            msg = "Mock server already running"
            raise RuntimeError(msg)

        # Set environment variables
        env = os.environ.copy()
        env["MOCK_SERVER_PORT"] = str(self.port)
        env["MOCK_SERVER_URL"] = self.url
        env["USE_MOCK_SERVER"] = "true"

        # Update current process environment
        os.environ.update(
            {
                "MOCK_SERVER_PORT": str(self.port),
                "MOCK_SERVER_URL": self.url,
                "USE_MOCK_SERVER": "true",
            }
        )

        # Start server
        self.process = subprocess.Popen(
            [sys.executable, "-m", "mock_server.run_server"],
            env=env,
            stdout=None if verbose else subprocess.PIPE,
            stderr=None if verbose else subprocess.PIPE,
        )

        # Wait for server
        if not wait_for_server(self.url, timeout=30):
            self.stop()
            msg = "Mock server failed to start"
            raise RuntimeError(msg)

        return self.url

    def stop(self) -> None:
        """Stop the mock server."""
        if not self.process:
            return

        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.process = None

    def __enter__(self):
        """Context manager entry."""
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
