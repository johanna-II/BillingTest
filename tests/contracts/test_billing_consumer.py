"""Consumer contract tests for Billing API interactions (Legacy Pact v2 - Deprecated)."""

import os

import pytest
import requests
from pact import Consumer, Like, Provider, Term

# This file uses Pact Python v2 which is deprecated.
# Please use test_billing_consumer_v3.py for new tests.

# Pact configuration
PACT_DIR = os.path.join(os.path.dirname(__file__), "pacts")
os.makedirs(PACT_DIR, exist_ok=True)


@pytest.fixture(scope="session")
def pact():
    """Set up Pact consumer."""
    consumer = Consumer("BillingTest")
    provider = Provider("BillingAPI")

    pact = consumer.has_pact_with(provider, pact_dir=PACT_DIR)

    pact.start_service()
    yield pact
    try:
        pact.stop_service()
    except RuntimeError as e:
        if "error when stopping the Pact mock service" in str(e):
            # Ignore cleanup errors
            pass
        else:
            raise


@pytest.mark.contract
@pytest.mark.integration
@pytest.mark.mock_required
class TestContractBilling:
    """Contract tests for billing operations."""

    def test_get_contract_detail(self, pact) -> None:
        """Test contract detail retrieval matches expected format."""
        # Expected response format
        expected = {
            "id": Term(r"[0-9]+", "12345"),
            "status": Term(r"(ACTIVE|INACTIVE|PENDING)", "ACTIVE"),
            "customer": {
                "id": Like("CUST001"),
                "name": Like("Test Customer"),
                "email": Term(r".+@.+\..+", "test@example.com"),
            },
            "items": Like(
                [
                    {
                        "id": Like("ITEM001"),
                        "description": Like("Compute Instance"),
                        "quantity": Like(1),
                        "unit_price": Like(100.0),
                    }
                ]
            ),
            "created_at": Term(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2025-01-01T00:00:00"
            ),
        }

        # Define the interaction
        (
            pact.given("A contract exists")
            .upon_receiving("A request for contract details")
            .with_request("GET", "/api/v1/contracts/12345")
            .will_respond_with(200, body=expected)
        )

        # Execute the test
        with pact:
            # Use requests directly to avoid BillingAPIClient's header checking
            response = requests.get(
                f"http://localhost:{pact.port}/api/v1/contracts/12345"
            )

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "id" in data
            assert "status" in data
            assert data["status"] in ["ACTIVE", "INACTIVE", "PENDING"]
            assert "customer" in data
            assert "items" in data

    def test_create_credit_transaction(self, pact) -> None:
        """Test credit creation matches expected format."""
        # Request body
        credit_request = {
            "customer_id": "CUST001",
            "amount": 500.0,
            "currency": "USD",
            "description": "Monthly credit",
            "type": "ADJUSTMENT",
        }

        # Expected response
        expected = {
            "id": Term(r"[0-9a-f-]+", "550e8400-e29b-41d4-a716-446655440000"),
            "customer_id": Like("CUST001"),
            "amount": Like(500.0),
            "currency": Like("USD"),
            "description": Like("Monthly credit"),
            "type": Like("ADJUSTMENT"),
            "status": Term(r"(PENDING|APPROVED|REJECTED)", "APPROVED"),
            "created_at": Term(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2025-01-01T00:00:00"
            ),
        }

        # Define the interaction
        (
            pact.given("Customer exists")
            .upon_receiving("A request to create credit")
            .with_request(
                "POST",
                "/api/v1/credits",
                headers={"Content-Type": "application/json"},
                body=credit_request,
            )
            .will_respond_with(201, body=expected)
        )

        # Execute the test
        with pact:
            # Use requests directly to avoid BillingAPIClient's header checking
            response = requests.post(
                f"http://localhost:{pact.port}/api/v1/credits", json=credit_request
            )

            # Verify response
            assert response.status_code == 201
            data = response.json()
            assert data["customer_id"] == credit_request["customer_id"]
            assert data["amount"] == credit_request["amount"]
            assert data["status"] in ["PENDING", "APPROVED", "REJECTED"]

    def test_get_metering_data(self, pact) -> None:
        """Test metering data retrieval matches expected format."""
        # Expected response
        expected = {
            "project_id": Like("PROJ001"),
            "period": {
                "start": Term(
                    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2025-01-01T00:00:00"
                ),
                "end": Term(
                    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2025-01-31T23:59:59"
                ),
            },
            "usage": Like(
                [
                    {
                        "resource_type": Like("compute"),
                        "resource_id": Like("vm-001"),
                        "quantity": Like(744.0),
                        "unit": Like("hours"),
                        "cost": Like(74.40),
                    }
                ]
            ),
            "total_cost": Like(74.40),
        }

        # Define the interaction
        (
            pact.given("Metering data exists for project")
            .upon_receiving("A request for metering data")
            .with_request(
                "GET",
                "/api/v1/metering",
                query={"project_id": "PROJ001", "month": "2025-01"},
            )
            .will_respond_with(200, body=expected)
        )

        # Execute the test
        with pact:
            # Use requests directly to avoid BillingAPIClient's header checking
            response = requests.get(
                f"http://localhost:{pact.port}/api/v1/metering",
                params={"project_id": "PROJ001", "month": "2025-01"},
            )

            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert "project_id" in data
            assert "period" in data
            assert "usage" in data
            assert isinstance(data["usage"], list)
            assert "total_cost" in data

    def test_payment_status_update(self, pact) -> None:
        """Test payment status update matches expected format."""
        # Request body
        status_update = {
            "status": "COMPLETED",
            "transaction_id": "TXN123456",
            "completed_at": "2025-01-15T10:30:00",
        }

        # Expected response
        expected = {
            "payment_id": Like("PAY001"),
            "status": Like("COMPLETED"),
            "transaction_id": Like("TXN123456"),
            "amount": Like(1000.0),
            "currency": Like("USD"),
            "updated_at": Term(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2025-01-15T10:30:00"
            ),
        }

        # Define the interaction
        (
            pact.given("Payment exists")
            .upon_receiving("A request to update payment status")
            .with_request(
                "PATCH",
                "/api/v1/payments/PAY001",
                headers={"Content-Type": "application/json"},
                body=status_update,
            )
            .will_respond_with(200, body=expected)
        )

        # Execute the test
        with pact:
            # Use requests directly to avoid BillingAPIClient's header checking
            response = requests.patch(
                f"http://localhost:{pact.port}/api/v1/payments/PAY001",
                json=status_update,
            )

            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "COMPLETED"
            assert data["transaction_id"] == status_update["transaction_id"]


