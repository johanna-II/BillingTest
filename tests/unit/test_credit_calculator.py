"""Unit tests for CreditCalculator class - pure business logic testing."""

from datetime import datetime

import pytest

from libs.Credit import CreditCalculator
from libs.exceptions import ValidationException


class TestCreditCalculator:
    """Unit tests for credit calculation and validation logic."""

    def test_calculate_total_from_empty_history(self):
        """Test total calculation with empty history."""
        assert CreditCalculator.calculate_total_from_history([]) == 0

    def test_calculate_total_from_history(self):
        """Test total calculation from credit history."""
        # Create mock credit history objects
        from unittest.mock import Mock

        histories = [
            Mock(amount=1000),
            Mock(amount=2000),
            Mock(amount=-500),
        ]

        total = CreditCalculator.calculate_total_from_history(histories)
        assert total == 2500

    def test_validate_credit_amount_negative(self):
        """Test validation rejects negative amounts."""
        with pytest.raises(ValidationException, match="must be positive"):
            CreditCalculator.validate_credit_amount(-100)

    def test_validate_credit_amount_zero(self):
        """Test validation rejects zero amount."""
        with pytest.raises(ValidationException, match="must be positive"):
            CreditCalculator.validate_credit_amount(0)

    def test_validate_credit_amount_exceeds_limit(self):
        """Test validation rejects amounts over limit."""
        with pytest.raises(ValidationException, match="exceeds maximum limit"):
            CreditCalculator.validate_credit_amount(1_000_001)

    def test_validate_credit_amount_valid(self):
        """Test validation accepts valid amounts."""
        # Should not raise
        CreditCalculator.validate_credit_amount(100)
        CreditCalculator.validate_credit_amount(500_000)
        CreditCalculator.validate_credit_amount(1_000_000)

    def test_calculate_expiration_dates_default(self):
        """Test expiration date calculation with default 12 months."""
        start_str, end_str = CreditCalculator.calculate_expiration_dates()

        start = datetime.strptime(start_str, "%Y-%m-%d")
        end = datetime.strptime(end_str, "%Y-%m-%d")

        # Should be approximately 12 months apart (360 days)
        days_diff = (end - start).days
        assert 359 <= days_diff <= 365

    def test_calculate_expiration_dates_custom_months(self):
        """Test expiration date calculation with custom months."""
        start_str, end_str = CreditCalculator.calculate_expiration_dates(months=6)

        start = datetime.strptime(start_str, "%Y-%m-%d")
        end = datetime.strptime(end_str, "%Y-%m-%d")

        # Should be approximately 6 months apart (180 days)
        days_diff = (end - start).days
        assert 179 <= days_diff <= 182

    def test_calculate_expiration_dates_format(self):
        """Test expiration dates have correct format."""
        start_str, end_str = CreditCalculator.calculate_expiration_dates()

        # Should match YYYY-MM-DD format
        assert len(start_str) == 10
        assert len(end_str) == 10
        assert start_str[4] == "-" and start_str[7] == "-"
        assert end_str[4] == "-" and end_str[7] == "-"
