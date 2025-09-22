"""Unit tests for billing adjustment module."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from libs.adjustment import AdjustmentManager, Adjustments
from libs.constants import AdjustmentType, AdjustmentTarget
from libs.exceptions import ValidationException, APIRequestException


class TestAdjustmentManagerUnit:
    """Unit tests for AdjustmentManager class"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        with patch('libs.adjustment.BillingAPIClient') as mock_client_class:
            self.mock_client = Mock()
            mock_client_class.return_value = self.mock_client
            self.adjustment_manager = AdjustmentManager(month="2024-01")
            yield
    
    def test_init(self):
        """Test AdjustmentManager initialization"""
        assert self.adjustment_manager.month == "2024-01"
        assert hasattr(self.adjustment_manager, '_client')
    
    def test_apply_adjustment_billing_group_success(self):
        """Test successful adjustment application to billing group"""
        mock_response = {
            "adjustmentId": "adj-001",
            "status": "SUCCESS"
        }
        self.mock_client.post.return_value = mock_response
        
        result = self.adjustment_manager.apply_adjustment(
            adjustment_amount=1000.0,
            adjustment_type=AdjustmentType.FIXED_DISCOUNT,
            adjustment_target=AdjustmentTarget.BILLING_GROUP,
            target_id="bg-123",
            description="Test discount"
        )
        
        assert result == mock_response
        
        expected_data = {
            "adjustment": 1000.0,
            "adjustmentTypeCode": "FIXED_DISCOUNT",
            "descriptions": [{"locale": "ko_KR", "message": "Test discount"}],
            "monthFrom": "2024-01",
            "monthTo": "2024-01",
            "adjustmentId": None,
            "billingGroupId": "bg-123",
            "projectId": None
        }
        
        self.mock_client.post.assert_called_once_with(
            "billing/admin/billing-groups/adjustments",
            json_data=expected_data
        )
    
    def test_apply_adjustment_project_success(self):
        """Test successful adjustment application to project"""
        mock_response = {
            "adjustmentId": "adj-002",
            "status": "SUCCESS"
        }
        self.mock_client.post.return_value = mock_response
        
        result = self.adjustment_manager.apply_adjustment(
            adjustment_amount=15.5,
            adjustment_type=AdjustmentType.RATE_DISCOUNT,
            adjustment_target=AdjustmentTarget.PROJECT,
            target_id="proj-456",
            description="Project discount"
        )
        
        assert result == mock_response
        
        expected_data = {
            "adjustment": 15.5,
            "adjustmentTypeCode": "RATE_DISCOUNT",
            "descriptions": [{"locale": "ko_KR", "message": "Project discount"}],
            "monthFrom": "2024-01",
            "monthTo": "2024-01",
            "adjustmentId": None,
            "billingGroupId": None,
            "projectId": "proj-456"
        }
        
        self.mock_client.post.assert_called_once_with(
            "billing/admin/projects/adjustments",
            json_data=expected_data
        )
    
    def test_apply_adjustment_invalid_target(self):
        """Test adjustment with invalid target type"""
        with pytest.raises(ValidationException) as exc_info:
            self.adjustment_manager.apply_adjustment(
                adjustment_amount=1000,
                adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                adjustment_target="INVALID_TARGET",
                target_id="test-123"
            )
        
        assert "Invalid adjustment target" in str(exc_info.value)
    
    def test_apply_adjustment_api_error(self):
        """Test adjustment application with API error"""
        self.mock_client.post.side_effect = APIRequestException("API Error")
        
        with pytest.raises(APIRequestException):
            self.adjustment_manager.apply_adjustment(
                adjustment_amount=1000,
                adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                adjustment_target=AdjustmentTarget.BILLING_GROUP,
                target_id="bg-123"
            )
    
    def test_get_adjustments_billing_group(self):
        """Test retrieving adjustments for billing group"""
        mock_response = {
            "adjustments": [
                {"adjustmentId": "adj-001"},
                {"adjustmentId": "adj-002"},
                {"adjustmentId": "adj-003"}
            ]
        }
        self.mock_client.get.return_value = mock_response
        
        result = self.adjustment_manager.get_adjustments(
            adjustment_target=AdjustmentTarget.BILLING_GROUP,
            target_id="bg-123"
        )
        
        assert result == ["adj-001", "adj-002", "adj-003"]
        self.mock_client.get.assert_called_once_with(
            "billing/admin/billing-groups/adjustments",
            params={"page": 1, "itemsPerPage": 50, "billingGroupId": "bg-123"}
        )
    
    def test_get_adjustments_project(self):
        """Test retrieving adjustments for project"""
        mock_response = {
            "adjustments": [
                {"adjustmentId": "adj-004"},
                {"adjustmentId": "adj-005"}
            ]
        }
        self.mock_client.get.return_value = mock_response
        
        result = self.adjustment_manager.get_adjustments(
            adjustment_target=AdjustmentTarget.PROJECT,
            target_id="proj-456"
        )
        
        assert result == ["adj-004", "adj-005"]
        self.mock_client.get.assert_called_once_with(
            "billing/admin/projects/adjustments",
            params={"page": 1, "itemsPerPage": 50, "projectId": "proj-456"}
        )
    
    def test_get_adjustments_empty(self):
        """Test retrieving adjustments when none exist"""
        self.mock_client.get.return_value = {"adjustments": []}
        
        result = self.adjustment_manager.get_adjustments(
            adjustment_target=AdjustmentTarget.BILLING_GROUP,
            target_id="bg-123"
        )
        
        assert result == []
    
    def test_get_adjustments_with_pagination(self):
        """Test retrieving adjustments with pagination"""
        mock_response = {
            "adjustments": [
                {"adjustmentId": f"adj-{i:03d}"} for i in range(10)
            ]
        }
        self.mock_client.get.return_value = mock_response
        
        result = self.adjustment_manager.get_adjustments(
            adjustment_target=AdjustmentTarget.PROJECT,
            target_id="proj-123",
            page=2,
            items_per_page=10
        )
        
        assert len(result) == 10
        self.mock_client.get.assert_called_once_with(
            "billing/admin/projects/adjustments",
            params={"page": 2, "itemsPerPage": 10, "projectId": "proj-123"}
        )
    
    def test_delete_adjustment_single_billing_group(self):
        """Test deleting single adjustment for billing group"""
        self.adjustment_manager.delete_adjustment(
            adjustment_ids="adj-001",
            adjustment_target=AdjustmentTarget.BILLING_GROUP
        )
        
        self.mock_client.delete.assert_called_once_with(
            "billing/admin/billing-groups/adjustments",
            params={"adjustmentIds": "adj-001"}
        )
    
    def test_delete_adjustment_multiple_project(self):
        """Test deleting multiple adjustments for project"""
        adjustment_ids = ["adj-001", "adj-002", "adj-003"]
        
        self.adjustment_manager.delete_adjustment(
            adjustment_ids=adjustment_ids,
            adjustment_target=AdjustmentTarget.PROJECT
        )
        
        assert self.mock_client.delete.call_count == 3
        for idx, adj_id in enumerate(adjustment_ids):
            assert self.mock_client.delete.call_args_list[idx] == (
                ("billing/admin/projects/adjustments",),
                {"params": {"adjustmentIds": adj_id}}
            )
    
    def test_delete_adjustment_api_error(self):
        """Test delete adjustment with API error"""
        self.mock_client.delete.side_effect = APIRequestException("Delete failed")
        
        with pytest.raises(APIRequestException):
            self.adjustment_manager.delete_adjustment(
                adjustment_ids="adj-001",
                adjustment_target=AdjustmentTarget.BILLING_GROUP
            )
    
    def test_delete_all_adjustments_success(self):
        """Test deleting all adjustments for a target"""
        # Mock get_adjustments to return some adjustment IDs
        mock_adjustments = {
            "adjustments": [
                {"adjustmentId": "adj-001"},
                {"adjustmentId": "adj-002"}
            ]
        }
        self.mock_client.get.return_value = mock_adjustments
        
        # Delete should be called for each adjustment
        count = self.adjustment_manager.delete_all_adjustments(
            adjustment_target=AdjustmentTarget.BILLING_GROUP,
            target_id="bg-123"
        )
        
        assert count == 2
        assert self.mock_client.delete.call_count == 2
    
    def test_delete_all_adjustments_none_exist(self):
        """Test deleting all adjustments when none exist"""
        self.mock_client.get.return_value = {"adjustments": []}
        
        count = self.adjustment_manager.delete_all_adjustments(
            adjustment_target=AdjustmentTarget.PROJECT,
            target_id="proj-456"
        )
        
        assert count == 0
        self.mock_client.delete.assert_not_called()
    
    def test_string_representation(self):
        """Test string representation of AdjustmentManager"""
        assert repr(self.adjustment_manager) == "AdjustmentManager(month=2024-01)"


