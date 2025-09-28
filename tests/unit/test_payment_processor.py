"""Unit tests for PaymentProcessor - complex payment processing logic."""

from decimal import Decimal

from libs.constants import PaymentStatus
from libs.payment_processor import (
    PaymentMethod,
    PaymentProcessor,
    PaymentRequest,
    PaymentResult,
    ProcessingStatus,
    RetryPolicy,
)


class TestPaymentProcessor:
    """Unit tests for payment processing logic."""

    def test_calculate_processing_fee_bank_transfer(self):
        """Test processing fee calculation for bank transfer."""
        fees = PaymentProcessor.calculate_processing_fee(
            amount=Decimal("100000"),
            payment_method=PaymentMethod.BANK_TRANSFER,
            include_tax=True,
        )

        # 0.1% + 100 KRW fixed fee
        assert fees["percentage_fee"] == Decimal("100.00")  # 100000 * 0.001
        assert fees["fixed_fee"] == Decimal("100")
        assert fees["subtotal_fee"] == Decimal("200.00")
        assert fees["tax_amount"] == Decimal("20.00")  # 10% VAT
        assert fees["total_fee"] == Decimal("220.00")
        assert fees["net_amount"] == Decimal("99780.00")

    def test_calculate_processing_fee_credit_card(self):
        """Test processing fee calculation for credit card."""
        fees = PaymentProcessor.calculate_processing_fee(
            amount=Decimal("50000"),
            payment_method=PaymentMethod.CREDIT_CARD,
            include_tax=True,
        )

        # 2.9% + 0 KRW fixed fee
        assert fees["percentage_fee"] == Decimal("1450.00")  # 50000 * 0.029
        assert fees["fixed_fee"] == Decimal("0")
        assert fees["subtotal_fee"] == Decimal("1450.00")
        assert fees["tax_amount"] == Decimal("145.00")  # 10% VAT
        assert fees["total_fee"] == Decimal("1595.00")
        assert fees["net_amount"] == Decimal("48405.00")

    def test_calculate_processing_fee_without_tax(self):
        """Test processing fee calculation without tax."""
        fees = PaymentProcessor.calculate_processing_fee(
            amount=Decimal("10000"),
            payment_method=PaymentMethod.VIRTUAL_ACCOUNT,
            include_tax=False,
        )

        # 0.5% + 200 KRW fixed fee
        assert fees["percentage_fee"] == Decimal("50.00")  # 10000 * 0.005
        assert fees["fixed_fee"] == Decimal("200")
        assert fees["subtotal_fee"] == Decimal("250.00")
        assert fees["tax_amount"] == Decimal("0")
        assert fees["total_fee"] == Decimal("250.00")
        assert fees["net_amount"] == Decimal("9750.00")

    def test_calculate_retry_delay(self):
        """Test retry delay calculation with exponential backoff."""
        policy = RetryPolicy(
            initial_delay_seconds=60, backoff_multiplier=2.0, max_delay_seconds=3600
        )

        # First retry: 60 seconds
        assert PaymentProcessor.calculate_retry_delay(1, policy) == 60

        # Second retry: 120 seconds
        assert PaymentProcessor.calculate_retry_delay(2, policy) == 120

        # Third retry: 240 seconds
        assert PaymentProcessor.calculate_retry_delay(3, policy) == 240

        # Fourth retry: 480 seconds
        assert PaymentProcessor.calculate_retry_delay(4, policy) == 480

        # Check max delay cap
        assert PaymentProcessor.calculate_retry_delay(10, policy) == 3600

    def test_calculate_retry_delay_edge_cases(self):
        """Test retry delay calculation edge cases."""
        policy = RetryPolicy()

        # Zero or negative attempt number
        assert PaymentProcessor.calculate_retry_delay(0, policy) == 0
        assert PaymentProcessor.calculate_retry_delay(-1, policy) == 0

    def test_should_retry_success(self):
        """Test retry decision for successful payment."""
        result = PaymentResult(
            payment_id="PAY-001",
            status=ProcessingStatus.COMPLETED,
            transaction_id="TXN-001",
        )
        policy = RetryPolicy()

        # Should not retry successful payment
        assert not PaymentProcessor.should_retry(result, 1, policy)

    def test_should_retry_retriable_error(self):
        """Test retry decision for retriable errors."""
        result = PaymentResult(
            payment_id="PAY-001", status=ProcessingStatus.FAILED, error_code="TIMEOUT"
        )
        policy = RetryPolicy()

        # Should retry on first attempt
        assert PaymentProcessor.should_retry(result, 1, policy)
        assert PaymentProcessor.should_retry(result, 2, policy)

        # Should not retry after max attempts
        assert not PaymentProcessor.should_retry(result, 3, policy)

    def test_should_retry_non_retriable_error(self):
        """Test retry decision for non-retriable errors."""
        result = PaymentResult(
            payment_id="PAY-001",
            status=ProcessingStatus.FAILED,
            error_code="INVALID_CARD",
        )
        policy = RetryPolicy()

        # Should not retry non-retriable error
        assert not PaymentProcessor.should_retry(result, 1, policy)

    def test_payment_result_properties(self):
        """Test PaymentResult property methods."""
        # Successful payment
        success = PaymentResult(payment_id="PAY-001", status=ProcessingStatus.COMPLETED)
        assert success.is_successful
        assert not success.is_retriable

        # Failed payment
        failed = PaymentResult(payment_id="PAY-002", status=ProcessingStatus.FAILED)
        assert not failed.is_successful
        assert failed.is_retriable

        # Timeout payment
        timeout = PaymentResult(payment_id="PAY-003", status=ProcessingStatus.TIMEOUT)
        assert not timeout.is_successful
        assert timeout.is_retriable

    def test_reconcile_payment_no_discrepancy(self):
        """Test payment reconciliation with no discrepancies."""
        internal = {
            "payment_id": "PAY-001",
            "amount": "10000",
            "status": PaymentStatus.PAID.value,
        }

        gateway = {"payment_id": "PAY-001", "amount": "10000", "status": "COMPLETED"}

        record = PaymentProcessor.reconcile_payment(internal, gateway)

        assert record.payment_id == "PAY-001"
        assert record.internal_amount == Decimal("10000")
        assert record.gateway_amount == Decimal("10000")
        assert record.internal_status == PaymentStatus.PAID
        assert record.gateway_status == "COMPLETED"
        assert not record.has_discrepancy
        assert record.discrepancy_type is None

    def test_reconcile_payment_amount_mismatch(self):
        """Test payment reconciliation with amount mismatch."""
        internal = {
            "payment_id": "PAY-001",
            "amount": "10000",
            "status": PaymentStatus.PAID.value,
        }

        gateway = {"payment_id": "PAY-001", "amount": "9900", "status": "COMPLETED"}

        record = PaymentProcessor.reconcile_payment(internal, gateway)

        assert record.has_discrepancy
        assert record.discrepancy_type == "AMOUNT_MISMATCH"
        assert record.discrepancy_amount == Decimal("100")

    def test_reconcile_payment_status_mismatch(self):
        """Test payment reconciliation with status mismatch."""
        internal = {
            "payment_id": "PAY-001",
            "amount": "10000",
            "status": PaymentStatus.PAID.value,
        }

        gateway = {"payment_id": "PAY-001", "amount": "10000", "status": "PENDING"}

        record = PaymentProcessor.reconcile_payment(internal, gateway)

        assert record.has_discrepancy
        assert record.discrepancy_type == "STATUS_MISMATCH"

    def test_batch_reconcile(self):
        """Test batch reconciliation."""
        internal_records = [
            {
                "payment_id": "PAY-001",
                "amount": "10000",
                "status": PaymentStatus.PAID.value,
            },
            {
                "payment_id": "PAY-002",
                "amount": "20000",
                "status": PaymentStatus.PAID.value,
            },
            {
                "payment_id": "PAY-003",
                "amount": "30000",
                "status": PaymentStatus.PENDING.value,
            },
            {
                "payment_id": "PAY-004",
                "amount": "40000",
                "status": PaymentStatus.PAID.value,
            },
        ]

        gateway_records = [
            {"payment_id": "PAY-001", "amount": "10000", "status": "COMPLETED"},
            {
                "payment_id": "PAY-002",
                "amount": "19900",
                "status": "COMPLETED",
            },  # Amount mismatch
            {
                "payment_id": "PAY-003",
                "amount": "30000",
                "status": "FAILED",
            },  # Status mismatch
            {
                "payment_id": "PAY-005",
                "amount": "50000",
                "status": "COMPLETED",
            },  # Gateway only
        ]

        result = PaymentProcessor.batch_reconcile(internal_records, gateway_records)

        # Check matched records
        assert len(result["matched"]) == 1
        assert result["matched"][0].payment_id == "PAY-001"

        # Check discrepancies
        assert len(result["discrepancies"]) == 2
        discrepancy_ids = [r.payment_id for r in result["discrepancies"]]
        assert "PAY-002" in discrepancy_ids  # Amount mismatch
        assert "PAY-003" in discrepancy_ids  # Status mismatch

        # Check internal only
        assert len(result["internal_only"]) == 1
        assert result["internal_only"][0].payment_id == "PAY-004"

        # Check gateway only
        assert len(result["gateway_only"]) == 1
        assert result["gateway_only"][0].payment_id == "PAY-005"

    def test_validate_payment_request_valid(self):
        """Test validation of valid payment request."""
        request = PaymentRequest(
            payment_id="PAY-001",
            amount=Decimal("10000"),
            currency="KRW",
            payment_method=PaymentMethod.BANK_TRANSFER,
            customer_id="CUST-001",
            description="Test payment",
        )

        is_valid, error = PaymentProcessor.validate_payment_request(request)
        assert is_valid
        assert error is None

    def test_validate_payment_request_invalid_amount(self):
        """Test validation with invalid amount."""
        request = PaymentRequest(
            payment_id="PAY-001",
            amount=Decimal("-100"),
            currency="KRW",
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_id="CUST-001",
            description="Test payment",
        )

        is_valid, error = PaymentProcessor.validate_payment_request(request)
        assert not is_valid
        assert "Amount must be positive" in error

    def test_validate_payment_request_invalid_currency(self):
        """Test validation with invalid currency."""
        request = PaymentRequest(
            payment_id="PAY-001",
            amount=Decimal("10000"),
            currency="XXX",
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_id="CUST-001",
            description="Test payment",
        )

        is_valid, error = PaymentProcessor.validate_payment_request(request)
        assert not is_valid
        assert "Invalid currency" in error

    def test_validate_payment_request_virtual_account(self):
        """Test validation for virtual account requirements."""
        # Without bank code
        request = PaymentRequest(
            payment_id="PAY-001",
            amount=Decimal("10000"),
            currency="KRW",
            payment_method=PaymentMethod.VIRTUAL_ACCOUNT,
            customer_id="CUST-001",
            description="Test payment",
        )

        is_valid, error = PaymentProcessor.validate_payment_request(request)
        assert not is_valid
        assert "Bank code required" in error

        # With bank code
        request.metadata["bank_code"] = "004"
        is_valid, error = PaymentProcessor.validate_payment_request(request)
        assert is_valid
        assert error is None

    def test_format_payment_amount_krw(self):
        """Test formatting KRW amounts."""
        # With symbol
        formatted = PaymentProcessor.format_payment_amount(
            Decimal("1234567"), "KRW", include_symbol=True
        )
        assert formatted == "₩1,234,567"

        # Without symbol
        formatted = PaymentProcessor.format_payment_amount(
            Decimal("1234567"), "KRW", include_symbol=False
        )
        assert formatted == "1,234,567 KRW"

    def test_format_payment_amount_usd(self):
        """Test formatting USD amounts."""
        # With symbol
        formatted = PaymentProcessor.format_payment_amount(
            Decimal("1234.56"), "USD", include_symbol=True
        )
        assert formatted == "$1,234.56"

        # Without symbol
        formatted = PaymentProcessor.format_payment_amount(
            Decimal("1234.56"), "USD", include_symbol=False
        )
        assert formatted == "1,234.56 USD"

    def test_format_payment_amount_jpy(self):
        """Test formatting JPY amounts."""
        formatted = PaymentProcessor.format_payment_amount(
            Decimal("123456"), "JPY", include_symbol=True
        )
        assert formatted == "¥123,456"

    def test_simulate_payment_processing(self):
        """Test payment processing simulation."""
        request = PaymentRequest(
            payment_id="PAY-TEST",
            amount=Decimal("10000"),
            currency="KRW",
            payment_method=PaymentMethod.CREDIT_CARD,
            customer_id="CUST-001",
            description="Test payment",
        )

        # Test with high success rate (should mostly succeed)
        successes = 0
        for _ in range(10):
            result = PaymentProcessor.simulate_payment_processing(
                request, success_rate=1.0, processing_time_ms=1  # 100% success
            )
            if result.is_successful:
                successes += 1

        assert successes == 10

        # Test with zero success rate (should always fail)
        failures = 0
        for _ in range(10):
            result = PaymentProcessor.simulate_payment_processing(
                request, success_rate=0.0, processing_time_ms=1  # 0% success
            )
            if not result.is_successful:
                failures += 1

        assert failures == 10

    def test_retry_policy_defaults(self):
        """Test RetryPolicy default values."""
        policy = RetryPolicy()

        assert policy.max_attempts == 3
        assert policy.initial_delay_seconds == 60
        assert policy.backoff_multiplier == 2.0
        assert policy.max_delay_seconds == 3600
        assert "TIMEOUT" in policy.retriable_error_codes
        assert "GATEWAY_ERROR" in policy.retriable_error_codes

    def test_payment_request_defaults(self):
        """Test PaymentRequest default values."""
        request = PaymentRequest(
            payment_id="PAY-001",
            amount=Decimal("10000"),
            currency="KRW",
            payment_method=PaymentMethod.BANK_TRANSFER,
            customer_id="CUST-001",
            description="Test",
        )

        assert request.metadata == {}

        # With metadata
        request2 = PaymentRequest(
            payment_id="PAY-002",
            amount=Decimal("20000"),
            currency="KRW",
            payment_method=PaymentMethod.VIRTUAL_ACCOUNT,
            customer_id="CUST-002",
            description="Test",
            metadata={"bank_code": "004"},
        )

        assert request2.metadata["bank_code"] == "004"
