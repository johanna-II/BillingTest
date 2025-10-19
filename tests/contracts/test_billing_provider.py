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

    def test_verify_billing_api_contract(self):
        """Verify the mock server satisfies all consumer contracts."""
        # Find all pact files
        pact_files = []
        pact_dir_path = Path(PACT_DIR)
        if pact_dir_path.exists():
            for file in pact_dir_path.iterdir():
                if file.suffix == ".json":
                    pact_files.append(str(file))

        if not pact_files:
            pytest.skip("No pact files found to verify")

        # Run mock server and verify contracts
        with mock_server_running():
            # Pact v3 API
            verifier = Verifier("BillingAPI", host=MOCK_SERVER_URL)

            # Add pact sources
            for pact_file in pact_files:
                print(f"Adding pact file: {pact_file}")
                verifier.add_source(pact_file)

            # Set provider state handler (body=True means state changes in request body)
            verifier.state_handler(f"{MOCK_SERVER_URL}/pact-states", body=True)

            # Verify
            print("Running verification...")
            verifier.verify()

    def test_mock_server_contract_compliance(self):
        """Test that mock server responses match contract expectations."""
        with mock_server_running():
            # First set up the provider state
            response = requests.post(
                f"{MOCK_SERVER_URL}/pact-states",
                json={"state": "A contract exists"},
                timeout=5,
            )
            assert response.status_code == 200

            # Test contract endpoint
            response = requests.get(
                f"{MOCK_SERVER_URL}/api/v1/contracts/12345",
                timeout=5,
            )
            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "id" in data
            assert data["id"] == "12345"
            assert "status" in data
            assert data["status"] in ["ACTIVE", "INACTIVE", "PENDING"]

            # Test credit creation
            credit_data = {
                "customer_id": "CUST001",
                "amount": 500.0,
                "currency": "USD",
                "description": "Monthly credit",
                "type": "ADJUSTMENT",
            }
            response = requests.post(
                f"{MOCK_SERVER_URL}/api/v1/credits",
                json=credit_data,
                timeout=5,
            )
            assert response.status_code == 201
            data = response.json()
            assert "creditId" in data
            assert "status" in data

            # Test meter submission
            meter_data = {
                "resource_id": "RES001",
                "meter_name": "cpu.usage",
                "value": 85.5,
                "unit": "percent",
                "timestamp": "2024-01-01T00:00:00Z",
                "metadata": {"region": "us-east-1"},
            }
            response = requests.post(
                f"{MOCK_SERVER_URL}/api/v1/billing/meters",
                json=meter_data,
                headers={"uuid": "test-uuid"},
                timeout=5,
            )
            assert response.status_code == 200

    def test_billing_groups_endpoints(self):
        """Test billing groups endpoints."""
        with mock_server_running():
            # Test apply contract
            contract_data = {
                "contractId": "contract-123",
                "name": "Test Contract",
                "defaultYn": "Y",
                "monthFrom": "2024-01",
            }
            response = requests.put(
                f"{MOCK_SERVER_URL}/api/v1/billing/admin/billing-groups/bg-123",
                json=contract_data,
                timeout=5,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["billingGroupId"] == "bg-123"
            assert data["contractId"] == "contract-123"

            # Test delete contract
            response = requests.delete(
                f"{MOCK_SERVER_URL}/api/v1/billing/admin/billing-groups/bg-123/contracts",
                timeout=5,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "DELETED"


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
