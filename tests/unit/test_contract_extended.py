"""Extended unit tests for contract management module to improve coverage."""

from unittest.mock import Mock, patch

import pytest
from pytest import approx

from libs.Contract import ContractManager
from libs.exceptions import APIRequestException, ValidationException


class TestContractManagerExtended:
    """Extended unit tests for ContractManager class."""

    @pytest.fixture
    def mock_client(self):
        """Mock HTTP client."""
        return Mock()

    @pytest.fixture
    def contract_manager(self, mock_client):
        """Create ContractManager with mocked dependencies."""
        with patch("libs.Contract.BillingAPIClient", return_value=mock_client):
            manager = ContractManager(
                month="2024-01", billing_group_id="billing-group-123"
            )
            manager._client = mock_client
            return manager

    def test_get_contract_details_success(self, contract_manager, mock_client) -> None:
        """Test successful get_contract_details."""
        mock_response = {
            "contract": {
                "contractId": "contract-123",
                "baseFee": 50000,
                "name": "Test Contract",
                "description": "Test Description",
            }
        }
        mock_client.get.return_value = mock_response

        result = contract_manager.get_contract_details(contract_id="contract-123")

        assert result["contract_id"] == "contract-123"
        assert result["base_fee"] == 50000
        assert result["contract_info"]["name"] == "Test Contract"

        mock_client.get.assert_called_once_with(
            "billing/admin/contracts/contract-123",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

    def test_get_contract_details_api_error(
        self, contract_manager, mock_client
    ) -> None:
        """Test get_contract_details with API error."""
        mock_client.get.side_effect = APIRequestException("API error")

        with pytest.raises(APIRequestException, match="API error"):
            contract_manager.get_contract_details(contract_id="contract-123")

    def test_get_counter_price_success(self, contract_manager, mock_client) -> None:
        """Test successful get_counter_price."""
        mock_response = {"prices": {"price": 8000, "originalPrice": 10000}}
        mock_client.get.return_value = mock_response

        result = contract_manager.get_counter_price(
            contract_id="contract-123", counter_name="Instances"
        )

        assert result["counter_name"] == "Instances"
        assert result["price"] == 8000
        assert result["original_price"] == 10000
        assert result["discount_amount"] == 2000
        assert result["discount_rate"] == approx(20.0)

        mock_client.get.assert_called_once_with(
            "billing/admin/contracts/contract-123/products/prices",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            params={"counterNames": "Instances"},
        )

    def test_get_counter_price_with_retry(self, contract_manager, mock_client) -> None:
        """Test get_counter_price with retry on failure."""
        # First two attempts fail, third succeeds
        mock_client.get.side_effect = [
            APIRequestException("Temporary error"),
            APIRequestException("Another temporary error"),
            {"prices": {"price": 5000, "originalPrice": 5000}},
        ]

        result = contract_manager.get_counter_price(
            contract_id="contract-123", counter_name="Storage"
        )

        assert result["price"] == 5000
        assert result["discount_rate"] == approx(0.0)
        assert mock_client.get.call_count == 3

    def test_get_counter_price_all_retries_fail(
        self, contract_manager, mock_client
    ) -> None:
        """Test get_counter_price when all retries fail."""
        mock_client.get.side_effect = APIRequestException("Persistent error")

        with pytest.raises(APIRequestException, match="Persistent error"):
            contract_manager.get_counter_price(
                contract_id="contract-123", counter_name="Network"
            )

        assert mock_client.get.call_count == 3

    def test_get_multiple_counter_prices_success(
        self, contract_manager, mock_client
    ) -> None:
        """Test successful get_multiple_counter_prices."""
        # Mock different responses for different counters
        mock_client.get.side_effect = [
            {"prices": {"price": 8000, "originalPrice": 10000}},
            {"prices": {"price": 5000, "originalPrice": 6000}},
            {"prices": {"price": 3000, "originalPrice": 3000}},
        ]

        counter_names = ["Instances", "Storage", "Network"]
        result = contract_manager.get_multiple_counter_prices(
            contract_id="contract-123", counter_names=counter_names
        )

        assert len(result) == 3
        assert result["Instances"]["price"] == 8000
        assert result["Storage"]["price"] == 5000
        assert result["Network"]["price"] == 3000
        assert result["Network"]["discount_rate"] == approx(0.0)

    def test_get_multiple_counter_prices_partial_failure(
        self, contract_manager, mock_client
    ) -> None:
        """Test get_multiple_counter_prices with some failures."""
        # Mock mixed success and failure
        mock_client.get.side_effect = [
            {"prices": {"price": 8000, "originalPrice": 10000}},
            APIRequestException("Failed to get Storage price"),
            APIRequestException("Failed to get Storage price"),
            APIRequestException("Failed to get Storage price"),  # All retries fail
            {"prices": {"price": 3000, "originalPrice": 3000}},
        ]

        counter_names = ["Instances", "Storage", "Network"]
        result = contract_manager.get_multiple_counter_prices(
            contract_id="contract-123", counter_names=counter_names
        )

        assert len(result) == 3
        assert result["Instances"]["price"] == 8000
        assert "error" in result["Storage"]
        assert "Failed to get Storage price" in result["Storage"]["error"]
        assert result["Network"]["price"] == 3000

    def test_validate_month_format_invalid(self) -> None:
        """Test month validation with various invalid formats."""
        invalid_months = [
            "2024-1",  # Single digit month
            "2024/01",  # Wrong separator
            "24-01",  # Two digit year
            "2024-13",  # Invalid month
            "2024-00",  # Zero month
            "202401",  # No separator
            "Jan-2024",  # Text month
            "",  # Empty
        ]

        for invalid_month in invalid_months:
            with pytest.raises(ValidationException, match="Invalid month format"):
                ContractManager._validate_month_format(invalid_month)

    def test_repr(self, contract_manager) -> None:
        """Test string representation."""
        repr_str = repr(contract_manager)
        assert (
            repr_str
            == "ContractManager(month=2024-01, billing_group_id=billing-group-123)"
        )

    def test_apply_contract_api_error(self, contract_manager, mock_client) -> None:
        """Test apply_contract with API error."""
        mock_client.put.side_effect = APIRequestException("Contract application failed")

        with pytest.raises(APIRequestException, match="Contract application failed"):
            contract_manager.apply_contract(contract_id="contract-456")

    def test_delete_contract_api_error(self, contract_manager, mock_client) -> None:
        """Test delete_contract with API error."""
        mock_client.delete.side_effect = APIRequestException("Contract deletion failed")

        with pytest.raises(APIRequestException, match="Contract deletion failed"):
            contract_manager.delete_contract()

    def test_get_counter_price_zero_original_price(
        self, contract_manager, mock_client
    ) -> None:
        """Test get_counter_price when original price is zero."""
        mock_response = {"prices": {"price": 0, "originalPrice": 0}}
        mock_client.get.return_value = mock_response

        result = contract_manager.get_counter_price(
            contract_id="contract-123", counter_name="FreeCounter"
        )

        assert result["price"] == 0
        assert result["original_price"] == 0
        assert result["discount_amount"] == 0
        assert result["discount_rate"] == approx(0.0)  # Should handle division by zero
