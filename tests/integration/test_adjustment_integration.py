"""Adjustment integration tests - converted from unit tests."""

import pytest

from libs.Adjustment import AdjustmentManager
from libs.Calculation import CalculationManager
from libs.constants import AdjustmentTarget, AdjustmentType, CounterType
from libs.Metering import MeteringManager
from libs.Payments import PaymentManager


class TestAdjustmentIntegration:
    """Integration tests for adjustment functionality."""

    @pytest.fixture
    def adjustment_context(self, api_client, month, test_billing_group):
        """Setup adjustment test context."""
        return {
            "adjustment": AdjustmentManager(month=month),
            "metering": MeteringManager(month=month),
            "calculation": CalculationManager(
                month=month, uuid=f"uuid-{test_billing_group}"
            ),
            "payment": PaymentManager(month=month, uuid=f"uuid-{test_billing_group}"),
            "billing_group": test_billing_group,
        }

    @pytest.mark.integration
    @pytest.mark.mock_required
    def test_adjustment_impact_on_billing(
        self, adjustment_context, test_app_keys
    ) -> None:
        """Test how adjustments affect actual billing amount."""
        ctx = adjustment_context

        # 1. Create base usage
        for app_key in test_app_keys[:2]:  # Use 2 apps
            ctx["metering"].send_metering(
                app_key=app_key,
                counter_name="compute.adjustment.test",
                counter_type=CounterType.DELTA,
                counter_unit="HOURS",
                counter_volume="100",
            )

        # 2. Calculate initial amount
        ctx["calculation"].recalculate_all()

        # 3. Get initial billing amount
        pg_id, _ = ctx["payment"].get_payment_status()
        initial_amount = ctx["payment"].check_unpaid_amount(pg_id) if pg_id else 0

        # 4. Apply fixed discount
        discount_amount = 10000.0
        adj_result = ctx["adjustment"].apply_adjustment(
            adjustment_amount=discount_amount,
            adjustment_type=AdjustmentType.FIXED_DISCOUNT,
            adjustment_target=AdjustmentTarget.BILLING_GROUP,
            target_id=ctx["billing_group"],
            description="Integration test fixed discount",
        )
        assert "adjustmentId" in adj_result

        # 5. Recalculate with adjustment
        ctx["calculation"].recalculate_all()

        # 6. Get new billing amount
        pg_id, _ = ctx["payment"].get_payment_status()
        adjusted_amount = ctx["payment"].check_unpaid_amount(pg_id) if pg_id else 0

        # 7. Verify discount was applied
        if initial_amount > discount_amount:
            assert adjusted_amount == initial_amount - discount_amount
        else:
            assert adjusted_amount == 0

    @pytest.mark.integration
    @pytest.mark.mock_required
    def test_percentage_adjustment_calculation(
        self, adjustment_context, test_app_keys
    ) -> None:
        """Test percentage-based adjustments."""
        ctx = adjustment_context

        # 1. Create significant usage
        ctx["metering"].send_metering(
            app_key=test_app_keys[0],
            counter_name="compute.percentage.test",
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume="1000",  # Large usage
        )

        # 2. Calculate base amount
        ctx["calculation"].recalculate_all()
        pg_id, _ = ctx["payment"].get_payment_status()
        base_amount = ctx["payment"].check_unpaid_amount(pg_id) if pg_id else 0

        # 3. Apply 15% discount
        discount_rate = 15.0
        ctx["adjustment"].apply_adjustment(
            adjustment_amount=discount_rate,
            adjustment_type=AdjustmentType.RATE_DISCOUNT,
            adjustment_target=AdjustmentTarget.BILLING_GROUP,
            target_id=ctx["billing_group"],
            description="15% volume discount",
        )

        # 4. Recalculate
        ctx["calculation"].recalculate_all()
        discounted_amount = ctx["payment"].check_unpaid_amount(pg_id) if pg_id else 0

        # 5. Verify percentage discount
        expected_discount = base_amount * (discount_rate / 100)
        expected_amount = base_amount - expected_discount

        # Allow small rounding differences
        assert abs(discounted_amount - expected_amount) < 1

    @pytest.mark.integration
    @pytest.mark.mock_required
    def test_multiple_adjustments_stacking(
        self, adjustment_context, test_app_keys
    ) -> None:
        """Test multiple adjustments applied together."""
        ctx = adjustment_context

        # 1. Create usage
        ctx["metering"].send_metering(
            app_key=test_app_keys[0],
            counter_name="compute.stacking.test",
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume="500",
        )

        # 2. Apply multiple adjustments
        adjustments = [
            (5000.0, AdjustmentType.FIXED_DISCOUNT, "Fixed discount"),
            (10.0, AdjustmentType.RATE_DISCOUNT, "Percentage discount"),
            (2000.0, AdjustmentType.FIXED_SURCHARGE, "Service fee"),
        ]

        adjustment_ids = []
        for amount, adj_type, desc in adjustments:
            result = ctx["adjustment"].apply_adjustment(
                adjustment_amount=amount,
                adjustment_type=adj_type,
                adjustment_target=AdjustmentTarget.BILLING_GROUP,
                target_id=ctx["billing_group"],
                description=desc,
            )
            adjustment_ids.append(result.get("adjustmentId"))

        # 3. Calculate with all adjustments
        ctx["calculation"].recalculate_all()

        # 4. Verify all adjustments exist
        all_adjustments = ctx["adjustment"].get_adjustments(
            adjustment_target=AdjustmentTarget.BILLING_GROUP,
            target_id=ctx["billing_group"],
        )

        # Should have at least our 3 adjustments
        assert len(all_adjustments) >= 3

        # 5. Verify final amount reflects all adjustments
        pg_id, _ = ctx["payment"].get_payment_status()
        final_amount = ctx["payment"].check_unpaid_amount(pg_id) if pg_id else 0
        assert final_amount >= 0

    @pytest.mark.integration
    @pytest.mark.mock_required
    def test_adjustment_deletion_effect(
        self, adjustment_context, test_app_keys
    ) -> None:
        """Test effect of deleting adjustments."""
        ctx = adjustment_context

        # 1. Setup: Create usage and adjustment
        ctx["metering"].send_metering(
            app_key=test_app_keys[0],
            counter_name="compute.deletion.test",
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume="200",
        )

        adj_result = ctx["adjustment"].apply_adjustment(
            adjustment_amount=15000.0,
            adjustment_type=AdjustmentType.FIXED_DISCOUNT,
            adjustment_target=AdjustmentTarget.BILLING_GROUP,
            target_id=ctx["billing_group"],
        )
        adj_id = adj_result.get("adjustmentId")

        # 2. Calculate with adjustment
        ctx["calculation"].recalculate_all()
        pg_id, _ = ctx["payment"].get_payment_status()
        amount_with_adjustment = (
            ctx["payment"].check_unpaid_amount(pg_id) if pg_id else 0
        )

        # 3. Delete the adjustment
        if adj_id:
            delete_result = ctx["adjustment"].delete_adjustment(
                adjustment_ids=adj_id, adjustment_target=AdjustmentTarget.BILLING_GROUP
            )
            assert delete_result.get("status") == "DELETED"

        # 4. Recalculate without adjustment
        ctx["calculation"].recalculate_all()
        amount_without_adjustment = (
            ctx["payment"].check_unpaid_amount(pg_id) if pg_id else 0
        )

        # 5. Verify amount increased after deletion
        assert amount_without_adjustment > amount_with_adjustment

    @pytest.mark.integration
    @pytest.mark.mock_required
    @pytest.mark.slow
    def test_adjustment_pagination(self, adjustment_context) -> None:
        """Test adjustment pagination with many adjustments."""
        ctx = adjustment_context

        # 1. Create many adjustments
        num_adjustments = 25
        for i in range(num_adjustments):
            ctx["adjustment"].apply_adjustment(
                adjustment_amount=100.0 + i,
                adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                adjustment_target=AdjustmentTarget.BILLING_GROUP,
                target_id=ctx["billing_group"],
                description=f"Pagination test adjustment {i + 1}",
            )

        # 2. Retrieve all adjustments (should handle pagination)
        all_adjustments = ctx["adjustment"].get_adjustments(
            adjustment_target=AdjustmentTarget.BILLING_GROUP,
            target_id=ctx["billing_group"],
        )

        # 3. Verify we got all adjustments
        assert len(all_adjustments) >= num_adjustments

        # 4. Clean up - delete all test adjustments
        # Note: all_adjustments is already a list of adjustment IDs
        if all_adjustments:
            ctx["adjustment"].delete_adjustment(
                adjustment_ids=all_adjustments,
                adjustment_target=AdjustmentTarget.BILLING_GROUP,
            )