@pytest.mark.contract
@pytest.mark.integration
@pytest.mark.mock_required
class TestContractErrorHandling:
    """Contract tests for error scenarios."""

    def test_contract_not_found(self, pact) -> None:
        """Test 404 response for non-existent contract."""
        expected_error = {
            "error": Like("NOT_FOUND"),
            "message": Like("Contract not found"),
            "code": Like(404),
        }

        # Define the interaction
        (
            pact.given("Contract does not exist")
            .upon_receiving("A request for non-existent contract")
            .with_request("GET", "/api/v1/contracts/99999")
            .will_respond_with(404, body=expected_error)
        )

        # Execute the test
        with pact:
            # Use requests directly to avoid BillingAPIClient's header checking
            response = requests.get(
                f"http://localhost:{pact.port}/api/v1/contracts/99999"
            )

            # Verify response
            assert response.status_code == 404
            data = response.json()
            assert data["error"] == "NOT_FOUND"
            assert "message" in data

    def test_invalid_credit_amount(self, pact) -> None:
        """Test validation error for invalid credit amount."""
        # Invalid request
        invalid_request = {
            "customer_id": "CUST001",
            "amount": -100.0,  # Negative amount
            "currency": "USD",
            "description": "Invalid credit",
        }

        expected_error = {
            "error": Like("VALIDATION_ERROR"),
            "message": Like("Invalid credit amount"),
            "field": Like("amount"),
            "code": Like(400),
        }

        # Define the interaction
        (
            pact.given("Customer exists")
            .upon_receiving("A request with invalid credit amount")
            .with_request(
                "POST",
                "/api/v1/credits",
                headers={"Content-Type": "application/json"},
                body=invalid_request,
            )
            .will_respond_with(400, body=expected_error)
        )

        # Execute the test
        with pact:
            # Use requests directly to avoid BillingAPIClient's header checking
            response = requests.post(
                f"http://localhost:{pact.port}/api/v1/credits", json=invalid_request
            )

            # Verify response
            assert response.status_code == 400
            data = response.json()
            assert data["error"] == "VALIDATION_ERROR"
            assert data["field"] == "amount"
