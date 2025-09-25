"""Mock server management for parallel test execution."""

import os
import socket
import subprocess
import sys
import time
from contextlib import closing

import requests


def find_free_port():
    """Find a free port on the system."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


class MockServerManager:
    """Manages mock server lifecycle for tests."""

    def __init__(self, port: int | None = None) -> None:
        """Initialize mock server manager.

        Args:
            port: Specific port to use. If None, finds a free port.
        """
        self.port = port or find_free_port()
        self.process = None
        self.url = f"http://localhost:{self.port}"

    def start(self) -> None:
        """Start the mock server."""
        env = os.environ.copy()
        env["MOCK_SERVER_PORT"] = str(self.port)

        # Start server process
        self.process = subprocess.Popen(
            [sys.executable, "-m", "mock_server.run_server"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for server to be ready
        self._wait_for_server()

    def _wait_for_server(self, timeout: int = 30) -> None:
        """Wait for server to become ready.

        Args:
            timeout: Maximum seconds to wait.

        Raises:
            RuntimeError: If server doesn't start within timeout.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.url}/health", timeout=1)
                if response.status_code == 200:
                    return
            except requests.exceptions.RequestException:
                time.sleep(0.5)

        msg = f"Mock server failed to start on port {self.port}"
        raise RuntimeError(msg)

    def stop(self) -> None:
        """Stop the mock server."""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            self.process = None

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


def get_mock_server_url() -> str:
    """Get mock server URL from environment or default."""
    port = os.environ.get("MOCK_SERVER_PORT", "5000")
    return f"http://localhost:{port}"
