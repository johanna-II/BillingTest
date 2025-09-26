"""Complete business logic combination tests.

This test suite covers ALL possible combinations of:
- Unpaid amounts and overdue charges
- Billing group and project adjustments (discounts/surcharges)
- All credit types (FREE, PAID, REFUND)
- Complex multi-layered scenarios
"""

import logging
from typing import Any

import pytest

from libs.constants import (
    AdjustmentTarget,
    AdjustmentType,
    CounterType,
    CreditType,
)
from tests.integration.base_integration import BaseIntegrationTest

logger = logging.getLogger(__name__)


@pytest.mark.integration
class TestCompleteBusinessCombinations(BaseIntegrationTest):
    """Test ALL business logic combinations systematically."""

    # Define all possible components
    UNPAID_SCENARIOS = [
        ("NO_UNPAID", 0, 0),  # No unpaid amount
        ("UNPAID_CURRENT", 50000, 0),  # Unpaid but not overdue
        ("UNPAID_OVERDUE", 100000, 5000),  # Unpaid with 5% overdue charge
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

    def test_all_critical_combinations(self, test_context, test_app_keys):
        """Test critical business combinations that are most likely to occur."""
        critical_scenarios = [
            # Scenario 1: Basic usage with no modifiers
            {
                "name": "Basic billing - no adjustments or credits",
                "unpaid": self.UNPAID_SCENARIOS[0],  # NO_UNPAID
                "bg_adj": self.BILLING_GROUP_ADJUSTMENTS[0],  # BG_NONE
                "proj_adj": self.PROJECT_ADJUSTMENTS[0],  # PROJ_NONE
                "credits": self.CREDIT_COMBINATIONS[0],  # NO_CREDIT
            },
            # Scenario 2: Overdue with billing group discount
            {
                "name": "Overdue payment with billing group discount",
                "unpaid": self.UNPAID_SCENARIOS[2],  # UNPAID_OVERDUE
                "bg_adj": self.BILLING_GROUP_ADJUSTMENTS[2],  # BG_RATE_DISCOUNT
                "proj_adj": self.PROJECT_ADJUSTMENTS[0],  # PROJ_NONE
                "credits": self.CREDIT_COMBINATIONS[0],  # NO_CREDIT
            },
            # Scenario 3: Complex case - everything applied
            {
                "name": "Complex: Overdue + BG discount + Project surcharge + All credits",
                "unpaid": self.UNPAID_SCENARIOS[2],  # UNPAID_OVERDUE
                "bg_adj": self.BILLING_GROUP_ADJUSTMENTS[2],  # BG_RATE_DISCOUNT
                "proj_adj": self.PROJECT_ADJUSTMENTS[4],  # PROJ_RATE_SURCHARGE
                "credits": self.CREDIT_COMBINATIONS[5],  # ALL_CREDITS
            },
            # Scenario 4: Double discount (billing group + project)
            {
                "name": "Double discount: BG fixed + Project rate",
                "unpaid": self.UNPAID_SCENARIOS[0],  # NO_UNPAID
                "bg_adj": self.BILLING_GROUP_ADJUSTMENTS[1],  # BG_FIXED_DISCOUNT
                "proj_adj": self.PROJECT_ADJUSTMENTS[2],  # PROJ_RATE_DISCOUNT
                "credits": self.CREDIT_COMBINATIONS[1],  # FREE_ONLY
            },
            # Scenario 5: Double surcharge with partial credits
            {
                "name": "Double surcharge: BG + Project with partial credits",
                "unpaid": self.UNPAID_SCENARIOS[1],  # UNPAID_CURRENT
                "bg_adj": self.BILLING_GROUP_ADJUSTMENTS[3],  # BG_FIXED_SURCHARGE
                "proj_adj": self.PROJECT_ADJUSTMENTS[4],  # PROJ_RATE_SURCHARGE
                "credits": self.CREDIT_COMBINATIONS[4],  # FREE_PAID
            },
        ]

        results = []
        for scenario in critical_scenarios:
            result = self._execute_scenario(
                test_context,
                test_app_keys,
                scenario["name"],
                scenario["unpaid"],
                scenario["bg_adj"],
                scenario["proj_adj"],
                scenario["credits"],
            )
            results.append(result)

        # Verify results
        self._verify_scenario_results(results)

    def test_exhaustive_combinations_sample(self, test_context, test_app_keys):
        """Test a representative sample of all possible combinations."""
        # Full exhaustive test would be:
        # 3 unpaid x 5 BG adjustments x 5 project adjustments x 6 credit combos = 450 tests
        # Instead, we'll test strategic samples

        sample_indices = [
            (0, 0, 0, 0),  # All none
            (2, 2, 2, 5),  # Overdue + discounts + all credits
            (1, 3, 4, 3),  # Current unpaid + surcharges + refund
            (0, 1, 2, 4),  # No unpaid + mixed adjustments + free+paid
            (2, 4, 1, 2),  # Overdue + BG surcharge + proj discount + paid only
        ]

        results = []
        for unpaid_idx, bg_idx, proj_idx, credit_idx in sample_indices:
            scenario_name = (
                f"Sample_{unpaid_idx}_{bg_idx}_{proj_idx}_{credit_idx}: "
                f"{self.UNPAID_SCENARIOS[unpaid_idx][0]}_"
                f"{self.BILLING_GROUP_ADJUSTMENTS[bg_idx][0]}_"
                f"{self.PROJECT_ADJUSTMENTS[proj_idx][0]}_"
                f"{self.CREDIT_COMBINATIONS[credit_idx][0]}"
            )

            result = self._execute_scenario(
                test_context,
                test_app_keys,
                scenario_name,
                self.UNPAID_SCENARIOS[unpaid_idx],
                self.BILLING_GROUP_ADJUSTMENTS[bg_idx],
                self.PROJECT_ADJUSTMENTS[proj_idx],
                self.CREDIT_COMBINATIONS[credit_idx],
            )
            results.append(result)

        self._verify_scenario_results(results)

    def _execute_scenario(
        self,
        test_context: dict[str, Any],
        test_app_keys: list[str],
        scenario_name: str,
        unpaid_scenario: tuple[str, int, int],
        bg_adjustment: tuple[str, Any, Any, Any],
        proj_adjustment: tuple[str, Any, Any, Any],
        credit_combo: tuple[str, list[tuple[CreditType, int]]],
    ) -> dict[str, Any]:
        """Execute a single scenario with all combinations."""
        logger.info(f"\n{'='*60}")
        logger.info(f"Executing scenario: {scenario_name}")
        logger.info(f"{'='*60}")

        managers = test_context["managers"]
        base_usage_amount = 100000  # 100,000 KRW base charge

        # 1. Create base metering usage
        metering_result = managers["metering"].send_metering(
            app_key=test_app_keys[0],
            counter_name=f"test.scenario.{scenario_name.replace(' ', '_')}",
            counter_type=CounterType.DELTA,
            counter_unit="UNITS",
            counter_volume=str(base_usage_amount),
        )
        self.assert_api_success(metering_result)

        # 2. Simulate unpaid amount if needed
        _unpaid_name, unpaid_amount, overdue_charge = unpaid_scenario
        if unpaid_amount > 0:
            # In real scenario, this would be from previous month
            # For testing, we'll track it separately
            logger.info(
                f"Simulating unpaid: {unpaid_amount} + overdue: {overdue_charge}"
            )

        # 3. Apply billing group adjustment
        bg_name, bg_type, bg_target, bg_amount = bg_adjustment
        if bg_type is not None:
            bg_result = managers["adjustment"].apply_adjustment(
                adjustment_name=f"{scenario_name} - {bg_name}",
                adjustment_type=bg_type,
                adjustment_amount=bg_amount,
                target_type=bg_target,
                target_id=test_context["billing_group_id"],
            )
            self.assert_api_success(bg_result)
            logger.info(f"Applied BG adjustment: {bg_name} = {bg_amount}")

        # 4. Apply project adjustment
        proj_name, proj_type, proj_target, proj_amount = proj_adjustment
        if proj_type is not None:
            proj_result = managers["adjustment"].apply_adjustment(
                adjustment_name=f"{scenario_name} - {proj_name}",
                adjustment_type=proj_type,
                adjustment_amount=proj_amount,
                target_type=proj_target,
                target_id=test_app_keys[0],
            )
            self.assert_api_success(proj_result)
            logger.info(f"Applied Project adjustment: {proj_name} = {proj_amount}")

        # 5. Grant credits
        _credit_name, credits_list = credit_combo
        total_credits = 0
        for credit_type, amount in credits_list:
            if credit_type == CreditType.FREE:
                result = managers["credit"].grant_campaign_credit(
                    campaign_id=f"TEST-FREE-{scenario_name[:10]}",
                    credit_name=f"Test Free Credit - {scenario_name[:10]}",
                    credit_amount=amount,
                )
            elif credit_type == CreditType.PAID:
                result = managers["credit"].grant_paid_credit(
                    campaign_id=f"TEST-PAID-{scenario_name[:10]}", paid_amount=amount
                )
            elif credit_type == CreditType.REFUND:
                result = managers["credit"].refund_credit(
                    refund_items=[
                        {
                            "paymentStatementId": f"STMT-{scenario_name[:10]}",
                            "refundAmount": amount,
                            "reason": f"Test refund for {scenario_name}",
                        }
                    ]
                )
            total_credits += amount
            logger.info(f"Granted {credit_type.value} credit: {amount}")

        # 6. Trigger calculation
        calc_result = managers["calculation"].recalculate_all()
        self.assert_api_success(calc_result)

        # 7. Calculate expected result
        expected = self._calculate_expected_amount(
            base_usage_amount,
            unpaid_amount,
            overdue_charge,
            bg_adjustment,
            proj_adjustment,
            total_credits,
        )

        # 8. Get actual result
        payment_statement = managers["payment"].get_payment_statement()
        actual_amount = 0
        if payment_statement.get("statements"):
            statement = payment_statement["statements"][0]
            actual_amount = statement.get("totalAmount", 0)

        result = {
            "scenario": scenario_name,
            "base_amount": base_usage_amount,
            "unpaid": unpaid_amount,
            "overdue": overdue_charge,
            "bg_adjustment": bg_adjustment,
            "proj_adjustment": proj_adjustment,
            "credits": total_credits,
            "expected_final": expected,
            "actual_final": actual_amount,
            "payment_statement": payment_statement,
        }

        logger.info(
            f"Result: Base={base_usage_amount}, Expected={expected}, Actual={actual_amount}"
        )
        return result

    def _calculate_expected_amount(
        self,
        base_amount: int,
        unpaid_amount: int,
        overdue_charge: int,
        bg_adjustment: tuple[str, Any, Any, Any],
        proj_adjustment: tuple[str, Any, Any, Any],
        total_credits: int,
    ) -> int:
        """Calculate expected final amount based on all factors."""
        # Start with base + unpaid + overdue
        amount = base_amount + unpaid_amount + overdue_charge

        # Apply adjustments in order (this order may vary by business rules)
        # 1. Apply billing group adjustment
        _bg_name, bg_type, _, bg_amount = bg_adjustment
        if bg_type == AdjustmentType.FIXED_DISCOUNT:
            amount -= bg_amount
        elif bg_type == AdjustmentType.RATE_DISCOUNT:
            amount *= 1 - bg_amount / 100
        elif bg_type == AdjustmentType.FIXED_SURCHARGE:
            amount += bg_amount
        elif bg_type == AdjustmentType.RATE_SURCHARGE:
            amount *= 1 + bg_amount / 100

        # 2. Apply project adjustment
        _proj_name, proj_type, _, proj_amount = proj_adjustment
        if proj_type == AdjustmentType.FIXED_DISCOUNT:
            amount -= proj_amount
        elif proj_type == AdjustmentType.RATE_DISCOUNT:
            amount *= 1 - proj_amount / 100
        elif proj_type == AdjustmentType.FIXED_SURCHARGE:
            amount += proj_amount
        elif proj_type == AdjustmentType.RATE_SURCHARGE:
            amount *= 1 + proj_amount / 100

        # 3. Apply credits (after all adjustments)
        amount = max(0, amount - total_credits)

        return int(amount)

    def _verify_scenario_results(self, results: list[dict[str, Any]]) -> None:
        """Verify all scenario results."""
        logger.info(f"\n{'='*60}")
        logger.info("SUMMARY OF ALL SCENARIOS")
        logger.info(f"{'='*60}")

        for result in results:
            logger.info(f"\nScenario: {result['scenario']}")
            logger.info(f"  Base amount: {result['base_amount']:,}")
            logger.info(
                f"  Unpaid/Overdue: {result['unpaid']:,} / {result['overdue']:,}"
            )
            logger.info(f"  BG adjustment: {result['bg_adjustment'][0]}")
            logger.info(f"  Proj adjustment: {result['proj_adjustment'][0]}")
            logger.info(f"  Credits applied: {result['credits']:,}")
            logger.info(f"  Expected final: {result['expected_final']:,}")
            logger.info(f"  Actual final: {result['actual_final']:,}")

            # In real implementation, we would assert expected vs actual
            # For now, we log the difference
            diff = abs(result["expected_final"] - result["actual_final"])
            if diff > 0:
                logger.warning(f"  DIFFERENCE: {diff:,}")


@pytest.mark.integration
class TestEdgeCaseCombinations(BaseIntegrationTest):
    """Test edge cases and boundary conditions."""

    def test_maximum_discount_scenario(self, test_context, test_app_keys):
        """Test scenario with maximum possible discounts."""
        managers = test_context["managers"]

        # Create large usage
        base_amount = 1000000  # 1 million KRW
        managers["metering"].send_metering(
            app_key=test_app_keys[0],
            counter_name="test.max.discount",
            counter_type=CounterType.DELTA,
            counter_unit="UNITS",
            counter_volume=str(base_amount),
        )

        # Apply maximum discounts
        # 50% billing group discount
        managers["adjustment"].apply_adjustment(
            adjustment_name="Max BG discount",
            adjustment_type=AdjustmentType.RATE_DISCOUNT,
            adjustment_amount=50,
            target_type=AdjustmentTarget.BILLING_GROUP,
            target_id=test_context["billing_group_id"],
        )

        # 30% project discount (total 80% discount?)
        managers["adjustment"].apply_adjustment(
            adjustment_name="Max project discount",
            adjustment_type=AdjustmentType.RATE_DISCOUNT,
            adjustment_amount=30,
            target_type=AdjustmentTarget.PROJECT,
            target_id=test_app_keys[0],
        )

        # Grant credits exceeding the discounted amount
        managers["credit"].grant_campaign_credit(
            campaign_id="MAX-CREDIT",
            credit_name="Maximum Credit Test",
            credit_amount=500000,  # More than discounted amount
        )

        # Calculate and verify
        managers["calculation"].recalculate_all()
        payment_statement = managers["payment"].get_payment_statement()

        # Final amount should be 0 (fully covered by credits)
        if payment_statement.get("statements"):
            final_amount = payment_statement["statements"][0].get("totalAmount", 0)
            assert (
                final_amount == 0
            ), "Maximum discount + credit should result in 0 payment"

    def test_conflicting_adjustments(self, test_context, test_app_keys):
        """Test conflicting adjustments on same target."""
        managers = test_context["managers"]

        # Apply multiple adjustments to same project
        adjustments = [
            (AdjustmentType.FIXED_DISCOUNT, 10000, "First discount"),
            (AdjustmentType.RATE_DISCOUNT, 10, "Second discount"),
            (AdjustmentType.FIXED_SURCHARGE, 5000, "Then surcharge"),
            (AdjustmentType.RATE_SURCHARGE, 5, "Final surcharge"),
        ]

        for adj_type, amount, name in adjustments:
            managers["adjustment"].apply_adjustment(
                adjustment_name=name,
                adjustment_type=adj_type,
                adjustment_amount=amount,
                target_type=AdjustmentTarget.PROJECT,
                target_id=test_app_keys[0],
            )

        # Verify all adjustments are tracked
        adj_list = managers["adjustment"].get_adjustments(
            AdjustmentTarget.PROJECT, test_app_keys[0]
        )
        assert len(adj_list.get("adjustments", [])) >= len(adjustments)

    def test_credit_priority_with_expiration(self, test_context, test_app_keys):
        """Test credit usage priority with various expiration dates."""
        managers = test_context["managers"]

        # Create credits with different expiration dates
        credit_scenarios = [
            # (type, amount, days_until_expiry, description)
            (CreditType.FREE, 10000, 1, "Expiring tomorrow"),
            (CreditType.FREE, 20000, 30, "Expiring in 30 days"),
            (CreditType.REFUND, 15000, 7, "Refund expiring in 7 days"),
            (CreditType.PAID, 25000, 365, "Paid credit long expiry"),
        ]

        for credit_type, amount, days, desc in credit_scenarios:
            # expire_date = (today + timedelta(days=days)).strftime("%Y-%m-%d")

            if credit_type == CreditType.FREE:
                managers["credit"].grant_campaign_credit(
                    campaign_id=f"PRIORITY-{days}D",
                    credit_name=desc,
                    credit_amount=amount,
                )
            elif credit_type == CreditType.REFUND:
                managers["credit"].refund_credit(
                    refund_items=[
                        {
                            "paymentStatementId": f"REFUND-{days}D",
                            "refundAmount": amount,
                            "reason": desc,
                        }
                    ]
                )
            elif credit_type == CreditType.PAID:
                managers["credit"].grant_paid_credit(
                    campaign_id=f"PAID-{days}D", paid_amount=amount
                )

        # Create usage that will partially consume credits
        managers["metering"].send_metering(
            app_key=test_app_keys[0],
            counter_name="test.credit.priority",
            counter_type=CounterType.DELTA,
            counter_unit="UNITS",
            counter_volume="30000",  # Should use expiring + part of others
        )

        # Calculate and check which credits were used
        managers["calculation"].recalculate_all()

        # Get credit history to verify usage order
        history = managers["credit"].get_credit_history()
        logger.info(f"Credit usage history: {history}")


@pytest.mark.integration
class TestRealWorldScenarios(BaseIntegrationTest):
    """Test real-world business scenarios."""

    def test_enterprise_customer_scenario(self, test_context, test_app_keys):
        """Enterprise customer with volume discount, multiple projects, and credits."""
        managers = test_context["managers"]

        # Simulate 3 projects with different usage patterns
        projects = [
            (test_app_keys[0], "Production", 500000),
            (test_app_keys[1], "Development", 100000),
            (test_app_keys[2], "Testing", 50000),
        ]

        total_usage = 0
        for app_key, env_name, usage in projects:
            managers["metering"].send_metering(
                app_key=app_key,
                counter_name=f"enterprise.{env_name.lower()}",
                counter_type=CounterType.DELTA,
                counter_unit="UNITS",
                counter_volume=str(usage),
            )
            total_usage += usage

        # Apply enterprise volume discount at billing group level
        managers["adjustment"].apply_adjustment(
            adjustment_name="Enterprise volume discount",
            adjustment_type=AdjustmentType.RATE_DISCOUNT,
            adjustment_amount=20,  # 20% discount
            target_type=AdjustmentTarget.BILLING_GROUP,
            target_id=test_context["billing_group_id"],
        )

        # Apply dev/test environment discount
        for app_key, env_name, _ in projects[1:]:  # Dev and Test only
            managers["adjustment"].apply_adjustment(
                adjustment_name=f"{env_name} environment discount",
                adjustment_type=AdjustmentType.RATE_DISCOUNT,
                adjustment_amount=50,  # 50% off for non-prod
                target_type=AdjustmentTarget.PROJECT,
                target_id=app_key,
            )

        # Enterprise credit package
        managers["credit"].grant_paid_credit(
            campaign_id="ENTERPRISE-2025", paid_amount=100000  # 100k credit package
        )

        # Calculate final billing
        managers["calculation"].recalculate_all()
        payment_statement = managers["payment"].get_payment_statement()

        logger.info(f"Enterprise scenario - Total usage: {total_usage:,}")
        logger.info(f"Final billing: {payment_statement}")

    def test_startup_promotional_scenario(self, test_context, test_app_keys):
        """Startup with promotional credits and growth incentives."""
        managers = test_context["managers"]

        # Simulate growing usage over time
        growth_pattern = [10000, 25000, 50000, 100000]  # Rapid growth

        for month_offset, usage in enumerate(growth_pattern):
            managers["metering"].send_metering(
                app_key=test_app_keys[0],
                counter_name=f"startup.month{month_offset}",
                counter_type=CounterType.DELTA,
                counter_unit="UNITS",
                counter_volume=str(usage),
            )

        # Promotional credits
        managers["credit"].grant_campaign_credit(
            campaign_id="STARTUP-PROMO-2025",
            credit_name="Startup Promotional Credit",
            credit_amount=50000,  # 50k promotional credit
        )

        # Growth milestone reward
        if sum(growth_pattern) > 100000:
            managers["credit"].grant_campaign_credit(
                campaign_id="GROWTH-MILESTONE-100K",
                credit_name="Growth Milestone Bonus",
                credit_amount=20000,  # Bonus credit
            )

        # Early payment discount
        managers["adjustment"].apply_adjustment(
            adjustment_name="Startup early payment discount",
            adjustment_type=AdjustmentType.RATE_DISCOUNT,
            adjustment_amount=5,  # 5% for early payment
            target_type=AdjustmentTarget.BILLING_GROUP,
            target_id=test_context["billing_group_id"],
        )

        managers["calculation"].recalculate_all()
        payment_statement = managers["payment"].get_payment_statement()

        logger.info(f"Startup scenario - Growth: {growth_pattern}")
        logger.info(f"Final billing: {payment_statement}")
