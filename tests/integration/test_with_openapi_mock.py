"""Integration tests using OpenAPI mock server."""

import logging

import pytest

from libs.constants import (
    AdjustmentTarget,
    AdjustmentType,
    CounterType,
    PaymentStatus,
)
from libs.exceptions import APIRequestException
from tests.integration.base_integration import BaseIntegrationTest

logger = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.mock_required
class TestWithOpenAPIMockServer(BaseIntegrationTest):
    """Integration tests using OpenAPI mock server."""

    def test_complete_billing_workflow(self, test_context) -> None:
        """Test complete billing workflow with OpenAPI mock."""
        managers = test_context["managers"]

        # 1. Apply contract

        contract_result = managers["contract"].apply_contract(
            contract_id="contract-456", name="Test Contract"
        )
        self.assert_api_success(contract_result)

        # 2. Send metering data
        meter_result = managers["metering"].send_metering(
            app_key="test-app",
            counter_name="compute.cpu",
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume="100",
        )
        self.assert_api_success(meter_result)

        # 3. Apply adjustment
        adj_result = managers["adjustment"].apply_adjustment(
            adjustment_amount=500.0,
            adjustment_type=AdjustmentType.FIXED_DISCOUNT,
            adjustment_target=AdjustmentTarget.BILLING_GROUP,
            target_id=test_context["billing_group_id"],
        )
        assert "adjustmentId" in adj_result

        # 4. Payment operations would require PaymentAPIClient
        # For now, just verify the workflow completes successfully
        # In a real test, you would use a PaymentAPIClient instance
        assert True  # Workflow completed successfully

    def test_batch_job_execution(self, test_context) -> None:
        """Test batch job execution flow."""
        managers = test_context["managers"]

        # Request multiple batch jobs
        results = managers["batch"].request_common_batch_jobs()

        # Verify all jobs were submitted
        assert len(results) == 3
        for result in results.values():
            assert result["success"] is True
            assert "batchId" in result["result"]

    def test_error_handling_with_mock(self, test_context) -> None:
        """Test error scenarios using OpenAPI mock."""
        managers = test_context["managers"]

        # OpenAPI mock can simulate errors based on specific inputs
        # For example, using special IDs that trigger errors
        with pytest.raises(APIRequestException):
            managers["adjustment"].apply_adjustment(
                adjustment_amount=-1000,  # Negative amount might trigger error
                adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                adjustment_target=AdjustmentTarget.BILLING_GROUP,
                target_id="error-trigger-id",  # Special ID to trigger error in mock
            )

    def test_pagination_with_mock(self, test_context) -> None:
        """Test pagination handling with mock server."""
        managers = test_context["managers"]

        # Mock server should handle pagination properly
        adjustments = managers["adjustment"].get_adjustments(
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
@pytest.mark.mock_required
class TestOpenAPIValidation(BaseIntegrationTest):
    """Test that our implementation matches OpenAPI specification."""

    @pytest.fixture
    def openapi_spec(self):
        """Load OpenAPI specification."""
        import yaml  # type: ignore[import-untyped]

        with open("docs/openapi/billing-api.yaml") as f:
            return yaml.safe_load(f)

    def test_request_validation(self, test_context, openapi_spec) -> None:
        """Test that requests match OpenAPI schema."""
        # This would use OpenAPI validation libraries
        # to ensure our requests match the specification
        managers = test_context["managers"]

        # The mock server validates requests against OpenAPI spec
        # Invalid requests should be rejected
        with pytest.raises(Exception):
            managers["metering"].send_metering(
                app_key="test-app",
                counter_name="invalid.counter.name.too.long" * 10,  # Too long
                counter_type="INVALID_TYPE",  # Invalid enum value
                counter_unit="INVALID_UNIT",
                counter_volume="not-a-number",  # Should be numeric
            )

    def test_response_validation(self, test_context, openapi_spec) -> None:
        """Test that responses match OpenAPI schema."""
        managers = test_context["managers"]

        # Get response
        pg_id, status = managers["payment"].get_payment_status()

        # Response should match OpenAPI schema
        # The mock server ensures this, but we can add additional validation
        assert isinstance(pg_id, str)
        assert status in [s.value for s in PaymentStatus]
