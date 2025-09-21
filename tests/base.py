"""Base classes and utilities for billing tests."""

import math
from typing import Dict, Any, Tuple, Optional, List
import pytest
from dataclasses import dataclass

from libs import (
    InitializeConfig,
    Metering,
    Calculation,
    Payments,
    Adjustments,
    Contract,
    Credit,
    Batch,
    CounterType,
)


@dataclass
class MeteringItem:
    """Data class for metering information."""

    counter_name: str
    counter_type: CounterType
    counter_unit: str
    counter_volume: str
    resource_id: str = "test"
    resource_name: str = "test"


class BaseBillingTest:
    """Base class for billing test cases."""

    # Common constants
    VAT_RATE = 0.1  # 10% VAT
    DEFAULT_TIMEOUT = 300  # 5 minutes

    @pytest.fixture(scope="class")
    def test_config(self, env: str, member: str, month: str) -> InitializeConfig:
        """Initialize test configuration."""
        return InitializeConfig(env, member, month)

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, test_config: InitializeConfig) -> None:
        """Common setup and teardown for each test."""
        # Setup: Ensure payment status is REGISTERED
        test_config.before_test()

        yield

        # Teardown: Clean up test data
        self._cleanup_test_data(test_config)

    def _cleanup_test_data(self, test_config: InitializeConfig) -> None:
        """Clean up test data after each test.

        Override this method in subclasses for specific cleanup needs.
        """
        pass

    def send_metering_data(
        self,
        test_config: InitializeConfig,
        metering_items: List[MeteringItem],
        app_key_index: int = 0,
    ) -> None:
        """Send metering data for testing.

        Args:
            test_config: Test configuration
            metering_items: List of metering items to send
            app_key_index: Index of app key to use
        """
        metering_obj = Metering(test_config.month)
        metering_obj.appkey = test_config.appkey[app_key_index]

        for item in metering_items:
            metering_obj.send_iaas_metering(
                counter_name=item.counter_name,
                counter_type=item.counter_type.value,
                counter_unit=item.counter_unit,
                counter_volume=item.counter_volume,
            )

    def perform_calculation(
        self, test_config: InitializeConfig, wait_for_stable: bool = True
    ) -> Calculation:
        """Perform billing calculation.

        Args:
            test_config: Test configuration
            wait_for_stable: Whether to wait for calculation to stabilize

        Returns:
            Calculation object
        """
        calc_obj = Calculation(test_config.month, test_config.uuid)
        calc_obj.recalculation_all()

        if wait_for_stable:
            calc_obj.check_stable()

        return calc_obj

    def get_payment_info(self, test_config: InitializeConfig) -> Tuple[str, str]:
        """Get payment information.

        Args:
            test_config: Test configuration

        Returns:
            Tuple of (payment_group_id, payment_status)
        """
        payments_obj = Payments(test_config.month)
        payments_obj.uuid = test_config.uuid
        return payments_obj.inquiry_payment()

    def make_payment(
        self, test_config: InitializeConfig, payment_group_id: str
    ) -> None:
        """Make payment for the given payment group.

        Args:
            test_config: Test configuration
            payment_group_id: Payment group ID
        """
        payments_obj = Payments(test_config.month)
        payments_obj.uuid = test_config.uuid
        payments_obj.payment(payment_group_id)

    def calculate_total_with_vat(
        self, base_amount: float, vat_rate: float = VAT_RATE
    ) -> float:
        """Calculate total amount including VAT.

        Args:
            base_amount: Base amount before VAT
            vat_rate: VAT rate (default: 10%)

        Returns:
            Total amount including VAT
        """
        vat = math.floor(base_amount * vat_rate)
        return base_amount + vat

    def assert_payment_equals(
        self, actual: float, expected: float, message: str = ""
    ) -> None:
        """Assert that payment amounts are equal within tolerance.

        Args:
            actual: Actual payment amount
            expected: Expected payment amount
            message: Optional assertion message
        """
        tolerance = 0.01  # Allow 0.01 difference for rounding

        assert (
            abs(actual - expected) <= tolerance
        ), f"{message}\nExpected: {expected}, Actual: {actual}, Difference: {abs(actual - expected)}"


