"""Unit tests for Adjustment validation logic - extracted from integration tests."""

from unittest.mock import Mock

import pytest

from libs.Adjustment import AdjustmentManager
from libs.constants import AdjustmentTarget, AdjustmentType
from libs.exceptions import ValidationException


class TestAdjustmentValidation:
    """Unit tests for adjustment parameter validation."""

    @pytest.fixture
    def adjustment_manager(self):
        """Create AdjustmentManager with mocked client."""
        mock_client = Mock()
        return AdjustmentManager(month="2024-01", client=mock_client)

    def test_validate_negative_adjustment_amount(self, adjustment_manager):
        """Test validation rejects negative adjustment amounts."""
        # This logic is currently in integration tests but should be unit tested
        with pytest.raises(
            ValidationException, match="Adjustment amount cannot be negative"
        ):
            adjustment_manager._validate_adjustment_params(
                adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                adjustment_target=AdjustmentTarget.PROJECT,
                adjustment_amount=-100,
            )

    def test_validate_rate_adjustment_exceeds_100(self, adjustment_manager):
        """Test validation rejects rate adjustments over 100%."""
        with pytest.raises(
            ValidationException, match="Rate discount cannot exceed 100%"
        ):
            adjustment_manager._validate_adjustment_params(
                adjustment_type=AdjustmentType.RATE_DISCOUNT,
                adjustment_target=AdjustmentTarget.PROJECT,
                adjustment_amount=150,
            )

    def test_validate_missing_target_id(self, adjustment_manager):
        """Test validation requires target_id for non-organization adjustments."""
        with pytest.raises(ValidationException, match="target_id is required"):
            adjustment_manager._get_adjustment_endpoint_and_data(
                adjustment_target=AdjustmentTarget.PROJECT.value,
                target_id=None,
                adjustment_data={},
            )

    def test_build_adjustment_data_fixed(self, adjustment_manager):
        """Test building adjustment data for fixed amounts."""
        data = adjustment_manager._build_adjustment_data(
            adjustment_amount=1000,
            adjustment_type=AdjustmentType.FIXED_DISCOUNT,
            description="Test discount",
        )

        assert data["adjustment"] == 1000
        assert data["adjustmentTypeCode"] == AdjustmentType.FIXED_DISCOUNT
        assert data["descriptions"][0]["message"] == "Test discount"

    def test_build_adjustment_data_rate(self, adjustment_manager):
        """Test building adjustment data for rate adjustments."""
        data = adjustment_manager._build_adjustment_data(
            adjustment_amount=10,
            adjustment_type=AdjustmentType.RATE_SURCHARGE,
            description="Service fee",
        )

        assert data["adjustment"] == 10
        assert data["adjustmentTypeCode"] == AdjustmentType.RATE_SURCHARGE
        assert data["descriptions"][0]["message"] == "Service fee"

    def test_normalize_adjustment_params(self, adjustment_manager):
        """Test parameter normalization handles various input formats."""
        # Test with string types
        params = adjustment_manager._normalize_adjustment_params(
            adjustmentType="FIXED_DISCOUNT",
            adjustmentTarget="PROJECT",
            adjustment="1000",  # legacy parameter name
        )

        assert params[0] == 1000  # adjustment_amount
        assert params[1] == "FIXED_DISCOUNT"  # adjustment_type (string)
        assert params[2] == "PROJECT"  # adjustment_target (string)

    def test_get_endpoint_for_project_adjustment(self, adjustment_manager):
        """Test endpoint generation for project adjustments."""
        endpoint, data = adjustment_manager._get_adjustment_endpoint_and_data(
            adjustment_target=AdjustmentTarget.PROJECT.value,
            target_id="app-123",
            adjustment_data={"test": "data"},
        )

        assert endpoint == "billing/admin/projects/adjustments"
        assert data["projectId"] == "app-123"
        assert data["test"] == "data"

    def test_get_endpoint_for_billing_group_adjustment(self, adjustment_manager):
        """Test endpoint generation for billing group adjustments."""
        endpoint, data = adjustment_manager._get_adjustment_endpoint_and_data(
            adjustment_target=AdjustmentTarget.BILLING_GROUP.value,
            target_id="bg-123",
            adjustment_data={"test": "data"},
        )

        assert endpoint == "billing/admin/billing-groups/adjustments"
        assert data["billingGroupId"] == "bg-123"
        assert data["test"] == "data"
