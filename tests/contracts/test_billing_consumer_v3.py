"""Consumer contract tests for Billing API interactions using Pact Python v3."""

import os
from datetime import datetime

import pytest
from pact import EachLike, Format, Like, Pact, Term

# Pact configuration
PACT_DIR = os.path.join(os.path.dirname(__file__), "pacts")
os.makedirs(PACT_DIR, exist_ok=True)


@pytest.fixture(scope="session")
def pact():
    """Set up Pact consumer."""
    pact = Pact(
        consumer_name="BillingTest",
        provider_name="BillingAPI",
        log_dir=os.path.join(os.path.dirname(__file__), "logs"),
        pact_dir=PACT_DIR,
    )

    pact.start_service()
    yield pact
    pact.stop_service()


@pytest.mark.contract
@pytest.mark.consumer
@pytest.mark.integration
@pytest.mark.mock_required
class TestContractBilling:
    """Contract tests for billing operations."""

    def test_get_contract_detail(self, pact):
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
            "items": EachLike(
                {
                    "id": Like("ITEM001"),
                    "description": Like("Compute Instance"),
                    "quantity": Like(1),
                    "unit_price": Like(100.0),
                    "total": Like(100.0),
                }
            ),
            "total_amount": Like(500.0),
            "currency": Term(r"[A-Z]{3}", "USD"),
            "created_at": Format().iso_8601_datetime(),
            "updated_at": Format().iso_8601_datetime(),
        }

        # Define the interaction
        (
            pact.given("A contract exists")
            .upon_receiving("a request for contract details")
            .with_request("GET", "/api/v1/contracts/12345")
            .will_respond_with(200, body=expected)
        )

        # Execute the test
        with pact:
            # Make actual request
            response = pact.session.get(f"{pact.uri}/api/v1/contracts/12345")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "12345"
            assert data["status"] == "ACTIVE"
            assert "customer" in data
            assert "items" in data

    def test_create_credit(self, pact):
        """Test credit creation."""
        request_body = {
            "customer_id": Like("CUST001"),
            "amount": Like(500.0),
            "currency": Term(r"[A-Z]{3}", "USD"),
            "reason": Like("Monthly adjustment"),
            "type": Term(r"(ADJUSTMENT|REFUND|PROMOTION)", "ADJUSTMENT"),
        }

        expected_response = {
            "id": Term(r"CREDIT_[0-9A-F]+", "CREDIT_12345"),
            "status": Term(r"(ACTIVE|PENDING|APPLIED)", "ACTIVE"),
            "customer_id": Like("CUST001"),
            "amount": Like(500.0),
            "currency": Like("USD"),
            "created_at": Format().iso_8601_datetime(),
            "expires_at": Format().iso_8601_datetime(),
        }

        # Define the interaction
        (
            pact.given("Customer exists")
            .upon_receiving("a request to create a credit")
            .with_request(
                "POST",
                "/api/v1/credits",
                headers={"Content-Type": "application/json"},
                body=request_body,
            )
            .will_respond_with(201, body=expected_response)
        )

        # Execute the test
        with pact:
            response = pact.session.post(
                f"{pact.uri}/api/v1/credits",
                json={
                    "customer_id": "CUST001",
                    "amount": 500.0,
                    "currency": "USD",
                    "reason": "Monthly adjustment",
                    "type": "ADJUSTMENT",
                },
            )
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "ACTIVE"
            assert data["customer_id"] == "CUST001"
            assert data["amount"] == 500.0

    def test_meter_submission(self, pact):
        """Test meter data submission."""
        request_body = {
            "resource_id": Like("RES001"),
            "meter_name": Like("cpu.usage"),
            "value": Like(85.5),
            "unit": Term(r"(percent|count|bytes|seconds)", "percent"),
            "timestamp": Format().iso_8601_datetime(),
            "metadata": Like({"region": "us-east-1", "instance_type": "t2.micro"}),
        }

        expected_response = {
            "id": Term(r"METER_[0-9A-F]+", "METER_67890"),
            "status": "ACCEPTED",
            "resource_id": Like("RES001"),
            "timestamp": Format().iso_8601_datetime(),
        }

        # Define the interaction
        (
            pact.given("Resource exists")
            .upon_receiving("meter data submission")
            .with_request(
                "POST",
                "/api/v1/meters",
                headers={"Content-Type": "application/json"},
                body=request_body,
            )
            .will_respond_with(201, body=expected_response)
        )

        # Execute the test
        with pact:
            response = pact.session.post(
                f"{pact.uri}/api/v1/meters",
                json={
                    "resource_id": "RES001",
                    "meter_name": "cpu.usage",
                    "value": 85.5,
                    "unit": "percent",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "metadata": {"region": "us-east-1", "instance_type": "t2.micro"},
                },
            )
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "ACCEPTED"
            assert data["resource_id"] == "RES001"

    def test_payment_status(self, pact):
        """Test payment status check."""
        expected_response = {
            "payment_id": Term(r"PAY_[0-9A-F]+", "PAY_ABC123"),
            "status": Term(r"(PENDING|PROCESSING|COMPLETED|FAILED)", "PENDING"),
            "amount": Like(1500.0),
            "currency": Like("USD"),
            "due_date": Format().iso_8601_date(),
            "invoice": {
                "id": Like("INV001"),
                "url": Term(
                    r"https://.+/invoices/.+",
                    "https://api.example.com/invoices/INV001",
                ),
            },
        }

        # Define the interaction
        (
            pact.given("Payment exists")
            .upon_receiving("a request for payment status")
            .with_request("GET", "/api/v1/payments/PAY_ABC123")
            .will_respond_with(200, body=expected_response)
        )

        # Execute the test
        with pact:
            response = pact.session.get(f"{pact.uri}/api/v1/payments/PAY_ABC123")
            assert response.status_code == 200
            data = response.json()
            assert data["payment_id"] == "PAY_ABC123"
            assert data["status"] in ["PENDING", "PROCESSING", "COMPLETED", "FAILED"]

    def test_adjustment_application(self, pact):
        """Test applying billing adjustments."""
        request_body = {
            "type": Term(r"(DISCOUNT|CREDIT|PENALTY)", "DISCOUNT"),
            "amount": Like(100.0),
            "reason": Like("Promotional discount"),
            "target_invoice": Like("INV001"),
        }

        expected_response = {
            "adjustment_id": Term(r"ADJ_[0-9A-F]+", "ADJ_XYZ789"),
            "status": "APPLIED",
            "original_amount": Like(1500.0),
            "adjusted_amount": Like(1400.0),
            "applied_at": Format().iso_8601_datetime(),
        }

        # Define the interaction
        (
            pact.given("Invoice exists")
            .upon_receiving("adjustment application request")
            .with_request(
                "POST",
                "/api/v1/adjustments",
                headers={"Content-Type": "application/json"},
                body=request_body,
            )
            .will_respond_with(201, body=expected_response)
        )

        # Execute the test
        with pact:
            response = pact.session.post(
                f"{pact.uri}/api/v1/adjustments",
                json={
                    "type": "DISCOUNT",
                    "amount": 100.0,
                    "reason": "Promotional discount",
                    "target_invoice": "INV001",
                },
            )
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "APPLIED"
            assert data["adjustment_id"] == "ADJ_XYZ789"
