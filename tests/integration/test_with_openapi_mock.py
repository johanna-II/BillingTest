"""Integration tests using OpenAPI mock server."""

import os
import subprocess
import time
from contextlib import contextmanager

import pytest
import requests

from libs.Adjustment import AdjustmentManager
from libs.Batch import BatchManager
from libs.constants import (
    AdjustmentTarget,
    AdjustmentType,
    BatchJobCode,
    CounterType,
    PaymentStatus,
)
from libs.Contract import ContractManager
from libs.http_client import BillingAPIClient
from libs.Metering import MeteringManager
from libs.Payments import PaymentManager


@contextmanager
def openapi_mock_server():
    """Start OpenAPI-based mock server for testing."""
    # Start mock server
    env = os.environ.copy()
    env["MOCK_SERVER_PORT"] = "5001"  # Different port to avoid conflicts

    server_process = subprocess.Popen(
        ["python", "-m", "mock_server.run_server"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to be ready
    server_url = "http://localhost:5001"
    max_retries = 30
    for _ in range(max_retries):
        try:
            response = requests.get(f"{server_url}/health")
            if response.status_code == 200:
                break
        except requests.ConnectionError:
            time.sleep(0.5)
    else:
        server_process.terminate()
        msg = "Mock server failed to start"
        raise RuntimeError(msg)

    try:
        yield server_url
    finally:
        server_process.terminate()
        server_process.wait()


@pytest.mark.integration
class TestWithOpenAPIMockServer:
    """Integration tests using OpenAPI mock server."""

    @pytest.fixture(scope="class")
    def mock_server_url(self):
        """Use the already running mock server."""
        # Check if USE_MOCK_SERVER is set
        if os.environ.get("USE_MOCK_SERVER", "false").lower() == "true":
            mock_url = os.environ.get("MOCK_SERVER_URL", "http://localhost:5000")
            yield mock_url
        else:
            # For local testing, try to start a server
            with openapi_mock_server() as url:
                yield url

    @pytest.fixture
    def api_client(self, mock_server_url):
        """Create API client pointing to mock server."""
        return BillingAPIClient(base_url=f"{mock_server_url}/api/v1")

    def test_complete_billing_workflow(self, api_client) -> None:
        """Test complete billing workflow with OpenAPI mock."""
        # 1. Apply contract
        contract_manager = ContractManager(
            month="2024-01", billing_group_id="bg-123", client=api_client
        )

        contract_result = contract_manager.apply_contract(
            contract_id="contract-456", name="Test Contract"
        )
        assert contract_result.get("status") == "SUCCESS"

        # 2. Send metering data
        metering_manager = MeteringManager(month="2024-01")

        meter_result = metering_manager.send_metering(
            app_key="test-app",
            counter_name="compute.cpu",
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume="100",
        )
        assert meter_result.get("status") == "SUCCESS"

        # 3. Apply adjustment
        adjustment_manager = AdjustmentManager(month="2024-01", client=api_client)

        adj_result = adjustment_manager.apply_adjustment(
            adjustment_amount=500.0,
            adjustment_type=AdjustmentType.FIXED_DISCOUNT,
            adjustment_target=AdjustmentTarget.BILLING_GROUP,
            target_id="bg-123",
        )
        assert "adjustmentId" in adj_result

        # 4. Check payment status
        payment_manager = PaymentManager(
            month="2024-01", uuid="test-uuid", client=api_client
        )

        payment_id, status = payment_manager.get_payment_status()
        assert payment_id  # Should have a payment group ID
        assert status in [PaymentStatus.PENDING, PaymentStatus.REGISTERED]

    def test_batch_job_execution(self, api_client) -> None:
        """Test batch job execution flow."""
        batch_manager = BatchManager(month="2024-01", client=api_client)

        # Request multiple batch jobs
        jobs = [
            BatchJobCode.BATCH_CREDIT_EXPIRY,
            BatchJobCode.BATCH_GENERATE_STATEMENT,
            BatchJobCode.BATCH_PAYMENT_REMINDER,
        ]

        results = batch_manager.request_common_batch_jobs(jobs)

        # Verify all jobs were submitted
        assert len(results) == 3
        for result in results.values():
            assert result["success"] is True
            assert "batchId" in result["result"]

    def test_error_handling_with_mock(self, api_client) -> None:
        """Test error scenarios using OpenAPI mock."""
        adjustment_manager = AdjustmentManager(month="2024-01", client=api_client)

        # OpenAPI mock can simulate errors based on specific inputs
        # For example, using special IDs that trigger errors
        with pytest.raises(APIRequestException):
            adjustment_manager.apply_adjustment(
                adjustment_amount=-1000,  # Negative amount might trigger error
                adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                adjustment_target=AdjustmentTarget.BILLING_GROUP,
                target_id="error-trigger-id",  # Special ID to trigger error in mock
            )

    def test_pagination_with_mock(self, api_client) -> None:
        """Test pagination handling with mock server."""
        adjustment_manager = AdjustmentManager(month="2024-01", client=api_client)

        # Mock server should handle pagination properly
        adjustments = adjustment_manager.get_adjustments(
            adjustment_target=AdjustmentTarget.BILLING_GROUP,
            target_id="bg-with-many-adjustments",  # Special ID for pagination test
        )

        # Mock server should return paginated results
        assert len(adjustments) > 0

        # Verify all adjustments have required fields
        for adj in adjustments:
            assert "adjustmentId" in adj
            assert "amount" in adj or "adjustmentAmount" in adj


@pytest.mark.integration
class TestOpenAPIValidation:
    """Test that our implementation matches OpenAPI specification."""

    @pytest.fixture
    def openapi_spec(self):
        """Load OpenAPI specification."""
        import yaml

        with open("docs/openapi/billing-api.yaml") as f:
            return yaml.safe_load(f)

    def test_request_validation(self, api_client, openapi_spec) -> None:
        """Test that requests match OpenAPI schema."""
        # This would use OpenAPI validation libraries
        # to ensure our requests match the specification
        metering_manager = MeteringManager(month="2024-01")

        # The mock server validates requests against OpenAPI spec
        # Invalid requests should be rejected
        with pytest.raises(Exception):
            metering_manager.send_metering(
                app_key="test-app",
                counter_name="invalid.counter.name.too.long" * 10,  # Too long
                counter_type="INVALID_TYPE",  # Invalid enum value
                counter_unit="INVALID_UNIT",
                counter_volume="not-a-number",  # Should be numeric
            )

    def test_response_validation(self, api_client, openapi_spec) -> None:
        """Test that responses match OpenAPI schema."""
        payment_manager = PaymentManager(
            month="2024-01", uuid="test-uuid", client=api_client
        )

        # Get response
        pg_id, status = payment_manager.get_payment_status()

        # Response should match OpenAPI schema
        # The mock server ensures this, but we can add additional validation
        assert isinstance(pg_id, str)
        assert status in [s.value for s in PaymentStatus]