class TestAdjustmentsLegacyWrapper:
    """Unit tests for legacy Adjustments wrapper"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        with patch('libs.adjustment.AdjustmentManager') as mock_manager_class:
            self.mock_manager = Mock()
            mock_manager_class.return_value = self.mock_manager
            self.adjustments = Adjustments(month="2024-01")
            yield
    
    def test_apply_adjustment_legacy_billing_group(self):
        """Test legacy apply_adjustment with billing group"""
        self.adjustments.apply_adjustment(
            adjustment=1000,
            adjustmentType="FIXED_DISCOUNT",
            adjustmentTarget="BillingGroup",
            billingGroupId="bg-123"
        )
        
        self.mock_manager.apply_adjustment.assert_called_once_with(
            adjustment_amount=1000,
            adjustment_type="FIXED_DISCOUNT",
            adjustment_target="BillingGroup",
            target_id="bg-123"
        )
    
    def test_apply_adjustment_legacy_project(self):
        """Test legacy apply_adjustment with project"""
        self.adjustments.apply_adjustment(
            adjustment=15.5,
            adjustmentType="RATE_DISCOUNT",
            adjustmentTarget="Project",
            projectId="proj-456"
        )
        
        self.mock_manager.apply_adjustment.assert_called_once_with(
            adjustment_amount=15.5,
            adjustment_type="RATE_DISCOUNT",
            adjustment_target="Project",
            target_id="proj-456"
        )
    
    def test_apply_adjustment_legacy_missing_params(self):
        """Test legacy apply_adjustment with missing parameters"""
        with pytest.raises(ValidationException) as exc_info:
            self.adjustments.apply_adjustment(
                adjustment=1000,
                adjustmentType="FIXED_DISCOUNT"
                # Missing adjustmentTarget
            )
        
        assert "Missing required parameters" in str(exc_info.value)
    
    def test_apply_adjustment_legacy_no_target_id(self):
        """Test legacy apply_adjustment without target ID"""
        with pytest.raises(ValidationException) as exc_info:
            self.adjustments.apply_adjustment(
                adjustment=1000,
                adjustmentType="FIXED_DISCOUNT",
                adjustmentTarget="BillingGroup"
                # Missing both billingGroupId and projectId
            )
        
        assert "Either billingGroupId or projectId must be provided" in str(exc_info.value)
    
    def test_inquiry_adjustment_legacy_billing_group(self):
        """Test legacy inquiry_adjustment for billing group"""
        self.mock_manager.get_adjustments.return_value = ["adj-001", "adj-002"]
        
        result = self.adjustments.inquiry_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupid="bg-123"  # Note lowercase 'id'
        )
        
        assert result == ["adj-001", "adj-002"]
        self.mock_manager.get_adjustments.assert_called_once_with(
            adjustment_target="BillingGroup",
            target_id="bg-123"
        )
    
    def test_inquiry_adjustment_legacy_project(self):
        """Test legacy inquiry_adjustment for project"""
        self.mock_manager.get_adjustments.return_value = ["adj-003"]
        
        result = self.adjustments.inquiry_adjustment(
            adjustmentTarget="Project",
            projectId="proj-456"
        )
        
        assert result == ["adj-003"]
        self.mock_manager.get_adjustments.assert_called_once_with(
            adjustment_target="Project",
            target_id="proj-456"
        )
    
    def test_inquiry_adjustment_legacy_missing_target(self):
        """Test legacy inquiry_adjustment without target"""
        result = self.adjustments.inquiry_adjustment(
            billingGroupid="bg-123"
            # Missing adjustmentTarget
        )
        
        assert result is None
        self.mock_manager.get_adjustments.assert_not_called()
    
    def test_inquiry_adjustment_legacy_api_error(self):
        """Test legacy inquiry_adjustment with API error"""
        self.mock_manager.get_adjustments.side_effect = APIRequestException("Error")
        
        result = self.adjustments.inquiry_adjustment(
            adjustmentTarget="BillingGroup",
            billingGroupid="bg-123"
        )
        
        assert result is None
    
    def test_delete_adjustment_legacy_single(self):
        """Test legacy delete_adjustment with single ID"""
        self.adjustments.delete_adjustment("adj-001")
        
        self.mock_manager.delete_adjustment.assert_called_once_with(
            "adj-001",
            AdjustmentTarget.PROJECT  # Default target
        )
    
    def test_delete_adjustment_legacy_multiple(self):
        """Test legacy delete_adjustment with multiple IDs"""
        adj_ids = ["adj-001", "adj-002", "adj-003"]
        self.adjustments.delete_adjustment(adj_ids)
        
        self.mock_manager.delete_adjustment.assert_called_once_with(
            adj_ids,
            AdjustmentTarget.PROJECT  # Default target
        )
    
    def test_delete_adjustment_legacy_empty(self):
        """Test legacy delete_adjustment with empty input"""
        self.adjustments.delete_adjustment([])
        
        self.mock_manager.delete_adjustment.assert_not_called()