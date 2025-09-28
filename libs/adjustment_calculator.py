"""Adjustment Calculator for billing adjustments and validation."""

from decimal import ROUND_HALF_UP, Decimal
from typing import Tuple

from .constants import AdjustmentTarget, AdjustmentType
from .exceptions import ValidationException


class AdjustmentCalculator:
    """Handles adjustment calculations and validations.

    This class encapsulates pure calculation and validation logic for adjustments,
    making it easier to test independently from API interactions.
    """

    # Maximum allowed rates for percentage adjustments
    MAX_DISCOUNT_RATE = Decimal("100")  # 100% discount maximum
    MAX_SURCHARGE_RATE = Decimal("200")  # 200% surcharge maximum

    # Minimum and maximum amounts for fixed adjustments
    MIN_ADJUSTMENT_AMOUNT = Decimal("0")
    MAX_FIXED_ADJUSTMENT = Decimal("1000000000")  # 1 billion

    # Decimal precision for monetary calculations
    DECIMAL_PLACES = 2

    @classmethod
    def round_amount(cls, amount: Decimal) -> Decimal:
        """Round amount to standard decimal places.

        Args:
            amount: Amount to round

        Returns:
            Rounded amount
        """
        return amount.quantize(
            Decimal(f"0.{'0' * cls.DECIMAL_PLACES}"), rounding=ROUND_HALF_UP
        )

    @classmethod
    def validate_adjustment_amount(
        cls, amount: float | Decimal, adjustment_type: AdjustmentType | str
    ) -> None:
        """Validate adjustment amount based on type.

        Args:
            amount: Adjustment amount
            adjustment_type: Type of adjustment

        Raises:
            ValidationException: If amount is invalid
        """
        # Convert to Decimal for precise validation
        decimal_amount = Decimal(str(amount))

        # Check if negative
        if decimal_amount < cls.MIN_ADJUSTMENT_AMOUNT:
            raise ValidationException("Adjustment amount cannot be negative")

        # Get adjustment type string
        type_str = (
            adjustment_type.value
            if isinstance(adjustment_type, AdjustmentType)
            else str(adjustment_type)
        )

        # Check based on type
        if "RATE" in type_str:
            # Rate-based adjustments
            if "DISCOUNT" in type_str and decimal_amount > cls.MAX_DISCOUNT_RATE:
                raise ValidationException(
                    f"Rate discount cannot exceed {cls.MAX_DISCOUNT_RATE}%"
                )
            elif "SURCHARGE" in type_str and decimal_amount > cls.MAX_SURCHARGE_RATE:
                raise ValidationException(
                    f"Rate surcharge cannot exceed {cls.MAX_SURCHARGE_RATE}%"
                )
        else:
            # Fixed adjustments
            if decimal_amount > cls.MAX_FIXED_ADJUSTMENT:
                raise ValidationException(
                    f"Fixed adjustment cannot exceed {cls.MAX_FIXED_ADJUSTMENT}"
                )

    @classmethod
    def calculate_adjustment(
        cls,
        base_amount: Decimal,
        adjustment_amount: Decimal,
        adjustment_type: AdjustmentType | str,
    ) -> Decimal:
        """Calculate the actual adjustment value.

        Args:
            base_amount: Base amount to apply adjustment to
            adjustment_amount: Adjustment amount (fixed or percentage)
            adjustment_type: Type of adjustment

        Returns:
            Calculated adjustment value (positive for discount, negative for surcharge)
        """
        # Get adjustment type string
        type_str = (
            adjustment_type.value
            if isinstance(adjustment_type, AdjustmentType)
            else str(adjustment_type)
        )

        # Calculate based on type
        if "RATE" in type_str:
            # Percentage-based
            adjustment_value = base_amount * adjustment_amount / Decimal("100")
        else:
            # Fixed amount
            adjustment_value = adjustment_amount

        # Apply sign based on discount/surcharge
        if "DISCOUNT" in type_str:
            # Discounts are positive (reduce the bill)
            final_value = adjustment_value
        else:
            # Surcharges are negative (increase the bill)
            final_value = -adjustment_value

        return cls.round_amount(final_value)

    @classmethod
    def apply_adjustment(
        cls,
        base_amount: Decimal,
        adjustment_amount: Decimal,
        adjustment_type: AdjustmentType | str,
    ) -> Tuple[Decimal, Decimal]:
        """Apply adjustment to base amount.

        Args:
            base_amount: Original amount
            adjustment_amount: Adjustment amount
            adjustment_type: Type of adjustment

        Returns:
            Tuple of (final_amount, adjustment_value)
        """
        adjustment_value = cls.calculate_adjustment(
            base_amount, adjustment_amount, adjustment_type
        )

        # Calculate final amount
        final_amount = base_amount - adjustment_value

        # Ensure final amount is not negative
        if final_amount < Decimal("0"):
            final_amount = Decimal("0")
            adjustment_value = base_amount

        return cls.round_amount(final_amount), cls.round_amount(adjustment_value)

    @classmethod
    def calculate_cumulative_adjustments(
        cls,
        base_amount: Decimal,
        adjustments: list[tuple[Decimal, AdjustmentType | str]],
    ) -> Tuple[Decimal, Decimal]:
        """Apply multiple adjustments cumulatively.

        Args:
            base_amount: Original amount
            adjustments: List of (amount, type) tuples

        Returns:
            Tuple of (final_amount, total_adjustment)
        """
        current_amount = base_amount
        total_adjustment = Decimal("0")

        for adjustment_amount, adjustment_type in adjustments:
            # Validate each adjustment
            cls.validate_adjustment_amount(adjustment_amount, adjustment_type)

            # Apply adjustment
            new_amount, adj_value = cls.apply_adjustment(
                current_amount, adjustment_amount, adjustment_type
            )

            current_amount = new_amount
            total_adjustment += adj_value

        return current_amount, total_adjustment

    @classmethod
    def is_valid_target_combination(
        cls,
        adjustment_target: AdjustmentTarget | str,
        adjustment_type: AdjustmentType | str,
    ) -> bool:
        """Check if target and type combination is valid.

        Some adjustment types may not be applicable to certain targets.

        Args:
            adjustment_target: Target of adjustment
            adjustment_type: Type of adjustment

        Returns:
            True if combination is valid
        """
        # Get string representations
        target_str = (
            adjustment_target.value
            if isinstance(adjustment_target, AdjustmentTarget)
            else str(adjustment_target)
        )
        type_str = (
            adjustment_type.value
            if isinstance(adjustment_type, AdjustmentType)
            else str(adjustment_type)
        )

        # All combinations are currently valid
        # This method exists for future business rule implementation
        return True

    @classmethod
    def calculate_effective_rate(
        cls, original_amount: Decimal, adjusted_amount: Decimal
    ) -> Decimal:
        """Calculate the effective discount/surcharge rate.

        Args:
            original_amount: Original amount before adjustment
            adjusted_amount: Amount after adjustment

        Returns:
            Effective rate as percentage
        """
        if original_amount == Decimal("0"):
            return Decimal("0")

        difference = original_amount - adjusted_amount
        rate = (difference / original_amount) * Decimal("100")

        return cls.round_amount(abs(rate))

    @classmethod
    def estimate_impact(
        cls,
        monthly_amount: Decimal,
        adjustment_amount: Decimal,
        adjustment_type: AdjustmentType | str,
        months: int = 12,
    ) -> Decimal:
        """Estimate the total impact of an adjustment over time.

        Args:
            monthly_amount: Monthly billing amount
            adjustment_amount: Adjustment amount
            adjustment_type: Type of adjustment
            months: Number of months to calculate

        Returns:
            Total impact amount
        """
        _, monthly_adjustment = cls.apply_adjustment(
            monthly_amount, adjustment_amount, adjustment_type
        )

        total_impact = monthly_adjustment * Decimal(str(months))
        return cls.round_amount(total_impact)
