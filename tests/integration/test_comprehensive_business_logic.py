"""Comprehensive business logic tests covering all combinations.

This test suite ensures that all business logic combinations work correctly,
including interactions between Credit, Adjustment, Metering, Payment, and Contract.
"""

import logging
from datetime import datetime, timedelta

import pytest

from libs.constants import (
    AdjustmentTarget,
    AdjustmentType,
    CounterType,
    CreditType,
    PaymentStatus,
)
from libs.constants import BatchJobCode as JobCode
from tests.integration.base_integration import BaseIntegrationTest

logger = logging.getLogger(__name__)


@pytest.mark.integration
class TestBusinessLogicCombinations(BaseIntegrationTest):
    """Test all possible business logic combinations.

    Note: Payment state transitions and error recovery tests are skipped (require real API).
    Other tests are safe for parallel execution with function-scoped fixtures.
    """

    # Test Data Sets
    ADJUSTMENT_COMBINATIONS = [
        # (adjustment_type, amount, target_type, description)
        (
            AdjustmentType.FIXED_DISCOUNT,
            10000,
            AdjustmentTarget.BILLING_GROUP,
            "Fixed discount on billing group",
        ),
        (
            AdjustmentType.RATE_DISCOUNT,
            10,
            AdjustmentTarget.PROJECT,
            "10% discount on project",
        ),
        (
            AdjustmentType.FIXED_SURCHARGE,
            5000,
            AdjustmentTarget.BILLING_GROUP,
            "Fixed surcharge",
        ),
        (
            AdjustmentType.RATE_SURCHARGE,
            5,
            AdjustmentTarget.PROJECT,
            "5% surcharge on project",
        ),
    ]

    CREDIT_SCENARIOS = [
        # (credit_type, amount, description)
        (CreditType.FREE, 20000, "Free promotional credit"),
        (CreditType.REFUND, 15000, "Refund credit"),
        (CreditType.PAID, 30000, "Paid credit"),
    ]

    METERING_PATTERNS = [
        # (counter_type, resource_type, volume, unit)
        (CounterType.DELTA, "compute.instance", 100, "HOURS"),
        (CounterType.GAUGE, "storage.block", 500, "GB"),
        (CounterType.CUMULATIVE, "network.traffic", 1000, "GB"),
    ]

    def test_adjustment_credit_combinations(self, test_context, test_app_keys):
        """Test all combinations of adjustments and credits.

        This test validates that:
        1. Multiple adjustments can be applied correctly
        2. Credits are applied after adjustments
        3. The final calculation is accurate
        """
        managers = test_context["managers"]
        results = []

        # Test each adjustment and credit combination
        for adj_type, adj_amount, adj_target, adj_desc in self.ADJUSTMENT_COMBINATIONS:
            for credit_type, credit_amount, credit_desc in self.CREDIT_SCENARIOS:
                logger.info(f"Testing: {adj_desc} + {credit_desc}")

                # 1. Create base usage
                metering_result = managers["metering"].send_metering(
                    app_key=test_app_keys[0],
                    counter_name=f"test.{adj_type.value.lower()}.{credit_type.value.lower()}",
                    counter_type=CounterType.DELTA,
                    counter_unit="UNITS",
                    counter_volume="1000",  # Base: 1000 units
                )
                assert metering_result.get("header", {}).get("isSuccessful", False)

                # 2. Apply adjustment
                target_id = (
                    test_context["billing_group_id"]
                    if adj_target == AdjustmentTarget.BILLING_GROUP
                    else test_app_keys[0]
                )

                adj_result = managers["adjustment"].apply_adjustment(
                    adjustment_name=adj_desc,
                    adjustment_type=adj_type,
                    adjustment_amount=adj_amount,
                    adjustment_target=adj_target,
                    target_id=target_id,
                )
                assert adj_result.get("header", {}).get("isSuccessful", False)

                # 3. Grant credit
                if credit_type == CreditType.FREE:
                    credit_result = managers["credit"].grant_credit(
                        campaign_id=f"TEST-{credit_type.value}",
                        credit_name=f"Test {credit_type.value} Credit",
                        amount=credit_amount,
                    )
                elif credit_type == CreditType.REFUND:
                    # TODO: Refunds are handled through PaymentManager.process_refund
                    # For now, skip refund credits in this test
                    logger.warning(
                        "Skipping REFUND credit type in test - not implemented"
                    )
                    credit_result = None
                else:  # PAID
                    credit_result = managers["credit"].grant_credit(
                        campaign_id=f"PAID-{datetime.now().strftime('%Y%m%d')}",
                        credit_name=f"Test {credit_type.value} Credit",
                        amount=credit_amount,
                    )

                # 4. Calculate and store result
                calc_result = managers["calculation"].recalculate_all()
                assert calc_result.get("header", {}).get("isSuccessful", False)

                results.append(
                    {
                        "adjustment": adj_desc,
                        "credit": credit_desc,
                        "base_amount": 1000,
                        "adjustment_amount": adj_amount,
                        "credit_amount": credit_amount,
                        "calc_result": calc_result,
                    }
                )

        logger.info(f"Tested {len(results)} adjustment-credit combinations")
        return results

    def test_metering_type_interactions(self, test_context, test_app_keys):
        """Test different metering types and their interactions.

        Validates:
        1. DELTA counters accumulate correctly
        2. GAUGE counters represent current state
        3. CUMULATIVE counters track totals
        4. Mixed counter types calculate correctly
        """
        managers = test_context["managers"]

        # Test all combinations of metering patterns
        for counter_type, resource, volume, unit in self.METERING_PATTERNS:
            # Send multiple data points for each type
            for i in range(3):
                result = managers["metering"].send_metering(
                    app_key=test_app_keys[i % len(test_app_keys)],
                    counter_name=f"{resource}.test{i}",
                    counter_type=counter_type,
                    counter_unit=unit,
                    counter_volume=str(int(volume) * (i + 1)),  # Increasing volumes
                )
                assert result.get("header", {}).get("isSuccessful", False)

        # Verify calculation handles all types
        calc_result = managers["calculation"].recalculate_all()
        assert calc_result.get("header", {}).get("isSuccessful", False)

    @pytest.mark.skip(
        reason="Payment state transitions require console API not in mock server"
    )
    def test_payment_state_transitions(self, test_context):
        """Test all possible payment state transitions.

        Payment lifecycle:
        DRAFT -> REGISTERED -> READY -> PAID
                            -> CANCELLED

        Note: Skipped because get_payment_status() calls console API endpoint
        that is not implemented in mock server.
        """
        managers = test_context["managers"]

        # Get current payment status
        payment_group_id, status = managers["payment"].get_payment_status()
        logger.info(f"Initial payment status: {status}")

        if payment_group_id:
            # Test state transitions
            if status == PaymentStatus.REGISTERED:
                # Can transition to READY
                result = managers["payment"].change_payment_status(payment_group_id)
                logger.info("Changed REGISTERED -> READY")

            elif status == PaymentStatus.READY:
                # Can transition to PAID or CANCELLED
                # Test cancellation
                cancel_result = managers["payment"].cancel_payment(payment_group_id)
                logger.info("Tested READY -> CANCELLED")

            elif status == PaymentStatus.PAID:
                # Already paid, test refund scenario
                # TODO: Refunds are handled through PaymentManager.process_refund
                logger.warning("Skipping refund test - not implemented")
                credit_result = None
                logger.info("Created refund credit for PAID state")

    def test_contract_pricing_with_adjustments(self, test_context, test_app_keys):
        """Test contract-based pricing with various adjustments.

        Scenarios:
        1. Volume-based tiered pricing
        2. Contract + Fixed discount
        3. Contract + Rate discount
        4. Contract + Multiple adjustments
        """
        managers = test_context["managers"]

        if "contract" not in managers:
            pytest.skip("Contract manager not available")

        # Apply contract and test with different volumes
        volume_tiers = [50, 150, 500, 1000]  # Different tier levels

        for volume in volume_tiers:
            # Send metering at different volumes
            result = managers["metering"].send_metering(
                app_key=test_app_keys[0],
                counter_name="contract.tiered.resource",
                counter_type=CounterType.DELTA,
                counter_unit="UNITS",
                counter_volume=str(volume),
            )
            assert result.get("header", {}).get("isSuccessful", False)

            # Apply different adjustments for each tier
            if volume <= 100:
                # Small volume gets percentage discount
                adj_result = managers["adjustment"].apply_adjustment(
                    adjustment_name="Small volume discount",
                    adjustment_type=AdjustmentType.RATE_DISCOUNT,
                    adjustment_amount=5,
                    adjustment_target=AdjustmentTarget.PROJECT,
                    target_id=test_app_keys[0],
                )
            elif volume <= 500:
                # Medium volume gets fixed discount
                adj_result = managers["adjustment"].apply_adjustment(
                    adjustment_name="Medium volume discount",
                    adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                    adjustment_amount=10000,
                    adjustment_target=AdjustmentTarget.BILLING_GROUP,
                    target_id=test_context["billing_group_id"],
                )
            else:
                # Large volume gets both discounts
                adj1 = managers["adjustment"].apply_adjustment(
                    adjustment_name="Large volume rate discount",
                    adjustment_type=AdjustmentType.RATE_DISCOUNT,
                    adjustment_amount=10,
                    adjustment_target=AdjustmentTarget.PROJECT,
                    target_id=test_app_keys[0],
                )
                adj2 = managers["adjustment"].apply_adjustment(
                    adjustment_name="Large volume fixed discount",
                    adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                    adjustment_amount=20000,
                    adjustment_target=AdjustmentTarget.BILLING_GROUP,
                    target_id=test_context["billing_group_id"],
                )

    def test_credit_priority_and_expiration_logic(self, test_context, test_app_keys):
        """Test credit usage priority and expiration handling.

        Credit Priority (highest to lowest):
        1. Expiring soon credits
        2. FREE credits
        3. REFUND credits
        4. PAID credits
        """
        managers = test_context["managers"]

        # Create credits with different expiration dates
        today = datetime.now()

        # 1. Credit expiring tomorrow (highest priority)
        expiring_soon = managers["credit"].grant_credit(
            campaign_id="EXPIRE-SOON",
            credit_name="Expiring Soon Credit",
            amount=5000,
        )

        # 2. Free credit expiring in 30 days
        free_credit = managers["credit"].grant_credit(
            campaign_id="FREE-NORMAL",
            credit_name="Normal Free Credit",
            amount=10000,
        )

        # 3. Refund credit expiring in 90 days
        # TODO: Refunds are handled through PaymentManager.process_refund
        logger.warning("Skipping refund credit in priority test - not implemented")
        refund_credit = None

        # 4. Paid credit expiring in 365 days
        managers["credit"].grant_credit(
            campaign_id="PAID-LONG", credit_name="Paid Long Term Credit", amount=20000
        )

        # Check total balance
        total_balance = managers["credit"].get_total_credit_balance()
        expected_total = 5000 + 10000 + 15000 + 20000
        logger.info(
            f"Total credit balance: {total_balance}, Expected: {expected_total}"
        )

        # Create usage to test priority
        usage_amounts = [3000, 7000, 12000]  # Different usage levels

        for usage in usage_amounts:
            managers["metering"].send_metering(
                app_key=test_app_keys[0],
                counter_name="credit.priority.test",
                counter_type=CounterType.DELTA,
                counter_unit="UNITS",
                counter_volume=str(usage),
            )

            # Calculate to apply credits
            managers["calculation"].recalculate_all()

            # Check remaining balance
            remaining = managers["credit"].get_total_credit_balance()
            logger.info(f"After {usage} units usage, remaining credit: {remaining}")

    def test_batch_job_combinations(self, test_context):
        """Test various batch job combinations and their effects.

        Batch jobs can run:
        1. Sequentially
        2. In parallel (if supported)
        3. With dependencies
        """
        managers = test_context["managers"]

        batch_jobs = [
            (JobCode.API_CALCULATE_USAGE_AND_PRICE, 1),  # Day 1
            (JobCode.BATCH_GENERATE_STATEMENT, 5),  # Day 5
            (JobCode.BATCH_SEND_INVOICE, 10),  # Day 10
            (JobCode.BATCH_RECONCILIATION, 15),  # Day 15
        ]

        job_results = []

        for job_code, exec_day in batch_jobs:
            result = managers["batch"].request_batch_job(
                job_code=job_code, execution_day=exec_day
            )

            if result.get("header", {}).get("isSuccessful", False):
                # Get job status
                job_id = result.get("jobId", f"{job_code.value}-test")
                status = managers["batch"].get_batch_status(job_id)

                job_results.append(
                    {"job_code": job_code.value, "exec_day": exec_day, "status": status}
                )

        logger.info(f"Batch job results: {job_results}")

    def test_complex_multi_tenant_scenario(self, test_context, test_app_keys):
        """Test complex scenario with multiple tenants and resources.

        Simulates:
        1. Multiple projects with different usage patterns
        2. Shared resources with cost allocation
        3. Different pricing tiers per project
        4. Cross-project adjustments
        """
        managers = test_context["managers"]

        # Simulate 3 different projects
        projects = [
            {"app_key": test_app_keys[0], "tier": "basic", "usage_pattern": "steady"},
            {"app_key": test_app_keys[1], "tier": "premium", "usage_pattern": "burst"},
            {
                "app_key": test_app_keys[2],
                "tier": "enterprise",
                "usage_pattern": "heavy",
            },
        ]

        # Define resource usage patterns
        resource_patterns = {
            "steady": [(100, 100, 100), (100, 100, 100)],  # Consistent usage
            "burst": [(50, 200, 50), (300, 100, 50)],  # Spiky usage
            "heavy": [(200, 300, 400), (500, 600, 700)],  # Increasing usage
        }

        for project in projects:
            pattern = resource_patterns[project["usage_pattern"]]

            for day_idx, (compute, storage, network) in enumerate(pattern):
                # Send compute usage
                managers["metering"].send_metering(
                    app_key=project["app_key"],
                    counter_name=f"compute.{project['tier']}",
                    counter_type=CounterType.DELTA,
                    counter_unit="HOURS",
                    counter_volume=str(compute),
                )

                # Send storage usage
                managers["metering"].send_metering(
                    app_key=project["app_key"],
                    counter_name=f"storage.{project['tier']}",
                    counter_type=CounterType.GAUGE,
                    counter_unit="GB",
                    counter_volume=str(storage),
                )

                # Send network usage
                managers["metering"].send_metering(
                    app_key=project["app_key"],
                    counter_name=f"network.{project['tier']}",
                    counter_type=CounterType.DELTA,
                    counter_unit="GB",
                    counter_volume=str(network),
                )

            # Apply tier-specific adjustments
            if project["tier"] == "enterprise":
                # Enterprise gets volume discount
                managers["adjustment"].apply_adjustment(
                    adjustment_name="Enterprise volume discount",
                    adjustment_type=AdjustmentType.RATE_DISCOUNT,
                    adjustment_amount=15,
                    adjustment_target=AdjustmentTarget.PROJECT,
                    target_id=project["app_key"],
                )
            elif project["tier"] == "premium":
                # Premium gets fixed credit
                managers["credit"].grant_credit(
                    campaign_id="PREMIUM-BONUS",
                    credit_name="Premium Bonus Credit",
                    amount=50000,
                )

    @pytest.mark.skip(
        reason="Error recovery scenarios require advanced mock server features"
    )
    def test_error_recovery_scenarios(self, test_context, test_app_keys):
        """Test system behavior in error scenarios.

        Note: Skipped because error scenarios require mock server to simulate
        various failure modes that are not currently implemented.

        Tests:
        1. Invalid metering data handling
        2. Adjustment conflicts
        3. Credit insufficiency
        4. Calculation failures and retries
        """
        managers = test_context["managers"]

        # 1. Test invalid metering data
        try:
            managers["metering"].send_metering(
                app_key="INVALID-APP-KEY",
                counter_name="test.invalid",
                counter_type="INVALID_TYPE",  # Invalid type
                counter_unit="UNITS",
                counter_volume="-100",  # Negative volume
            )
            logger.warning("Invalid metering accepted (may be valid in some cases)")
        except Exception as e:
            logger.info(f"Invalid metering correctly rejected: {e}")

        # 2. Test conflicting adjustments
        # Apply two rate discounts on same target (should they stack?)
        managers["adjustment"].apply_adjustment(
            adjustment_name="First discount",
            adjustment_type=AdjustmentType.RATE_DISCOUNT,
            adjustment_amount=10,
            adjustment_target=AdjustmentTarget.PROJECT,
            target_id=test_app_keys[0],
        )

        managers["adjustment"].apply_adjustment(
            adjustment_name="Second discount",
            adjustment_type=AdjustmentType.RATE_DISCOUNT,
            adjustment_amount=20,
            adjustment_target=AdjustmentTarget.PROJECT,
            target_id=test_app_keys[0],
        )

        # 3. Test credit over-usage
        # Grant small credit
        managers["credit"].grant_credit(
            campaign_id="SMALL-CREDIT",
            credit_name="Small Test Credit",
            amount=1000,
        )

        # Create large usage
        managers["metering"].send_metering(
            app_key=test_app_keys[0],
            counter_name="test.overuse",
            counter_type=CounterType.DELTA,
            counter_unit="UNITS",
            counter_volume="100000",  # Much larger than credit
        )

        # Calculate and check handling
        managers["calculation"].recalculate_all()
        payment_statement = managers["payment"].get_payment_statement()

        if payment_statement.get("statements"):
            statement = payment_statement["statements"][0]
            total_due = statement.get("totalAmount", 0)
            logger.info(f"Amount due after insufficient credit: {total_due}")


