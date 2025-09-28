"""Unit tests for PaymentValidator - pure validation logic testing."""

import pytest

from libs.exceptions import ValidationException
from libs.Payments import PaymentStatus, PaymentValidator


class TestPaymentValidator:
    """Unit tests for payment validation logic."""

    def test_validate_month_format_valid(self):
        """Test valid month formats."""
        # Should not raise
        PaymentValidator.validate_month_format("2024-01")
        PaymentValidator.validate_month_format("2024-12")
        PaymentValidator.validate_month_format("2025-06")

    def test_validate_month_format_invalid_format(self):
        """Test invalid month formats."""
        invalid_formats = [
            "2024",  # Missing month
            "01-2024",  # Wrong order
            "2024-1",  # Single digit month
            "2024-13",  # Invalid month
            "2024-00",  # Zero month
            "24-01",  # 2-digit year
            "2024/01",  # Wrong separator
            "2024.01",  # Wrong separator
            "202401",  # No separator
            "",  # Empty
            "abc",  # Non-numeric
        ]

        for invalid in invalid_formats:
            with pytest.raises(ValidationException, match="Invalid month format"):
                PaymentValidator.validate_month_format(invalid)

    def test_validate_payment_group_id_valid(self):
        """Test valid payment group IDs."""
        # Should not raise
        PaymentValidator.validate_payment_group_id("pg-123")
        PaymentValidator.validate_payment_group_id("payment-group-abc123")
        PaymentValidator.validate_payment_group_id("PG_001")

    def test_validate_payment_group_id_invalid(self):
        """Test invalid payment group IDs."""
        with pytest.raises(
            ValidationException, match="Payment group ID cannot be empty"
        ):
            PaymentValidator.validate_payment_group_id("")

        with pytest.raises(
            ValidationException, match="Payment group ID cannot be empty"
        ):
            PaymentValidator.validate_payment_group_id(None)

    def test_status_transition_valid(self):
        """Test valid payment status transitions."""
        # PENDING -> REGISTERED
        assert PaymentValidator.is_valid_transition(
            PaymentStatus.PENDING, PaymentStatus.REGISTERED
        )

        # REGISTERED -> PAID
        assert PaymentValidator.is_valid_transition(
            PaymentStatus.REGISTERED, PaymentStatus.PAID
        )

        # REGISTERED -> CANCELLED
        assert PaymentValidator.is_valid_transition(
            PaymentStatus.REGISTERED, PaymentStatus.CANCELLED
        )

    def test_status_transition_invalid(self):
        """Test invalid payment status transitions."""
        # Cannot go backwards
        assert not PaymentValidator.is_valid_transition(
            PaymentStatus.PAID, PaymentStatus.PENDING
        )

        # Cannot skip states
        assert not PaymentValidator.is_valid_transition(
            PaymentStatus.PENDING, PaymentStatus.PAID
        )

        # Cannot change from final states
        assert not PaymentValidator.is_valid_transition(
            PaymentStatus.PAID, PaymentStatus.CANCELLED
        )

    def test_validate_amount_valid(self):
        """Test valid payment amounts."""
        # Should not raise
        PaymentValidator.validate_amount(100)
        PaymentValidator.validate_amount(0.01)
        PaymentValidator.validate_amount(999999)

    def test_validate_amount_invalid(self):
        """Test invalid payment amounts."""
        with pytest.raises(ValidationException, match="Amount must be positive"):
            PaymentValidator.validate_amount(0)

        with pytest.raises(ValidationException, match="Amount must be positive"):
            PaymentValidator.validate_amount(-100)

        with pytest.raises(ValidationException, match="Amount exceeds maximum"):
            PaymentValidator.validate_amount(10_000_000)  # 10 million

    def test_format_currency(self):
        """Test currency formatting."""
        assert PaymentValidator.format_currency(1000) == "₩1,000"
        assert PaymentValidator.format_currency(1234567) == "₩1,234,567"
        assert PaymentValidator.format_currency(0) == "₩0"
        assert PaymentValidator.format_currency(100.50) == "₩101"  # Rounds up
