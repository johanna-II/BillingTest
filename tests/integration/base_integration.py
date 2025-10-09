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
            billing_client = BillingAPIClient(base_url=mock_url, use_mock=True)
            payment_client = PaymentAPIClient(base_url=mock_url)
        else:
            # Use real API with default configuration
            from config import url

            billing_client = BillingAPIClient(base_url=url.BASE_BILLING_URL)
            payment_client = PaymentAPIClient(base_url=url.BASE_BILLING_URL)

        return {"billing": billing_client, "payment": payment_client}

    @pytest.fixture(scope="class")
    def test_context(self, api_clients, month, member, worker_id) -> dict[str, Any]:
        """Create test context with all managers.

        Each worker gets unique identifiers to avoid conflicts in parallel execution.
        """
        # Use worker_id to ensure unique IDs per worker in parallel execution
        uuid = f"uuid-{member}-{worker_id}"
        billing_group_id = f"bg-{member}-{worker_id}"

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
            # Temporarily reduce retries and timeout for cleanup to avoid blocking tests
            original_timeout = payment_mgr._client.timeout
            original_retry_config = payment_mgr._client.retry_config

            # Create minimal retry config for cleanup (max 10 seconds total)
            from libs.http_client import RetryConfig

            cleanup_retry_config = RetryConfig(
                total=2,  # Only 2 retries for cleanup
                backoff_factor=1.0,  # Linear backoff
                connect=2,
                read=2,
            )

            payment_mgr._client.timeout = 3  # 3 second timeout per request
            payment_mgr._client.retry_config = cleanup_retry_config
            # Re-setup session with new retry config
            payment_mgr._client._setup_session()

            try:
                pg_id, status = payment_mgr.get_payment_status()
                if pg_id and status in ["PENDING", "REGISTERED"]:
                    payment_mgr.cancel_payment(pg_id)
            finally:
                # Restore original configuration
                payment_mgr._client.timeout = original_timeout
                payment_mgr._client.retry_config = original_retry_config
                payment_mgr._client._setup_session()
        except Exception as e:
            # Ignore cleanup errors - data may not exist yet or API may be unavailable
            import logging

            logging.getLogger(__name__).debug(f"Cleanup ignored error: {e}")
            pass

        try:
            # Reset all mock server data for this UUID
            uuid = test_context["uuid"]
            # Use any manager's client to make the reset call
            client = test_context["managers"]["credit"]._client
            headers = {"uuid": uuid}
            client.post("test/reset", headers=headers)
        except Exception:
            pass  # Ignore reset errors in case mock server doesn't have this endpoint

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
            # If expected_message is provided and not default "SUCCESS", check it
            if expected_message != "SUCCESS":
                result_msg = response["header"].get("resultMessage", "")
                # Allow partial match or exact match
                assert (
                    expected_message in result_msg or result_msg == "SUCCESS"
                ), f"Expected '{expected_message}' but got '{result_msg}'"
        elif "status" in response:
            assert response["status"] == expected_message
        else:
            # For simple success responses
            assert response.get(
                "success", False
            ), f"Operation failed: {response.get('message', 'Unknown error')}"
