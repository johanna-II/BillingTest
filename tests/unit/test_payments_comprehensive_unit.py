"""Comprehensive unit tests for payment management module."""

from unittest.mock import Mock

import pytest

from libs.constants import PaymentStatus
from libs.exceptions import APIRequestException, ValidationException
from libs.Payments import PaymentManager, PaymentStatement


class TestPaymentManagerComprehensiveUnit:
    """Comprehensive unit tests for PaymentManager class."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.payment_manager = PaymentManager(
            month="2024-01", uuid="test-uuid-123", client=self.mock_client
        )
        # Mock the PaymentAPI instance
        self.mock_api = Mock()
        self.payment_manager._client = self.mock_api

    def test_get_payment_group_id_from_admin_api(self) -> None:
        """Test getting payment group ID from admin API."""
        mock_response = {
            "statements": [
                {
                    "paymentGroupId": "pg-new-123",
                    "month": "2024-01",
                    "uuid": "test-uuid",
                    "paymentStatusCode": "PENDING",
                }
            ]
        }
        self.mock_api.get_statements_admin.return_value = mock_response

        pg_id, status = self.payment_manager.get_payment_status(use_admin_api=True)

        assert pg_id == "pg-new-123"
        assert status == PaymentStatus.PENDING
        self.mock_api.get_statements_admin.assert_called_once_with(
            "2024-01", "test-uuid-123"
        )

    def test_get_payment_group_id_from_console_api(self) -> None:
        """Test getting payment group ID from console API when admin API returns empty."""
        # Admin API returns empty
        self.mock_api.get_statements_admin.return_value = {"statements": []}

        # Console API returns data
        mock_console_response = {
            "statements": [
                {
                    "paymentGroupId": "pg-console-456",
                    "month": "2024-01",
                    "uuid": "test-uuid-123",
                    "paymentStatusCode": "PAID",
                }
            ]
        }
        self.mock_api.get_statements_console.return_value = mock_console_response

        pg_id, status = self.payment_manager.get_payment_status(use_admin_api=False)

        assert pg_id == "pg-console-456"
        assert status == PaymentStatus.PAID
        # Console API should be called
        assert self.mock_api.get_statements_console.called

    def test_get_payment_group_id_no_statements(self) -> None:
        """Test getting payment group ID when no statements exist."""
        self.mock_api.get_statements_admin.return_value = {"statements": []}
        self.mock_api.get_statements_console.return_value = {"statements": []}

        pg_id, status = self.payment_manager.get_payment_status()

        assert pg_id == ""
        assert status == PaymentStatus.UNKNOWN

    def test_get_payment_status_unpaid(self) -> None:
        """Test getting payment status for unpaid invoice."""
        mock_response = {
            "statements": [
                {
                    "paymentGroupId": "pg-123",
                    "paymentStatusCode": "PENDING",
                    "totalAmount": 1000.0,
                }
            ]
        }
        # Mock both admin and console APIs since default is console
        self.mock_api.get_statements_admin.return_value = mock_response
        self.mock_api.get_statements_console.return_value = mock_response

        pg_id, status = self.payment_manager.get_payment_status()

        assert pg_id == "pg-123"
        assert status == PaymentStatus.PENDING

    def test_get_payment_status_paid(self) -> None:
        """Test getting payment status for paid invoice."""
        mock_response = {
            "statements": [
                {
                    "paymentGroupId": "pg-123",
                    "paymentStatusCode": "PAID",
                    "totalAmount": 1000.0,
                }
            ]
        }
        # Mock both admin and console APIs since default is console
        self.mock_api.get_statements_admin.return_value = mock_response
        self.mock_api.get_statements_console.return_value = mock_response

        pg_id, status = self.payment_manager.get_payment_status()

        assert pg_id == "pg-123"
        assert status == PaymentStatus.PAID

    def test_get_payment_status_unknown(self) -> None:
        """Test getting payment status when no statements exist."""
        self.mock_api.get_statements_admin.return_value = {"statements": []}
        self.mock_api.get_statements_console.return_value = {"statements": []}

        pg_id, status = self.payment_manager.get_payment_status()

        assert pg_id == ""
        assert status == PaymentStatus.UNKNOWN

    def test_create_payment_record_success(self) -> None:
        """Test creating payment record successfully."""
        mock_response = {"paymentId": "payment-123", "status": "CREATED"}
        self.mock_api.create_payment.return_value = mock_response

        result = self.payment_manager.create_payment_record(
            payment_group_id="pg-123", amount=1000.0, payment_method="CREDIT_CARD"
        )

        assert result == mock_response
        self.mock_api.create_payment.assert_called_once_with(
            payment_group_id="pg-123", amount=1000.0, payment_method="CREDIT_CARD"
        )

    def test_create_payment_record_invalid_amount(self) -> None:
        """Test creating payment record with invalid amount."""
        with pytest.raises(ValidationException) as exc_info:
            self.payment_manager.create_payment_record(
                payment_group_id="pg-123",
                amount=-100.0,  # Negative amount
                payment_method="CREDIT_CARD",
            )

        assert "Amount must be positive" in str(exc_info.value)

    def test_update_payment_status_success(self) -> None:
        """Test updating payment status successfully."""
        mock_response = {"status": "UPDATED", "newStatus": "PAID"}
        self.mock_api.change_status.return_value = mock_response

        result = self.payment_manager.change_payment_status(
            payment_group_id="pg-123", target_status=PaymentStatus.PAID
        )

        assert result == mock_response
        self.mock_api.change_status.assert_called_once_with(
            "2024-01", "pg-123", PaymentStatus.PAID
        )

    def test_get_payment_details_success(self) -> None:
        """Test getting payment details successfully."""
        mock_details = {
            "paymentId": "payment-123",
            "amount": 1000.0,
            "status": "PAID",
            "paymentDate": "2024-01-15",
        }
        self.mock_api.get_payment_details.return_value = mock_details

        result = self.payment_manager.get_payment_details("payment-123")

        assert result == mock_details
        self.mock_api.get_payment_details.assert_called_once_with("payment-123")

    def test_process_refund_success(self) -> None:
        """Test processing refund successfully."""
        mock_response = {
            "refundId": "refund-123",
            "status": "REFUNDED",
            "refundAmount": 500.0,
        }
        self.mock_api.process_refund.return_value = mock_response

        result = self.payment_manager.process_refund(
            payment_id="payment-123", amount=500.0, reason="Customer request"
        )

        assert result == mock_response
        self.mock_api.process_refund.assert_called_once_with(
            payment_id="payment-123", amount=500.0, reason="Customer request"
        )

    def test_get_payment_history_success(self) -> None:
        """Test getting payment history successfully."""
        mock_history = [
            {
                "paymentId": "payment-1",
                "date": "2024-01-01",
                "amount": 1000.0,
                "status": "PAID",
            },
            {
                "paymentId": "payment-2",
                "date": "2024-01-15",
                "amount": 2000.0,
                "status": "PAID",
            },
        ]
        self.mock_api.get_payment_history.return_value = mock_history

        result = self.payment_manager.get_payment_history(
            payment_group_id="pg-123",  # Pass payment_group_id directly
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        assert result == mock_history
        assert len(result) == 2

    def test_validate_payment_amount(self) -> None:
        """Test payment amount validation."""
        # Valid amounts
        assert self.payment_manager.validate_payment_amount(100.0) is True
        assert self.payment_manager.validate_payment_amount(0.01) is True
        assert self.payment_manager.validate_payment_amount(999999.99) is True

        # Invalid amounts
        assert self.payment_manager.validate_payment_amount(0) is False
        assert self.payment_manager.validate_payment_amount(-100) is False
        assert self.payment_manager.validate_payment_amount(None) is False

    def test_calculate_late_fee(self) -> None:
        """Test late fee calculation."""
        # Basic late fee calculation
        fee = self.payment_manager.calculate_late_fee(amount=1000.0, days_late=10)

        # Assuming 0.1% per day
        expected_fee = 1000.0 * 0.001 * 10
        assert fee == expected_fee

        # No fee for on-time payment
        fee = self.payment_manager.calculate_late_fee(amount=1000.0, days_late=0)
        assert fee == 0.0

    def test_retry_failed_payment(self) -> None:
        """Test retrying failed payment."""
        # First attempt fails, second succeeds
        self.mock_api.retry_payment.side_effect = [
            APIRequestException("Payment failed"),
            {"status": "SUCCESS", "paymentId": "payment-retry-123"},
        ]

        result = self.payment_manager.retry_failed_payment(
            payment_id="payment-failed-123", max_retries=3
        )

        assert result is not None
        assert result["status"] == "SUCCESS"
        assert self.mock_api.retry_payment.call_count == 2

    def test_batch_payment_processing(self) -> None:
        """Test batch payment processing."""
        payment_requests = [
            {"payment_group_id": "pg-1", "amount": 1000.0},
            {"payment_group_id": "pg-2", "amount": 2000.0},
            {"payment_group_id": "pg-3", "amount": 3000.0},
        ]

        # Mock successful processing
        self.mock_api.process_batch_payments.return_value = {
            "processed": 3,
            "failed": 0,
            "results": [
                {"payment_group_id": "pg-1", "success": True},
                {"payment_group_id": "pg-2", "success": True},
                {"payment_group_id": "pg-3", "success": True},
            ],
        }

        result = self.payment_manager.process_batch_payments(payment_requests)

        assert result["processed"] == 3
        assert result["failed"] == 0
        assert all(r["success"] for r in result["results"])

    def test_payment_method_validation(self) -> None:
        """Test payment method validation."""
        valid_methods = ["CREDIT_CARD", "BANK_TRANSFER", "PAYPAL", "CASH"]
        invalid_methods = ["BITCOIN", "CHECK", "", None]

        for method in valid_methods:
            assert self.payment_manager.validate_payment_method(method) is True

        for method in invalid_methods:
            assert self.payment_manager.validate_payment_method(method) is False


class TestPaymentStatementDataclass:
    """Unit tests for PaymentStatement dataclass."""

    def test_from_api_response_complete_data(self) -> None:
        """Test creating PaymentStatement from complete API response."""
        api_data = {
            "paymentGroupId": "pg-123",
            "paymentStatusCode": "PAID",
            "totalAmount": 1500.50,
            "month": "2024-01",
            "uuid": "test-uuid-123",
        }

        statement = PaymentStatement.from_api_response(api_data)

        assert statement.payment_group_id == "pg-123"
        assert statement.payment_status == PaymentStatus.PAID
        assert statement.total_amount == 1500.50
        assert statement.month == "2024-01"
        assert statement.uuid == "test-uuid-123"

    def test_from_api_response_missing_fields(self) -> None:
        """Test creating PaymentStatement with missing optional fields."""
        api_data = {
            "paymentGroupId": "pg-456",
            "paymentStatusCode": "PENDING",
            # Missing totalAmount, month, uuid
        }

        statement = PaymentStatement.from_api_response(api_data)

        assert statement.payment_group_id == "pg-456"
        assert statement.payment_status == PaymentStatus.PENDING
        assert statement.total_amount == 0.0  # Default value
        assert statement.month == ""  # Default value
        assert statement.uuid == ""  # Default value

    def test_from_api_response_unknown_status(self) -> None:
        """Test creating PaymentStatement with unknown status code."""
        api_data = {"paymentGroupId": "pg-789", "paymentStatusCode": "INVALID_STATUS"}

        statement = PaymentStatement.from_api_response(api_data)

        assert statement.payment_status == PaymentStatus.UNKNOWN

    def test_payment_statement_equality(self) -> None:
        """Test PaymentStatement equality comparison."""
        statement1 = PaymentStatement(
            payment_group_id="pg-123",
            payment_status=PaymentStatus.PAID,
            total_amount=1000.0,
        )

        statement2 = PaymentStatement(
            payment_group_id="pg-123",
            payment_status=PaymentStatus.PAID,
            total_amount=1000.0,
        )

        statement3 = PaymentStatement(
            payment_group_id="pg-456",
            payment_status=PaymentStatus.PAID,
            total_amount=1000.0,
        )

        assert statement1 == statement2
        assert statement1 != statement3
