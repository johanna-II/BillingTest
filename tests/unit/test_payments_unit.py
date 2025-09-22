"""Unit tests for PaymentManager to improve coverage."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from libs.Payments import PaymentManager
from libs.exceptions import APIRequestException, ValidationException
from libs.constants import PaymentStatus


class TestPaymentManagerUnit:
    """Unit tests for PaymentManager class."""

    @pytest.fixture
    def mock_client(self):
        """Mock HTTP client."""
        return Mock()

    @pytest.fixture
    def payment_manager(self, mock_client):
        """Create PaymentManager with mocked dependencies."""
        with patch('libs.Payments.BillingAPIClient', return_value=mock_client):
            manager = PaymentManager(month="2024-01", uuid="test-uuid-123")
            manager._client = mock_client
            return manager

    def test_init(self):
        """Test PaymentManager initialization."""
        manager = PaymentManager(month="2024-01", uuid="test-uuid")
        assert manager.month == "2024-01"
        assert manager.uuid == "test-uuid"
        assert hasattr(manager, '_client')

    def test_get_payment_status_console_api(self, payment_manager, mock_client):
        """Test payment status retrieval using console API."""
        mock_response = {
            "statements": [
                {"paymentGroupId": "pg-123", "paymentStatusCode": "REGISTERED"}
            ]
        }
        mock_client.get.return_value = mock_response

        payment_id, status = payment_manager.get_payment_status(use_admin_api=False)
        
        assert payment_id == "pg-123"
        assert status == PaymentStatus.REGISTERED
        mock_client.get.assert_called_once()

    def test_get_payment_status_admin_api(self, payment_manager, mock_client):
        """Test payment status retrieval using admin API."""
        mock_response = {
            "statements": [
                {"paymentGroupId": "pg-123", "paymentStatusCode": "PAID"}
            ]
        }
        mock_client.get.return_value = mock_response

        payment_id, status = payment_manager.get_payment_status(use_admin_api=True)
        
        assert payment_id == "pg-123"
        assert status == PaymentStatus.PAID

    def test_get_payment_status_no_payments(self, payment_manager, mock_client):
        """Test payment status when no payments exist."""
        mock_client.get.return_value = {"statements": []}
        
        payment_id, status = payment_manager.get_payment_status()
        
        assert payment_id == ""
        assert status == PaymentStatus.UNKNOWN

    def test_get_payment_status_with_payment(self, payment_manager, mock_client):
        """Test payment status retrieval."""
        mock_response = {
            "statements": [{
                "paymentGroupId": "pg-123",
                "paymentStatusCode": "PAID"
            }]
        }
        mock_client.get.return_value = mock_response
        
        payment_id, status = payment_manager.get_payment_status()
        
        # Should return values from the payment list
        assert payment_id == "pg-123"
        assert status == PaymentStatus.PAID

    def test_change_payment_status_success(self, payment_manager, mock_client):
        """Test successful payment status change."""
        mock_response = {"status": "REGISTERED"}
        mock_client.put.return_value = mock_response
        
        result = payment_manager.change_payment_status("pg-123")
        
        assert result == mock_response
        mock_client.put.assert_called_once()

    def test_cancel_payment_success(self, payment_manager, mock_client):
        """Test successful payment cancellation."""
        mock_response = {"status": "CANCELLED"}
        mock_client.delete.return_value = mock_response
        
        result = payment_manager.cancel_payment("pg-123")
        
        assert result == mock_response
        mock_client.delete.assert_called_once()

    def test_make_payment_success(self, payment_manager, mock_client):
        """Test successful payment."""
        mock_response = {"paymentId": "pay-123", "status": "PAID"}
        mock_client.post.return_value = mock_response
        
        result = payment_manager.make_payment("pg-123")
        
        assert result == mock_response
        mock_client.post.assert_called_once()

    def test_make_payment_with_retry(self, payment_manager, mock_client):
        """Test payment with retry on failure."""
        # First attempt fails, second succeeds
        mock_client.post.side_effect = [
            APIRequestException("Network error"),
            {"paymentId": "pay-123", "status": "PAID"}
        ]
        
        result = payment_manager.make_payment("pg-123", retry_on_failure=True)
        
        assert result == {"paymentId": "pay-123", "status": "PAID"}
        assert mock_client.post.call_count == 2

    def test_make_payment_max_retries_exceeded(self, payment_manager, mock_client):
        """Test payment failure after max retries."""
        mock_client.post.side_effect = APIRequestException("Network error")
        
        with pytest.raises(APIRequestException):
            payment_manager.make_payment("pg-123", retry_on_failure=True, max_retries=2)
        
        assert mock_client.post.call_count == 2

    def test_check_unpaid_amount(self, payment_manager, mock_client):
        """Test unpaid amount calculation."""
        mock_client.get.return_value = {
            "statements": [
                {"totalAmount": 30000}
            ]
        }
        
        unpaid_amount = payment_manager.check_unpaid()
        
        assert unpaid_amount == 30000

    def test_payment_status_validation(self, payment_manager):
        """Test payment status validation."""
        # This tests the enum validation
        valid_statuses = ["PAID", "READY", "REGISTERED", "CANCELLED"]
        for status in valid_statuses:
            # Should not raise exception
            assert status in [s.value for s in PaymentStatus]

    @patch('libs.Payments.logger')
    def test_logging_on_operations(self, mock_logger, payment_manager, mock_client):
        """Test that operations are properly logged."""
        mock_client.get.return_value = {"list": []}
        
        payment_manager.get_payment_status()
        
        # Should log warning for no payments found
        mock_logger.warning.assert_called()

    def test_error_handling_in_cancel_payment(self, payment_manager, mock_client):
        """Test error handling in cancel payment."""
        mock_client.delete.side_effect = APIRequestException("Cannot cancel")
        
        with pytest.raises(APIRequestException):
            payment_manager.cancel_payment("pg-123")
        
        mock_client.delete.assert_called_once()

    def test_validate_month_format(self):
        """Test month format validation."""
        # Valid format
        manager = PaymentManager(month="2024-01", uuid="test")
        assert manager.month == "2024-01"
        
        # Should accept various formats (if implementation allows)
        manager = PaymentManager(month="2024-12", uuid="test")
        assert manager.month == "2024-12"
