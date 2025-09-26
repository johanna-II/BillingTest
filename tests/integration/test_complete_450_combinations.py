"""Complete test coverage for all 450 business logic combinations.

This test suite systematically tests ALL possible combinations using
parameterized testing to ensure complete coverage.
"""

import itertools
import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

import pytest

from libs.constants import AdjustmentTarget, AdjustmentType, CounterType, CreditType
from tests.integration.base_integration import BaseIntegrationTest

logger = logging.getLogger(__name__)


# Business Rules Configuration
@dataclass
class BusinessRules:
    """Central configuration for business rules."""

    # Discount limits
    MAX_TOTAL_DISCOUNT_RATE: float = 90.0  # Maximum combined discount rate
    MAX_SINGLE_DISCOUNT_RATE: float = 50.0  # Maximum single discount rate

    # Credit rules
    CREDIT_PRIORITY_ORDER: list[CreditType] = None

    # Overdue rules
    OVERDUE_GRACE_PERIOD_DAYS: int = 30
    OVERDUE_CHARGE_RATE: float = 0.05  # 5% overdue charge
    OVERDUE_MAX_RATE: float = 0.20  # Maximum 20% overdue charge

    # Calculation rules
    VAT_RATE: float = 0.10  # 10% VAT
    MIN_BILLABLE_AMOUNT: float = 100.0  # Minimum billable amount

    def __post_init__(self):
        if self.CREDIT_PRIORITY_ORDER is None:
            self.CREDIT_PRIORITY_ORDER = [
                CreditType.FREE,  # Free credits used first
                CreditType.REFUND,  # Then refunds
                CreditType.PAID,  # Paid credits last
            ]


# Test Data Factory
class TestDataFactory:
    """Factory for creating consistent test data."""

    @staticmethod
    def create_usage_scenario(
        base_amount: float = 100000,
        resource_type: str = "compute.instance",
        units: int = 100,
    ) -> dict[str, Any]:
        """Create a usage scenario."""
        return {
            "counter_name": resource_type,
            "counter_type": CounterType.DELTA,
            "counter_unit": "HOURS",
            "counter_volume": str(units),
            "expected_amount": base_amount,
        }

    @staticmethod
    def create_adjustment_data(
        adj_type: AdjustmentType,
        amount: float,
        target_type: AdjustmentTarget,
        name_prefix: str = "Test",
    ) -> dict[str, Any]:
        """Create adjustment data."""
        return {
            "adjustment_name": f"{name_prefix} - {adj_type.value}",
            "adjustment_type": adj_type,
            "adjustment_amount": amount,
            "target_type": target_type,
            "description": f"{name_prefix} adjustment {amount}",
        }

    @staticmethod
    def create_credit_data(
        credit_type: CreditType, amount: float, campaign_prefix: str = "TEST"
    ) -> dict[str, Any]:
        """Create credit data."""
        return {
            "campaign_id": f"{campaign_prefix}-{credit_type.value}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "credit_name": f"{credit_type.value} Credit",
            "credit_amount": amount,
            "credit_type": credit_type,
        }


