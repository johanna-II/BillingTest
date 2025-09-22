"""Comprehensive unit tests for payment management module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from libs.Payments import PaymentManager, Payments, PaymentStatement
from libs.constants import PaymentStatus
from libs.exceptions import APIRequestException, ValidationException


class TestPaymentManagerComprehensiveUnit:
    """Comprehensive unit tests for PaymentManager class."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.payment_manager = PaymentManager(month="2024-01", uuid="test-uuid-123", client=self.mock_client)
        yield
    
    def test_init(self):
        """Test PaymentManager initialization."""
        assert hasattr(self.payment_manager, '_api_client')
        assert hasattr(self.payment_manager, '_validator')
    
    def test_get_payment_group_id_from_admin_api(self):
        """Test getting payment group ID from admin API."""
        mock_response = [
            {
                "paymentGroupId": "pg-new-123",
                "month": "2024-01",
                "uuid": "test-uuid",
                "paymentStatusCode": "PENDING"
            }
        ]
        self.payment_manager._api_client.get_payment_statements_admin.return_value = mock_response
        
        pg_id = self.payment_manager.get_payment_group_id(
            uuid="test-uuid",
            month="2024-01"
        )
        
        assert pg_id == "pg-new-123"
        self.payment_manager._api_client.get_payment_statements_admin.assert_called_once_with(
            month="2024-01",
            uuid="test-uuid"
        )
    
    def test_get_payment_group_id_from_console_api(self):
        """Test getting payment group ID from console API when admin API returns empty."""
        # Admin API returns empty
        self.payment_manager._api_client.get_payment_statements_admin.return_value = []
        
        # Console API returns data
        mock_console_response = [
            {
                "paymentGroupId": "pg-console-456",
                "month": "2024-01",
                "uuid": "test-uuid",
                "paymentStatusCode": "PAID"
            }
        ]
        self.payment_manager._api_client.get_payment_statements_console.return_value = mock_console_response
        
        pg_id = self.payment_manager.get_payment_group_id(
            uuid="test-uuid",
            month="2024-01"
        )
        
        assert pg_id == "pg-console-456"
        # Both APIs should be called
        assert self.payment_manager._api_client.get_payment_statements_admin.called
        assert self.payment_manager._api_client.get_payment_statements_console.called
    
    def test_get_payment_group_id_no_statements(self):
        """Test getting payment group ID when no statements exist."""
        self.payment_manager._api_client.get_payment_statements_admin.return_value = []
        self.payment_manager._api_client.get_payment_statements_console.return_value = []
        
        pg_id = self.payment_manager.get_payment_group_id(
            uuid="test-uuid",
            month="2024-01"
        )
        
        assert pg_id == ""
    
    def test_get_payment_status_unpaid(self):
        """Test getting payment status for unpaid invoice."""
        mock_statements = [
            {
                "paymentGroupId": "pg-123",
                "paymentStatusCode": "PENDING",
                "totalAmount": 1000.0
            }
        ]
        self.payment_manager._api_client.get_payment_statements_admin.return_value = mock_statements
        
        status = self.payment_manager.get_payment_status(
            uuid="test-uuid",
            month="2024-01"
        )
        
        assert status == PaymentStatus.PENDING
    
    def test_get_payment_status_paid(self):
        """Test getting payment status for paid invoice."""
        mock_statements = [
            {
                "paymentGroupId": "pg-123",
                "paymentStatusCode": "PAID",
                "totalAmount": 1000.0
            }
        ]
        self.payment_manager._api_client.get_payment_statements_admin.return_value = mock_statements
        
        status = self.payment_manager.get_payment_status(
            uuid="test-uuid",
            month="2024-01"
        )
        
        assert status == PaymentStatus.PAID
    
    def test_get_payment_status_unknown(self):
        """Test getting payment status when no statements exist."""
        self.payment_manager._api_client.get_payment_statements_admin.return_value = []
        self.payment_manager._api_client.get_payment_statements_console.return_value = []
        
        status = self.payment_manager.get_payment_status(
            uuid="test-uuid",
            month="2024-01"
        )
        
        assert status == PaymentStatus.UNKNOWN
    
    def test_create_payment_record_success(self):
        """Test creating payment record successfully."""
        mock_response = {
            "paymentId": "payment-123",
            "status": "CREATED"
        }
        self.payment_manager._api_client.create_payment.return_value = mock_response
        
        result = self.payment_manager.create_payment_record(
            payment_group_id="pg-123",
            amount=1000.0,
            payment_method="CREDIT_CARD"
        )
        
        assert result == mock_response
        self.payment_manager._api_client.create_payment.assert_called_once_with(
            payment_group_id="pg-123",
            amount=1000.0,
            payment_method="CREDIT_CARD"
        )
    
    def test_create_payment_record_invalid_amount(self):
        """Test creating payment record with invalid amount."""
        with pytest.raises(ValidationException) as exc_info:
            self.payment_manager.create_payment_record(
                payment_group_id="pg-123",
                amount=-100.0,  # Negative amount
                payment_method="CREDIT_CARD"
            )
        
        assert "Amount must be positive" in str(exc_info.value)
    
    def test_update_payment_status_success(self):
        """Test updating payment status successfully."""
        mock_response = {
            "status": "UPDATED",
            "newStatus": "PAID"
        }
        self.payment_manager._api_client.update_payment_status.return_value = mock_response
        
        result = self.payment_manager.update_payment_status(
            payment_id="payment-123",
            new_status=PaymentStatus.PAID
        )
        
        assert result == mock_response
        self.payment_manager._api_client.update_payment_status.assert_called_once_with(
            payment_id="payment-123",
            status="PAID"
        )
    
    def test_get_payment_details_success(self):
        """Test getting payment details successfully."""
        mock_details = {
            "paymentId": "payment-123",
            "amount": 1000.0,
            "status": "PAID",
            "paymentDate": "2024-01-15"
        }
        self.payment_manager._api_client.get_payment_details.return_value = mock_details
        
        result = self.payment_manager.get_payment_details("payment-123")
        
        assert result == mock_details
        self.payment_manager._api_client.get_payment_details.assert_called_once_with("payment-123")
    
    def test_process_refund_success(self):
        """Test processing refund successfully."""
        mock_response = {
            "refundId": "refund-123",
            "status": "REFUNDED",
            "refundAmount": 500.0
        }
        self.payment_manager._api_client.process_refund.return_value = mock_response
        
        result = self.payment_manager.process_refund(
            payment_id="payment-123",
            amount=500.0,
            reason="Customer request"
        )
        
        assert result == mock_response
        self.payment_manager._api_client.process_refund.assert_called_once_with(
            payment_id="payment-123",
            amount=500.0,
            reason="Customer request"
        )
    
    def test_get_payment_history_success(self):
        """Test getting payment history successfully."""
        mock_history = [
            {
                "paymentId": "payment-1",
                "date": "2024-01-01",
                "amount": 1000.0,
                "status": "PAID"
            },
            {
                "paymentId": "payment-2",
                "date": "2024-01-15",
                "amount": 2000.0,
                "status": "PAID"
            }
        ]
        self.payment_manager._api_client.get_payment_history.return_value = mock_history
        
        result = self.payment_manager.get_payment_history(
            uuid="test-uuid",
            start_date="2024-01-01",
            end_date="2024-01-31"
        )
        
        assert result == mock_history
        assert len(result) == 2
    
    def test_validate_payment_amount(self):
        """Test payment amount validation."""
        # Valid amounts
        assert self.payment_manager.validate_payment_amount(100.0) is True
        assert self.payment_manager.validate_payment_amount(0.01) is True
        assert self.payment_manager.validate_payment_amount(999999.99) is True
        
        # Invalid amounts
        assert self.payment_manager.validate_payment_amount(0) is False
        assert self.payment_manager.validate_payment_amount(-100) is False
        assert self.payment_manager.validate_payment_amount(None) is False
    
    def test_calculate_late_fee(self):
        """Test late fee calculation."""
        # Basic late fee calculation
        fee = self.payment_manager.calculate_late_fee(
            amount=1000.0,
            days_late=10
        )
        
        # Assuming 0.1% per day
        expected_fee = 1000.0 * 0.001 * 10
        assert fee == expected_fee
        
        # No fee for on-time payment
        fee = self.payment_manager.calculate_late_fee(
            amount=1000.0,
            days_late=0
        )
        assert fee == 0.0
    
    def test_retry_failed_payment(self):
        """Test retrying failed payment."""
        # First attempt fails, second succeeds
        self.payment_manager._api_client.retry_payment.side_effect = [
            APIRequestException("Payment failed"),
            {"status": "SUCCESS", "paymentId": "payment-retry-123"}
        ]
        
        result = self.payment_manager.retry_failed_payment(
            payment_id="payment-failed-123",
            max_retries=3
        )
        
        assert result is not None
        assert result["status"] == "SUCCESS"
        assert self.payment_manager._api_client.retry_payment.call_count == 2
    
    def test_batch_payment_processing(self):
        """Test batch payment processing."""
        payment_requests = [
            {"payment_group_id": "pg-1", "amount": 1000.0},
            {"payment_group_id": "pg-2", "amount": 2000.0},
            {"payment_group_id": "pg-3", "amount": 3000.0}
        ]
        
        # Mock successful processing
        self.payment_manager._api_client.process_batch_payments.return_value = {
            "processed": 3,
            "failed": 0,
            "results": [
                {"payment_group_id": "pg-1", "success": True},
                {"payment_group_id": "pg-2", "success": True},
                {"payment_group_id": "pg-3", "success": True}
            ]
        }
        
        result = self.payment_manager.process_batch_payments(payment_requests)
        
        assert result["processed"] == 3
        assert result["failed"] == 0
        assert all(r["success"] for r in result["results"])
    
    def test_error_handling_api_error(self):
        """Test error handling for API errors."""
        self.payment_manager._api_client.get_payment_statements_admin.side_effect = APIRequestException("API Error")
        
        with pytest.raises(APIRequestException) as exc_info:
            self.payment_manager.get_payment_group_id("test-uuid", "2024-01")
        
        assert "API Error" in str(exc_info.value)
    
    def test_payment_method_validation(self):
        """Test payment method validation."""
        valid_methods = ["CREDIT_CARD", "BANK_TRANSFER", "PAYPAL", "CASH"]
        invalid_methods = ["BITCOIN", "CHECK", "", None]
        
        for method in valid_methods:
            assert self.payment_manager.validate_payment_method(method) is True
        
        for method in invalid_methods:
            assert self.payment_manager.validate_payment_method(method) is False
    
    @patch('libs.Payments.logger')
    def test_logging_on_operations(self, mock_logger):
        """Test that operations are properly logged."""
        self.payment_manager._api_client.get_payment_statements_admin.return_value = []
        self.payment_manager._api_client.get_payment_statements_console.return_value = []
        
        self.payment_manager.get_payment_group_id("test-uuid", "2024-01")
        
        # Verify logging occurred
        assert mock_logger.warning.called  # Should log warning when no statements found


