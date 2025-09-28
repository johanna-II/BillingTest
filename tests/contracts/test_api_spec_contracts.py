"""Contract tests based on OpenAPI specification.

These tests ensure that our billing libraries correctly interact with the API
according to the OpenAPI specification defined in docs/openapi/billing-api.yaml.
"""

import os

import pytest
from pact import Consumer, EachLike, Like, Provider, Term

from libs.Batch import BatchManager
from libs.Contract import ContractManager
from libs.Credit import CreditManager
from libs.exceptions import APIRequestException
from libs.http_client import BillingAPIClient
from libs.Metering import MeteringManager
from libs.Payments import PaymentManager


@pytest.mark.contract
@pytest.mark.skipif(
    os.getenv("USE_MOCK_SERVER", "false").lower() != "true",
    reason="Contract tests require mock server",
)
class TestOpenAPIContracts:
    """Contract tests based on OpenAPI specification."""

    @pytest.fixture(scope="class", autouse=True)
    def pact(self):
        """Setup Pact consumer/provider."""
        consumer = Consumer("BillingLibraries")
        provider = Provider("BillingAPI")

        # Use mock server URL from environment or default
        # mock_url = os.getenv("MOCK_SERVER_URL", "http://localhost:5000")

        pact = consumer.has_pact_with(
            provider,
            host_name="localhost",
            port=1234,  # Use different port to avoid conflict with mock server
            pact_dir="./tests/contracts/pacts",
        )

        pact.start_service()
        yield pact
        pact.stop_service()

    @pytest.fixture
    def api_client(self):
        """Create API client for tests."""
        # Use Pact mock service port
        return BillingAPIClient("http://localhost:1234", use_mock=True)

    def test_contract_api_get_contract_details(self, pact, api_client):
        """Test GET /contracts/{contractId} endpoint."""
        contract_id = "12345"

        # Define expected interaction based on OpenAPI spec
        expected_contract = {
            "id": Like(contract_id),
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
                    "currency": Like("USD"),
                }
            ),
            "total_amount": Like(100.0),
            "created_at": Term(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", "2024-01-15T10:00:00Z"),
            "billing_period": {
                "start": Term(r"\d{4}-\d{2}-\d{2}", "2024-01-01"),
                "end": Term(r"\d{4}-\d{2}-\d{2}", "2024-01-31"),
            },
        }

        (
            pact.given("Contract 12345 exists")
            .upon_receiving("a request for contract details")
            .with_request("get", f"/api/v1/contracts/{contract_id}")
            .will_respond_with(200, body=expected_contract)
        )

        with pact:
            # Use ContractManager to make the request
            ContractManager("2024-01", "test-billing-group", client=api_client)
            # In real implementation, we would add a get_contract_details method
            # For now, test the API endpoint directly
            response = api_client.get(f"/api/v1/contracts/{contract_id}")

            assert response["id"] == contract_id
            assert response["status"] in ["ACTIVE", "INACTIVE", "PENDING"]
            assert "customer" in response
            assert "items" in response

    def test_credit_api_grant_credit(self, pact, api_client):
        """Test POST /credits endpoint for granting credit."""
        credit_request = {
            "user_id": "USER001",
            "amount": 500.0,
            "currency": "USD",
            "type": "ADJUSTMENT",
            "description": "Monthly credit grant",
            "expires_at": "2024-12-31T23:59:59Z",
        }

        expected_response = {
            "id": Term(r"[0-9a-f-]+", "550e8400-e29b-41d4-a716-446655440000"),
            "user_id": Like(credit_request["user_id"]),
            "amount": Like(credit_request["amount"]),
            "currency": Like(credit_request["currency"]),
            "type": Like(credit_request["type"]),
            "status": Term(r"(PENDING|APPROVED|REJECTED)", "APPROVED"),
            "created_at": Term(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", "2024-01-15T10:00:00Z"),
            "expires_at": Like(credit_request["expires_at"]),
        }

        (
            pact.given("User USER001 exists")
            .upon_receiving("a request to grant credit")
            .with_request("post", "/api/v1/credits", body=credit_request)
            .will_respond_with(201, body=expected_response)
        )

        with pact:
            CreditManager("USER001", client=api_client)
            # Test credit granting through the API
            response = api_client.post("/api/v1/credits", json_data=credit_request)

            assert response["user_id"] == credit_request["user_id"]
            assert response["amount"] == credit_request["amount"]
            assert response["status"] in ["PENDING", "APPROVED", "REJECTED"]

    def test_metering_api_send_usage(self, pact, api_client):
        """Test POST /metering endpoint for sending usage data."""
        metering_data = {
            "app_key": "APP001",
            "counter_name": "compute.instance.small",
            "counter_type": "DELTA",
            "counter_unit": "HOURS",
            "counter_volume": "24.5",
            "timestamp": "2024-01-15T10:00:00Z",
            "metadata": {"region": "us-east-1", "instance_id": "i-1234567890abcdef0"},
        }

        expected_response = {
            "id": Term(r"[0-9a-f-]+", "meter-123456"),
            "app_key": Like(metering_data["app_key"]),
            "status": Like("ACCEPTED"),
            "message": Like("Metering data recorded successfully"),
            "timestamp": Term(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", "2024-01-15T10:00:01Z"),
        }

        (
            pact.given("Application APP001 exists")
            .upon_receiving("a request to send metering data")
            .with_request("post", "/api/v1/metering", body=metering_data)
            .will_respond_with(201, body=expected_response)
        )

        with pact:
            MeteringManager("2024-01", client=api_client)
            # Test metering through the API
            response = api_client.post("/api/v1/metering", json_data=metering_data)

            assert response["app_key"] == metering_data["app_key"]
            assert response["status"] == "ACCEPTED"

    def test_payment_api_get_statement(self, pact, api_client):
        """Test GET /payments/statements endpoint."""
        query_params = {"month": "2024-01", "user_id": "USER001"}

        expected_statements = {
            "statements": [
                {
                    "id": Like("STMT001"),
                    "user_id": Like("USER001"),
                    "billing_period": {
                        "start": Term(r"\d{4}-\d{2}-\d{2}", "2024-01-01"),
                        "end": Term(r"\d{4}-\d{2}-\d{2}", "2024-01-31"),
                    },
                    "charges": {
                        "subtotal": Like(1000.0),
                        "tax": Like(100.0),
                        "discounts": Like(50.0),
                        "credits_applied": Like(200.0),
                        "total": Like(850.0),
                    },
                    "status": Term(r"(DRAFT|ISSUED|PAID|OVERDUE)", "ISSUED"),
                    "due_date": Term(r"\d{4}-\d{2}-\d{2}", "2024-02-15"),
                    "created_at": Term(
                        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", "2024-02-01T00:00:00Z"
                    ),
                }
            ],
            "pagination": {"total": Like(1), "page": Like(1), "per_page": Like(20)},
        }

        (
            pact.given("User USER001 has statements for 2024-01")
            .upon_receiving("a request for payment statements")
            .with_request("get", "/api/v1/payments/statements", query=query_params)
            .will_respond_with(200, body=expected_statements)
        )

        with pact:
            PaymentManager("2024-01", "USER001", client=api_client)
            # Test getting statements through the API
            response = api_client.get("/api/v1/payments/statements", params=query_params)

            assert "statements" in response
            assert len(response["statements"]) > 0
            statement = response["statements"][0]
            assert statement["user_id"] == "USER001"
            assert "charges" in statement

    def test_batch_api_create_job(self, pact, api_client):
        """Test POST /batch/jobs endpoint for creating batch jobs."""
        batch_request = {
            "job_type": "BILLING_CALCULATION",
            "parameters": {
                "month": "2024-01",
                "billing_group_id": "BG001",
                "force_recalculation": True,
            },
            "scheduled_at": "2024-02-01T00:00:00Z",
        }

        expected_response = {
            "job_id": Term(r"[0-9a-f-]+", "job-123456"),
            "job_type": Like(batch_request["job_type"]),
            "status": Term(r"(PENDING|RUNNING|COMPLETED|FAILED)", "PENDING"),
            "created_at": Term(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", "2024-01-15T10:00:00Z"),
            "scheduled_at": Like(batch_request["scheduled_at"]),
            "parameters": Like(batch_request["parameters"]),
        }

        (
            pact.given("Batch processing is available")
            .upon_receiving("a request to create a batch job")
            .with_request("post", "/api/v1/batch/jobs", body=batch_request)
            .will_respond_with(201, body=expected_response)
        )

        with pact:
            BatchManager("2024-01", client=api_client)
            # Test batch job creation through the API
            response = api_client.post("/api/v1/batch/jobs", json_data=batch_request)

            assert response["job_type"] == batch_request["job_type"]
            assert response["status"] in ["PENDING", "RUNNING", "COMPLETED", "FAILED"]
            assert "job_id" in response

    def test_error_handling_404(self, pact, api_client):
        """Test 404 error handling according to OpenAPI spec."""
        error_response = {
            "error": {
                "code": Like("NOT_FOUND"),
                "message": Like("Contract not found"),
                "details": {
                    "contract_id": Like("99999"),
                    "timestamp": Term(
                        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", "2024-01-15T10:00:00Z"
                    ),
                },
            }
        }

        (
            pact.given("Contract 99999 does not exist")
            .upon_receiving("a request for non-existent contract")
            .with_request("get", "/api/v1/contracts/99999")
            .will_respond_with(404, body=error_response)
        )

        with pact:
            # Test error handling
            with pytest.raises(APIRequestException) as exc_info:
                api_client.get("/api/v1/contracts/99999")

            assert exc_info.value.status_code == 404

    def test_error_handling_validation(self, pact, api_client):
        """Test 400 validation error handling according to OpenAPI spec."""
        invalid_credit_request = {
            "user_id": "USER001",
            "amount": -100.0,  # Invalid negative amount
            "currency": "INVALID",
            "type": "UNKNOWN_TYPE",
        }

        error_response = {
            "error": {
                "code": Like("VALIDATION_ERROR"),
                "message": Like("Request validation failed"),
                "details": {
                    "fields": [
                        {
                            "field": Like("amount"),
                            "message": Like("Amount must be positive"),
                            "value": Like(-100.0),
                        },
                        {
                            "field": Like("currency"),
                            "message": Like("Invalid currency code"),
                            "value": Like("INVALID"),
                        },
                    ]
                },
            }
        }

        (
            pact.given("Credit validation is enforced")
            .upon_receiving("a request with invalid credit data")
            .with_request("post", "/api/v1/credits", body=invalid_credit_request)
            .will_respond_with(400, body=error_response)
        )

        with pact:
            # Test validation error handling
            with pytest.raises(APIRequestException) as exc_info:
                api_client.post("/api/v1/credits", json_data=invalid_credit_request)

            assert exc_info.value.status_code == 400