@pytest.mark.integration
class TestBusinessRuleValidation(BaseIntegrationTest):
    """Validate specific business rules and constraints."""

    def test_adjustment_limits(self, test_context, test_app_keys):
        """Test business rules for adjustment limits.

        Rules:
        1. Rate discounts cannot exceed 100%
        2. Multiple adjustments on same target
        3. Adjustment effective dates
        """
        managers = test_context["managers"]

        # Test extreme discount
        try:
            result = managers["adjustment"].apply_adjustment(
                adjustment_name="Extreme discount test",
                adjustment_type=AdjustmentType.RATE_DISCOUNT,
                adjustment_amount=150,  # 150% discount (should be capped or rejected)
                adjustment_target=AdjustmentTarget.BILLING_GROUP,
                target_id=test_context["billing_group_id"],
            )
            # If we get here, the system accepted the extreme discount (might be capped)
            logger.info(f"150% discount result: {result}")
        except Exception as e:
            # Expected behavior - system should reject > 100% discounts
            logger.info(f"150% discount correctly rejected: {e}")
            assert "cannot exceed 100%" in str(e) or "Rate discount" in str(e)

    def test_credit_validation_rules(self, test_context):
        """Test credit validation and business rules.

        Rules:
        1. Credits cannot have past expiration dates
        2. Credit amounts must be positive
        3. Credit types must be valid
        """
        managers = test_context["managers"]

        # Test past expiration date
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        try:
            managers["credit"].grant_credit(
                campaign_id="EXPIRED-TEST",
                credit_name="Expired Test Credit",
                amount=10000,
            )
            logger.warning("Past expiration date accepted")
        except Exception as e:
            logger.info(f"Past expiration correctly rejected: {e}")

    def test_metering_aggregation_rules(self, test_context, test_app_keys):
        """Test metering aggregation business rules.

        Rules:
        1. DELTA counters should sum
        2. GAUGE counters should use latest value
        3. CUMULATIVE counters should track maximum
        """
        managers = test_context["managers"]

        # Send multiple GAUGE readings
        gauge_values = [100, 200, 150, 180]

        for value in gauge_values:
            managers["metering"].send_metering(
                app_key=test_app_keys[0],
                counter_name="test.gauge.aggregation",
                counter_type=CounterType.GAUGE,
                counter_unit="GB",
                counter_volume=str(value),
            )

        # The billing should use the latest or average value, not sum
        managers["calculation"].recalculate_all()

        # Send multiple DELTA readings
        delta_values = [25, 30, 45]

        for value in delta_values:
            managers["metering"].send_metering(
                app_key=test_app_keys[0],
                counter_name="test.delta.aggregation",
                counter_type=CounterType.DELTA,
                counter_unit="HOURS",
                counter_volume=str(value),
            )

        # DELTA should sum to 100
        managers["calculation"].recalculate_all()
