"""Unit tests for ContractManager to improve coverage."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from libs.Contract import ContractManager
from libs.exceptions import APIRequestException
from libs.constants import ContractType, DiscountType


class TestContractManagerUnit:
    """Unit tests for ContractManager class."""
    
    @pytest.fixture
    def mock_client(self):
        """Mock HTTP client."""
        return Mock()
    
    @pytest.fixture
    def contract_manager(self, mock_client):
        """Create ContractManager with mocked dependencies."""
        with patch('libs.Contract.BillingAPIClient', return_value=mock_client):
            manager = ContractManager("2024-01", "billing-group-123")
            manager._client = mock_client
            return manager
    
    def test_init(self):
        """Test ContractManager initialization."""
        manager = ContractManager("2024-01", "billing-group-123")
        assert manager.month == "2024-01"
        assert manager.billing_group_id == "billing-group-123"
        assert hasattr(manager, '_client')
    
    def test_repr(self):
        """Test string representation."""
        manager = ContractManager("2024-01", "billing-group-123")
        repr_str = repr(manager)
        assert "ContractManager" in repr_str
        assert "2024-01" in repr_str
        assert "billing-group-123" in repr_str
    
    def test_get_contracts_success(self, contract_manager, mock_client):
        """Test successful contract retrieval."""
        mock_response = {
            "contracts": [
                {"contractId": "c1", "type": "VOLUME", "discountRate": 10},
                {"contractId": "c2", "type": "PERIOD", "discountRate": 20}
            ]
        }
        mock_client.get.return_value = mock_response
        
        contracts = contract_manager.get_contracts()
        
        assert contracts == mock_response["contracts"]
        mock_client.get.assert_called_once_with(
            f"billing/contracts",
            params={
                "month": "2024-01",
                "billingGroupId": "billing-group-123"
            }
        )
    
    def test_get_contracts_empty(self, contract_manager, mock_client):
        """Test empty contract list."""
        mock_client.get.return_value = {"contracts": []}
        
        contracts = contract_manager.get_contracts()
        
        assert contracts == []
    
    def test_get_contracts_error(self, contract_manager, mock_client):
        """Test contract retrieval error handling."""
        mock_client.get.side_effect = APIRequestException("Failed to get contracts")
        
        with pytest.raises(APIRequestException):
            contract_manager.get_contracts()
    
    def test_create_volume_contract(self, contract_manager, mock_client):
        """Test creating volume-based contract."""
        mock_response = {"contractId": "new-contract-123", "status": "ACTIVE"}
        mock_client.post.return_value = mock_response
        
        result = contract_manager.create_contract(
            contract_type=ContractType.VOLUME,
            discount_rate=15.5,
            min_volume=1000
        )
        
        assert result == mock_response
        mock_client.post.assert_called_once()
        
        # Verify request data
        call_args = mock_client.post.call_args
        request_data = call_args[1]["json_data"]
        assert request_data["contractType"] == "VOLUME"
        assert request_data["discountRate"] == 15.5
        assert request_data["minVolume"] == 1000
    
    def test_create_period_contract(self, contract_manager, mock_client):
        """Test creating period-based contract."""
        mock_response = {"contractId": "period-contract-456", "status": "ACTIVE"}
        mock_client.post.return_value = mock_response
        
        result = contract_manager.create_contract(
            contract_type=ContractType.PERIOD,
            discount_rate=20.0,
            period_months=12
        )
        
        assert result == mock_response
        assert mock_client.post.call_args[1]["json_data"]["periodMonths"] == 12
    
    def test_update_contract(self, contract_manager, mock_client):
        """Test updating existing contract."""
        mock_response = {"contractId": "c1", "status": "UPDATED"}
        mock_client.put.return_value = mock_response
        
        result = contract_manager.update_contract(
            contract_id="c1",
            discount_rate=25.0
        )
        
        assert result == mock_response
        mock_client.put.assert_called_once_with(
            "billing/contracts/c1",
            json_data={"discountRate": 25.0}
        )
    
    def test_delete_contract(self, contract_manager, mock_client):
        """Test deleting contract."""
        mock_response = {"message": "Contract deleted"}
        mock_client.delete.return_value = mock_response
        
        result = contract_manager.delete_contract("c1")
        
        assert result == mock_response
        mock_client.delete.assert_called_once_with("billing/contracts/c1")
    
    def test_get_counter_price(self, contract_manager, mock_client):
        """Test getting counter price with contract discount."""
        mock_response = {
            "prices": {
                "price": 900,
                "originalPrice": 1000
            }
        }
        mock_client.get.return_value = mock_response
        
        result = contract_manager.get_counter_price("contract-123", "cpu.usage")
        
        assert result["counter_name"] == "cpu.usage"
        assert result["price"] == 900
        assert result["original_price"] == 1000
        assert result["discount_amount"] == 100
        assert result["discount_rate"] == 10.0
    
    def test_get_counter_price_no_discount(self, contract_manager, mock_client):
        """Test counter price when no discount applies."""
        mock_response = {
            "prices": {
                "price": 1000,
                "originalPrice": 1000
            }
        }
        mock_client.get.return_value = mock_response
        
        result = contract_manager.get_counter_price("contract-123", "storage.usage")
        
        assert result["discount_amount"] == 0
        assert result["discount_rate"] == 0
    
    def test_get_counter_price_with_retry(self, contract_manager, mock_client):
        """Test retry logic for counter price retrieval."""
        # First two attempts fail, third succeeds
        mock_client.get.side_effect = [
            APIRequestException("Network error"),
            APIRequestException("Timeout"),
            {"prices": {"price": 800, "originalPrice": 1000}}
        ]
        
        result = contract_manager.get_counter_price("contract-123", "network.usage")
        
        assert result["price"] == 800
        assert mock_client.get.call_count == 3
    
    def test_get_counter_price_max_retries_exceeded(self, contract_manager, mock_client):
        """Test counter price retrieval fails after max retries."""
        mock_client.get.side_effect = APIRequestException("Persistent error")
        
        with pytest.raises(APIRequestException):
            contract_manager.get_counter_price("contract-123", "failed.counter")
        
        # Should attempt 3 times
        assert mock_client.get.call_count == 3
    
    def test_get_multiple_counter_prices(self, contract_manager, mock_client):
        """Test getting prices for multiple counters."""
        mock_client.get.side_effect = [
            {"prices": {"price": 900, "originalPrice": 1000}},
            {"prices": {"price": 1800, "originalPrice": 2000}},
            {"prices": {"price": 500, "originalPrice": 500}}
        ]
        
        counter_names = ["cpu.usage", "memory.usage", "storage.usage"]
        results = contract_manager.get_multiple_counter_prices("contract-123", counter_names)
        
        assert len(results) == 3
        assert results["cpu.usage"]["price"] == 900
        assert results["memory.usage"]["price"] == 1800
        assert results["storage.usage"]["price"] == 500
        assert results["storage.usage"]["discount_rate"] == 0
    
    def test_apply_contract_discount(self, contract_manager, mock_client):
        """Test applying contract discount to billing."""
        mock_response = {"status": "DISCOUNT_APPLIED", "totalDiscount": 5000}
        mock_client.post.return_value = mock_response
        
        result = contract_manager.apply_contract_discount(
            contract_id="contract-123",
            billing_id="bill-456"
        )
        
        assert result == mock_response
        mock_client.post.assert_called_once()
    
    def test_contract_type_validation(self):
        """Test contract type enum values."""
        assert ContractType.VOLUME == "VOLUME"
        assert ContractType.PERIOD == "PERIOD"
        assert ContractType.COMMITMENT == "COMMITMENT"
        assert ContractType.PARTNER == "PARTNER"
    
    def test_discount_type_validation(self):
        """Test discount type enum values."""
        assert DiscountType.PERCENTAGE == "PERCENTAGE"
        assert DiscountType.FIXED_AMOUNT == "FIXED_AMOUNT"
    
    @patch('libs.Contract.logger')
    def test_logging_on_operations(self, mock_logger, contract_manager, mock_client):
        """Test that operations are properly logged."""
        mock_client.get.return_value = {"contracts": []}
        
        contract_manager.get_contracts()
        
        mock_logger.info.assert_called()
    
    def test_legacy_contracts_class(self):
        """Test legacy Contracts class."""
        from libs.Contract import Contracts
        
        contracts = Contracts("2024-01", "billing-group-123")
        assert contracts.month == "2024-01"
        assert contracts.billing_group_id == "billing-group-123"
