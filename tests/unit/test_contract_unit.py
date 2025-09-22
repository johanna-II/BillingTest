"""Unit tests for contract management module."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from libs.Contract import ContractManager, Contract
from libs.exceptions import APIRequestException, ValidationException


class TestContractManagerUnit:
    """Unit tests for ContractManager class"""
    
    @pytest.fixture
    def mock_client(self):
        """Mock HTTP client."""
        return Mock()
    
    @pytest.fixture
    def contract_manager(self, mock_client):
        """Create ContractManager with mocked dependencies."""
        with patch('libs.Contract.BillingAPIClient', return_value=mock_client):
            manager = ContractManager(month="2024-01", billing_group_id="billing-group-123")
            manager._client = mock_client
            return manager
    
    def test_init(self):
        """Test ContractManager initialization."""
        manager = ContractManager(month="2024-01", billing_group_id="bg-123")
        assert manager.month == "2024-01"
        assert manager.billing_group_id == "bg-123"
        assert hasattr(manager, '_client')
    
    def test_init_invalid_month(self):
        """Test ContractManager initialization with invalid month."""
        with pytest.raises(ValidationException) as exc_info:
            ContractManager(month="2024-1", billing_group_id="bg-123")
        
        assert "Invalid month format" in str(exc_info.value)
    
    def test_repr(self, contract_manager):
        """Test string representation."""
        assert repr(contract_manager) == "ContractManager(month=2024-01, billing_group_id=billing-group-123)"
    
    def test_apply_contract_success(self, contract_manager, mock_client):
        """Test successful contract application."""
        mock_response = {
            "status": "SUCCESS",
            "billingGroupId": "billing-group-123",
            "contractId": "contract-456"
        }
        mock_client.put.return_value = mock_response
        
        result = contract_manager.apply_contract(
            contract_id="contract-456",
            name="Test Contract",
            is_default=True
        )
        
        assert result == mock_response
        
        # Verify API call
        expected_data = {
            "contractId": "contract-456",
            "defaultYn": "Y",
            "monthFrom": "2024-01",
            "name": "Test Contract"
        }
        
        mock_client.put.assert_called_once_with(
            "billing/admin/billing-groups/billing-group-123",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json_data=expected_data
        )
    
    def test_apply_contract_not_default(self, contract_manager, mock_client):
        """Test applying non-default contract."""
        mock_response = {"status": "SUCCESS"}
        mock_client.put.return_value = mock_response
        
        result = contract_manager.apply_contract(
            contract_id="contract-789",
            name="Secondary Contract",
            is_default=False
        )
        
        assert result == mock_response
        
        # Check defaultYn is "N"
        call_args = mock_client.put.call_args
        assert call_args[1]["json_data"]["defaultYn"] == "N"
    
    def test_apply_contract_default_name(self, contract_manager, mock_client):
        """Test applying contract with default name."""
        mock_response = {"status": "SUCCESS"}
        mock_client.put.return_value = mock_response
        
        result = contract_manager.apply_contract(contract_id="contract-999")
        
        assert result == mock_response
        
        # Check default name was used
        call_args = mock_client.put.call_args
        assert call_args[1]["json_data"]["name"] == "billing group default"
    
    def test_apply_contract_api_error(self, contract_manager, mock_client):
        """Test contract application with API error."""
        mock_client.put.side_effect = APIRequestException("Failed to apply contract")
        
        with pytest.raises(APIRequestException) as exc_info:
            contract_manager.apply_contract("contract-123")
        
        assert "Failed to apply contract" in str(exc_info.value)
    
    def test_delete_contract_success(self, contract_manager, mock_client):
        """Test successful contract deletion."""
        mock_response = {"status": "DELETED"}
        mock_client.delete.return_value = mock_response
        
        result = contract_manager.delete_contract()
        
        assert result == mock_response
        
        # Verify API call
        mock_client.delete.assert_called_once_with(
            "billing/admin/billing-groups/billing-group-123/contracts",
            headers={"Accept": "application/json", "Content-Type": "application/json"}
        )
    
    def test_delete_contract_api_error(self, contract_manager, mock_client):
        """Test contract deletion with API error."""
        mock_client.delete.side_effect = APIRequestException("Failed to delete contract")
        
        with pytest.raises(APIRequestException) as exc_info:
            contract_manager.delete_contract()
        
        assert "Failed to delete contract" in str(exc_info.value)
    
    def test_validate_month_format_valid(self):
        """Test month format validation with valid formats."""
        valid_months = ["2024-01", "2024-12", "2023-06", "2022-09"]
        
        for month in valid_months:
            # Should not raise exception
            ContractManager._validate_month_format(month)
    
    def test_validate_month_format_invalid(self):
        """Test month format validation with invalid formats."""
        invalid_months = ["2024", "2024-1", "2024-13", "24-01", "2024/01", ""]
        
        for month in invalid_months:
            with pytest.raises(ValidationException):
                ContractManager._validate_month_format(month)
    
    @patch('libs.Contract.logger')
    def test_logging_on_apply_contract(self, mock_logger, contract_manager, mock_client):
        """Test that contract application is logged."""
        mock_client.put.return_value = {"status": "SUCCESS"}
        
        contract_manager.apply_contract("contract-123")
        
        # Verify logging occurred
        assert mock_logger.info.called
    
    @patch('libs.Contract.logger')
    def test_logging_on_delete_contract(self, mock_logger, contract_manager, mock_client):
        """Test that contract deletion is logged."""
        mock_client.delete.return_value = {"status": "DELETED"}
        
        contract_manager.delete_contract()
        
        # Verify logging occurred
        assert mock_logger.info.called
    
    @patch('libs.Contract.logger')
    def test_logging_on_error(self, mock_logger, contract_manager, mock_client):
        """Test that errors are logged."""
        mock_client.put.side_effect = APIRequestException("Test error")
        
        with pytest.raises(APIRequestException):
            contract_manager.apply_contract("contract-123")
        
        # Verify error was logged
        assert mock_logger.exception.called


class TestContractLegacyWrapper:
    """Unit tests for legacy Contract wrapper."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        with patch('libs.Contract.ContractManager') as mock_manager_class:
            self.mock_manager = Mock()
            mock_manager_class.return_value = self.mock_manager
            self.contract = Contract(
                month="2024-01",
                bgId="bg-123"
            )
            yield
    
    def test_init_legacy(self):
        """Test legacy Contract initialization."""
        assert self.contract.month == "2024-01"
        assert self.contract.bgId == "bg-123"
        assert hasattr(self.contract, '_contractId')
        assert hasattr(self.contract, '_manager')
    
    def test_repr_legacy(self):
        """Test string representation of legacy Contract."""
        repr_str = repr(self.contract)
        assert "month: 2024-01" in repr_str
        assert "bgId: bg-123" in repr_str
        assert "contractId:" in repr_str
    
    def test_apply_contract_legacy(self):
        """Test legacy apply_contract method."""
        self.contract.contractId = "contract-456"
        
        self.contract.apply_contract()
        
        self.mock_manager.apply_contract.assert_called_once_with("contract-456")
    
    def test_apply_contract_legacy_exception_suppressed(self):
        """Test legacy apply_contract suppresses exceptions."""
        self.mock_manager.apply_contract.side_effect = Exception("Test error")
        self.contract.contractId = "contract-456"
        
        # Should not raise exception
        self.contract.apply_contract()
        
        self.mock_manager.apply_contract.assert_called_once()
    
    def test_delete_contract_legacy(self):
        """Test legacy delete_contract method."""
        self.mock_manager.delete_contract.return_value = {"status": "DELETED"}
        
        self.contract.delete_contract()
        
        self.mock_manager.delete_contract.assert_called_once()
    
    def test_delete_contract_legacy_exception_suppressed(self):
        """Test legacy delete_contract suppresses exceptions."""
        self.mock_manager.delete_contract.side_effect = Exception("Test error")
        
        # Should not raise exception
        self.contract.delete_contract()
        
        self.mock_manager.delete_contract.assert_called_once()
    
    def test_inquiry_contract_legacy(self):
        """Test legacy inquiry_contract method."""
        self.contract.contractId = "contract-456"
        
        self.contract.inquiry_contract()
        
        self.mock_manager.get_contract_details.assert_called_once_with("contract-456")
    
    def test_inquiry_priceby_counter_name_legacy(self):
        """Test legacy inquiry_priceby_counter_name method."""
        self.contract.contractId = "contract-456"
        self.contract.counterName = "CPU"
        self.mock_manager.get_counter_price.return_value = {
            "price": 100,
            "original_price": 120
        }
        
        result = self.contract.inquiry_priceby_counter_name()
        
        assert result["price"] == {100}
        assert result["originalPrice"] == {120}
        self.mock_manager.get_counter_price.assert_called_once_with("contract-456", "CPU")


