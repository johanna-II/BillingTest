"""Unit tests for PaymentManager to improve coverage."""

from unittest.mock import Mock, patch

import pytest

from libs.constants import PaymentStatus
from libs.exceptions import APIRequestException
from libs.Payments import PaymentManager


class TestPaymentManagerUnit:
    """Unit tests for PaymentManager class."""

    @pytest.fixture
    def mock_client(self):
        """Mock HTTP client."""
        return Mock()

    @pytest.fixture
    def payment_manager(self, mock_client):
        """Create PaymentManager with mocked dependencies."""
        with patch("libs.Payments.PaymentAPIClient", return_value=mock_client):
            manager = PaymentManager(month="2024-01", uuid="test-uuid-123")
            manager._client = mock_client
            return manager

    def test_get_payment_status_console_api(self, payment_manager, mock_client) -> None:
        """Test payment status retrieval using console API."""
        mock_response = {
            "statements": [
                {"paymentGroupId": "pg-123", "paymentStatusCode": "REGISTERED"}
            ]
        }
        mock_client.get_statements_console.return_value = mock_response

        payment_id, status = payment_manager.get_payment_status(use_admin_api=False)

        assert payment_id == "pg-123"
        assert status == PaymentStatus.REGISTERED
        mock_client.get_statements_console.assert_called_once()

    def test_get_payment_status_admin_api(self, payment_manager, mock_client) -> None:
        """Test payment status retrieval using admin API."""
        mock_response = {
            "statements": [{"paymentGroupId": "pg-123", "paymentStatusCode": "PAID"}]
        }
        mock_client.get_statements_admin.return_value = mock_response

        payment_id, status = payment_manager.get_payment_status(use_admin_api=True)

        assert payment_id == "pg-123"
        assert status == PaymentStatus.PAID

    def test_get_payment_status_no_payments(self, payment_manager, mock_client) -> None:
        """Test payment status when no payments exist."""
        mock_client.get_statements_admin.return_value = {"statements": []}
        mock_client.get_statements_console.return_value = {"statements": []}

        payment_id, status = payment_manager.get_payment_status()

        assert payment_id == ""
        assert status == PaymentStatus.UNKNOWN

    def test_get_payment_status_with_payment(
        self, payment_manager, mock_client
    ) -> None:
        """Test payment status retrieval."""
        mock_response = {
            "statements": [{"paymentGroupId": "pg-123", "paymentStatusCode": "PAID"}]
        }
        mock_client.get_statements_admin.return_value = mock_response
        mock_client.get_statements_console.return_value = mock_response

        payment_id, status = payment_manager.get_payment_status()

        # Should return values from the payment list
        assert payment_id == "pg-123"
        assert status == PaymentStatus.PAID

    def test_change_payment_status_success(self, payment_manager, mock_client) -> None:
        """Test successful payment status change."""
        mock_response = {"status": "REGISTERED"}
        mock_client.change_status.return_value = mock_response

        result = payment_manager.change_payment_status("pg-123")

        assert result == mock_response
        mock_client.change_status.assert_called_once()

    def test_cancel_payment_success(self, payment_manager, mock_client) -> None:
        """Test successful payment cancellation."""
        mock_response = {"status": "CANCELLED"}
        mock_client.cancel_payment.return_value = mock_response

        result = payment_manager.cancel_payment("pg-123")

        assert result == mock_response
        mock_client.cancel_payment.assert_called_once()

    def test_make_payment_success(self, payment_manager, mock_client) -> None:
        """Test successful payment."""
        mock_response = {"paymentId": "pay-123", "status": "PAID"}
        mock_client.make_payment.return_value = mock_response

        result = payment_manager.make_payment("pg-123")

        assert result == mock_response
        mock_client.make_payment.assert_called_once()

    def test_make_payment_with_retry(self, payment_manager, mock_client) -> None:
        """Test payment with retry on failure."""
        # First attempt fails, second succeeds
        mock_client.make_payment.side_effect = [
            APIRequestException("Network error"),
            {"paymentId": "pay-123", "status": "PAID"},
        ]

        result = payment_manager.make_payment("pg-123", retry_on_failure=True)

        assert result == {"paymentId": "pay-123", "status": "PAID"}
        assert mock_client.make_payment.call_count == 2

    def test_make_payment_max_retries_exceeded(
        self, payment_manager, mock_client
    ) -> None:
        """Test payment failure after max retries."""
        mock_client.make_payment.side_effect = APIRequestException("Network error")

        with pytest.raises(APIRequestException):
            payment_manager.make_payment("pg-123", retry_on_failure=True, max_retries=2)

        assert mock_client.make_payment.call_count == 2

    def test_check_unpaid_amount(self, payment_manager, mock_client) -> None:
        """Test unpaid amount calculation."""
        mock_client.get_unpaid_statements.return_value = {
            "statements": [{"totalAmount": 30000}]
        }

        unpaid_amount = payment_manager.check_unpaid()

        assert unpaid_amount == 30000

    def test_payment_status_validation(self, payment_manager) -> None:
        """Test payment status validation."""
        # This tests the enum validation
        valid_statuses = ["PAID", "READY", "REGISTERED", "CANCELLED"]
        for status in valid_statuses:
            # Should not raise exception
            assert status in [s.value for s in PaymentStatus]

    def test_error_handling_in_cancel_payment(
        self, payment_manager, mock_client
    ) -> None:
        """Test error handling in cancel payment."""
        mock_client.cancel_payment.side_effect = APIRequestException("Cannot cancel")

        with pytest.raises(APIRequestException):
            payment_manager.cancel_payment("pg-123")

        mock_client.cancel_payment.assert_called_once()
