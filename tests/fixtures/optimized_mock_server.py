"""Optimized mock server management for faster integration tests."""

import logging
import os
import socket
import subprocess
import sys
import threading
import time
from contextlib import closing, contextmanager

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
        except:
            return False

    def _wait_for_server(self) -> None:
        """Wait for server to become ready with optimized polling."""
        start_time = time.time()

        # Use exponential backoff for health checks
        check_interval = 0.05
        max_interval = 0.5

        while time.time() - start_time < self._startup_timeout:
            try:
                response = requests.get(f"{self.url}/health", timeout=1)
                if response.status_code == 200:
                    return
            except requests.exceptions.RequestException:
                pass

            time.sleep(check_interval)
            check_interval = min(check_interval * 1.5, max_interval)

        # Check if process crashed
        if self.process and self.process.poll() is not None:
            stderr = self.process.stderr.read() if self.process.stderr else b""
            error_msg = f"Mock server crashed: {stderr.decode()}"
            raise RuntimeError(error_msg)

        error_msg = f"Mock server failed to start on port {self.port}"
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

    def __exit__(self, exc_type, exc_val, exc_tb):
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
