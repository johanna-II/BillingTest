"""Contract tests for basic CRUD operations - moved from integration tests."""

import os

import pytest
from pact import EachLike, Format, Like, Pact, Term

PACT_DIR = os.path.join(os.path.dirname(__file__), "pacts")
os.makedirs(PACT_DIR, exist_ok=True)


@pytest.fixture(scope="session")
def pact():
    """Set up Pact consumer for CRUD operations."""
    pact = Pact(
        consumer_name="BillingCRUD",
        provider_name="BillingAPI",
        log_dir=os.path.join(os.path.dirname(__file__), "logs"),
        pact_dir=PACT_DIR,
    )

    pact.start_service()
    yield pact
    pact.stop_service()


@pytest.mark.contract
@pytest.mark.consumer
class TestCRUDContracts:
    """Contract tests for basic CRUD operations.

    These tests were moved from integration tests as they primarily
    validate API contracts rather than complex business logic.
    """

    def test_create_metering_data(self, pact):
        """Test creating metering data - basic CRUD operation."""
        # Request body
        metering_request = {
            "meterList": [
                {
                    "appKey": "test-app-001",
                    "counterName": "compute.instance",
                    "counterType": "DELTA",
                    "counterUnit": "HOURS",
                    "counterVolume": "24",
                    "resourceId": "vm-001",
                    "resourceName": "Test VM",
                    "parentResourceId": "project-001",
                    "source": "qa.billing.test",
                    "timestamp": "2024-01-01T00:00:00.000+09:00",
                }
            ]
        }

        # Expected response
        expected = {
            "header": {
                "isSuccessful": Like(True),
                "resultCode": Like(0),
                "resultMessage": Like("SUCCESS"),
            },
            "body": {"accepted": Like(1), "rejected": Like(0), "total": Like(1)},
        }

        # Define the interaction
        (
            pact.given("System is ready to accept metering data")
            .upon_receiving("a request to submit metering data")
            .with_request(
                "POST",
                "/api/v1/billing/meters",
                headers={"Content-Type": "application/json"},
                body=metering_request,
            )
            .will_respond_with(200, body=expected)
        )

        # Execute the test
        with pact:
            # Make actual request
            response = pact.session.post(f"{pact.uri}/api/v1/billing/meters", json=metering_request)
            assert response.status_code == 200
            data = response.json()
            assert data["header"]["isSuccessful"] is True
            assert data["body"]["accepted"] == 1

    def test_get_adjustment_list(self, pact):
        """Test retrieving adjustment list - basic read operation."""
        # Expected response format
        expected = {
            "header": {
                "isSuccessful": Like(True),
                "resultCode": Like(0),
                "resultMessage": Like("SUCCESS"),
            },
            "adjustments": EachLike(
                {
                    "adjustmentId": Term(r"adj-[0-9a-f]+", "adj-001"),
                    "adjustmentType": Term(
                        r"(FIXED_DISCOUNT|RATE_DISCOUNT|FIXED_SURCHARGE|RATE_SURCHARGE)",
                        "FIXED_DISCOUNT",
                    ),
                    "adjustmentAmount": Like(100.0),
                    "adjustmentTarget": Term(r"(PROJECT|BILLING_GROUP|ORGANIZATION)", "PROJECT"),
                    "targetId": Like("test-app-001"),
                    "description": Like("Test adjustment"),
                    "createdAt": Format().iso_8601_datetime(),
                }
            ),
        }

        # Define the interaction
        (
            pact.given("Adjustments exist for a project")
            .upon_receiving("a request to get adjustment list")
            .with_request(
                "GET",
                "/api/v1/billing/adjustments",
                query={
                    "adjustmentTarget": "PROJECT",
                    "targetId": "test-app-001",
                    "page": "1",
                    "itemsPerPage": "50",
                },
            )
            .will_respond_with(200, body=expected)
        )

        # Execute the test
        with pact:
            response = pact.session.get(
                f"{pact.uri}/api/v1/billing/adjustments",
                params={
                    "adjustmentTarget": "PROJECT",
                    "targetId": "test-app-001",
                    "page": "1",
                    "itemsPerPage": "50",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["header"]["isSuccessful"] is True
            assert "adjustments" in data

    def test_create_credit_grant(self, pact):
        """Test granting credit - basic create operation."""
        # Request body
        credit_request = {
            "campaignId": "CAMP-2024-01",
            "creditName": "Test Credit Grant",
            "amount": 10000,
            "creditType": "CAMPAIGN",
            "startDate": "2024-01-01",
            "endDate": "2024-12-31",
        }

        # Expected response
        expected = {
            "header": {
                "isSuccessful": Like(True),
                "resultCode": Like(0),
                "resultMessage": Like("SUCCESS"),
            },
            "creditId": Term(r"credit-[0-9a-f]+", "credit-001"),
            "campaignId": Like("CAMP-2024-01"),
            "amount": Like(10000),
            "status": Like("ACTIVE"),
        }

        # Define the interaction
        (
            pact.given("System can grant credits")
            .upon_receiving("a request to grant campaign credit")
            .with_request(
                "POST",
                "/api/v1/billing/credits",
                headers={"Content-Type": "application/json"},
                body=credit_request,
            )
            .will_respond_with(201, body=expected)
        )

        # Execute the test
        with pact:
            response = pact.session.post(f"{pact.uri}/api/v1/billing/credits", json=credit_request)
            assert response.status_code == 201
            data = response.json()
            assert data["header"]["isSuccessful"] is True
            assert data["amount"] == 10000

    def test_get_payment_status(self, pact):
        """Test retrieving payment status - basic read operation."""
        # Expected response
        expected = {
            "header": {
                "isSuccessful": Like(True),
                "resultCode": Like(0),
                "resultMessage": Like("SUCCESS"),
            },
            "statements": EachLike(
                {
                    "paymentGroupId": Term(r"pg-[0-9a-f]+", "pg-001"),
                    "paymentStatusCode": Term(
                        r"(PENDING|REGISTERED|PAID|CANCELLED|FAILED)", "REGISTERED"
                    ),
                    "amount": Like(50000.0),
                    "currency": Like("KRW"),
                    "dueDate": Format().iso_8601_datetime(),
                }
            ),
        }

        # Define the interaction
        (
            pact.given("Payment exists for the month")
            .upon_receiving("a request to get payment status")
            .with_request(
                "GET",
                "/api/v1/billing/payments/2024-01",
                headers={"uuid": "test-uuid-123"},
            )
            .will_respond_with(200, body=expected)
        )

        # Execute the test
        with pact:
            response = pact.session.get(
                f"{pact.uri}/api/v1/billing/payments/2024-01",
                headers={"uuid": "test-uuid-123"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["header"]["isSuccessful"] is True
            assert "statements" in data

    def test_delete_adjustment(self, pact):
        """Test deleting adjustment - basic delete operation."""
        # Expected response (204 No Content)
        # Pact v3 handles empty responses better

        # Define the interaction
        (
            pact.given("Adjustment adj-001 exists")
            .upon_receiving("a request to delete adjustment")
            .with_request("DELETE", "/api/v1/billing/adjustments/adj-001")
            .will_respond_with(204)
        )

        # Execute the test
        with pact:
            response = pact.session.delete(f"{pact.uri}/api/v1/billing/adjustments/adj-001")
            assert response.status_code == 204

    def test_update_contract_status(self, pact):
        """Test updating contract status - basic update operation."""
        # Request body
        update_request = {"status": "ACTIVE", "effectiveDate": "2024-01-01"}

        # Expected response
        expected = {
            "header": {
                "isSuccessful": Like(True),
                "resultCode": Like(0),
                "resultMessage": Like("SUCCESS"),
            },
            "contractId": Like("contract-001"),
            "status": Like("ACTIVE"),
            "updatedAt": Format().iso_8601_datetime(),
        }

        # Define the interaction
        (
            pact.given("Contract contract-001 exists")
            .upon_receiving("a request to update contract status")
            .with_request(
                "PATCH",
                "/api/v1/billing/contracts/contract-001",
                headers={"Content-Type": "application/json"},
                body=update_request,
            )
            .will_respond_with(200, body=expected)
        )

        # Execute the test
        with pact:
            response = pact.session.patch(
                f"{pact.uri}/api/v1/billing/contracts/contract-001", json=update_request
            )
            assert response.status_code == 200
            data = response.json()
            assert data["header"]["isSuccessful"] is True
            assert data["status"] == "ACTIVE"


@pytest.mark.contract
@pytest.mark.consumer
class TestCRUDErrorContracts:
    """Contract tests for CRUD error scenarios."""

    def test_create_with_invalid_data(self, pact):
        """Test creating with invalid data."""
        # Invalid request (missing required fields)
        invalid_request = {
            "meterList": [
                {
                    "appKey": "",  # Empty required field
                    "counterName": "",
                    "counterType": "INVALID_TYPE",
                }
            ]
        }

        expected_error = {
            "header": {
                "isSuccessful": Like(False),
                "resultCode": Like(400),
                "resultMessage": Like("Validation error"),
            },
            "errors": EachLike(
                {
                    "field": Like("appKey"),
                    "message": Like("Required field cannot be empty"),
                }
            ),
        }

        # Define the interaction
        (
            pact.given("System validates input")
            .upon_receiving("a request with invalid metering data")
            .with_request(
                "POST",
                "/api/v1/billing/meters",
                headers={"Content-Type": "application/json"},
                body=invalid_request,
            )
            .will_respond_with(400, body=expected_error)
        )

        # Execute the test
        with pact:
            response = pact.session.post(f"{pact.uri}/api/v1/billing/meters", json=invalid_request)
            assert response.status_code == 400
            data = response.json()
            assert data["header"]["isSuccessful"] is False

    def test_get_non_existent_resource(self, pact):
        """Test getting non-existent resource."""
        expected_error = {
            "header": {
                "isSuccessful": Like(False),
                "resultCode": Like(404),
                "resultMessage": Like("Resource not found"),
            }
        }

        # Define the interaction
        (
            pact.given("Adjustment does not exist")
            .upon_receiving("a request for non-existent adjustment")
            .with_request("GET", "/api/v1/billing/adjustments/non-existent")
            .will_respond_with(404, body=expected_error)
        )

        # Execute the test
        with pact:
            response = pact.session.get(f"{pact.uri}/api/v1/billing/adjustments/non-existent")
            assert response.status_code == 404
            data = response.json()
            assert data["header"]["isSuccessful"] is False
