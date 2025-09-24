"""Tests for project-level billing adjustments."""

import math
import pytest

from libs.constants import CounterType
from tests.base import BaseAdjustmentTest, MeteringItem


class TestProjectAdjustment(BaseAdjustmentTest):
    """Test suite for project-level adjustments (discounts/surcharges)."""

    # Test data constants
    METERING_DATA = [
        MeteringItem(
            counter_name="compute.c2.c8m8",
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume="720",
        ),
        MeteringItem(
            counter_name="storage.volume.ssd",
            counter_type=CounterType.DELTA,
            counter_unit="KB",
            counter_volume="524288000",
        ),
        MeteringItem(
            counter_name="network.floating_ip",
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume="720",
        ),
        MeteringItem(
            counter_name="compute.g2.t4.c8m64",
            counter_type=CounterType.GAUGE,
            counter_unit="HOURS",
            counter_volume="720",
        ),
    ]

    @pytest.fixture(scope="class", autouse=True)
    def setup_metering_data(self, test_config) -> None:
        """Set up metering data for all tests in the class."""
        # Clean existing data
        test_config.clean_data()

        # Send metering data
        self.send_metering_data(test_config, self.METERING_DATA)

    def test_fixed_discount_adjustment(self, test_config) -> None:
        """Test fixed amount discount on project."""
        discount_amount = 100

        # Apply adjustment
        self.apply_adjustment(
            test_config,
            adjustment_type="FIXED_DISCOUNT",
            adjustment_amount=discount_amount,
        )

        # Perform calculation
        self.perform_calculation(test_config)

        # Get results
        statements, total_payments = test_config.common_test()

        # Calculate expected total
        adjusted_charge = statements["charge"] - discount_amount
        expected_total = self.calculate_total_with_vat(adjusted_charge)

        # Verify results
        test_config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=expected_total,
        )

    def test_percentage_discount_adjustment(self, test_config) -> None:
        """Test percentage discount on project."""
        discount_percentage = 10

        # Apply adjustment
        self.apply_adjustment(
            test_config,
            adjustment_type="RATE_DISCOUNT",
            adjustment_amount=discount_percentage,
        )

        # Perform calculation
        self.perform_calculation(test_config)

        # Get results
        statements, total_payments = test_config.common_test()

        # Calculate expected total
        discount_amount = math.ceil(statements["charge"] * (discount_percentage * 0.01))
        adjusted_charge = statements["charge"] - discount_amount
        expected_total = self.calculate_total_with_vat(adjusted_charge)

        # Verify results
        test_config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=expected_total,
        )

    def test_fixed_surcharge_adjustment(self, test_config) -> None:
        """Test fixed amount surcharge on project."""
        surcharge_amount = 10000

        # Apply adjustment
        self.apply_adjustment(
            test_config,
            adjustment_type="FIXED_SURCHARGE",
            adjustment_amount=surcharge_amount,
        )

        # Perform calculation
        self.perform_calculation(test_config)

        # Get results
        statements, total_payments = test_config.common_test()

        # Calculate expected total
        adjusted_charge = statements["charge"] + surcharge_amount
        expected_total = self.calculate_total_with_vat(adjusted_charge)

        # Verify results
        test_config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=expected_total,
        )

    def test_combined_fixed_adjustments(self, test_config) -> None:
        """Test combination of fixed discount and fixed surcharge."""
        discount_amount = 100
        surcharge_amount = 1000

        # Apply both adjustments
        self.apply_adjustment(
            test_config,
            adjustment_type="FIXED_DISCOUNT",
            adjustment_amount=discount_amount,
        )

        self.apply_adjustment(
            test_config,
            adjustment_type="FIXED_SURCHARGE",
            adjustment_amount=surcharge_amount,
        )

        # Perform calculation
        self.perform_calculation(test_config)

        # Get results
        statements, total_payments = test_config.common_test()

        # Calculate expected total
        adjusted_charge = statements["charge"] - discount_amount + surcharge_amount
        expected_total = self.calculate_total_with_vat(adjusted_charge)

        # Verify results
        test_config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=expected_total,
        )

    def test_combined_percentage_and_fixed_adjustments(self, test_config) -> None:
        """Test combination of percentage discount and fixed surcharge."""
        discount_percentage = 10
        surcharge_amount = 2000

        # Apply both adjustments
        self.apply_adjustment(
            test_config,
            adjustment_type="RATE_DISCOUNT",
            adjustment_amount=discount_percentage,
        )

        self.apply_adjustment(
            test_config,
            adjustment_type="FIXED_SURCHARGE",
            adjustment_amount=surcharge_amount,
        )

        # Perform calculation
        self.perform_calculation(test_config)

        # Get results
        statements, total_payments = test_config.common_test()

        # Calculate expected total
        # Note: The order of operations matters - check business logic
        total_before_discount = statements["charge"] + surcharge_amount
        discount_amount = math.ceil(total_before_discount * discount_percentage * 0.01)
        adjusted_charge = total_before_discount - discount_amount
        expected_total = self.calculate_total_with_vat(adjusted_charge)

        # Verify results
        test_config.verify_assert(
            statements=statements["totalAmount"],
            payments=total_payments,
            expected_result=expected_total,
        )
