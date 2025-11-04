"""Optimized mock server management for faster integration tests."""

import logging
import os
import socket
import subprocess
import sys
import threading
import time
from contextlib import closing, contextmanager
from typing import IO

import requests

logger = logging.getLogger(__name__)


def find_free_port() -> int:
    """Find a free port on the system."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


class OptimizedMockServerManager:
    """Optimized mock server manager with connection pooling and caching."""

    # Class-level cache for running servers
    _running_servers: dict[int, "OptimizedMockServerManager"] = {}
    _lock = threading.Lock()

    def __init__(self, port: int | None = None, reuse_existing: bool = True) -> None:
        """Initialize optimized mock server manager.

        Args:
            port: Specific port to use. If None, finds a free port.
            reuse_existing: Whether to reuse existing server on the same port.
        """
        self.port = port or find_free_port()
        self.process: subprocess.Popen[bytes] | None = None
        self.url = f"http://localhost:{self.port}"
        self.reuse_existing = reuse_existing
        self._is_shared = False
        self._health_check_interval = 0.1  # Faster health checks
        self._startup_timeout = 10  # Shorter timeout

    @classmethod
    def get_or_create(cls, port: int | None = None) -> "OptimizedMockServerManager":
        """Get existing server or create new one."""
        with cls._lock:
            if port and port in cls._running_servers:
                server = cls._running_servers[port]
                server._is_shared = True
                logger.info(f"Reusing existing mock server on port {port}")
                return server

            server = cls(port=port)
            if server.port in cls._running_servers:
                # Race condition - another thread created it
                return cls._running_servers[server.port]

            cls._running_servers[server.port] = server
            return server

    def start(self) -> None:
        """Start the mock server if not already running."""
        if self._is_server_running():
            logger.info(f"Mock server already running on port {self.port}")
            return

        env = os.environ.copy()
        env["MOCK_SERVER_PORT"] = str(self.port)
        env["MOCK_OPTIMIZE_MODE"] = "true"  # Enable optimizations in mock server

        # Start server process with optimized settings
        self.process = subprocess.Popen(
            [sys.executable, "-m", "mock_server.run_server"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # Use CREATE_NO_WINDOW on Windows to avoid console popup
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )

        # Wait for server with faster checks
        self._wait_for_server()
        logger.info(f"Mock server started on port {self.port}")

    def _is_server_running(self) -> bool:
        """Check if server is already running on the port."""
        try:
            response = requests.get(f"{self.url}/health", timeout=0.5)
            return response.status_code == 200
        except (requests.RequestException, ConnectionError):
            return False

    def _get_process_output(self) -> tuple[bytes, bytes]:
        """Safely read stdout and stderr from the process without blocking.

        Returns:
            Tuple of (stdout_bytes, stderr_bytes). Returns empty bytes if process
            is None or pipes are not available.
        """
        if not self.process:
            return b"", b""

        # Check if process has exited
        process_exited = self.process.poll() is not None

        # Read stdout
        stdout = b""
        if self.process.stdout:
            if process_exited:
                # Process has exited - drain all remaining data
                stdout = self.process.stdout.read()
            else:
                # Process still running - use non-blocking read
                stdout = self._read_available(self.process.stdout)

        # Read stderr
        stderr = b""
        if self.process.stderr:
            if process_exited:
                # Process has exited - drain all remaining data
                stderr = self.process.stderr.read()
            else:
                # Process still running - use non-blocking read
                stderr = self._read_available(self.process.stderr)

        return stdout, stderr

    def _read_available(self, stream: IO[bytes]) -> bytes:
        """Read available data from stream without blocking.

        Args:
            stream: The stream to read from (stdout or stderr from subprocess)

        Returns:
            Available bytes from the stream, or empty bytes if none available
        """
        try:
            # Try to peek at the buffer - this doesn't block
            if hasattr(stream, "peek"):
                peeked = stream.peek()
                if peeked:
                    # Data is available, read it
                    return stream.read(len(peeked))
            return b""
        except (OSError, ValueError):
            # Stream might be closed or unavailable
            return b""

    def _wait_for_server(self) -> None:
        """Wait for server to become ready with optimized polling."""
        start_time = time.time()
        check_interval = 0.05
        max_interval = 0.5
        attempt = 0

        while time.time() - start_time < self._startup_timeout:
            attempt += 1

            # Check for process crash
            self._check_process_crashed(attempt)

            # Try health check
            if self._try_health_check(attempt, start_time):
                return  # Success

            # Wait before next attempt
            time.sleep(check_interval)
            check_interval = min(check_interval * 1.5, max_interval)

        # Timeout reached
        self._raise_timeout_error(time.time() - start_time, attempt)

    def _check_process_crashed(self, attempt: int) -> None:
        """Check if server process crashed. Raises RuntimeError if crashed."""
        if not self.process or self.process.poll() is None:
            return

        # Process crashed - raise error
        stdout, stderr = self._get_process_output()
        error_msg = (
            f"Mock server crashed during startup (attempt {attempt}):\n"
            f"STDOUT: {stdout.decode()}\n"
            f"STDERR: {stderr.decode()}"
        )
        raise RuntimeError(error_msg)

    def _try_health_check(self, attempt: int, start_time: float) -> bool:
        """Try health check. Returns True if successful."""
        try:
            response = requests.get(
                f"{self.url}/health",
                timeout=2,
                allow_redirects=False,
            )
            if response.status_code == 200:
                logger.info(
                    f"Mock server health check passed on attempt {attempt} "
                    f"after {time.time() - start_time:.2f}s"
                )
                return True

            logger.debug(f"Health check returned status {response.status_code}")
            return False

        except requests.exceptions.ConnectionError as e:
            logger.debug(f"Connection failed on attempt {attempt}: {e}")
            return False
        except requests.exceptions.Timeout:
            logger.debug(f"Health check timeout on attempt {attempt}")
            return False
        except requests.exceptions.RequestException as e:
            logger.debug(f"Health check error on attempt {attempt}: {e}")
            return False

    def _raise_timeout_error(self, elapsed: float, attempt: int) -> None:
        """Raise detailed timeout error."""
        if self.process:
            process_status = (
                "running"
                if self.process.poll() is None
                else f"exited with code {self.process.returncode}"
            )
            stdout, stderr = self._get_process_output()
            error_msg = (
                f"Mock server failed to start on port {self.port} after {elapsed:.2f}s "
                f"({attempt} attempts).\n"
                f"Process status: {process_status}\n"
                f"STDOUT: {stdout.decode()}\n"
                f"STDERR: {stderr.decode()}"
            )
        else:
            error_msg = (
                f"Mock server failed to start on port {self.port} after {elapsed:.2f}s "
                f"({attempt} attempts). No process was created."
            )

        raise RuntimeError(error_msg)

    def stop(self) -> None:
        """Stop the mock server if not shared."""
        if self._is_shared:
            logger.info(f"Not stopping shared mock server on port {self.port}")
            return

        with self._lock:
            if self.port in self._running_servers:
                del self._running_servers[self.port]

        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            self.process = None
            logger.info(f"Mock server stopped on port {self.port}")

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        """Context manager exit."""
        self.stop()


class MockServerPool:
    """Pool of mock servers for parallel test execution."""

    def __init__(self, pool_size: int = 4) -> None:
        """Initialize server pool.

        Args:
            pool_size: Number of servers in the pool.
        """
        self.pool_size = pool_size
        self.servers: list[OptimizedMockServerManager] = []
        self._current_index = 0
        self._lock = threading.Lock()

    def initialize(self) -> None:
        """Initialize all servers in the pool."""
        for _ in range(self.pool_size):
            server = OptimizedMockServerManager(reuse_existing=False)
            server.start()
            self.servers.append(server)
        logger.info(f"Initialized mock server pool with {self.pool_size} servers")

    def get_server(self) -> OptimizedMockServerManager:
        """Get next available server from pool (round-robin)."""
        with self._lock:
            server = self.servers[self._current_index]
            self._current_index = (self._current_index + 1) % self.pool_size
            return server

    def shutdown(self) -> None:
        """Shutdown all servers in the pool."""
        for server in self.servers:
            server.stop()
        self.servers.clear()
        logger.info("Mock server pool shut down")


@contextmanager
def optimized_mock_server(port: int | None = None, reuse: bool = True):
    """Context manager for optimized mock server.

    Args:
        port: Specific port to use.
        reuse: Whether to reuse existing servers.

    Yields:
        Mock server URL.
    """
    if reuse:
        server = OptimizedMockServerManager.get_or_create(port)
    else:
        server = OptimizedMockServerManager(port=port, reuse_existing=False)

    try:
        server.start()
        yield server.url
    finally:
        if not reuse:
            server.stop()


# Global server pool for test sessions
_global_server_pool: MockServerPool | None = None


def get_global_server_pool(size: int = 4) -> MockServerPool:
    """Get or create global server pool."""
    global _global_server_pool
    if _global_server_pool is None:
        _global_server_pool = MockServerPool(pool_size=size)
        _global_server_pool.initialize()
    return _global_server_pool


def cleanup_global_server_pool() -> None:
    """Clean up global server pool."""
    global _global_server_pool
    if _global_server_pool:
        _global_server_pool.shutdown()
        _global_server_pool = None