class TestPaymentStatementDataclass:
    """Unit tests for PaymentStatement dataclass."""
    
    def test_from_api_response_complete_data(self):
        """Test creating PaymentStatement from complete API response."""
        api_data = {
            "paymentGroupId": "pg-123",
            "paymentStatusCode": "PAID",
            "totalAmount": 1500.50,
            "month": "2024-01",
            "uuid": "test-uuid-123"
        }
        
        statement = PaymentStatement.from_api_response(api_data)
        
        assert statement.payment_group_id == "pg-123"
        assert statement.payment_status == PaymentStatus.PAID
        assert statement.total_amount == 1500.50
        assert statement.month == "2024-01"
        assert statement.uuid == "test-uuid-123"
    
    def test_from_api_response_missing_fields(self):
        """Test creating PaymentStatement with missing optional fields."""
        api_data = {
            "paymentGroupId": "pg-456",
            "paymentStatusCode": "PENDING"
            # Missing totalAmount, month, uuid
        }
        
        statement = PaymentStatement.from_api_response(api_data)
        
        assert statement.payment_group_id == "pg-456"
        assert statement.payment_status == PaymentStatus.PENDING
        assert statement.total_amount == 0.0  # Default value
        assert statement.month == ""  # Default value
        assert statement.uuid == ""  # Default value
    
    def test_from_api_response_unknown_status(self):
        """Test creating PaymentStatement with unknown status code."""
        api_data = {
            "paymentGroupId": "pg-789",
            "paymentStatusCode": "INVALID_STATUS"
        }
        
        statement = PaymentStatement.from_api_response(api_data)
        
        assert statement.payment_status == PaymentStatus.UNKNOWN
    
    def test_payment_statement_equality(self):
        """Test PaymentStatement equality comparison."""
        statement1 = PaymentStatement(
            payment_group_id="pg-123",
            payment_status=PaymentStatus.PAID,
            total_amount=1000.0
        )
        
        statement2 = PaymentStatement(
            payment_group_id="pg-123",
            payment_status=PaymentStatus.PAID,
            total_amount=1000.0
        )
        
        statement3 = PaymentStatement(
            payment_group_id="pg-456",
            payment_status=PaymentStatus.PAID,
            total_amount=1000.0
        )
        
        assert statement1 == statement2
        assert statement1 != statement3


