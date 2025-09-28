"""Unit tests for error handling logic - extracted from integration tests."""

from unittest.mock import Mock

import pytest

from libs.Adjustment import AdjustmentManager
from libs.constants import AdjustmentTarget, AdjustmentType, CreditType
from libs.Credit import CreditManager
from libs.exceptions import APIRequestException, ValidationException
from libs.Payments import PaymentManager


class TestManagerErrorHandling:
    """Unit tests for Manager error handling - moved from integration tests."""

    def test_adjustment_negative_amount_error(self):
        """Test adjustment validation for negative amounts."""
        mock_client = Mock()
        manager = AdjustmentManager(month="2024-01", client=mock_client)

        # Mock the internal validation to raise exception
        with pytest.raises(ValidationException):
            # This should fail during parameter validation
            manager.apply_adjustment(
                adjustment_amount=-100,
                adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                adjustment_target=AdjustmentTarget.PROJECT,
                target_id="test-app-001",
                description="Invalid negative adjustment",
            )

        # API call should not be made
        mock_client.post.assert_not_called()

    def test_adjustment_excessive_rate_error(self):
        """Test adjustment validation for excessive rate."""
        mock_client = Mock()
        manager = AdjustmentManager(month="2024-01", client=mock_client)

        with pytest.raises(ValidationException):
            manager.apply_adjustment(
                adjustment_amount=200,  # 200% rate
                adjustment_type=AdjustmentType.RATE_DISCOUNT,
                adjustment_target=AdjustmentTarget.PROJECT,
                target_id="test-app-001",
                description="Invalid rate",
            )

    def test_credit_excessive_amount_error(self):
        """Test credit validation for excessive amounts."""
        mock_client = Mock()
        manager = CreditManager(uuid="test-uuid", client=mock_client)

        # This should fail during validation
        with pytest.raises(ValidationException, match="exceeds maximum limit"):
            manager.grant_credit(
                campaign_id="INVALID-CAMPAIGN",
                credit_name="Test",
                amount=999999999,  # Exceeds limits
                credit_type=CreditType.CAMPAIGN,
            )

        # API call should not be made
        mock_client.post.assert_not_called()

    def test_credit_negative_amount_error(self):
        """Test credit validation for negative amounts."""
        mock_client = Mock()
        manager = CreditManager(uuid="test-uuid", client=mock_client)

        with pytest.raises(ValidationException, match="must be positive"):
            manager.grant_credit(
                amount=-1000,
                credit_type=CreditType.FREE,
                credit_name="Invalid negative credit",
            )

    def test_payment_invalid_group_id_error(self):
        """Test payment validation for invalid group ID."""
        mock_client = Mock()
        # Mock API to return error
        mock_client.make_payment = Mock(side_effect=APIRequestException("Invalid payment group"))

        manager = PaymentManager(month="2024-01", uuid="test-uuid", client=mock_client)

        with pytest.raises(APIRequestException, match="Invalid payment group"):
            manager.make_payment(payment_group_id="INVALID-GROUP-ID")

    def test_payment_empty_group_id_error(self):
        """Test payment validation for empty group ID."""
        mock_client = Mock()
        manager = PaymentManager(month="2024-01", uuid="test-uuid", client=mock_client)

        with pytest.raises(ValidationException, match="Payment group ID cannot be empty"):
            manager.make_payment(payment_group_id="")

    def test_adjustment_missing_required_params(self):
        """Test adjustment validation for missing required parameters."""
        mock_client = Mock()
        manager = AdjustmentManager(month="2024-01", client=mock_client)

        # Missing adjustment_type
        with pytest.raises(ValidationException):
            manager.apply_adjustment(
                adjustment_amount=100,
                adjustment_target=AdjustmentTarget.PROJECT,
                target_id="test-app-001",
            )

    def test_credit_zero_amount_error(self):
        """Test credit validation for zero amount."""
        mock_client = Mock()
        manager = CreditManager(uuid="test-uuid", client=mock_client)

        with pytest.raises(ValidationException, match="must be positive"):
            manager.grant_credit(amount=0, credit_type=CreditType.FREE, credit_name="Zero credit")

    def test_api_error_propagation(self):
        """Test that API errors are properly propagated."""
        mock_client = Mock()
        mock_client.post.side_effect = APIRequestException("Network error")

        manager = AdjustmentManager(month="2024-01", client=mock_client)

        # Valid parameters but API fails
        with pytest.raises(APIRequestException, match="Network error"):
            manager.apply_adjustment(
                adjustment_amount=100,
                adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                adjustment_target=AdjustmentTarget.PROJECT,
                target_id="test-app-001",
                description="Valid adjustment",
            )

    def test_concurrent_operation_handling(self):
        """Test handling of concurrent operations - unit test version."""
        mock_client = Mock()
        mock_client.post.return_value = {"adjustmentId": "adj-001"}

        manager = AdjustmentManager(month="2024-01", client=mock_client)

        # Simulate rapid consecutive calls
        adjustment_ids = []
        for i in range(5):
            result = manager.apply_adjustment(
                description=f"Concurrent Test {i}",
                adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                adjustment_amount=1000 * (i + 1),
                adjustment_target=AdjustmentTarget.PROJECT,
                target_id="test-app-001",
            )
            adjustment_ids.append(result["adjustmentId"])

        # All calls should succeed
        assert len(adjustment_ids) == 5
        assert mock_client.post.call_count == 5
