#!/usr/bin/env python3
"""Debug script to test mock server connectivity."""

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request


def check_mock_server(url="http://localhost:5000/health"):
    """Check if mock server is running."""
    try:
        # Only allow http/https URLs
        if not url.startswith(("http://", "https://")):
            error_msg = f"Invalid URL scheme: {url}"
            raise ValueError(error_msg)  # noqa: TRY301

        response = urllib.request.urlopen(url, timeout=5)  # noqa: S310
        if response.status == 200:
            print(f"✅ Mock server is running at {url}")
            return True
    except Exception as e:
        print(f"❌ Mock server not accessible: {e}")
        return False


def test_docker_setup():
    """Test Docker Compose setup."""
    print("\n=== Testing Docker Setup ===")

    # Check docker compose command
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            text=True,
            check=False,
        )
        print(f"Docker Compose: {result.stdout.strip()}")
    except subprocess.SubprocessError:
        print("❌ Docker Compose not found")
        return False

    # Start mock server
    print("\nStarting mock server...")
    subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            "docker-compose.test.yml",
            "up",
            "-d",
            "mock-server",
        ],
        check=True,
    )

    # Wait for health
    print("Waiting for mock server to be healthy...")
    for i in range(30):
        if check_mock_server():
            break
        time.sleep(1)
    else:
        print("❌ Mock server failed to start")
        # Show logs
        subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                "docker-compose.test.yml",
                "logs",
                "mock-server",
            ],
            check=False,
        )
        return False

    # Test a simple integration test
    print("\n=== Running Sample Integration Test ===")
    result = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            "docker-compose.test.yml",
            "run",
            "--rm",
            "test-integration",
            "python",
            "-m",
            "pytest",
            "tests/integration/test_with_openapi_mock.py::TestWithOpenAPIMockServer::test_complete_billing_workflow",
            "-vv",
            "--use-mock",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return code:", result.returncode)

    # Cleanup
    print("\nCleaning up...")
    subprocess.run(
        ["docker", "compose", "-f", "docker-compose.test.yml", "down", "-v"],
        check=False,
    )

    return result.returncode == 0


def test_local_setup():
    """Test local setup."""
    print("\n=== Testing Local Setup ===")

    # Set environment
    os.environ["USE_MOCK_SERVER"] = "true"
    os.environ["MOCK_SERVER_URL"] = "http://localhost:5000"
    os.environ["MOCK_SERVER_PORT"] = "5000"

    # Start mock server
    print("Starting local mock server...")
    server = subprocess.Popen(
        [sys.executable, "-m", "mock_server.run_server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for startup
    time.sleep(5)

    if not check_mock_server():
        stdout, stderr = server.communicate(timeout=5)
        print("STDOUT:", stdout.decode())
        print("STDERR:", stderr.decode())
        return False

    # Run a test
    print("\n=== Running Sample Test ===")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration/test_with_openapi_mock.py::TestWithOpenAPIMockServer::test_complete_billing_workflow",
            "-vv",
            "--use-mock",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    print("STDOUT:", result.stdout[-1000:])  # Last 1000 chars
    print("Return code:", result.returncode)

    # Cleanup
    server.terminate()
    server.wait()

    return result.returncode == 0


if __name__ == "__main__":
    print("Mock Server Debug Script")
    print("=" * 50)

    mode = sys.argv[1] if len(sys.argv) > 1 else "docker"

    if mode == "docker":
        success = test_docker_setup()
    elif mode == "local":
        success = test_local_setup()
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: python test_mock_debug.py [docker|local]")
        sys.exit(1)

    sys.exit(0 if success else 1)
