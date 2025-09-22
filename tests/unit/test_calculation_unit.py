"""Unit tests for billing calculation module."""

import pytest
from unittest.mock import Mock, patch
from libs.calculation import CalculationManager, Calculation
from libs.constants import BatchJobCode
from libs.exceptions import ValidationException, APIRequestException


class TestCalculationManagerUnit:
    """Unit tests for CalculationManager class"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        with patch('libs.calculation.BillingAPIClient') as mock_client_class:
            self.mock_client = Mock()
            mock_client_class.return_value = self.mock_client
            self.calculator = CalculationManager(month="2024-01", uuid="test-uuid-123")
            yield
    
    def test_init(self):
        """Test CalculationManager initialization"""
        assert self.calculator.month == "2024-01"
        assert self.calculator.uuid == "test-uuid-123"
        assert hasattr(self.calculator, '_client')
    
    def test_recalculate_all_success(self):
        """Test successful full recalculation"""
        # Mock successful post response
        self.mock_client.post.return_value = {
            "status": "STARTED",
            "jobId": "calc-job-123"
        }
        
        # Mock successful completion check
        self.mock_client.wait_for_completion.return_value = True
        
        result = self.calculator.recalculate_all(include_usage=True, timeout=300)
        
        assert result["status"] == "STARTED"
        assert result["jobId"] == "calc-job-123"
        
        # Verify API call
        self.mock_client.post.assert_called_once_with(
            "billing/admin/calculations",
            json_data={
                "includeUsage": True,
                "month": "2024-01",
                "uuid": "test-uuid-123"
            }
        )
        
        # Verify completion check was called
        self.mock_client.wait_for_completion.assert_called_once()
    
    def test_recalculate_all_without_usage(self):
        """Test recalculation without usage data"""
        self.mock_client.post.return_value = {"status": "STARTED"}
        self.mock_client.wait_for_completion.return_value = True
        
        result = self.calculator.recalculate_all(include_usage=False)
        
        # Verify includeUsage is False in the request
        call_args = self.mock_client.post.call_args
        assert call_args[1]["json_data"]["includeUsage"] is False
    
    def test_recalculate_all_timeout(self):
        """Test recalculation with timeout"""
        self.mock_client.post.return_value = {"status": "STARTED"}
        # Mock timeout scenario
        self.mock_client.wait_for_completion.return_value = False
        
        result = self.calculator.recalculate_all(timeout=10)
        
        assert result["status"] == "STARTED"
        # Verify timeout was passed correctly
        wait_call = self.mock_client.wait_for_completion.call_args
        assert wait_call[1]["max_wait_time"] == 10
    
    def test_recalculate_all_api_error(self):
        """Test recalculation with API error"""
        self.mock_client.post.side_effect = APIRequestException("Calculation failed")
        
        with pytest.raises(APIRequestException) as exc_info:
            self.calculator.recalculate_all()
        
        assert "Calculation failed" in str(exc_info.value)
    
    def test_wait_for_calculation_completion(self):
        """Test waiting for calculation completion"""
        self.mock_client.wait_for_completion.return_value = True
        
        result = self.calculator._wait_for_calculation_completion(timeout=60, check_interval=2)
        
        assert result is True
        
        # Verify correct parameters were passed
        self.mock_client.wait_for_completion.assert_called_once_with(
            check_endpoint="billing/admin/progress",
            completion_field="progress",
            max_field="maxProgress",
            progress_code=BatchJobCode.API_CALCULATE_USAGE_AND_PRICE.value,
            check_interval=2,
            max_wait_time=60
        )
    
    def test_delete_resources_success(self):
        """Test successful resource deletion"""
        self.mock_client.delete.return_value = {
            "status": "DELETED",
            "deletedCount": 150
        }
        
        result = self.calculator.delete_resources()
        
        assert result["status"] == "DELETED"
        assert result["deletedCount"] == 150
        
        # Verify API call
        self.mock_client.delete.assert_called_once_with(
            "billing/admin/resources",
            params={"month": "2024-01"},
            headers={"uuid": "test-uuid-123"}
        )
    
    def test_delete_resources_api_error(self):
        """Test resource deletion with API error"""
        self.mock_client.delete.side_effect = APIRequestException("Delete failed")
        
        with pytest.raises(APIRequestException) as exc_info:
            self.calculator.delete_resources()
        
        assert "Delete failed" in str(exc_info.value)
    
    def test_get_calculation_status_success(self):
        """Test getting calculation status"""
        mock_status = {
            "progress": 75,
            "maxProgress": 100,
            "status": "IN_PROGRESS",
            "currentStep": "Calculating usage costs"
        }
        self.mock_client.get.return_value = mock_status
        
        result = self.calculator.get_calculation_status()
        
        assert result["progress"] == 75
        assert result["maxProgress"] == 100
        assert result["status"] == "IN_PROGRESS"
        
        self.mock_client.get.assert_called_once_with("billing/admin/progress")
    
    def test_get_calculation_status_error(self):
        """Test getting calculation status with error"""
        self.mock_client.get.side_effect = APIRequestException("Status check failed")
        
        with pytest.raises(APIRequestException) as exc_info:
            self.calculator.get_calculation_status()
        
        assert "Status check failed" in str(exc_info.value)
    
    def test_string_representation(self):
        """Test string representation of CalculationManager"""
        assert repr(self.calculator) == "CalculationManager(month=2024-01, uuid=test-uuid-123)"


class TestCalculationLegacyWrapper:
    """Unit tests for legacy Calculation wrapper"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        with patch('libs.calculation.CalculationManager') as mock_manager_class:
            self.mock_manager = Mock()
            mock_manager_class.return_value = self.mock_manager
            self.calculation = Calculation(month="2024-01", uuid="test-uuid-123")
            yield
    
    def test_init_legacy(self):
        """Test legacy Calculation initialization"""
        assert self.calculation.month == "2024-01"
        assert self.calculation.uuid == "test-uuid-123"
        assert hasattr(self.calculation, '_manager')
    
    def test_recalculation_all_legacy(self):
        """Test legacy recalculation_all method"""
        # Should not raise exception even if manager method fails
        self.mock_manager.recalculate_all.side_effect = Exception("Test error")
        
        # Should suppress the exception
        self.calculation.recalculation_all()
        
        self.mock_manager.recalculate_all.assert_called_once()
    
    def test_check_stable_legacy_completed(self):
        """Test legacy check_stable method when calculation completes"""
        self.mock_manager._wait_for_calculation_completion.return_value = True
        
        # Should not raise any exception
        self.calculation.check_stable()
        
        self.mock_manager._wait_for_calculation_completion.assert_called_once()
    
    def test_check_stable_legacy_not_completed(self):
        """Test legacy check_stable method when calculation doesn't complete"""
        self.mock_manager._wait_for_calculation_completion.return_value = False
        
        # Should not raise any exception
        self.calculation.check_stable()
        
        self.mock_manager._wait_for_calculation_completion.assert_called_once()
    
    def test_delete_resources_legacy(self):
        """Test legacy delete_resources method"""
        # Should not raise exception even if manager method fails
        self.mock_manager.delete_resources.side_effect = Exception("Delete error")
        
        # Should suppress the exception
        self.calculation.delete_resources()
        
        self.mock_manager.delete_resources.assert_called_once()
    
    def test_delete_resources_legacy_success(self):
        """Test legacy delete_resources method with success"""
        self.mock_manager.delete_resources.return_value = {"status": "DELETED"}
        
        # Should not raise exception
        self.calculation.delete_resources()
        
        self.mock_manager.delete_resources.assert_called_once()


