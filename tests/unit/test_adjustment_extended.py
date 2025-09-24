"""Extended unit tests for Adjustment module to improve coverage."""

from unittest.mock import Mock, patch

import pytest

from libs.Adjustment import AdjustmentManager
from libs.constants import AdjustmentTarget, AdjustmentType
from libs.exceptions import APIRequestException, ValidationException


class TestAdjustmentExtended:
    """Extended tests to improve Adjustment module coverage."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        with patch("libs.Adjustment.BillingAPIClient") as mock_client_class:
            self.mock_client = Mock()
            mock_client_class.return_value = self.mock_client
            self.adjustment_manager = AdjustmentManager(month="2024-01")
            yield

    def test_repr(self):
        """Test __repr__ method."""
        repr_str = repr(self.adjustment_manager)
        assert repr_str == "AdjustmentManager(month=2024-01)"

    def test_apply_adjustment_legacy_params_project(self):
        """Test apply_adjustment with legacy parameters for project."""
        mock_response = {"adjustmentId": "adj-001", "status": "SUCCESS"}
        self.mock_client.post.return_value = mock_response

        # Test with legacy parameter names and no target_id
        result = self.adjustment_manager.apply_adjustment(
            adjustment=1000.0,
            adjustmentType="FIXED_DISCOUNT",
            adjustmentTarget="Project",
            projectId="proj-123",
        )

        assert result == mock_response
        # Verify correct endpoint and data
        expected_data = {
            "adjustment": 1000.0,
            "adjustmentTypeCode": "FIXED_DISCOUNT",
            "descriptions": [
                {"locale": "ko_KR", "message": "QA billing automation test"}
            ],
            "monthFrom": "2024-01",
            "monthTo": "2024-01",
            "adjustmentId": None,
            "billingGroupId": None,
            "projectId": "proj-123",
        }
        self.mock_client.post.assert_called_once_with(
            "billing/admin/projects/adjustments", json_data=expected_data
        )

    def test_apply_adjustment_legacy_params_billing_group(self):
        """Test apply_adjustment with legacy parameters for billing group."""
        mock_response = {"adjustmentId": "adj-002", "status": "SUCCESS"}
        self.mock_client.post.return_value = mock_response

        # Test with legacy parameter names and no target_id
        result = self.adjustment_manager.apply_adjustment(
            adjustment=500.0,
            adjustmentType="RATE_DISCOUNT",
            adjustmentTarget="BillingGroup",
            billingGroupId="bg-456",
        )

        assert result == mock_response
        # Verify correct endpoint and data
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

    def test_apply_adjustment_api_exception(self):
        """Test apply_adjustment when API request fails."""
        self.mock_client.post.side_effect = APIRequestException("API error")

        with pytest.raises(APIRequestException) as exc_info:
            self.adjustment_manager.apply_adjustment(
                adjustment_amount=1000.0,
                adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                adjustment_target=AdjustmentTarget.BILLING_GROUP,
                target_id="bg-123",
            )

        assert "API error" in str(exc_info.value)

    def test_get_adjustments_api_exception(self):
        """Test get_adjustments when API request fails."""
        self.mock_client.get.side_effect = APIRequestException("Failed to retrieve")

        with pytest.raises(APIRequestException) as exc_info:
            self.adjustment_manager.get_adjustments(
                adjustment_target=AdjustmentTarget.PROJECT, target_id="proj-123"
            )

        assert "Failed to retrieve" in str(exc_info.value)

    def test_delete_adjustment_dict_format_with_string_ids(self):
        """Test delete_adjustment with dict format containing string IDs."""
        adjustment_data = {"adjustments": ["adj-001", "adj-002", "adj-003"]}

        self.adjustment_manager.delete_adjustment(
            adjustment_ids=adjustment_data,
            adjustment_target=AdjustmentTarget.BILLING_GROUP,
        )

        assert self.mock_client.delete.call_count == 3

    def test_delete_adjustment_dict_format_with_objects(self):
        """Test delete_adjustment with dict format containing adjustment objects."""
        adjustment_data = {
            "adjustments": [
                {"adjustmentId": "adj-001", "billingGroupId": "bg-123"},
                {"adjustmentId": "adj-002", "billingGroupId": "bg-123"},
                {"adjustmentId": "adj-003", "projectId": "proj-456"},
            ]
        }

        # Test with inferred target from first object
        self.adjustment_manager.delete_adjustment(adjustment_ids=adjustment_data)

        # Should use billing group endpoint for all since target was inferred from first
        assert self.mock_client.delete.call_count == 3
        for i in range(3):
            self.mock_client.delete.assert_any_call(
                "billing/admin/billing-groups/adjustments",
                params={"adjustmentIds": f"adj-00{i+1}"},
            )

    def test_delete_adjustment_empty_dict(self):
        """Test delete_adjustment with empty dict."""
        adjustment_data = {"adjustments": []}

        # Should return early without calling delete
        self.adjustment_manager.delete_adjustment(
            adjustment_ids=adjustment_data, adjustment_target=AdjustmentTarget.PROJECT
        )

        self.mock_client.delete.assert_not_called()

    def test_delete_adjustment_empty_list(self):
        """Test delete_adjustment with empty list."""
        self.adjustment_manager.delete_adjustment(
            adjustment_ids=[], adjustment_target=AdjustmentTarget.BILLING_GROUP
        )

        self.mock_client.delete.assert_not_called()

    def test_delete_adjustment_no_target_validation_error(self):
        """Test delete_adjustment without target raises ValidationException."""
        with pytest.raises(ValidationException) as exc_info:
            self.adjustment_manager.delete_adjustment(adjustment_ids=["adj-001"])

        assert "adjustment_target is required" in str(exc_info.value)

    def test_delete_adjustment_api_exception(self):
        """Test delete_adjustment when API request fails."""
        self.mock_client.delete.side_effect = APIRequestException("Delete failed")

        with pytest.raises(APIRequestException) as exc_info:
            self.adjustment_manager.delete_adjustment(
                adjustment_ids="adj-001", adjustment_target=AdjustmentTarget.PROJECT
            )

        assert "Delete failed" in str(exc_info.value)

    def test_inquiry_adjustment_project(self):
        """Test legacy inquiry_adjustment method for project."""
        mock_response = {
            "adjustments": [{"adjustmentId": "adj-001"}, {"adjustmentId": "adj-002"}]
        }
        self.mock_client.get.return_value = mock_response

        result = self.adjustment_manager.inquiry_adjustment(projectId="proj-123")

        assert result == {"adjustments": ["adj-001", "adj-002"]}
        self.mock_client.get.assert_called_once_with(
            "billing/admin/projects/adjustments",
            params={"page": 1, "itemsPerPage": 50, "projectId": "proj-123"},
        )

    def test_inquiry_adjustment_billing_group(self):
        """Test legacy inquiry_adjustment method for billing group."""
        mock_response = {
            "adjustments": [{"adjustmentId": "adj-003"}, {"adjustmentId": "adj-004"}]
        }
        self.mock_client.get.return_value = mock_response

        result = self.adjustment_manager.inquiry_adjustment(billingGroupId="bg-456")

        assert result == {"adjustments": ["adj-003", "adj-004"]}
        self.mock_client.get.assert_called_once_with(
            "billing/admin/billing-groups/adjustments",
            params={"page": 1, "itemsPerPage": 50, "billingGroupId": "bg-456"},
        )

    def test_inquiry_adjustment_no_target(self):
        """Test legacy inquiry_adjustment method with no target."""
        result = self.adjustment_manager.inquiry_adjustment()

        assert result == {"adjustments": []}
        self.mock_client.get.assert_not_called()

    def test_apply_adjustment_with_alternative_legacy_params(self):
        """Test apply_adjustment with alternative legacy parameter names."""
        mock_response = {"adjustmentId": "adj-005", "status": "SUCCESS"}
        self.mock_client.post.return_value = mock_response

        # Test with project_id and billing_group_id instead of projectId/billingGroupId
        result = self.adjustment_manager.apply_adjustment(
            adjustment=2000.0,
            adjustmentType="FIXED_SURCHARGE",
            adjustmentTarget="Project",
            project_id="proj-789",
        )

        assert result == mock_response
        # Verify projectId was correctly set
        call_args = self.mock_client.post.call_args
        assert call_args[1]["json_data"]["projectId"] == "proj-789"

    def test_apply_adjustment_billing_group_alternative_params(self):
        """Test apply_adjustment with billing_group_id parameter."""
        mock_response = {"adjustmentId": "adj-006", "status": "SUCCESS"}
        self.mock_client.post.return_value = mock_response

        result = self.adjustment_manager.apply_adjustment(
            adjustment=1500.0,
            adjustmentType="RATE_SURCHARGE",
            adjustmentTarget="BillingGroup",
            billing_group_id="bg-789",
        )

        assert result == mock_response
        # Verify billingGroupId was correctly set
        call_args = self.mock_client.post.call_args
        assert call_args[1]["json_data"]["billingGroupId"] == "bg-789"
