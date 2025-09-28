"""Property-based tests for calculator classes using example-based approach."""

from decimal import Decimal

from libs.adjustment_calculator import AdjustmentCalculator
from libs.billing_calculator import BillingCalculator, Discount, DiscountType, LineItem
from libs.constants import AdjustmentType
from libs.contract_validator import ContractValidator
from libs.metering_calculator import MeteringCalculator


class TestPropertyBasedCalculators:
    """Property-based tests for various calculator classes."""

    def test_billing_round_amount_idempotent(self):
        """Test that rounding is idempotent - rounding twice gives same result."""
        test_amounts = [
            Decimal("10.555"),
            Decimal("99.999"),
            Decimal("0.001"),
            Decimal("1234.5678"),
            Decimal("0.01"),
            Decimal("999999.99"),
        ]

        for amount in test_amounts:
            rounded_once = BillingCalculator.round_amount(amount)
            rounded_twice = BillingCalculator.round_amount(rounded_once)
            assert rounded_once == rounded_twice

    def test_billing_percentage_discount_bounds(self):
        """Test that percentage discounts never exceed base amount."""
        test_cases = [
            (Decimal("100"), Decimal("10")),
            (Decimal("1000"), Decimal("50")),
            (Decimal("500"), Decimal("100")),
            (Decimal("0.01"), Decimal("25")),
            (Decimal("999999"), Decimal("99.99")),
        ]

        for base_amount, discount_percentage in test_cases:
            discount = Discount(
                name="Test discount",
                discount_type=DiscountType.PERCENTAGE,
                value=discount_percentage,
            )

            discount_amount = BillingCalculator.calculate_discount(base_amount, discount)

            # Discount should never exceed base amount
            assert discount_amount <= base_amount
            assert discount_amount >= Decimal("0")

            # Percentage calculation should be correct
            expected = BillingCalculator.round_amount(base_amount * discount_percentage / 100)
            assert discount_amount == expected

    def test_contract_discount_calculation_consistency(self):
        """Test contract discount calculations are consistent."""
        test_cases = [
            (1000.0, 800.0),  # 20% discount
            (500.0, 500.0),  # No discount
            (1000.0, 0.0),  # 100% discount
            (999.99, 100.01),  # Large discount
            (0.01, 0.01),  # Small amounts
        ]

        for original_price, discounted_price in test_cases:
            discount_amount, discount_rate = ContractValidator.calculate_discount(
                original_price, discounted_price
            )

            # Verify calculations
            assert discount_amount >= Decimal("0")
            assert discount_rate >= Decimal("0")
            assert discount_rate <= Decimal("100")

            # Verify reverse calculation (within rounding error)
            if original_price > 0:
                calculated_discount = Decimal(str(original_price)) * discount_rate / 100
                calculated_discount = calculated_discount.quantize(Decimal("0.01"))
                assert abs(calculated_discount - discount_amount) <= Decimal("0.01")

    def test_metering_parse_volume_valid(self):
        """Test that valid volume strings are parsed correctly."""
        test_volumes = [
            "100",
            "100.5",
            "0.01",
            "1e3",
            "1.5e2",
            "1e-2",
            "999999.999",
        ]

        for volume_str in test_volumes:
            volume = MeteringCalculator.parse_volume(volume_str)
            assert volume == float(volume_str)
            assert isinstance(volume, float)

    def test_metering_unit_conversion_reversible(self):
        """Test that unit conversions are reversible."""
        test_cases = [
            (100.0, "KB", "MB"),
            (50.0, "MB", "GB"),
            (1.5, "GB", "TB"),
            (3600.0, "SECONDS", "HOURS"),
            (24.0, "HOURS", "DAYS"),
            (60.0, "MINUTES", "HOURS"),
        ]

        for value, from_unit, to_unit in test_cases:
            # Skip if units are incompatible
            from_category = MeteringCalculator._get_unit_category(from_unit)
            to_category = MeteringCalculator._get_unit_category(to_unit)

            if from_category != to_category:
                continue

            # Convert forward and back
            converted = MeteringCalculator.convert_units(value, from_unit, to_unit)
            back_converted = MeteringCalculator.convert_units(converted, to_unit, from_unit)

            # Should be approximately equal (accounting for floating point precision)
            assert abs(back_converted - value) < 0.0001

    def test_adjustment_apply_never_negative(self):
        """Test that adjustments never result in negative amounts."""
        test_cases = [
            (
                Decimal("100"),
                Decimal("200"),
                AdjustmentType.FIXED_DISCOUNT,
            ),  # Exceeds base
            (Decimal("1000"), Decimal("50"), AdjustmentType.RATE_DISCOUNT),
            (
                Decimal("500"),
                Decimal("100"),
                AdjustmentType.RATE_DISCOUNT,
            ),  # 100% discount
            (Decimal("100"), Decimal("50"), AdjustmentType.FIXED_SURCHARGE),
            (Decimal("1000"), Decimal("150"), AdjustmentType.RATE_SURCHARGE),
        ]

        for base_amount, adjustment_amount, adjustment_type in test_cases:
            # Validate amount first
            try:
                AdjustmentCalculator.validate_adjustment_amount(adjustment_amount, adjustment_type)
            except Exception:
                # Skip invalid adjustments
                continue

            final_amount, _ = AdjustmentCalculator.apply_adjustment(
                base_amount, adjustment_amount, adjustment_type
            )

            assert final_amount >= Decimal("0"), f"Final amount {final_amount} is negative"

    def test_billing_invoice_total_consistency(self):
        """Test that invoice totals are calculated consistently."""
        test_cases = [
            [Decimal("100")],
            [Decimal("50"), Decimal("75"), Decimal("25")],
            [Decimal("1000"), Decimal("2000"), Decimal("3000")],
            [Decimal("0.01"), Decimal("0.02"), Decimal("0.03")],
        ]

        for amounts in test_cases:
            # Create line items
            line_items = [
                LineItem(
                    description=f"Item {i}",
                    quantity=Decimal("1"),
                    unit_price=amount,
                    unit="unit",
                )
                for i, amount in enumerate(amounts)
            ]

            totals = BillingCalculator.calculate_invoice_total(line_items)

            # Verify basic consistency
            assert totals["subtotal"] == sum(item.subtotal for item in line_items)
            assert totals["total"] >= totals["subtotal"]  # Total includes tax
            assert totals["taxable_amount"] == totals["subtotal"]  # No discounts

    def test_metering_monthly_projection_reasonable(self):
        """Test that monthly projections are reasonable."""
        test_cases = [
            (100.0, 10, 30),  # 10 days in 30-day month
            (500.0, 15, 31),  # Half month
            (1000.0, 1, 28),  # Single day in February
            (250.0, 30, 30),  # Full month
        ]

        for daily_usage, days_elapsed, days_in_month in test_cases:
            projection = MeteringCalculator.calculate_monthly_projection(
                daily_usage, days_elapsed, days_in_month
            )

            # Projection should be reasonable
            avg_daily = daily_usage / days_elapsed
            assert projection == avg_daily * days_in_month

    def test_billing_distribute_amount_exact(self):
        """Test that amount distribution is exact."""
        test_cases = [
            (
                Decimal("100"),
                [Decimal("1"), Decimal("1"), Decimal("1")],
            ),  # Equal weights
            (
                Decimal("1000"),
                [Decimal("2"), Decimal("3"), Decimal("5")],
            ),  # Different weights
            (
                Decimal("99.99"),
                [Decimal("1"), Decimal("2"), Decimal("3"), Decimal("4")],
            ),  # Rounding
            (
                Decimal("0.03"),
                [Decimal("1"), Decimal("1"), Decimal("1")],
            ),  # Small amount
        ]

        for total_amount, weights in test_cases:
            distributions = BillingCalculator.distribute_amount(total_amount, weights)

            # Sum should equal total exactly
            assert sum(distributions) == total_amount
            assert len(distributions) == len(weights)
            assert all(d >= Decimal("0") for d in distributions)

    def test_calculator_edge_cases(self):
        """Test edge cases across all calculators."""
        # Test zero amounts
        assert BillingCalculator.round_amount(Decimal("0")) == Decimal("0.00")

        # Test maximum discount
        discount = Discount("Max", DiscountType.PERCENTAGE, Decimal("100"))
        assert BillingCalculator.calculate_discount(Decimal("1000"), discount) == Decimal("1000.00")

        # Test zero original price in contract
        amount, rate = ContractValidator.calculate_discount(0, 0)
        assert amount == Decimal("0.00")
        assert rate == Decimal("0.00")

        # Test same unit conversion
        assert MeteringCalculator.convert_units(100, "KB", "KB") == 100

        # Test zero adjustment
        final, adj = AdjustmentCalculator.apply_adjustment(
            Decimal("100"), Decimal("0"), AdjustmentType.FIXED_DISCOUNT
        )
        assert final == Decimal("100.00")
        assert adj == Decimal("0.00")
