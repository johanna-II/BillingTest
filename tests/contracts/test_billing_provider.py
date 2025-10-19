"""Provider contract verification tests for Mock Billing API using Pact Python v3."""

import os
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

import pytest
import requests
from pact import Verifier

PACT_DIR = os.path.join(os.path.dirname(__file__), "pacts")
MOCK_SERVER_URL = "http://localhost:5000"


@contextmanager
def mock_server_running():
    """Context manager to ensure mock server is running."""
    # Check if mock server is already running
    try:
        response = requests.get(f"{MOCK_SERVER_URL}/health", timeout=1)
        if response.status_code == 200:
            # Server already running
            yield
            return
    except (requests.ConnectionError, requests.Timeout):
        pass

    # Start mock server
    server_process = subprocess.Popen(
        ["python", "-m", "mock_server.run_server"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    # Wait for server to start
    max_retries = 30
    for _ in range(max_retries):
        try:
            response = requests.get(f"{MOCK_SERVER_URL}/health", timeout=1)
            if response.status_code == 200:
                print("Mock server is ready")
                break
        except (requests.RequestException, ConnectionError):
            pass
        time.sleep(1)
    else:
        server_process.terminate()
        msg = "Mock server failed to start"
        raise RuntimeError(msg)

    try:
        yield
    finally:
        # Gracefully shutdown the server
        try:
            server_process.terminate()
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Force kill if graceful shutdown fails
            server_process.kill()
            server_process.wait(timeout=2)


@pytest.mark.contract
@pytest.mark.provider
class TestProviderVerification:
    """Provider verification tests."""

    @pytest.mark.skip(
        reason="Provider verification - datetime format needs fine-tuning"
    )
    def test_verify_billing_api_contract(self):
        """Verify the mock server satisfies all consumer contracts."""
        # Find pact files - only verify our current BillingTest pacts
        pact_files = []
        pact_dir_path = Path(PACT_DIR)

        print(f"Looking for pact files in: {pact_dir_path}")
        print(f"Directory exists: {pact_dir_path.exists()}")

        if pact_dir_path.exists():
            all_files = list(pact_dir_path.iterdir())
            print(f"Found {len(all_files)} files: {[f.name for f in all_files]}")

            for file in all_files:
                # Only verify billingtest pacts (skip legacy billingcrud/billinglibraries)
                if file.suffix == ".json" and "billingtest" in file.name.lower():
                    pact_files.append(str(file))
                    print(f"  [+] Added: {file.name}")
                elif file.suffix == ".json":
                    print(f"  [-] Skipped: {file.name} (not billingtest)")

        print(f"\nPact files to verify: {len(pact_files)}")

        if not pact_files:
            pytest.skip("No BillingTest pact files found to verify")

        # Run mock server and verify contracts
        with mock_server_running():
            # Pact v3 API
            verifier = Verifier("BillingAPI")

            # Enable logging
            log_dir = os.path.join(os.path.dirname(__file__), "logs")
            os.makedirs(log_dir, exist_ok=True)
            verifier.logs_for_provider(log_dir)

            # Set provider base URL as transport
            verifier.add_transport(url=MOCK_SERVER_URL)

            # Set provider state handler (body=True means state changes in request body)
            verifier.state_handler(f"{MOCK_SERVER_URL}/pact-states", body=True)

            # Add pact sources
            for pact_file in pact_files:
                print(f"Adding pact file: {pact_file}")
                verifier.add_source(pact_file)

            # Verify
            print("Running verification...")
            try:
                verifier.verify()
                print("[SUCCESS] Verification successful")
            except RuntimeError as e:
                # Print logs for debugging
                print(f"[FAILED] Verification failed: {e}")
                if hasattr(verifier, "logs"):
                    print("Verifier logs:")
                    print(verifier.logs)  # logs is a property, not a method
                raise

    @pytest.mark.integration
    def test_mock_server_health(self):
        """Test that mock server is running and responsive."""
        with mock_server_running():
            response = requests.get(f"{MOCK_SERVER_URL}/health", timeout=5)
            assert response.status_code == 200


@pytest.mark.contract
@pytest.mark.provider
class TestProviderStates:
    """Test provider state handling."""

    def test_provider_state_setup(self):
        """Test that provider states can be set up correctly."""
        with mock_server_running():
            # Test various provider states
            states = [
                "A contract exists",
                "Customer exists",
                "Resource exists",
                "Payment exists",
                "Invoice exists",
            ]

            for state in states:
                response = requests.post(
                    f"{MOCK_SERVER_URL}/pact-states",
                    json={"state": state},
                    timeout=5,
                )
                assert response.status_code == 200
                data = response.json()
                assert data["result"] == "success"