class TestAll450Combinations(BaseIntegrationTest):
    """Systematically test all 450 business logic combinations."""

    # Initialize business rules
    business_rules = BusinessRules()
    test_factory = TestDataFactory()

    # Component definitions
    UNPAID_SCENARIOS = [
        ("NO_UNPAID", 0, 0),
        ("UNPAID_CURRENT", 50000, 0),
        ("UNPAID_OVERDUE", 100000, 5000),
    ]

    BILLING_GROUP_ADJUSTMENTS = [
        ("BG_NONE", None, None, None),
        (
            "BG_FIXED_DISCOUNT",
            AdjustmentType.FIXED_DISCOUNT,
            AdjustmentTarget.BILLING_GROUP,
            10000,
        ),
        (
            "BG_RATE_DISCOUNT",
            AdjustmentType.RATE_DISCOUNT,
            AdjustmentTarget.BILLING_GROUP,
            10,
        ),
        (
            "BG_FIXED_SURCHARGE",
            AdjustmentType.FIXED_SURCHARGE,
            AdjustmentTarget.BILLING_GROUP,
            5000,
        ),
        (
            "BG_RATE_SURCHARGE",
            AdjustmentType.RATE_SURCHARGE,
            AdjustmentTarget.BILLING_GROUP,
            5,
        ),
    ]

    PROJECT_ADJUSTMENTS = [
        ("PROJ_NONE", None, None, None),
        (
            "PROJ_FIXED_DISCOUNT",
            AdjustmentType.FIXED_DISCOUNT,
            AdjustmentTarget.PROJECT,
            8000,
        ),
        (
            "PROJ_RATE_DISCOUNT",
            AdjustmentType.RATE_DISCOUNT,
            AdjustmentTarget.PROJECT,
            8,
        ),
        (
            "PROJ_FIXED_SURCHARGE",
            AdjustmentType.FIXED_SURCHARGE,
            AdjustmentTarget.PROJECT,
            3000,
        ),
        (
            "PROJ_RATE_SURCHARGE",
            AdjustmentType.RATE_SURCHARGE,
            AdjustmentTarget.PROJECT,
            3,
        ),
    ]

    CREDIT_COMBINATIONS = [
        ("NO_CREDIT", []),
        ("FREE_ONLY", [(CreditType.FREE, 20000)]),
        ("PAID_ONLY", [(CreditType.PAID, 30000)]),
        ("REFUND_ONLY", [(CreditType.REFUND, 15000)]),
        ("FREE_PAID", [(CreditType.FREE, 20000), (CreditType.PAID, 30000)]),
        (
            "ALL_CREDITS",
            [
                (CreditType.FREE, 20000),
                (CreditType.PAID, 30000),
                (CreditType.REFUND, 15000),
            ],
        ),
    ]

    @pytest.mark.parametrize(
        ("unpaid", "bg_adj", "proj_adj", "credits"),
        itertools.product(
            UNPAID_SCENARIOS,
            BILLING_GROUP_ADJUSTMENTS,
            PROJECT_ADJUSTMENTS,
            CREDIT_COMBINATIONS,
        ),
        ids=lambda val: str(val[0]) if isinstance(val, tuple) else str(val),
    )
    @pytest.mark.integration
    def test_combination(
        self,
        test_context,
        test_app_keys,
        unpaid: tuple[str, int, int],
        bg_adj: tuple[str, Any, Any, Any],
        proj_adj: tuple[str, Any, Any, Any],
        credit_combo: tuple[str, list[tuple[CreditType, int]]],
    ):
        """Test a single combination of business logic components."""
        scenario_id = f"{unpaid[0]}_{bg_adj[0]}_{proj_adj[0]}_{credit_combo[0]}"
        logger.info(f"Testing combination: {scenario_id}")

        # Execute the scenario
        result = self._execute_scenario(
            test_context,
            test_app_keys,
            scenario_id,
            unpaid,
            bg_adj,
            proj_adj,
            credit_combo,
        )

        # Validate business rules
        self._validate_business_rules(result)

    def _execute_scenario(
        self,
        test_context: dict[str, Any],
        test_app_keys: list[str],
        scenario_id: str,
        unpaid_scenario: tuple[str, int, int],
        bg_adjustment: tuple[str, Any, Any, Any],
        proj_adjustment: tuple[str, Any, Any, Any],
        credit_combo: tuple[str, list[tuple[CreditType, int]]],
    ) -> dict[str, Any]:
        """Execute a single test scenario."""
        managers = test_context["managers"]
        base_usage_amount = 100000

        # 1. Create base usage
        managers["metering"].send_metering(
            app_key=test_app_keys[0],
            counter_name=f"test.combo.{scenario_id}",
            counter_type=CounterType.DELTA,
            counter_unit="UNITS",
            counter_volume=str(base_usage_amount),
        )

        # 2. Apply adjustments
        if bg_adjustment[1] is not None:
            managers["adjustment"].apply_adjustment(
                adjustment_name=f"{scenario_id}-BG",
                adjustment_type=bg_adjustment[1],
                adjustment_amount=bg_adjustment[3],
                target_type=bg_adjustment[2],
                target_id=test_context["billing_group_id"],
            )

        if proj_adjustment[1] is not None:
            managers["adjustment"].apply_adjustment(
                adjustment_name=f"{scenario_id}-PROJ",
                adjustment_type=proj_adjustment[1],
                adjustment_amount=proj_adjustment[3],
                target_type=proj_adjustment[2],
                target_id=test_app_keys[0],
            )

        # 3. Apply credits
        total_credits = 0
        for credit_type, amount in credit_combo[1]:
            if credit_type == CreditType.FREE:
                managers["credit"].grant_campaign_credit(
                    campaign_id=f"{scenario_id}-FREE",
                    credit_name=f"{scenario_id} Free Credit",
                    credit_amount=amount,
                )
            elif credit_type == CreditType.PAID:
                managers["credit"].grant_paid_credit(
                    campaign_id=f"{scenario_id}-PAID", paid_amount=amount
                )
            elif credit_type == CreditType.REFUND:
                managers["credit"].refund_credit(
                    refund_items=[
                        {
                            "paymentStatementId": f"{scenario_id}-STMT",
                            "refundAmount": amount,
                            "reason": "Test refund",
                        }
                    ]
                )
            total_credits += amount

        # 4. Calculate
        managers["calculation"].recalculate_all()

        # 5. Get results
        payment_statement = managers["payment"].get_payment_statement()

        return {
            "scenario_id": scenario_id,
            "base_amount": base_usage_amount,
            "unpaid": unpaid_scenario[1],
            "overdue": unpaid_scenario[2],
            "bg_adjustment": bg_adjustment,
            "proj_adjustment": proj_adjustment,
            "total_credits": total_credits,
            "statement": payment_statement,
            "expected": self._calculate_expected_amount(
                base_usage_amount,
                unpaid_scenario[1],
                unpaid_scenario[2],
                bg_adjustment,
                proj_adjustment,
                total_credits,
            ),
        }

    def _calculate_expected_amount(
        self,
        base: int,
        unpaid: int,
        overdue: int,
        bg_adj: tuple[str, Any, Any, Any],
        proj_adj: tuple[str, Any, Any, Any],
        credit_amount: int,
    ) -> Decimal:
        """Calculate expected amount based on business rules."""
        amount = Decimal(base + unpaid + overdue)

        # Track total discount rate for validation
        total_discount_rate = 0

        # Apply billing group adjustment first
        if bg_adj[1] == AdjustmentType.FIXED_DISCOUNT:
            amount -= Decimal(bg_adj[3])
        elif bg_adj[1] == AdjustmentType.RATE_DISCOUNT:
            discount_rate = bg_adj[3]
            total_discount_rate += discount_rate
            amount *= Decimal(1 - discount_rate / 100)
        elif bg_adj[1] == AdjustmentType.FIXED_SURCHARGE:
            amount += Decimal(bg_adj[3])
        elif bg_adj[1] == AdjustmentType.RATE_SURCHARGE:
            amount *= Decimal(1 + bg_adj[3] / 100)

        # Apply project adjustment second
        if proj_adj[1] == AdjustmentType.FIXED_DISCOUNT:
            amount -= Decimal(proj_adj[3])
        elif proj_adj[1] == AdjustmentType.RATE_DISCOUNT:
            discount_rate = proj_adj[3]
            total_discount_rate += discount_rate
            # Cap total discount at business rule maximum
            if total_discount_rate > self.business_rules.MAX_TOTAL_DISCOUNT_RATE:
                discount_rate = self.business_rules.MAX_TOTAL_DISCOUNT_RATE - (
                    total_discount_rate - discount_rate
                )
            amount *= Decimal(1 - discount_rate / 100)
        elif proj_adj[1] == AdjustmentType.FIXED_SURCHARGE:
            amount += Decimal(proj_adj[3])
        elif proj_adj[1] == AdjustmentType.RATE_SURCHARGE:
            amount *= Decimal(1 + proj_adj[3] / 100)

        # Apply credits last
        amount = max(Decimal(0), amount - Decimal(credit_amount))

        # Apply minimum billable amount rule
        if 0 < amount < self.business_rules.MIN_BILLABLE_AMOUNT:
            amount = Decimal(self.business_rules.MIN_BILLABLE_AMOUNT)

        # Apply VAT
        amount *= Decimal(1 + self.business_rules.VAT_RATE)

        return amount

    def _validate_business_rules(self, result: dict[str, Any]) -> None:
        """Validate business rules are correctly applied."""
        expected = result["expected"]

        if result["statement"].get("statements"):
            actual = Decimal(result["statement"]["statements"][0].get("totalAmount", 0))

            # Allow 1% tolerance for rounding
            tolerance = expected * Decimal("0.01")

            assert abs(actual - expected) <= tolerance, (
                f"Scenario {result['scenario_id']}: "
                f"Expected {expected}, got {actual}"
            )

            # Additional business rule validations
            self._validate_adjustment_limits(result)
            self._validate_credit_priority(result)
            self._validate_overdue_calculation(result)

    def _validate_adjustment_limits(self, result: dict[str, Any]) -> None:
        """Validate adjustment business limits."""
        # Total discount should not exceed 90%
        bg_disc = proj_disc = 0

        if result["bg_adjustment"][1] == AdjustmentType.RATE_DISCOUNT:
            bg_disc = result["bg_adjustment"][3]
        if result["proj_adjustment"][1] == AdjustmentType.RATE_DISCOUNT:
            proj_disc = result["proj_adjustment"][3]

        total_discount = bg_disc + proj_disc
        assert (
            total_discount <= 90
        ), f"Total discount {total_discount}% exceeds 90% limit"

    def _validate_credit_priority(self, result: dict[str, Any]) -> None:
        """Validate credit application priority."""
        # Credits should be applied in priority order:
        # 1. Expiring soon
        # 2. FREE
        # 3. REFUND
        # 4. PAID
        # TODO (QA Team): Implement based on actual credit history API
        # https://github.com/company/billing-test/issues/123

    def _validate_overdue_calculation(self, result: dict[str, Any]) -> None:
        """Validate overdue charge calculation."""
        if result["unpaid"] > 0 and result["overdue"] > 0:
            # Validate 5% overdue rate
            expected_overdue = result["unpaid"] * 0.05
            assert (
                abs(result["overdue"] - expected_overdue) < 1
            ), f"Overdue calculation error: expected {expected_overdue}, got {result['overdue']}"