# Additional test class for edge cases
class TestCalculationEdgeCases:
    """Test edge cases and boundary conditions"""
    
    @patch('libs.calculation.BillingAPIClient')
    def test_month_format_variations(self, mock_client_class):
        """Test various month format inputs"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Valid formats should work
        valid_months = ["2024-01", "2024-12", "2023-06"]
        for month in valid_months:
            calc = CalculationManager(month=month, uuid="test-uuid")
            assert calc.month == month
    
    @patch('libs.calculation.BillingAPIClient')
    def test_uuid_variations(self, mock_client_class):
        """Test various UUID formats"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Different UUID formats
        uuids = [
            "123e4567-e89b-12d3-a456-426614174000",
            "test-uuid-123",
            "simple-uuid",
            "UPPERCASE-UUID-123"
        ]
        
        for uuid_val in uuids:
            calc = CalculationManager(month="2024-01", uuid=uuid_val)
            assert calc.uuid == uuid_val
    
    @patch('libs.calculation.BillingAPIClient')
    def test_concurrent_calculations(self, mock_client_class):
        """Test handling of concurrent calculation requests"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Simulate concurrent calculation already running
        mock_client.post.side_effect = APIRequestException("Calculation already in progress")
        
        calc = CalculationManager(month="2024-01", uuid="test-uuid")
        
        with pytest.raises(APIRequestException) as exc_info:
            calc.recalculate_all()
        
        assert "Calculation already in progress" in str(exc_info.value)