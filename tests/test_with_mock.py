"""Test configuration for running tests with mock server."""

import os
import subprocess
import time
from contextlib import contextmanager

import pytest
import requests


@contextmanager
def mock_server_context():
    """Context manager to start and stop mock server."""
    # Set environment variable to use mock server
    os.environ["USE_MOCK_SERVER"] = "true"

    # Start mock server as subprocess
    server_process = subprocess.Popen(
        ["python", "-m", "mock_server.run_server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    max_retries = 30
    for _i in range(max_retries):
        try:
            mock_url = os.environ.get("MOCK_SERVER_URL", "http://localhost:5000")
            response = requests.get(f"{mock_url}/health")
            if response.status_code == 200:
                break
        except requests.ConnectionError:
            time.sleep(1)
    else:
        server_process.terminate()
        msg = "Mock server failed to start"
        raise RuntimeError(msg)

    try:
        yield
    finally:
        # Clean up
        server_process.terminate()
        server_process.wait()
        os.environ.pop("USE_MOCK_SERVER", None)


@pytest.fixture(scope="session", autouse=True)
def mock_server():
    """Pytest fixture to run mock server during tests."""
    if os.environ.get("USE_MOCK_SERVER", "false").lower() == "true":
        with mock_server_context():
            yield
    else:
        yield
