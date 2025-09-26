"""Base class and utilities for integration tests."""

import os
from typing import Any

import pytest

from libs.Adjustment import AdjustmentManager
from libs.Batch import BatchManager
from libs.Calculation import CalculationManager
from libs.Contract import ContractManager
from libs.Credit import CreditManager
from libs.http_client import BillingAPIClient
from libs.Metering import MeteringManager
from libs.payment_api_client import PaymentAPIClient
from libs.Payments import PaymentManager


class BaseIntegrationTest:
    """Base class for integration tests with common setup."""

    @pytest.fixture(scope="class")
    def api_clients(self, use_mock) -> dict[str, Any]:
        """Create API clients based on test configuration."""
        if use_mock:
            mock_url = os.environ.get("MOCK_SERVER_URL", "http://localhost:5000")
            billing_client = BillingAPIClient(base_url=f"{mock_url}/api/v1")
            payment_client = PaymentAPIClient(base_url=f"{mock_url}/payment/api/v1")
        else:
            # Use real API with default configuration
            billing_client = BillingAPIClient()
            payment_client = PaymentAPIClient()

        return {"billing": billing_client, "payment": payment_client}

    @pytest.fixture(scope="class")
    def test_context(self, api_clients, month, member) -> dict[str, Any]:
        """Create test context with all managers."""
        uuid = f"uuid-{member}-test"
        billing_group_id = f"bg-{member}-test"

        return {
            "uuid": uuid,
            "billing_group_id": billing_group_id,
            "month": month,
            "member": member,
            "clients": api_clients,
            "managers": self._create_managers(
                api_clients, month, uuid, billing_group_id
            ),
        }

    def _create_managers(
        self, api_clients: dict[str, Any], month: str, uuid: str, billing_group_id: str
    ) -> dict[str, Any]:
        """Create all manager instances."""
        billing_client = api_clients["billing"]

        return {
            "adjustment": AdjustmentManager(month=month, client=billing_client),
            "batch": BatchManager(month=month, client=billing_client),
            "contract": ContractManager(
                month=month, billing_group_id=billing_group_id, client=billing_client
            ),
            "calculation": CalculationManager(
                month=month, uuid=uuid, client=billing_client
            ),
            "metering": MeteringManager(month=month, client=billing_client),
            "payment": PaymentManager(month=month, uuid=uuid, client=billing_client),
            "credit": CreditManager(uuid=uuid, client=billing_client),
        }

    @pytest.fixture(autouse=True)
    def cleanup_test_data(self, test_context):
        """Clean up test data before and after each test."""
        # Clean before test
        self._cleanup_data(test_context)

        yield

        # Clean after test
        self._cleanup_data(test_context)

    def _cleanup_data(self, test_context: dict[str, Any]) -> None:
        """Helper to clean test data."""
        try:
            # Cancel any pending payments
            payment_mgr = test_context["managers"]["payment"]
            pg_id, status = payment_mgr.get_payment_status()
            if pg_id and status in ["PENDING", "REGISTERED"]:
                payment_mgr.cancel_payment(pg_id)
        except Exception:
            pass  # Ignore cleanup errors

    @pytest.fixture
    def test_app_keys(self, member) -> list[str]:
        """Generate unique app keys for testing."""
        worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
        return [
            f"app-{member}-{worker_id}-001",
            f"app-{member}-{worker_id}-002",
            f"app-{member}-{worker_id}-003",
        ]

    def assert_api_success(
        self, response: dict[str, Any], expected_message: str = "SUCCESS"
    ) -> None:
        """Assert API response is successful."""
        assert response is not None, "Response is None"

        # Check different response formats
        if "header" in response:
            assert response["header"].get(
                "isSuccessful", False
            ), f"API request failed: {response['header'].get('resultMessage')}"
            assert response["header"].get("resultMessage") == expected_message
        elif "status" in response:
            assert response["status"] == expected_message
        else:
            # For simple success responses
            assert response.get(
                "success", False
            ), f"Operation failed: {response.get('message', 'Unknown error')}"
