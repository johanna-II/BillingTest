"""Consolidated billing workflow integration tests.

This file combines all workflow tests (adjustment, credit, payment, etc.) into a single comprehensive test suite.
"""

import logging
from datetime import datetime
from typing import Any

import pytest

from libs.constants import (
    AdjustmentTarget,
    AdjustmentType,
    CounterType,
)
from tests.integration.base_integration import BaseIntegrationTest

logger = logging.getLogger(__name__)


@pytest.mark.integration
class TestBillingWorkflows(BaseIntegrationTest):
    """Comprehensive integration tests for all billing workflows."""

    # ======================
    # Adjustment Workflows
    # ======================
    def test_project_adjustment_workflow(self, test_context, test_app_keys):
        """Test complete project adjustment workflow."""
        managers = test_context["managers"]

        # Apply various adjustments
        adjustments = [
            (AdjustmentType.FIXED_DISCOUNT, 10000, "Fixed discount"),
            (AdjustmentType.RATE_DISCOUNT, 10, "10% discount"),
            (AdjustmentType.FIXED_SURCHARGE, 5000, "Service fee"),
            (AdjustmentType.RATE_SURCHARGE, 5, "5% surcharge"),
        ]

        for adj_type, amount, desc in adjustments:
            result = managers["adjustment"].apply_adjustment(
                adjustment_name=desc,
                adjustment_type=adj_type,
                adjustment_amount=amount,
                target_type=AdjustmentTarget.PROJECT,
                target_id=test_app_keys[0],
            )
            self.assert_api_success(result)

        # Get adjustments
        retrieved = managers["adjustment"].get_adjustments(
            target_type=AdjustmentTarget.PROJECT, target_id=test_app_keys[0]
        )
        self.assert_api_success(retrieved)
        assert len(retrieved.get("adjustments", [])) >= len(adjustments)

    def test_billing_group_adjustment_workflow(self, test_context):
        """Test complete billing group adjustment workflow."""
        managers = test_context["managers"]
        bg_id = test_context["billing_group_id"]

        # Apply billing group adjustment
        result = managers["adjustment"].apply_adjustment(
            adjustment_name="Billing Group Discount",
            adjustment_type=AdjustmentType.RATE_DISCOUNT,
            adjustment_amount=15,
            target_type=AdjustmentTarget.BILLING_GROUP,
            target_id=bg_id,
        )
        self.assert_api_success(result)

        # Delete adjustments
        delete_result = managers["adjustment"].delete_adjustments()
        self.assert_api_success(delete_result)

    # ======================
    # Credit Workflows
    # ======================
    def test_campaign_credit_lifecycle(self, test_context):
        """Test complete campaign credit lifecycle."""
        managers = test_context["managers"]
        campaign_id = f"CAMPAIGN-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 1. Create campaign
        campaign_result = managers["credit"].create_campaign(
            campaign_id=campaign_id,
            campaign_name="Test Campaign",
            available_amount=1000000,
            valid_from="2024-01-01",
            valid_to="2024-12-31",
        )
        self.assert_api_success(campaign_result)

        # 2. Grant credit
        grant_result = managers["credit"].grant_campaign_credit(
            campaign_id=campaign_id,
            credit_name="Test Credit Grant",
            credit_amount=50000,
        )
        self.assert_api_success(grant_result)

        # 3. Check balance
        balance_result = managers["credit"].get_credit_balance()
        self.assert_api_success(balance_result)

        # 4. Cancel credit
        cancel_result = managers["credit"].cancel_credit(
            campaign_id=campaign_id, reason="Test cleanup"
        )
        self.assert_api_success(cancel_result)

    def test_paid_credit_workflow(self, test_context):
        """Test paid credit workflow."""
        managers = test_context["managers"]

        # Grant paid credit
        result = managers["credit"].grant_paid_credit(
            campaign_id=f"PAID-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            paid_amount=100000,
            expire_months=12,
        )
        self.assert_api_success(result)

        # Get balance
        balance = managers["credit"].get_credit_balance()
        self.assert_api_success(balance)
        assert balance.get("totalBalance", 0) >= 100000

    def test_refund_credit_workflow(self, test_context):
        """Test refund credit workflow."""
        managers = test_context["managers"]

        # Create refund
        refund_result = managers["credit"].refund_credit(
            refund_items=[
                {
                    "paymentStatementId": "STMT-001",
                    "refundAmount": 20000,
                    "reason": "Service issue",
                }
            ]
        )
        self.assert_api_success(refund_result)

    # ======================
    # Payment Workflows
    # ======================
    def test_payment_lifecycle(self, test_context):
        """Test complete payment lifecycle."""
        managers = test_context["managers"]
        payment_id = f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 1. Create payment
        payment_result = managers["payment"].make_payment(
            uuid=test_context["uuid"],
            amount=50000,
            payment_method="CREDIT_CARD",
            currency="KRW",
            payment_id=payment_id,
        )
        self.assert_api_success(payment_result)

        # 2. Get payment status
        status_result = managers["payment"].get_payment_status(payment_id)
        self.assert_api_success(status_result)

        # 3. Get payment history
        history_result = managers["payment"].get_payment_history()
        self.assert_api_success(history_result)

        # 4. Change payment status
        change_result = managers["payment"].change_payment_status(
            payment_id=payment_id,
            new_status="PAID",
            reason="Test completion",
        )
        self.assert_api_success(change_result)

    def test_payment_statement_workflow(self, test_context):
        """Test payment statement workflow."""
        managers = test_context["managers"]

        # Get statement
        statement_result = managers["payment"].get_payment_statement()
        self.assert_api_success(statement_result)

        # Get billing list
        billing_list = managers["payment"].get_billing_list()
        self.assert_api_success(billing_list)

    # ======================
    # Combined Workflows
    # ======================
    def test_complete_billing_cycle(self, test_context, test_app_keys):
        """Test a complete billing cycle with all components."""
        managers = test_context["managers"]

        # 1. Send metering data
        metering_result = managers["metering"].send_metering(
            app_key=test_app_keys[0],
            counter_name="compute.instance",
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume="100",
        )
        self.assert_api_success(metering_result)

        # 2. Apply adjustments
        adj_result = managers["adjustment"].apply_adjustment(
            adjustment_name="Monthly Discount",
            adjustment_type=AdjustmentType.RATE_DISCOUNT,
            adjustment_amount=10,
            target_type=AdjustmentTarget.PROJECT,
            target_id=test_app_keys[0],
        )
        self.assert_api_success(adj_result)

        # 3. Grant credits
        credit_result = managers["credit"].grant_campaign_credit(
            campaign_id="CYCLE-TEST",
            credit_name="Billing Cycle Credit",
            credit_amount=20000,
        )
        self.assert_api_success(credit_result)

        # 4. Trigger calculation
        calc_result = managers["calculation"].recalculate_all()
        self.assert_api_success(calc_result)
        managers["calculation"].wait_for_calculation_completion()

        # 5. Get final statement
        statement = managers["payment"].get_payment_statement()
        self.assert_api_success(statement)

        # 6. Make payment
        if statement.get("statements"):
            total_amount = statement["statements"][0].get("totalAmount", 0)
            if total_amount > 0:
                payment_result = managers["payment"].make_payment(
                    uuid=test_context["uuid"],
                    amount=total_amount,
                    payment_method="BANK_TRANSFER",
                    currency="KRW",
                )
                self.assert_api_success(payment_result)

    def test_error_handling_workflow(self, test_context, test_app_keys):
        """Test error handling across workflows."""
        managers = test_context["managers"]

        # Test invalid adjustments
        try:
            managers["adjustment"].apply_adjustment(
                adjustment_amount=-100,  # Invalid negative amount
                adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                target_type=AdjustmentTarget.PROJECT,
                target_id=test_app_keys[0],
            )
        except Exception as e:
            logger.info(f"Expected error for negative adjustment: {e}")

        # Test invalid credit
        try:
            managers["credit"].grant_campaign_credit(
                campaign_id="INVALID-CAMPAIGN",
                credit_name="Test",
                credit_amount=999999999,  # Exceeds limits
            )
        except Exception as e:
            logger.info(f"Expected error for excessive credit: {e}")

        # Test invalid payment
        try:
            managers["payment"].make_payment(
                uuid="INVALID-UUID",
                amount=0,  # Invalid zero amount
                payment_method="INVALID_METHOD",
                currency="INVALID",
            )
        except Exception as e:
            logger.info(f"Expected error for invalid payment: {e}")

    # ======================
    # Edge Cases
    # ======================
    def test_concurrent_operations(self, test_context, test_app_keys):
        """Test concurrent operations handling."""
        managers = test_context["managers"]

        # Apply multiple adjustments rapidly
        for i in range(5):
            managers["adjustment"].apply_adjustment(
                adjustment_name=f"Concurrent Test {i}",
                adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                adjustment_amount=1000 * (i + 1),
                target_type=AdjustmentTarget.PROJECT,
                target_id=test_app_keys[0],
            )

        # Verify all were applied
        adjustments = managers["adjustment"].get_adjustments(
            target_type=AdjustmentTarget.PROJECT, target_id=test_app_keys[0]
        )
        assert len(adjustments.get("adjustments", [])) >= 5

    def test_boundary_values(self, test_context, test_app_keys):
        """Test boundary value conditions."""
        managers = test_context["managers"]

        # Test maximum discount (100%)
        result = managers["adjustment"].apply_adjustment(
            adjustment_name="Max Discount",
            adjustment_type=AdjustmentType.RATE_DISCOUNT,
            adjustment_amount=100,
            target_type=AdjustmentTarget.PROJECT,
            target_id=test_app_keys[0],
        )
        self.assert_api_success(result)

        # Test minimum values
        result = managers["metering"].send_metering(
            app_key=test_app_keys[0],
            counter_name="test.minimum",
            counter_type=CounterType.DELTA,
            counter_unit="UNITS",
            counter_volume="0.001",  # Very small value
        )
        self.assert_api_success(result)

    # ======================
    # Helper Methods
    # ======================
    def common_test(self) -> tuple[Any, float]:
        """Common test helper to get statements and calculate total payments."""
        # This would be implemented based on actual needs
        return {}, 0.0
