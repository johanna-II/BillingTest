"""Consumer contract tests for Billing API interactions using Pact Python v3."""

import os
from datetime import datetime, timezone

import pytest
import requests
from pact import Pact, match
from pytest import approx

# Pact configuration
PACT_DIR = os.path.join(os.path.dirname(__file__), "pacts")
os.makedirs(PACT_DIR, exist_ok=True)


@pytest.fixture
def pact():
    """Set up Pact consumer (v3 API) - function scoped for isolation."""
    pact_instance = Pact("BillingTest", "BillingAPI")
    yield pact_instance
    # Persist contract after each test
    pact_instance.write_file(directory=PACT_DIR)


@pytest.mark.contract
@pytest.mark.consumer
@pytest.mark.integration
@pytest.mark.mock_required
class TestContractBilling:
    """Contract tests for billing operations."""

    def test_get_contract_detail(self, pact):
        """Test contract detail retrieval matches expected format."""
        # Define the interaction
        (
            pact.upon_receiving("a request for contract details")
            .given("A contract exists")
            .with_request("GET", "/api/v1/contracts/12345")
            .will_respond_with(200)
            .with_header("Content-Type", "application/json")
            .with_body(
                {
                    "id": match.regex("12345", regex=r"[0-9]+"),
                    "status": match.regex("ACTIVE", regex=r"(ACTIVE|INACTIVE|PENDING)"),
                    "customer": {
                        "id": match.like("CUST001"),
                        "name": match.like("Test Customer"),
                        "email": match.regex("test@example.com", regex=r".+@.+\..+"),
                    },
                    "items": match.each_like(
                        {
                            "id": match.like("ITEM001"),
                            "description": match.like("Compute Instance"),
                            "quantity": match.like(1),
                            "unit_price": match.like(100.0),
                            "total": match.like(100.0),
                        }
                    ),
                    "total_amount": match.like(500.0),
                    "currency": match.regex("USD", regex=r"[A-Z]{3}"),
                    "created_at": match.regex(
                        "2025-01-01T00:00:00+00:00",
                        regex=r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}",
                    ),
                    "updated_at": match.regex(
                        "2025-01-01T00:00:00+00:00",
                        regex=r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}",
                    ),
                }
            )
        )

        # Execute the test
        with pact.serve() as srv:
            response = requests.get(
                f"{srv.url}/api/v1/contracts/12345",
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "12345"
            assert data["status"] == "ACTIVE"
            assert "customer" in data
            assert "items" in data

    def test_create_credit(self, pact):
        """Test credit creation."""
        request_body = {
            "customer_id": "CUST001",
            "amount": 500.0,
            "currency": "USD",
            "reason": "Monthly adjustment",
            "type": "ADJUSTMENT",
        }

        # Define the interaction
        (
            pact.upon_receiving("a request to create a credit")
            .given("Customer exists")
            .with_request("POST", "/api/v1/credits")
            .with_header("Content-Type", "application/json")
            .with_body(request_body)
            .will_respond_with(201)
            .with_header("Content-Type", "application/json")
            .with_body(
                {
                    "id": match.regex("CREDIT_12345", regex=r"CREDIT_[0-9A-F]+"),
                    "status": match.regex("ACTIVE", regex=r"(ACTIVE|PENDING|APPLIED)"),
                    "customer_id": match.like("CUST001"),
                    "amount": match.like(500.0),
                    "currency": match.like("USD"),
                    "created_at": match.regex(
                        "2025-01-01T00:00:00+00:00",
                        regex=r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}",
                    ),
                    "expires_at": match.regex(
                        "2025-01-01T00:00:00+00:00",
                        regex=r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}",
                    ),
                }
            )
        )

        # Execute the test
        with pact.serve() as srv:
            response = requests.post(
                f"{srv.url}/api/v1/credits",
                json=request_body,
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "ACTIVE"
            assert data["customer_id"] == "CUST001"
            assert data["amount"] == approx(500.0)

    def test_meter_submission(self, pact):
        """Test meter data submission."""
        request_body = {
            "resource_id": "RES001",
            "meter_name": "cpu.usage",
            "value": 85.5,
            "unit": "percent",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {"region": "us-east-1", "instance_type": "t2.micro"},
        }

        # Define the interaction
        (
            pact.upon_receiving("meter data submission")
            .given("Resource exists")
            .with_request("POST", "/api/v1/meters")
            .with_header("Content-Type", "application/json")
            .with_body(request_body)
            .will_respond_with(201)
            .with_header("Content-Type", "application/json")
            .with_body(
                {
                    "id": match.regex("METER_67890", regex=r"METER_[0-9A-F]+"),
                    "status": "ACCEPTED",
                    "resource_id": match.like("RES001"),
                    "timestamp": match.regex(
                        "2025-01-01T00:00:00+00:00",
                        regex=r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}",
                    ),
                }
            )
        )

        # Execute the test
        with pact.serve() as srv:
            response = requests.post(
                f"{srv.url}/api/v1/meters",
                json=request_body,
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "ACCEPTED"
            assert data["resource_id"] == "RES001"

    def test_payment_status(self, pact):
        """Test payment status check."""
        # Define the interaction
        (
            pact.upon_receiving("a request for payment status")
            .given("Payment exists")
            .with_request("GET", "/api/v1/payments/PAY_ABC123")
            .will_respond_with(200)
            .with_header("Content-Type", "application/json")
            .with_body(
                {
                    "payment_id": match.regex("PAY_ABC123", regex=r"PAY_[0-9A-F]+"),
                    "status": match.regex(
                        "PENDING", regex=r"(PENDING|PROCESSING|COMPLETED|FAILED)"
                    ),
                    "amount": match.like(1500.0),
                    "currency": match.like("USD"),
                    "due_date": match.date(),
                    "invoice": {
                        "id": match.like("INV001"),
                        "url": match.regex(
                            "https://api.example.com/invoices/INV001",
                            regex=r"https://.+/invoices/.+",
                        ),
                    },
                }
            )
        )

        # Execute the test
        with pact.serve() as srv:
            response = requests.get(
                f"{srv.url}/api/v1/payments/PAY_ABC123",
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["payment_id"] == "PAY_ABC123"
            assert data["status"] in ["PENDING", "PROCESSING", "COMPLETED", "FAILED"]

    def test_adjustment_application(self, pact):
        """Test applying billing adjustments."""
        request_body = {
            "type": "DISCOUNT",
            "amount": 100.0,
            "reason": "Promotional discount",
            "target_invoice": "INV001",
        }

        # Define the interaction
        (
            pact.upon_receiving("adjustment application request")
            .given("Invoice exists")
            .with_request("POST", "/api/v1/adjustments")
            .with_header("Content-Type", "application/json")
            .with_body(request_body)
            .will_respond_with(201)
            .with_header("Content-Type", "application/json")
            .with_body(
                {
                    "adjustment_id": match.regex("ADJ_XYZ789", regex=r"ADJ_[0-9A-F]+"),
                    "status": "APPLIED",
                    "original_amount": match.like(1500.0),
                    "adjusted_amount": match.like(1400.0),
                    "applied_at": match.regex(
                        "2025-01-01T00:00:00+00:00",
                        regex=r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}",
                    ),
                }
            )
        )

        # Execute the test
        with pact.serve() as srv:
            response = requests.post(
                f"{srv.url}/api/v1/adjustments",
                json=request_body,
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "APPLIED"
            assert data["adjustment_id"] == "ADJ_XYZ789"
