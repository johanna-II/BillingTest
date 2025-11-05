"""Domain service for billing calculations.

This service orchestrates the complex business logic of billing calculation,
coordinating between different domain models and repositories.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from src.domain.models import (
    Adjustment,
    BillingPeriod,
    BillingStatement,
    Credit,
    UnpaidAmount,
    UsageAggregation,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.domain.repositories import (
        AdjustmentRepository,
        ContractRepository,
        CreditRepository,
        MeteringRepository,
        PaymentRepository,
    )


class BillingCalculationService:
    """Service for calculating billing statements.

    This service contains the core business logic for billing calculation,
    including the order of operations and business rules.
    """

    # Default pricing rates by counter prefix (single source of truth)
    DEFAULT_RATES = {
        "compute": Decimal("1.0"),
        "storage": Decimal("0.1"),
        "network": Decimal("0.01"),
    }

    def __init__(
        self,
        metering_repo: "MeteringRepository",
        adjustment_repo: "AdjustmentRepository",
        credit_repo: "CreditRepository",
        contract_repo: "ContractRepository",
        payment_repo: "PaymentRepository",
    ):
        """Initialize with required repositories."""
        self.metering_repo = metering_repo
        self.adjustment_repo = adjustment_repo
        self.credit_repo = credit_repo
        self.contract_repo = contract_repo
        self.payment_repo = payment_repo

    def calculate_billing(
        self,
        user_id: str,
        billing_group_id: str,
        period: BillingPeriod,
        include_unpaid: bool = True,
    ) -> BillingStatement:
        """Calculate complete billing statement for a period.

        This is the main entry point that orchestrates the entire
        billing calculation process.

        Args:
            user_id: User identifier
            billing_group_id: Billing group identifier
            period: Billing period to calculate
            include_unpaid: Whether to include unpaid amounts from previous periods

        Returns:
            Complete billing statement
        """
        # 1. Aggregate usage data
        usage = self._aggregate_usage(user_id, period)

        # 2. Calculate base amount using contract pricing
        base_amount = self._calculate_base_amount(billing_group_id, usage, period)

        # 3. Get unpaid amounts if requested
        unpaid = None
        if include_unpaid:
            unpaid = self._get_unpaid_amounts(user_id, period)

        # 4. Get applicable adjustments
        adjustments = self._get_adjustments(billing_group_id, usage, period)

        # 5. Get available credits
        available_credits = self._get_available_credits(user_id, period)

        # 6. Create and calculate billing statement
        return BillingStatement(
            id=f"STMT-{user_id}-{period.month_string}",
            user_id=user_id,
            billing_group_id=billing_group_id,
            period=period,
            usage=usage,
            base_amount=base_amount,
            unpaid=unpaid,
            adjustments=adjustments,
            credits=available_credits,
        )

    def _aggregate_usage(self, user_id: str, period: BillingPeriod) -> UsageAggregation:
        """Aggregate all usage data for the period."""
        meters = self.metering_repo.find_by_user_and_period(
            user_id, period.start_date, period.end_date
        )

        aggregation = UsageAggregation(
            period_start=period.start_date, period_end=period.end_date
        )

        for meter in meters:
            aggregation.add_meter(meter)

        return aggregation

    def _calculate_base_amount(
        self, billing_group_id: str, usage: UsageAggregation, period: BillingPeriod
    ) -> Decimal:
        """Calculate base amount using contract pricing."""
        # Get active contract for billing group
        contract = self.contract_repo.find_active_contract(
            billing_group_id, period.start_date
        )

        if not contract:
            # Fallback to default pricing if no contract
            return self._calculate_default_pricing(usage)

        total = Decimal(0)

        # Calculate cost for each counter using contract pricing
        for counter_name in usage.unique_counters:
            volume = usage.get_usage_by_counter(counter_name)

            try:
                cost = contract.calculate_cost(counter_name, volume)
                total += cost
            except ValueError:
                # Counter not in contract, use default pricing
                default_cost = self._calculate_default_counter_cost(
                    counter_name, volume
                )
                total += default_cost

        return total

    def _calculate_default_pricing(self, usage: UsageAggregation) -> Decimal:
        """Calculate using default pricing rules.

        Delegates to _calculate_default_counter_cost for each counter
        to ensure consistent pricing logic.
        """
        total = Decimal(0)
        for counter_name in usage.unique_counters:
            volume = usage.get_usage_by_counter(counter_name)
            total += self._calculate_default_counter_cost(counter_name, volume)

        return total

    def _calculate_default_counter_cost(
        self, counter_name: str, volume: Decimal
    ) -> Decimal:
        """Calculate cost for a single counter using default pricing.

        Args:
            counter_name: Name of the counter
            volume: Usage volume

        Returns:
            Calculated cost based on counter-specific default rates
        """
        # Find matching rate by prefix
        for prefix, rate in self.DEFAULT_RATES.items():
            if counter_name.startswith(prefix):
                return volume * rate

        # Fallback to generic default if counter_name is unknown
        logger.warning(
            "No DEFAULT_RATES prefix matched for counter '%s' (volume=%s). "
            "Applying generic default rate of 1.0. "
            "This may indicate a misspelling or missing rate entry.",
            counter_name,
            volume,
        )
        return volume * Decimal("1.0")

    def _get_unpaid_amounts(
        self, user_id: str, current_period: BillingPeriod
    ) -> UnpaidAmount | None:
        """Get unpaid amounts from previous periods."""
        unpaid_payments = self.payment_repo.find_unpaid_by_user(
            user_id, current_period.start_date
        )

        if not unpaid_payments:
            return None

        total_unpaid = Decimal(sum(p.amount for p in unpaid_payments))

        # Calculate overdue days from oldest unpaid
        oldest_payment = min(unpaid_payments, key=lambda p: p.created_at)
        overdue_days = (current_period.start_date - oldest_payment.created_at).days

        # Apply overdue rules (simplified)
        overdue_rate = Decimal("0.05") if overdue_days > 30 else Decimal(0)

        return UnpaidAmount(
            amount=total_unpaid,
            overdue_days=max(0, overdue_days - 30),  # Grace period
            overdue_rate=overdue_rate,
            period=oldest_payment.payment_group_id[:7],  # Extract period
        )

    def _get_adjustments(
        self, billing_group_id: str, usage: UsageAggregation, period: BillingPeriod
    ) -> list[Adjustment]:
        """Get all applicable adjustments."""
        adjustments = []

        # Get billing group level adjustments
        bg_adjustments = self.adjustment_repo.find_by_billing_group(
            billing_group_id, period.start_date
        )
        adjustments.extend(bg_adjustments)

        # Get project level adjustments for each app
        for app_key in usage.unique_apps:
            proj_adjustments = self.adjustment_repo.find_by_project(
                app_key, period.start_date
            )
            adjustments.extend(proj_adjustments)

        # Sort by priority
        adjustments.sort(key=lambda a: a.priority)

        return adjustments

    def _get_available_credits(
        self, user_id: str, period: BillingPeriod
    ) -> list[Credit]:
        """Get all available credits for the user relative to the billing period.

        Credits are considered available if:
        1. They have a positive balance
        2. They were created before or during the billing period
        3. They never expire (expires_at is None) OR their expiration date is
           after the billing period start (valid during period)

        This ensures credits are evaluated against the historical billing period,
        not the current date, enabling correct billing for past periods.

        Args:
            user_id: User ID
            period: Billing period to evaluate credits against

        Returns:
            List of available credits sorted by priority
        """
        all_credits = self.credit_repo.find_by_user(user_id)

        # Filter to credits available during the billing period
        available = [
            c
            for c in all_credits
            if (
                c.balance > 0
                and c.created_at <= period.end_date
                and (
                    c.expires_at is None  # Never expires
                    or c.expires_at >= period.start_date  # Valid during period
                )
            )
        ]

        # Sort by priority (expiring soon first)
        available.sort(key=lambda c: (c.priority.value, c.id))

        return available


class BillingValidationService:
    """Service for validating billing rules and constraints."""

    @staticmethod
    def validate_adjustment_limits(adjustments: list[Adjustment]) -> None:
        """Validate that adjustments don't exceed business limits."""
        # Calculate total discount rate
        total_discount_rate = Decimal(0)

        for adj in adjustments:
            if adj.is_discount and adj.is_percentage:
                total_discount_rate += adj.amount

        # Business rule: Total discount cannot exceed 90%
        if total_discount_rate > 90:
            msg = f"Total discount rate {total_discount_rate}% exceeds maximum 90%"
            raise ValueError(msg)

    @staticmethod
    def validate_credit_usage(credit_list: list[Credit], _amount: Decimal) -> None:
        """Validate credit usage rules."""
        # Business rule: Cannot use expired credits
        for credit in credit_list:
            if credit.is_expired:
                msg = f"Cannot use expired credit {credit.id}"
                raise ValueError(msg)

        # Business rule: Must use credits in priority order
        # (This is enforced by the calculation logic)

    @staticmethod
    def validate_billing_period(period: BillingPeriod) -> None:
        """Validate billing period constraints."""
        # Business rule: Cannot calculate future periods
        if period.start_date > datetime.now(UTC):
            msg = "Cannot calculate billing for future periods"
            raise ValueError(msg)

        # Business rule: Cannot calculate periods older than 2 years
        two_years_ago = datetime.now(UTC) - timedelta(days=730)
        if period.end_date < two_years_ago:
            msg = "Cannot calculate billing for periods older than 2 years"
            raise ValueError(msg)