# Additional test for edge cases
class TestContractEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @patch('libs.Contract.BillingAPIClient')
    def test_empty_billing_group_id(self, mock_client_class):
        """Test with empty billing group ID."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Should still create manager (validation might happen later)
        manager = ContractManager(month="2024-01", billing_group_id="")
        assert manager.billing_group_id == ""
    
    @patch('libs.Contract.BillingAPIClient')
    def test_long_contract_name(self, mock_client_class):
        """Test with very long contract name."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.put.return_value = {"status": "SUCCESS"}
        
        manager = ContractManager(month="2024-01", billing_group_id="bg-123")
        manager._client = mock_client
        
        long_name = "A" * 500  # Very long name
        result = manager.apply_contract(
            contract_id="contract-123",
            name=long_name
        )
        
        assert result["status"] == "SUCCESS"
        
        # Verify the long name was sent
        call_args = mock_client.put.call_args
        assert call_args[1]["json_data"]["name"] == long_name
    
    @patch('libs.Contract.BillingAPIClient')
    def test_special_characters_in_ids(self, mock_client_class):
        """Test with special characters in IDs."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.put.return_value = {"status": "SUCCESS"}
        
        # IDs with special characters
        special_bg_id = "bg-123/456#test"
        special_contract_id = "contract@789!test"
        
        manager = ContractManager(month="2024-01", billing_group_id=special_bg_id)
        manager._client = mock_client
        
        result = manager.apply_contract(contract_id=special_contract_id)
        
        assert result["status"] == "SUCCESS"
        
        # Verify special characters were preserved
        call_args = mock_client.put.call_args
        assert special_bg_id in call_args[0][0]  # In endpoint URL
        assert call_args[1]["json_data"]["contractId"] == special_contract_id