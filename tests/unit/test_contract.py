"""Unit tests for contract management module."""

from unittest.mock import Mock, patch

import pytest

from libs.Contract import ContractManager
from libs.exceptions import ValidationException


class TestContractManagerUnit:
    """Unit tests for ContractManager class."""

    @pytest.fixture
    def mock_client(self):
        """Mock HTTP client."""
        return Mock()

    @pytest.fixture
    def contract_manager(self, mock_client):
        """Create ContractManager with mocked dependencies."""
        with patch("libs.Contract.BillingAPIClient", return_value=mock_client):
            manager = ContractManager(month="2024-01", billing_group_id="billing-group-123")
            manager._client = mock_client
            return manager

    def test_apply_contract_success(self, contract_manager, mock_client) -> None:
        """Test successful contract application."""
        mock_response = {
            "status": "SUCCESS",
            "billingGroupId": "billing-group-123",
            "contractId": "contract-456",
        }
        mock_client.put.return_value = mock_response

        result = contract_manager.apply_contract(
            contract_id="contract-456", name="Test Contract", is_default=True
        )

        assert result == mock_response

        # Verify API call
        expected_data = {
            "contractId": "contract-456",
            "defaultYn": "Y",
            "monthFrom": "2024-01",
            "name": "Test Contract",
        }

        mock_client.put.assert_called_once_with(
            "billing/admin/billing-groups/billing-group-123",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json_data=expected_data,
        )

    def test_apply_contract_not_default(self, contract_manager, mock_client) -> None:
        """Test applying non-default contract."""
        mock_response = {"status": "SUCCESS"}
        mock_client.put.return_value = mock_response

        result = contract_manager.apply_contract(
            contract_id="contract-789", name="Secondary Contract", is_default=False
        )

        assert result == mock_response

        # Check defaultYn is "N"
        call_args = mock_client.put.call_args
        assert call_args[1]["json_data"]["defaultYn"] == "N"

    def test_apply_contract_default_name(self, contract_manager, mock_client) -> None:
        """Test applying contract with default name."""
        mock_response = {"status": "SUCCESS"}
        mock_client.put.return_value = mock_response

        result = contract_manager.apply_contract(contract_id="contract-999")

        assert result == mock_response

        # Check default name was used
        call_args = mock_client.put.call_args
        assert call_args[1]["json_data"]["name"] == "billing group default"

    def test_delete_contract_success(self, contract_manager, mock_client) -> None:
        """Test successful contract deletion."""
        mock_response = {"status": "DELETED"}
        mock_client.delete.return_value = mock_response

        result = contract_manager.delete_contract()

        assert result == mock_response

        # Verify API call
        mock_client.delete.assert_called_once_with(
            "billing/admin/billing-groups/billing-group-123/contracts",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )


# Additional test for edge cases
class TestContractEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch("libs.Contract.BillingAPIClient")
    def test_empty_billing_group_id(self, mock_client_class) -> None:
        """Test with empty billing group ID."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Should raise validation error
        with pytest.raises(ValidationException, match="Billing group ID cannot be empty"):
            ContractManager(month="2024-01", billing_group_id="")

    @patch("libs.Contract.BillingAPIClient")
    def test_long_contract_name(self, mock_client_class) -> None:
        """Test with very long contract name."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.put.return_value = {"status": "SUCCESS"}

        manager = ContractManager(month="2024-01", billing_group_id="bg-123")
        manager._client = mock_client

        long_name = "A" * 500  # Very long name
        result = manager.apply_contract(contract_id="contract-123", name=long_name)

        assert result["status"] == "SUCCESS"

        # Verify the long name was sent
        call_args = mock_client.put.call_args
        assert call_args[1]["json_data"]["name"] == long_name

    @patch("libs.Contract.BillingAPIClient")
    def test_special_characters_in_ids(self, mock_client_class) -> None:
        """Test with special characters in IDs."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.put.return_value = {"status": "SUCCESS"}

        # Billing group ID with special characters is allowed (no validation on format)
        special_bg_id = "bg-123/456#test"
        manager = ContractManager(month="2024-01", billing_group_id=special_bg_id)
        manager._client = mock_client

        # Now test contract ID with special characters
        special_contract_id = "contract@789!test"
        manager = ContractManager(month="2024-01", billing_group_id="bg-123")
        manager._client = mock_client

        with pytest.raises(ValidationException, match="Invalid contract ID format"):
            manager.apply_contract(contract_id=special_contract_id)
