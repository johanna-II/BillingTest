"""Unit tests for Contract module to improve coverage to 80%."""
import pytest
from unittest.mock import Mock, patch
from libs.Contract import ContractManager
from libs.exceptions import ValidationException, APIRequestException

class TestContractCoverage:
    """Tests for ContractManager to reach 80% coverage"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        with patch('libs.Contract.BillingAPIClient') as mock_client_class:
            self.mock_client = Mock()
            mock_client_class.return_value = self.mock_client
            self.contract_manager = ContractManager(
                month="2024-01",
                billing_group_id="bg-123"
            )
            yield
    
    def test_get_contract_details_success(self):
        """Test successful get_contract_details"""
        # Mock response
        self.mock_client.get.return_value = {
            "contract": {
                "contractId": "contract-123",
                "baseFee": 1000,
                "contractName": "Premium Contract",
                "status": "ACTIVE"
            }
        }
        
        result = self.contract_manager.get_contract_details("contract-123")
        
        assert result["contract_id"] == "contract-123"
        assert result["base_fee"] == 1000
        assert result["contract_info"]["contractName"] == "Premium Contract"
        
        self.mock_client.get.assert_called_once_with(
            "billing/admin/contracts/contract-123",
            headers={"Accept": "application/json", "Content-Type": "application/json"}
        )
    
    def test_get_contract_details_error(self):
        """Test get_contract_details with API error"""
        self.mock_client.get.side_effect = APIRequestException("API Error")
        
        with pytest.raises(APIRequestException):
            self.contract_manager.get_contract_details("contract-123")
    
    def test_get_counter_price_success(self):
        """Test successful get_counter_price"""
        # Mock response
        self.mock_client.get.return_value = {
            "prices": {
                "price": 800,
                "originalPrice": 1000
            }
        }
        
        result = self.contract_manager.get_counter_price("contract-123", "CPU")
        
        assert result["counter_name"] == "CPU"
        assert result["price"] == 800
        assert result["original_price"] == 1000
        assert result["discount_amount"] == 200
        assert result["discount_rate"] == 20.0
        
        self.mock_client.get.assert_called_once_with(
            "billing/admin/contracts/contract-123/products/prices",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            params={"counterNames": "CPU"}
        )
    
    def test_get_counter_price_zero_original_price(self):
        """Test get_counter_price when original price is zero"""
        self.mock_client.get.return_value = {
            "prices": {
                "price": 0,
                "originalPrice": 0
            }
        }
        
        result = self.contract_manager.get_counter_price("contract-123", "FREE_ITEM")
        
        assert result["discount_rate"] == 0  # Should handle division by zero
    
    def test_get_counter_price_with_retries(self):
        """Test get_counter_price retry logic"""
        # First two calls fail, third succeeds
        self.mock_client.get.side_effect = [
            APIRequestException("Temporary error"),
            APIRequestException("Temporary error"),
            {"prices": {"price": 900, "originalPrice": 1000}}
        ]
        
        result = self.contract_manager.get_counter_price("contract-123", "MEMORY")
        
        assert result["price"] == 900
        assert self.mock_client.get.call_count == 3
    
    def test_get_counter_price_max_retries_exceeded(self):
        """Test get_counter_price when all retries fail"""
        self.mock_client.get.side_effect = APIRequestException("Persistent error")
        
        with pytest.raises(APIRequestException):
            self.contract_manager.get_counter_price("contract-123", "DISK")
        
        assert self.mock_client.get.call_count == 3  # Should try 3 times
    