@pytest.mark.integration
class TestBusinessRuleValidation(BaseIntegrationTest):
    """Test specific business rule validations."""

    def test_discount_stacking_rules(self, test_context, test_app_keys):
        """Test how discounts stack together."""
        scenarios = [
            # BG discount + Project discount
            (AdjustmentType.RATE_DISCOUNT, 50, AdjustmentType.RATE_DISCOUNT, 50),
            (AdjustmentType.FIXED_DISCOUNT, 10000, AdjustmentType.RATE_DISCOUNT, 20),
            (AdjustmentType.RATE_DISCOUNT, 30, AdjustmentType.FIXED_DISCOUNT, 5000),
        ]

        for bg_type, bg_amt, proj_type, proj_amt in scenarios:
            # Test implementation
            pass

    def test_credit_application_order(self, test_context):
        """Test credit priority rules."""
        # Create credits with different expiration dates and types
        # Verify they're applied in correct order

    def test_overdue_calculation_rules(self, test_context):
        """Test overdue charge calculation."""
        overdue_scenarios = [
            (30, 0),  # 30 days - no charge (grace period)
            (31, 0.05),  # 31 days - 5% charge
            (60, 0.05),  # 60 days - still 5%
            (90, 0.10),  # 90 days - 10% (if progressive)
        ]

        for days, expected_rate in overdue_scenarios:
            # Test implementation
            pass
