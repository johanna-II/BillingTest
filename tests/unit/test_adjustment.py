"""Comprehensive unit tests for AdjustmentManager.

This combines all adjustment-related unit tests into a single file.
"""

from unittest.mock import Mock

import pytest

from libs.Adjustment import AdjustmentManager
from libs.constants import AdjustmentTarget, AdjustmentType
from libs.exceptions import APIRequestException, ValidationException


class TestAdjustmentManager:
    """Test suite for AdjustmentManager."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.adjustment_manager = AdjustmentManager(
            month="2024-01", client=self.mock_client
        )

    def test_initialization(self) -> None:
        """Test AdjustmentManager initialization."""
        manager = AdjustmentManager(month="2024-01")
        assert manager.month == "2024-01"
        assert manager._client is not None

    def test_repr(self) -> None:
        """Test string representation."""
        assert repr(self.adjustment_manager) == "AdjustmentManager(month=2024-01)"

    # Modern parameter tests
    def test_apply_adjustment_modern_params_project(self) -> None:
        """Test apply_adjustment with modern parameters for project."""
        mock_response = {"adjustmentId": "adj-001", "status": "SUCCESS"}
        self.mock_client.post.return_value = mock_response

        result = self.adjustment_manager.apply_adjustment(
            adjustment_amount=1000.0,
            adjustment_type=AdjustmentType.FIXED_DISCOUNT,
            target_type=AdjustmentTarget.PROJECT,
            target_id="proj-123",
            description="Test discount",
        )

        assert result == mock_response
        expected_data = {
            "adjustment": 1000.0,
            "adjustmentTypeCode": "FIXED_DISCOUNT",
            "descriptions": [{"locale": "ko_KR", "message": "Test discount"}],
            "monthFrom": "2024-01",
            "monthTo": "2024-01",
            "adjustmentId": None,
            "billingGroupId": None,
            "projectId": "proj-123",
        }
        self.mock_client.post.assert_called_once_with(
            "billing/admin/projects/adjustments", json_data=expected_data
        )

    # Legacy parameter tests
    def test_apply_adjustment_legacy_params_billing_group(self) -> None:
        """Test apply_adjustment with legacy parameters for billing group."""
        mock_response = {"adjustmentId": "adj-002", "status": "SUCCESS"}
        self.mock_client.post.return_value = mock_response

        result = self.adjustment_manager.apply_adjustment(
            adjustment=500.0,
            adjustmentType="RATE_DISCOUNT",
            adjustmentTarget="BillingGroup",
            billingGroupId="bg-456",
        )

        assert result == mock_response
        expected_data = {
            "adjustment": 500.0,
            "adjustmentTypeCode": "RATE_DISCOUNT",
            "descriptions": [
                {"locale": "ko_KR", "message": "QA billing automation test"}
            ],
            "monthFrom": "2024-01",
            "monthTo": "2024-01",
            "adjustmentId": None,
            "billingGroupId": "bg-456",
            "projectId": None,
        }
        self.mock_client.post.assert_called_once_with(
            "billing/admin/billing-groups/adjustments", json_data=expected_data
        )

    # Mixed parameter tests
    def test_apply_adjustment_mixed_params(self) -> None:
        """Test apply_adjustment with mix of modern and legacy parameters."""
        mock_response = {"adjustmentId": "adj-003", "status": "SUCCESS"}
        self.mock_client.post.return_value = mock_response

        result = self.adjustment_manager.apply_adjustment(
            adjustment_amount=2000.0,
            adjustmentType="FIXED_SURCHARGE",  # Legacy type
            target_type=AdjustmentTarget.BILLING_GROUP,  # Modern target
            billingGroupId="bg-789",  # Legacy ID
        )

        assert result == mock_response

    # Validation tests
    def test_apply_adjustment_invalid_amount(self) -> None:
        """Test apply_adjustment with invalid amount."""
        with pytest.raises(ValidationException, match="Invalid adjustment amount"):
            self.adjustment_manager.apply_adjustment(
                adjustment_amount=-100,
                adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                target_type=AdjustmentTarget.PROJECT,
                target_id="proj-123",
            )

    def test_apply_adjustment_invalid_target(self) -> None:
        """Test apply_adjustment with invalid target."""
        with pytest.raises(ValidationException, match="Invalid adjustment target"):
            self.adjustment_manager.apply_adjustment(
                adjustment_amount=1000,
                adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                target_type=AdjustmentTarget.PROJECT,
                # Missing target_id
            )

    def test_apply_adjustment_api_exception(self) -> None:
        """Test apply_adjustment when API request fails."""
        self.mock_client.post.side_effect = APIRequestException("API error")

        with pytest.raises(APIRequestException) as exc_info:
            self.adjustment_manager.apply_adjustment(
                adjustment_amount=1000.0,
                adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                target_type=AdjustmentTarget.PROJECT,
                target_id="proj-123",
            )
        assert "API error" in str(exc_info.value)

    # Get adjustments tests
    def test_get_adjustments_project(self) -> None:
        """Test get_adjustments for project."""
        mock_response = {
            "adjustments": [
                {"adjustmentId": "adj-001", "amount": 1000},
                {"adjustmentId": "adj-002", "amount": 2000},
            ]
        }
        self.mock_client.get.return_value = mock_response

        result = self.adjustment_manager.get_adjustments(
            target_type=AdjustmentTarget.PROJECT, target_id="proj-123"
        )

        assert result == mock_response
        self.mock_client.get.assert_called_once_with(
            "billing/admin/projects/adjustments",
            params={"projectId": "proj-123", "month": "2024-01"},
        )

    def test_get_adjustments_billing_group(self) -> None:
        """Test get_adjustments for billing group."""
        mock_response = {"adjustments": []}
        self.mock_client.get.return_value = mock_response

        result = self.adjustment_manager.get_adjustments(
            target_type=AdjustmentTarget.BILLING_GROUP, target_id="bg-456"
        )

        assert result == mock_response
        self.mock_client.get.assert_called_once_with(
            "billing/admin/billing-groups/adjustments",
            params={"billingGroupId": "bg-456", "month": "2024-01"},
        )

    def test_get_adjustments_api_exception(self) -> None:
        """Test get_adjustments when API request fails."""
        self.mock_client.get.side_effect = APIRequestException("API error")

        with pytest.raises(APIRequestException):
            self.adjustment_manager.get_adjustments(
                target_type=AdjustmentTarget.PROJECT, target_id="proj-123"
            )

    # Delete adjustments tests
    def test_delete_adjustments_success(self) -> None:
        """Test successful delete_adjustments."""
        mock_response = {"deletedCount": 5}
        self.mock_client.delete.return_value = mock_response

        result = self.adjustment_manager.delete_adjustments()

        assert result == mock_response
        self.mock_client.delete.assert_called_once_with(
            "billing/admin/adjustments", params={"month": "2024-01"}
        )

    def test_delete_adjustments_api_exception(self) -> None:
        """Test delete_adjustments when API request fails."""
        self.mock_client.delete.side_effect = APIRequestException("API error")

        with pytest.raises(APIRequestException):
            self.adjustment_manager.delete_adjustments()

    # Edge cases
    def test_apply_adjustment_percentage_bounds(self) -> None:
        """Test percentage adjustment bounds."""
        # Test valid percentage
        self.mock_client.post.return_value = {"status": "SUCCESS"}

        self.adjustment_manager.apply_adjustment(
            adjustment_amount=100,  # 100%
            adjustment_type=AdjustmentType.RATE_DISCOUNT,
            target_type=AdjustmentTarget.PROJECT,
            target_id="proj-123",
        )

        # Test invalid percentage
        with pytest.raises(
            ValidationException, match="Rate adjustment cannot exceed 100%"
        ):
            self.adjustment_manager.apply_adjustment(
                adjustment_amount=101,  # 101%
                adjustment_type=AdjustmentType.RATE_DISCOUNT,
                target_type=AdjustmentTarget.PROJECT,
                target_id="proj-123",
            )

    def test_apply_adjustment_with_special_characters(self) -> None:
        """Test apply_adjustment with special characters in description."""
        mock_response = {"status": "SUCCESS"}
        self.mock_client.post.return_value = mock_response

        result = self.adjustment_manager.apply_adjustment(
            adjustment_amount=1000,
            adjustment_type=AdjustmentType.FIXED_DISCOUNT,
            target_type=AdjustmentTarget.PROJECT,
            target_id="proj-123",
            description="Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?",
        )

        assert result == mock_response

    def test_apply_adjustment_with_unicode(self) -> None:
        """Test apply_adjustment with unicode characters."""
        mock_response = {"status": "SUCCESS"}
        self.mock_client.post.return_value = mock_response

        result = self.adjustment_manager.apply_adjustment(
            adjustment_amount=1000,
            adjustment_type=AdjustmentType.FIXED_DISCOUNT,
            target_type=AdjustmentTarget.PROJECT,
            target_id="proj-123",
            description="한글 설명 テスト 测试",
        )

        assert result == mock_response

    def test_concurrent_adjustments(self) -> None:
        """Test applying multiple adjustments concurrently."""
        # This would need threading/asyncio in real implementation


class TestAdjustmentManagerIntegration:
    """Integration-style unit tests with more complex scenarios."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.adjustment_manager = AdjustmentManager(
            month="2024-01", client=self.mock_client
        )

    def test_multiple_adjustments_workflow(self) -> None:
        """Test workflow with multiple adjustments."""
        # Apply first adjustment
        self.mock_client.post.return_value = {"adjustmentId": "adj-001"}
        self.adjustment_manager.apply_adjustment(
            adjustment_amount=1000,
            adjustment_type=AdjustmentType.FIXED_DISCOUNT,
            target_type=AdjustmentTarget.PROJECT,
            target_id="proj-123",
        )

        # Apply second adjustment
        self.mock_client.post.return_value = {"adjustmentId": "adj-002"}
        self.adjustment_manager.apply_adjustment(
            adjustment_amount=5,
            adjustment_type=AdjustmentType.RATE_SURCHARGE,
            target_type=AdjustmentTarget.PROJECT,
            target_id="proj-123",
        )

        # Get all adjustments
        self.mock_client.get.return_value = {
            "adjustments": [
                {"adjustmentId": "adj-001", "amount": 1000},
                {"adjustmentId": "adj-002", "amount": 5},
            ]
        }
        adjustments = self.adjustment_manager.get_adjustments(
            AdjustmentTarget.PROJECT, "proj-123"
        )

        assert len(adjustments["adjustments"]) == 2

    def test_adjustment_error_recovery(self) -> None:
        """Test error recovery in adjustment workflow."""
        # First attempt fails
        self.mock_client.post.side_effect = [
            APIRequestException("Network error"),
            {"adjustmentId": "adj-001"},  # Success on retry
        ]

        # Should fail first time
        with pytest.raises(APIRequestException):
            self.adjustment_manager.apply_adjustment(
                adjustment_amount=1000,
                adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                target_type=AdjustmentTarget.PROJECT,
                target_id="proj-123",
            )

        # Should succeed on retry
        result = self.adjustment_manager.apply_adjustment(
            adjustment_amount=1000,
            adjustment_type=AdjustmentType.FIXED_DISCOUNT,
            target_type=AdjustmentTarget.PROJECT,
            target_id="proj-123",
        )
        assert result["adjustmentId"] == "adj-001"