class TestPaymentsLegacyWrapper:
    """Unit tests for legacy Payments wrapper."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        with patch('libs.Payments.PaymentManager') as mock_manager_class:
            self.mock_manager = Mock()
            mock_manager_class.return_value = self.mock_manager
            self.payments = Payments(month="2024-01")
            yield
    
    def test_init_legacy(self):
        """Test legacy Payments initialization."""
        assert self.payments.month == "2024-01"
        assert hasattr(self.payments, '_manager')
    
    def test_get_payment_group_id_legacy(self):
        """Test legacy get_payment_group_id method."""
        self.mock_manager.get_payment_group_id.return_value = "pg-legacy-123"
        
        pg_id = self.payments.get_payment_group_id()
        
        assert pg_id == "pg-legacy-123"
        self.mock_manager.get_payment_group_id.assert_called_once_with(
            uuid="test-uuid",
            month="2024-01"
        )
    
    def test_inquire_payment_status_legacy_unpaid(self):
        """Test legacy inquire_payment_status for unpaid invoice."""
        self.mock_manager.get_payment_group_id.return_value = "pg-123"
        self.mock_manager.get_payment_status.return_value = PaymentStatus.PENDING
        
        pg_id, status = self.payments.inquire_payment_status()
        
        assert pg_id == "pg-123"
        assert status == "PENDING"
    
    def test_inquire_payment_status_legacy_paid(self):
        """Test legacy inquire_payment_status for paid invoice."""
        self.mock_manager.get_payment_group_id.return_value = "pg-456"
        self.mock_manager.get_payment_status.return_value = PaymentStatus.PAID
        
        pg_id, status = self.payments.inquire_payment_status()
        
        assert pg_id == "pg-456"
        assert status == "PAID"
    
    def test_inquire_payment_status_legacy_no_payment_group(self):
        """Test legacy inquire_payment_status when no payment group exists."""
        self.mock_manager.get_payment_group_id.return_value = ""
        
        pg_id, status = self.payments.inquire_payment_status()
        
        assert pg_id == ""
        assert status == ""
    
    def test_inquire_payment_status_legacy_exception_handling(self):
        """Test legacy inquire_payment_status exception handling."""
        self.mock_manager.get_payment_group_id.side_effect = Exception("Test error")
        
        pg_id, status = self.payments.inquire_payment_status()
        
        assert pg_id == ""
        assert status == ""