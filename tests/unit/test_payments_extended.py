"""Extended unit tests for Payments module to improve coverage."""

from unittest.mock import Mock

import pytest

from libs.constants import PaymentStatus
from libs.exceptions import APIRequestException, ValidationException
from libs.payment_api_client import PaymentAPIClient
from libs.Payments import PaymentManager, PaymentValidator


class TestPaymentsExtended:
    """Extended tests to improve Payments module coverage."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_client = Mock(spec=PaymentAPIClient)
        self.payment_manager = PaymentManager(
            month="2024-01", uuid="test-uuid-123", client=self.mock_client
        )

    def test_repr(self) -> None:
        """Test __repr__ method."""
        repr_str = repr(self.payment_manager)
        assert repr_str == "PaymentManager(month='2024-01', uuid='test-uuid-123')"

    def test_context_manager(self) -> None:
        """Test context manager functionality."""
        # Test without close method
        with PaymentManager("2024-01", "test-uuid", client=self.mock_client) as pm:
            assert pm is not None

        # Test with close method
        self.mock_client.close = Mock()
        with PaymentManager("2024-01", "test-uuid", client=self.mock_client) as pm:
            assert pm is not None
        self.mock_client.close.assert_called_once()

    def test_payment_validator_invalid_month_format(self) -> None:
        """Test PaymentValidator with invalid month format."""
        with pytest.raises(ValidationException) as exc_info:
            PaymentValidator.validate_month_format("2024/01")
        assert "Invalid month format" in str(exc_info.value)

        with pytest.raises(ValidationException) as exc_info:
            PaymentValidator.validate_month_format("2024-13")  # Invalid month
        assert "Invalid month format" in str(exc_info.value)

    def test_payment_validator_empty_payment_group_id(self) -> None:
        """Test PaymentValidator with empty payment group ID."""
        with pytest.raises(ValidationException) as exc_info:
            PaymentValidator.validate_payment_group_id("")
        assert "Payment group ID cannot be empty" in str(exc_info.value)

        with pytest.raises(ValidationException) as exc_info:
            PaymentValidator.validate_payment_group_id("   ")
        assert "Payment group ID cannot be empty" in str(exc_info.value)

    def test_get_payment_status_api_exception(self) -> None:
        """Test get_payment_status when API request fails."""
        self.mock_client.get_statements_console.side_effect = APIRequestException(
            "API error"
        )

        with pytest.raises(APIRequestException) as exc_info:
            self.payment_manager.get_payment_status()
        assert "API error" in str(exc_info.value)

    def test_change_payment_status_api_exception(self) -> None:
        """Test change_payment_status when API request fails."""
        self.mock_client.change_status.side_effect = APIRequestException(
            "Change failed"
        )

        with pytest.raises(APIRequestException) as exc_info:
            self.payment_manager.change_payment_status(
                "pg-123", PaymentStatus.REGISTERED
            )
        assert "Change failed" in str(exc_info.value)

    def test_prepare_payment_no_payment(self) -> None:
        """Test prepare_payment when no payment found."""
        self.mock_client.get_statements_console.return_value = {"statements": []}

        with pytest.raises(ValidationException) as exc_info:
            self.payment_manager.prepare_payment()
        assert "No payment found" in str(exc_info.value)

    def test_prepare_payment_paid(self) -> None:
        """Test prepare_payment with PAID status."""
        # Mock get_payment_status
        self.mock_client.get_statements_console.return_value = {
            "statements": [{"paymentGroupId": "pg-123", "paymentStatusCode": "PAID"}]
        }

        # Mock cancel and change status
        self.mock_client.cancel_payment.return_value = {"status": "CANCELLED"}
        self.mock_client.change_status.return_value = {"status": "CHANGED"}

        pg_id, status = self.payment_manager.prepare_payment()

        assert pg_id == "pg-123"
        assert status == PaymentStatus.REGISTERED
        self.mock_client.cancel_payment.assert_called_once()
        self.mock_client.change_status.assert_called_once()

    def test_prepare_payment_ready(self) -> None:
        """Test prepare_payment with READY status."""
        self.mock_client.get_statements_console.return_value = {
            "statements": [{"paymentGroupId": "pg-123", "paymentStatusCode": "READY"}]
        }
        self.mock_client.change_status.return_value = {"status": "CHANGED"}

        pg_id, status = self.payment_manager.prepare_payment()

        assert pg_id == "pg-123"
        assert status == PaymentStatus.REGISTERED
        self.mock_client.change_status.assert_called_once()

    def test_prepare_payment_registered(self) -> None:
        """Test prepare_payment with REGISTERED status."""
        self.mock_client.get_statements_console.return_value = {
            "statements": [
                {"paymentGroupId": "pg-123", "paymentStatusCode": "REGISTERED"}
            ]
        }

        pg_id, status = self.payment_manager.prepare_payment()

        assert pg_id == "pg-123"
        assert status == PaymentStatus.REGISTERED
        # No status change should be called
        self.mock_client.change_status.assert_not_called()

    def test_prepare_payment_unknown(self) -> None:
        """Test prepare_payment with unknown status."""
        self.mock_client.get_statements_console.return_value = {
            "statements": [
                {"paymentGroupId": "pg-123", "paymentStatusCode": "UNKNOWN_STATUS"}
            ]
        }

        pg_id, status = self.payment_manager.prepare_payment()

        assert pg_id == "pg-123"
        assert status == PaymentStatus.UNKNOWN

    def test_get_payment_summary(self) -> None:
        """Test get_payment_summary method."""
        # Mock payment status
        self.mock_client.get_statements_console.return_value = {
            "statements": [{"paymentGroupId": "pg-123", "paymentStatusCode": "READY"}]
        }
        # Mock unpaid amount
        self.mock_client.get_unpaid_statements.return_value = {
            "statements": [{"billingDetails": {"charge": 1000.0}}]
        }

        summary = self.payment_manager.get_payment_summary()

        assert summary["month"] == "2024-01"
        assert summary["uuid"] == "test-uuid-123"
        assert summary["payment_group_id"] == "pg-123"
        assert summary["status"] == "READY"
        assert summary["status_code"] == "READY"
        assert summary["unpaid_amount"] == 1000.0
        assert summary["is_paid"] is False
        assert summary["is_ready"] is True
        assert summary["is_registered"] is False

    def test_check_unpaid_amount(self) -> None:
        """Test check_unpaid_amount legacy method."""
        self.mock_client.get_unpaid_statements.return_value = {
            "statements": [{"billingDetails": {"charge": 500.0}}]
        }

        amount = self.payment_manager.check_unpaid_amount("pg-123")

        assert amount == 500.0
        self.mock_client.get_unpaid_statements.assert_called_once()

    def test_get_payment_statement(self) -> None:
        """Test get_payment_statement legacy method."""
        mock_response = {"statements": [{"charge": 1000.0, "totalAmount": 1000.0}]}

        # Mock the get method on _client._client
        self.mock_client.get = Mock(return_value=mock_response)

        result = self.payment_manager.get_payment_statement()

        assert result == mock_response
        self.mock_client.get.assert_called_once_with(
            "billing/console/statements",
            params={"uuid": "test-uuid-123", "month": "2024-01"},
        )

    def test_get_payment_statement_exception(self) -> None:
        """Test get_payment_statement when exception occurs."""
        self.mock_client.get = Mock(side_effect=Exception("API error"))

        result = self.payment_manager.get_payment_statement()

        assert result == {"statements": []}

    def test_process_refund_invalid_amount(self) -> None:
        """Test process_refund with invalid amount."""
        with pytest.raises(ValidationException) as exc_info:
            self.payment_manager.process_refund("pay-123", -100.0)
        assert "Refund amount must be positive" in str(exc_info.value)

        with pytest.raises(ValidationException) as exc_info:
            self.payment_manager.process_refund("pay-123", 0)
        assert "Refund amount must be positive" in str(exc_info.value)

    def test_get_payment_history_with_payment_status(self) -> None:
        """Test get_payment_history when payment_group_id not provided."""
        # Mock payment status to return payment group ID
        self.mock_client.get_statements_console.return_value = {
            "statements": [
                {"paymentGroupId": "pg-123", "paymentStatusCode": "REGISTERED"}
            ]
        }

        # Mock payment history
        self.mock_client.get_payment_history.return_value = [
            {"paymentId": "pay-001", "amount": 1000.0}
        ]

        history = self.payment_manager.get_payment_history()

        assert len(history) == 1
        assert history[0]["paymentId"] == "pay-001"
        self.mock_client.get_payment_history.assert_called_once_with(
            payment_group_id="pg-123", start_date=None, end_date=None
        )

    def test_validate_payment_amount(self) -> None:
        """Test validate_payment_amount method."""
        assert self.payment_manager.validate_payment_amount(100.0) is True
        assert self.payment_manager.validate_payment_amount(0.01) is True
        assert self.payment_manager.validate_payment_amount(1000000.0) is True
        assert self.payment_manager.validate_payment_amount(0) is False
        assert self.payment_manager.validate_payment_amount(-100.0) is False
        assert self.payment_manager.validate_payment_amount(1000001.0) is False
        assert self.payment_manager.validate_payment_amount(None) is False

        # Test with custom limits
        assert (
            self.payment_manager.validate_payment_amount(
                50, min_amount=10, max_amount=100
            )
            is True
        )
        assert (
            self.payment_manager.validate_payment_amount(
                5, min_amount=10, max_amount=100
            )
            is False
        )

    def test_calculate_late_fee(self) -> None:
        """Test calculate_late_fee method."""
        fee = self.payment_manager.calculate_late_fee(1000.0, 10)
        assert fee == 10.0  # 1000 * 0.001 * 10

        fee = self.payment_manager.calculate_late_fee(1000.0, 10, fee_rate=0.002)
        assert fee == 20.0  # 1000 * 0.002 * 10

        fee = self.payment_manager.calculate_late_fee(1000.0, 0)
        assert fee == 0.0

    def test_retry_failed_payment(self) -> None:
        """Test retry_failed_payment method."""
        # Test successful retry
        self.mock_client.retry_payment.return_value = {"status": "SUCCESS"}

        result = self.payment_manager.retry_failed_payment("pay-123")

        assert result == {"status": "SUCCESS"}
        self.mock_client.retry_payment.assert_called_once_with(
            payment_id="pay-123", retry_count=1
        )

        # Test with custom max retries
        self.mock_client.retry_payment.side_effect = [
            APIRequestException("Retry failed"),
            APIRequestException("Retry failed"),
            {"status": "SUCCESS"},
        ]

        result = self.payment_manager.retry_failed_payment("pay-123", max_retries=3)

        assert result == {"status": "SUCCESS"}
        assert (
            self.mock_client.retry_payment.call_count == 4
        )  # 1 from previous + 3 from this test

    def test_retry_failed_payment_all_fail(self) -> None:
        """Test retry_failed_payment when all retries fail."""
        self.mock_client.retry_payment.side_effect = APIRequestException("Retry failed")

        with pytest.raises(APIRequestException) as exc_info:
            self.payment_manager.retry_failed_payment("pay-123", max_retries=2)

        assert "Retry failed" in str(exc_info.value)

    def test_process_batch_payments(self) -> None:
        """Test process_batch_payments method."""
        payment_requests = [
            {"paymentId": "pay-001", "amount": 100.0},
            {"paymentId": "pay-002", "amount": 200.0},
        ]

        self.mock_client.process_batch_payments.return_value = {
            "processed": 2,
            "failed": 0,
        }

        result = self.payment_manager.process_batch_payments(payment_requests)

        assert result["processed"] == 2
        assert result["failed"] == 0
        self.mock_client.process_batch_payments.assert_called_once_with(
            payment_requests
        )

    def test_validate_payment_method(self) -> None:
        """Test validate_payment_method."""
        assert self.payment_manager.validate_payment_method("CREDIT_CARD") is True
        assert self.payment_manager.validate_payment_method("BANK_TRANSFER") is True
        assert self.payment_manager.validate_payment_method("INVALID_METHOD") is False
        assert self.payment_manager.validate_payment_method("") is False
        assert self.payment_manager.validate_payment_method(None) is False

    def test_make_payment_with_retries(self) -> None:
        """Test make_payment with retry logic."""
        # Test immediate success
        self.mock_client.make_payment.return_value = {"status": "SUCCESS"}

        result = self.payment_manager.make_payment("pg-123")

        assert result == {"status": "SUCCESS"}
        self.mock_client.make_payment.assert_called_once()

        # Reset mock
        self.mock_client.reset_mock()

        # Test retry on exception with eventual success
        self.mock_client.make_payment.side_effect = [
            APIRequestException("Payment failed"),
            {"status": "SUCCESS"},
        ]

        result = self.payment_manager.make_payment("pg-123", retry_on_failure=True)

        assert result == {"status": "SUCCESS"}
        assert self.mock_client.make_payment.call_count == 2

    def test_make_payment_all_retries_fail(self) -> None:
        """Test make_payment when all retries fail."""
        self.mock_client.make_payment.side_effect = APIRequestException(
            "Payment failed"
        )

        with pytest.raises(APIRequestException):
            self.payment_manager.make_payment(
                "pg-123", retry_on_failure=True, max_retries=2
            )

    def test_make_payment_no_retry(self) -> None:
        """Test make_payment with retry disabled."""
        self.mock_client.make_payment.side_effect = APIRequestException(
            "Payment failed"
        )

        with pytest.raises(APIRequestException):
            self.payment_manager.make_payment("pg-123", retry_on_failure=False)

    def test_cancel_payment_api_exception(self) -> None:
        """Test cancel_payment when API fails."""
        self.mock_client.cancel_payment.side_effect = APIRequestException(
            "Cancel failed"
        )

        with pytest.raises(APIRequestException) as exc_info:
            self.payment_manager.cancel_payment("pg-123")
        assert "Cancel failed" in str(exc_info.value)