class BaseAdjustmentTest(BaseBillingTest):
    """Base class for adjustment-related tests."""

    def apply_adjustment(
        self,
        test_config: InitializeConfig,
        adjustment_type: str,
        adjustment_amount: float,
        target_type: str = "Project",
        target_id: Optional[str] = None,
    ) -> Adjustments:
        """Apply adjustment to billing.

        Args:
            test_config: Test configuration
            adjustment_type: Type of adjustment
            adjustment_amount: Amount of adjustment
            target_type: Target type (Project or BillingGroup)
            target_id: Target ID (uses first project ID if not specified)

        Returns:
            Adjustments object
        """
        if target_id is None and target_type == "Project":
            target_id = test_config.project_id[0]
        elif target_id is None and target_type == "BillingGroup":
            target_id = test_config.billing_group_id

        adj_obj = Adjustments(test_config.month)

        kwargs = {
            "adjustmentTarget": target_type,
            "adjustmentType": adjustment_type,
            "adjustment": adjustment_amount,
        }

        if target_type == "Project":
            kwargs["projectId"] = target_id
        else:
            kwargs["billingGroupId"] = target_id

        adj_obj.apply_adjustment(**kwargs)
        return adj_obj

    def _cleanup_test_data(self, test_config: InitializeConfig) -> None:
        """Clean up adjustments after test."""
        adj_obj = Adjustments(test_config.month)

        # Clean project adjustments
        for project_id in test_config.project_id:
            adj_list = adj_obj.inquiry_adjustment(
                adjustmentTarget="Project", projectId=project_id
            )
            if adj_list:
                adj_obj.delete_adjustment(adj_list)  

        # Clean billing group adjustments
        adj_list = adj_obj.inquiry_adjustment(
            adjustmentTarget="BillingGroup", billingGroupid=test_config.billing_group_id
        )
        if adj_list:
            adj_obj.delete_adjustment(adj_list)


class BaseContractTest(BaseBillingTest):
    """Base class for contract-related tests."""

    def apply_contract(
        self, test_config: InitializeConfig, contract_id: str, is_default: bool = True
    ) -> Contract:
        """Apply contract to billing group.

        Args:
            test_config: Test configuration
            contract_id: Contract ID to apply
            is_default: Whether this is the default contract

        Returns:
            Contract object
        """
        contract_obj = Contract(test_config.month, test_config.billing_group_id)
        contract_obj.contractId = contract_id
        contract_obj.apply_contract()
        return contract_obj

    def _cleanup_test_data(self, test_config: InitializeConfig) -> None:
        """Clean up contracts after test."""
        contract_obj = Contract(test_config.month, test_config.billing_group_id)
        contract_obj.delete_contract()


class BaseCreditTest(BaseBillingTest):
    """Base class for credit-related tests."""

    def grant_credit(
        self,
        test_config: InitializeConfig,
        campaign_id: str,
        amount: Optional[int] = None,
    ) -> Credit:
        """Grant credit to user.

        Args:
            test_config: Test configuration
            campaign_id: Campaign ID or coupon code
            amount: Credit amount (None for coupon-based credit)

        Returns:
            Credit object
        """
        credit_obj = Credit()
        credit_obj.uuid = test_config.uuid

        if amount is None:
            # Coupon-based credit
            credit_obj.give_credit(campaign_id)
        else:
            # Direct credit grant
            credit_obj.give_credit(campaign_id, amount)

        return credit_obj

    def _cleanup_test_data(self, test_config: InitializeConfig) -> None:
        """Clean up credits after test."""
        credit_obj = Credit()
        credit_obj.uuid = test_config.uuid
        credit_obj.campaign_id = getattr(test_config, "campaign_id", [])
        credit_obj.give_campaign_id = getattr(test_config, "give_campaign_id", [])
        credit_obj.paid_campaign_id = getattr(test_config, "paid_campaign_id", [])
        credit_obj.cancel_credit()
