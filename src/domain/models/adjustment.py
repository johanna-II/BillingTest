"""Adjustment domain models."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class AdjustmentType(Enum):
    """Types of billing adjustments."""

    FIXED_DISCOUNT = "FIXED_DISCOUNT"
    RATE_DISCOUNT = "RATE_DISCOUNT"
    FIXED_SURCHARGE = "FIXED_SURCHARGE"
    RATE_SURCHARGE = "RATE_SURCHARGE"


class AdjustmentTarget(Enum):
    """Targets for billing adjustments."""

    BILLING_GROUP = "BillingGroup"
    PROJECT = "Project"


@dataclass(frozen=True)
class Adjustment:
    """Represents a billing adjustment (discount or surcharge).

    This is an immutable value object representing adjustments
    that can be applied to billing calculations.
    """

    id: str
    name: str
    type: AdjustmentType
    target: AdjustmentTarget
    target_id: str
    amount: Decimal
    priority: int = 100  # Lower number = higher priority
    description: str = ""

    def __post_init__(self) -> None:
        """Validate adjustment invariants."""
        if self.amount < 0:
            msg = "Adjustment amount cannot be negative"
            raise ValueError(msg)

        # Validate percentage bounds for rate adjustments
        if self.type in (AdjustmentType.RATE_DISCOUNT, AdjustmentType.RATE_SURCHARGE):
            if self.amount > 100:
                msg = "Rate adjustment cannot exceed 100%"
                raise ValueError(msg)

    @property
    def is_discount(self) -> bool:
        """Check if this is a discount adjustment."""
        return self.type in (
            AdjustmentType.FIXED_DISCOUNT,
            AdjustmentType.RATE_DISCOUNT,
        )

    @property
    def is_surcharge(self) -> bool:
        """Check if this is a surcharge adjustment."""
        return self.type in (
            AdjustmentType.FIXED_SURCHARGE,
            AdjustmentType.RATE_SURCHARGE,
        )

    @property
    def is_percentage(self) -> bool:
        """Check if this is a percentage-based adjustment."""
        return self.type in (
            AdjustmentType.RATE_DISCOUNT,
            AdjustmentType.RATE_SURCHARGE,
        )

    def apply_to(self, amount: Decimal) -> Decimal:
        """Apply this adjustment to an amount and return the result."""
        if amount < 0:
            msg = "Cannot apply adjustment to negative amount"
            raise ValueError(msg)

        if self.type == AdjustmentType.FIXED_DISCOUNT:
            return max(Decimal(0), amount - self.amount)
        elif self.type == AdjustmentType.RATE_DISCOUNT:
            discount = amount * (self.amount / 100)
            return max(Decimal(0), amount - discount)
        elif self.type == AdjustmentType.FIXED_SURCHARGE:
            return amount + self.amount
        elif self.type == AdjustmentType.RATE_SURCHARGE:
            surcharge = amount * (self.amount / 100)
            return amount + surcharge
        else:
            # This should never happen if AdjustmentType enum is complete
            msg = f"Unknown adjustment type: {self.type}"  # type: ignore[unreachable]
            raise ValueError(msg)


@dataclass
class AdjustmentApplication:
    """Result of applying adjustments to an amount."""

    original_amount: Decimal
    adjustments: list[Adjustment]
    final_amount: Decimal

    @classmethod
    def apply_adjustments(
        cls,
        amount: Decimal,
        adjustments: list[Adjustment],
        order_by_priority: bool = True,
    ) -> AdjustmentApplication:
        """Apply multiple adjustments to an amount.

        Args:
            amount: Original amount to adjust
            adjustments: List of adjustments to apply
            order_by_priority: Whether to sort by priority before applying

        Returns:
            AdjustmentApplication with results
        """
        if order_by_priority:
            sorted_adjustments = sorted(adjustments, key=lambda a: a.priority)
        else:
            sorted_adjustments = adjustments

        current_amount = amount

        # Apply adjustments in order
        for adjustment in sorted_adjustments:
            current_amount = adjustment.apply_to(current_amount)

        return cls(
            original_amount=amount,
            adjustments=sorted_adjustments,
            final_amount=current_amount,
        )

    @property
    def total_discount(self) -> Decimal:
        """Calculate total discount applied."""
        if self.final_amount >= self.original_amount:
            return Decimal(0)
        return self.original_amount - self.final_amount

    @property
    def total_surcharge(self) -> Decimal:
        """Calculate total surcharge applied."""
        if self.final_amount <= self.original_amount:
            return Decimal(0)
        return self.final_amount - self.original_amount

    @property
    def discount_rate(self) -> Decimal:
        """Calculate effective discount rate."""
        if self.original_amount == 0:
            return Decimal(0)
        discount = self.total_discount
        if discount == 0:
            return Decimal(0)
        return (discount / self.original_amount) * 100

    @property
    def surcharge_rate(self) -> Decimal:
        """Calculate effective surcharge rate."""
        if self.original_amount == 0:
            return Decimal(0)
        surcharge = self.total_surcharge
        if surcharge == 0:
            return Decimal(0)
        return (surcharge / self.original_amount) * 100
