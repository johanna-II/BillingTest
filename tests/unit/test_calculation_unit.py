"""Unit tests for CalculationManager"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from libs.Calculation import CalculationManager
from libs.exceptions import APIRequestException


@pytest.mark.unit
class TestCalculationManagerUnit:
    """Unit tests for CalculationManager"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures - autouse ensures isolation per test"""
        # Create fresh mocks for each test to ensure isolation in parallel execution
        self.patcher = patch('libs.Calculation.BillingAPIClient')
        mock_client_class = self.patcher.start()
        
        self.mock_client = MagicMock()
        mock_client_class.return_value = self.mock_client
        
        # Create calculator instance
        self.calculator = CalculationManager(
            month="2024-01",
            uuid="test-uuid-123"
        )
        
        yield
        
        # Clean up
        self.patcher.stop()
    
    def test_init(self):
        """Test CalculationManager initialization"""
        assert self.calculator.month == "2024-01"
        assert self.calculator.uuid == "test-uuid-123"
        assert self.calculator._client == self.mock_client
    
    def test_recalculate_all_success(self):
        """Test successful recalculation"""
        # Mock successful response
        mock_response = {
            "status": "COMPLETED",
            "result": {
                "recalculationId": "recalc-123",
                "totalAmount": 10000
            }
        }
        self.mock_client.post.return_value = mock_response
        self.mock_client.wait_for_completion.return_value = True
        
        result = self.calculator.recalculate_all()
        
        # Verify API call
        self.mock_client.post.assert_called_once()
        call_args = self.mock_client.post.call_args
        assert "billing/admin/calculations" in call_args[0][0]
        
        # Verify result
        assert result == mock_response
    
    def test_recalculate_all_without_usage(self):
        """Test recalculate_all with include_usage=False"""
        self.mock_client.post.return_value = {"status": "STARTED", "jobId": "job-123"}
        self.mock_client.wait_for_completion.return_value = True
        
        result = self.calculator.recalculate_all(include_usage=False, timeout=60)
        
        # Verify includeUsage is False in the request
        call_args = self.mock_client.post.call_args
        assert call_args[1]["json_data"]["includeUsage"] is False
    
    @pytest.mark.serial  # Mark as serial to avoid timing issues in parallel
    def test_recalculate_all_timeout(self):
        """Test recalculation with timeout"""
        self.mock_client.post.return_value = {"status": "STARTED"}
        # Mock timeout scenario
        self.mock_client.wait_for_completion.return_value = False
        
        result = self.calculator.recalculate_all(timeout=10)
        
        assert result["status"] == "STARTED"
        # Verify timeout was passed correctly
        wait_call = self.mock_client.wait_for_completion.call_args
        assert wait_call[1]["timeout"] == 10
    
    @pytest.mark.serial  # Mark as serial to avoid timing issues in parallel
    def test_wait_for_calculation_completion(self):
        """Test waiting for calculation completion"""
        self.mock_client.wait_for_completion.return_value = True
        
        result = self.calculator._wait_for_calculation_completion(timeout=60, check_interval=2)
        
        assert result is True
        # Verify wait was called with correct parameters
        self.mock_client.wait_for_completion.assert_called_once()
        call_args = self.mock_client.wait_for_completion.call_args
        assert call_args[1]["timeout"] == 60
        assert call_args[1]["check_interval"] == 2
    
    def test_get_calculation_status(self):
        """Test getting calculation status"""
        mock_status = {
            "status": "IN_PROGRESS",
            "progress": 50,
            "estimatedTime": 120
        }
        self.mock_client.get.return_value = mock_status
        
        result = self.calculator.get_calculation_status()
        
        # Verify API call
        self.mock_client.get.assert_called_once()
        assert "billing/admin/progress" in self.mock_client.get.call_args[0][0]
        
        # Verify result
        assert result == mock_status
    
    def test_recalculate_all_api_error(self):
        """Test recalculation with API error"""
        self.mock_client.post.side_effect = APIRequestException("API Error", status_code=500)
        
        with pytest.raises(APIRequestException) as exc_info:
            self.calculator.recalculate_all()
        
        assert exc_info.value.status_code == 500
        assert "API Error" in str(exc_info.value)
    
    def test_delete_resources(self):
        """Test deleting calculation resources"""
        mock_response = {"status": "SUCCESS", "message": "Resources deleted"}
        self.mock_client.delete.return_value = mock_response
        
        result = self.calculator.delete_resources()
        
        # Verify API call
        self.mock_client.delete.assert_called_once()
        call_args = self.mock_client.delete.call_args
        assert "billing/admin/resources" in call_args[0][0]
        assert call_args[1]["params"]["month"] == "2024-01"
        assert call_args[1]["headers"]["uuid"] == "test-uuid-123"
        
        assert result == mock_response


# Additional test class for edge cases
class TestCalculationEdgeCases:
    """Test edge cases and boundary conditions"""
    
    @patch('libs.Calculation.BillingAPIClient')
    def test_month_format_variations(self, mock_client_class):
        """Test various month format inputs"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Valid formats should work
        valid_months = ["2024-01", "2024-12", "2023-06"]
        for month in valid_months:
            calc = CalculationManager(month=month, uuid="test-uuid")
            assert calc.month == month
    
    @patch('libs.Calculation.BillingAPIClient')
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
    
    @patch('libs.Calculation.BillingAPIClient')
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