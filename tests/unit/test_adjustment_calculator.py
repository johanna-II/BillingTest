"""Unit tests for AdjustmentCalculator - pure adjustment calculation logic."""

from decimal import Decimal

import pytest

from libs.adjustment_calculator import AdjustmentCalculator
from libs.constants import AdjustmentTarget, AdjustmentType
from libs.exceptions import ValidationException


class TestAdjustmentCalculator:
    """Unit tests for adjustment calculation logic."""

    def test_round_amount(self):
        """Test amount rounding."""
        assert AdjustmentCalculator.round_amount(Decimal("10.555")) == Decimal("10.56")
        assert AdjustmentCalculator.round_amount(Decimal("10.554")) == Decimal("10.55")
        assert AdjustmentCalculator.round_amount(Decimal("10.5")) == Decimal("10.50")
        assert AdjustmentCalculator.round_amount(Decimal("10")) == Decimal("10.00")

    def test_validate_adjustment_amount_negative(self):
        """Test validation rejects negative amounts."""
        with pytest.raises(ValidationException, match="cannot be negative"):
            AdjustmentCalculator.validate_adjustment_amount(
                -100, AdjustmentType.FIXED_DISCOUNT
            )

        with pytest.raises(ValidationException, match="cannot be negative"):
            AdjustmentCalculator.validate_adjustment_amount(
                Decimal("-50"), AdjustmentType.RATE_SURCHARGE
            )

    def test_validate_adjustment_amount_rate_discount(self):
        """Test rate discount validation."""
        # Valid rates
        AdjustmentCalculator.validate_adjustment_amount(
            50, AdjustmentType.RATE_DISCOUNT
        )
        AdjustmentCalculator.validate_adjustment_amount(
            100, AdjustmentType.RATE_DISCOUNT
        )

        # Invalid rate
        with pytest.raises(ValidationException, match="cannot exceed 100%"):
            AdjustmentCalculator.validate_adjustment_amount(
                150, AdjustmentType.RATE_DISCOUNT
            )

    def test_validate_adjustment_amount_rate_surcharge(self):
        """Test rate surcharge validation."""
        # Valid rates
        AdjustmentCalculator.validate_adjustment_amount(
            50, AdjustmentType.RATE_SURCHARGE
        )
        AdjustmentCalculator.validate_adjustment_amount(
            200, AdjustmentType.RATE_SURCHARGE
        )

        # Invalid rate
        with pytest.raises(ValidationException, match="cannot exceed 200%"):
            AdjustmentCalculator.validate_adjustment_amount(
                250, AdjustmentType.RATE_SURCHARGE
            )

    def test_validate_adjustment_amount_fixed(self):
        """Test fixed adjustment validation."""
        # Valid amounts
        AdjustmentCalculator.validate_adjustment_amount(
            1000, AdjustmentType.FIXED_DISCOUNT
        )
        AdjustmentCalculator.validate_adjustment_amount(
            999999999, AdjustmentType.FIXED_SURCHARGE
        )

        # Invalid amount
        with pytest.raises(ValidationException, match="cannot exceed"):
            AdjustmentCalculator.validate_adjustment_amount(
                1000000001, AdjustmentType.FIXED_DISCOUNT
            )

    def test_calculate_adjustment_fixed_discount(self):
        """Test fixed discount calculation."""
        adjustment = AdjustmentCalculator.calculate_adjustment(
            Decimal("1000"), Decimal("100"), AdjustmentType.FIXED_DISCOUNT
        )
        assert adjustment == Decimal("100.00")  # Positive for discount

    def test_calculate_adjustment_fixed_surcharge(self):
        """Test fixed surcharge calculation."""
        adjustment = AdjustmentCalculator.calculate_adjustment(
            Decimal("1000"), Decimal("50"), AdjustmentType.FIXED_SURCHARGE
        )
        assert adjustment == Decimal("-50.00")  # Negative for surcharge

    def test_calculate_adjustment_rate_discount(self):
        """Test rate discount calculation."""
        adjustment = AdjustmentCalculator.calculate_adjustment(
            Decimal("1000"), Decimal("10"), AdjustmentType.RATE_DISCOUNT
        )
        assert adjustment == Decimal("100.00")  # 10% of 1000

    def test_calculate_adjustment_rate_surcharge(self):
        """Test rate surcharge calculation."""
        adjustment = AdjustmentCalculator.calculate_adjustment(
            Decimal("1000"), Decimal("15"), AdjustmentType.RATE_SURCHARGE
        )
        assert adjustment == Decimal("-150.00")  # -15% of 1000

    def test_apply_adjustment_normal(self):
        """Test applying adjustment to base amount."""
        # Fixed discount
        final, adj_value = AdjustmentCalculator.apply_adjustment(
            Decimal("1000"), Decimal("200"), AdjustmentType.FIXED_DISCOUNT
        )
        assert final == Decimal("800.00")
        assert adj_value == Decimal("200.00")

        # Rate surcharge
        final, adj_value = AdjustmentCalculator.apply_adjustment(
            Decimal("1000"), Decimal("10"), AdjustmentType.RATE_SURCHARGE
        )
        assert final == Decimal("1100.00")
        assert adj_value == Decimal("-100.00")

    def test_apply_adjustment_exceeds_base(self):
        """Test adjustment that would result in negative amount."""
        # Large discount
        final, adj_value = AdjustmentCalculator.apply_adjustment(
            Decimal("100"), Decimal("200"), AdjustmentType.FIXED_DISCOUNT
        )
        assert final == Decimal("0.00")  # Capped at zero
        assert adj_value == Decimal("100.00")  # Only discounted the available amount

    def test_calculate_cumulative_adjustments(self):
        """Test applying multiple adjustments."""
        adjustments = [
            (Decimal("10"), AdjustmentType.RATE_DISCOUNT),  # 10% discount
            (Decimal("50"), AdjustmentType.FIXED_DISCOUNT),  # $50 discount
            (Decimal("5"), AdjustmentType.RATE_SURCHARGE),  # 5% surcharge
        ]

        final, total_adj = AdjustmentCalculator.calculate_cumulative_adjustments(
            Decimal("1000"), adjustments
        )

        # Step 1: 1000 - 100 (10%) = 900
        # Step 2: 900 - 50 = 850
        # Step 3: 850 + 42.50 (5%) = 892.50
        assert final == Decimal("892.50")
        assert total_adj == Decimal("107.50")  # Net discount

    def test_is_valid_target_combination(self):
        """Test target and type combination validation."""
        # All combinations should be valid currently
        assert AdjustmentCalculator.is_valid_target_combination(
            AdjustmentTarget.PROJECT, AdjustmentType.FIXED_DISCOUNT
        )
        assert AdjustmentCalculator.is_valid_target_combination(
            AdjustmentTarget.BILLING_GROUP, AdjustmentType.RATE_SURCHARGE
        )
        assert AdjustmentCalculator.is_valid_target_combination(
            AdjustmentTarget.CAMPAIGN, AdjustmentType.RATE_DISCOUNT
        )

    def test_calculate_effective_rate(self):
        """Test effective rate calculation."""
        # 20% discount
        rate = AdjustmentCalculator.calculate_effective_rate(
            Decimal("1000"), Decimal("800")
        )
        assert rate == Decimal("20.00")

        # 10% surcharge
        rate = AdjustmentCalculator.calculate_effective_rate(
            Decimal("1000"), Decimal("1100")
        )
        assert rate == Decimal("10.00")

        # Zero original amount
        rate = AdjustmentCalculator.calculate_effective_rate(
            Decimal("0"), Decimal("100")
        )
        assert rate == Decimal("0.00")

    def test_estimate_impact(self):
        """Test impact estimation over time."""
        # 10% monthly discount for 12 months
        impact = AdjustmentCalculator.estimate_impact(
            Decimal("1000"), Decimal("10"), AdjustmentType.RATE_DISCOUNT, months=12
        )
        assert impact == Decimal("1200.00")  # 100 * 12

        # Fixed surcharge for 6 months
        impact = AdjustmentCalculator.estimate_impact(
            Decimal("1000"), Decimal("50"), AdjustmentType.FIXED_SURCHARGE, months=6
        )
        assert impact == Decimal("-300.00")  # -50 * 6

    def test_string_adjustment_types(self):
        """Test with string adjustment types instead of enums."""
        # Should work with string values
        adjustment = AdjustmentCalculator.calculate_adjustment(
            Decimal("1000"), Decimal("15"), "RATE_DISCOUNT"
        )
        assert adjustment == Decimal("150.00")

        # Validation should also work with strings
        AdjustmentCalculator.validate_adjustment_amount(75, "RATE_SURCHARGE")

        with pytest.raises(ValidationException):
            AdjustmentCalculator.validate_adjustment_amount(-50, "FIXED_DISCOUNT")
