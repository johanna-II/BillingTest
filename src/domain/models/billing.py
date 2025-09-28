"""Billing domain models - Core aggregate root."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from .adjustment import Adjustment, AdjustmentApplication
from .credit import Credit, CreditApplication
from .metering import UsageAggregation
from .payment import UnpaidAmount


@dataclass
class BillingPeriod:
    """Value object representing a billing period."""

    year: int
    month: int
    start_date: datetime
    end_date: datetime

    @classmethod
    def from_month_string(cls, month_str: str) -> BillingPeriod:
        """Create from YYYY-MM format string."""
        year, month = map(int, month_str.split("-"))

        # Calculate start and end dates
        start_date = datetime(year, month, 1, tzinfo=UTC)
        if month == 12:
            end_date = datetime(year + 1, 1, 1, tzinfo=UTC) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1, tzinfo=UTC) - timedelta(seconds=1)

        return cls(year=year, month=month, start_date=start_date, end_date=end_date)

    @property
    def month_string(self) -> str:
        """Return YYYY-MM format string."""
        return f"{self.year:04d}-{self.month:02d}"


@dataclass
class BillingStatement:
    """Core aggregate root representing a complete billing statement.

    This class orchestrates the calculation of final billing amount
    by combining usage, adjustments, credits, and unpaid amounts.
    """

    # Identity
    id: str
    user_id: str
    billing_group_id: str
    period: BillingPeriod

    # Usage and base calculation
    usage: UsageAggregation
    base_amount: Decimal

    # Modifiers
    unpaid: UnpaidAmount | None = None
    adjustments: list[Adjustment] = field(default_factory=list)
    credits: list[Credit] = field(default_factory=list)

    # Calculation results (computed)
    adjustment_result: AdjustmentApplication | None = None
    credit_result: CreditApplication | None = None
    final_amount: Decimal = field(init=False)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "DRAFT"

    def __post_init__(self) -> None:
        """Calculate final amount on initialization."""
        self.calculate()

    def calculate(self) -> None:
        """Calculate the final billing amount.

        Order of operations:
        1. Start with base amount from usage
        2. Add any unpaid amounts and overdue charges
        3. Apply adjustments (discounts/surcharges)
        4. Apply credits
        """
        # 1. Start with base amount
        amount = self.base_amount

        # 2. Add unpaid amounts if any
        if self.unpaid:
            amount += self.unpaid.total_with_charges

        # 3. Apply adjustments
        if self.adjustments:
            self.adjustment_result = AdjustmentApplication.apply_adjustments(
                amount, self.adjustments
            )
            amount = self.adjustment_result.final_amount

        # 4. Apply credits
        if self.credits and amount > 0:
            available_credits = [c for c in self.credits if c.is_available]
            if available_credits:
                self.credit_result = self._apply_credits(amount, available_credits)
                amount = self.credit_result.remaining_amount

        self.final_amount = amount

    def _apply_credits(
        self, amount: Decimal, credit_list: list[Credit]
    ) -> CreditApplication:
        """Apply credits according to priority rules."""
        # Sort by priority (expiring soon > free > refund > paid)
        sorted_credits = sorted(credit_list, key=lambda c: (c.priority.value, c.id))

        application = CreditApplication(original_amount=amount)
        remaining = amount

        for credit in sorted_credits:
            if remaining <= 0:
                break

            if credit.is_available:
                use_amount = min(credit.balance, remaining)
                application.add_credit_usage(credit, use_amount)
                remaining -= use_amount

        return application

    def add_adjustment(self, adjustment: Adjustment) -> None:
        """Add an adjustment and recalculate."""
        self.adjustments.append(adjustment)
        self.calculate()

    def add_credit(self, credit: Credit) -> None:
        """Add a credit and recalculate."""
        self.credits.append(credit)
        self.calculate()

    def set_unpaid(self, unpaid: UnpaidAmount) -> None:
        """Set unpaid amount and recalculate."""
        self.unpaid = unpaid
        self.calculate()

    @property
    def total_adjustments(self) -> Decimal:
        """Get total adjustment amount (negative for discounts)."""
        if not self.adjustment_result:
            return Decimal(0)

        original = self.base_amount
        if self.unpaid:
            original += self.unpaid.total_with_charges

        return self.adjustment_result.final_amount - original

    @property
    def total_credits_applied(self) -> Decimal:
        """Get total credits applied."""
        if not self.credit_result:
            return Decimal(0)
        return self.credit_result.total_credits_applied

    @property
    def is_paid(self) -> bool:
        """Check if statement is fully paid."""
        return self.final_amount == 0

    @property
    def summary(self) -> dict:
        """Get billing summary."""
        return {
            "period": self.period.month_string,
            "user_id": self.user_id,
            "base_amount": float(self.base_amount),
            "unpaid_amount": float(self.unpaid.amount) if self.unpaid else 0,
            "overdue_charges": float(self.unpaid.overdue_charge) if self.unpaid else 0,
            "total_adjustments": float(self.total_adjustments),
            "total_credits": float(self.total_credits_applied),
            "final_amount": float(self.final_amount),
            "status": self.status,
        }
