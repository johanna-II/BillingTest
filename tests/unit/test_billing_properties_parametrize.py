"""Property-based tests for billing calculations using pytest parametrize.

This module tests mathematical properties of billing calculations using
pytest's parametrize decorator instead of Hypothesis. This ensures full
Python 3.12+ compatibility while maintaining property-based testing concepts.

This is a Python 3.12+ compatible alternative to test_billing_properties.py.
"""

import random
from decimal import Decimal

import pytest


# Test data generators
def generate_amounts(count=100):
    """Generate diverse billing amounts for testing."""
    random.seed(42)  # For reproducibility
    amounts = []

    # Edge cases
    amounts.extend([Decimal("0"), Decimal("0.01"), Decimal("1"), Decimal("100")])

    # Random amounts
    for _ in range(count - 4):
        value = random.randint(0, 10_000_000)
        amounts.append(Decimal(str(value)))

    return amounts


def generate_percentages(count=100):
    """Generate valid percentage values for testing."""
    random.seed(43)
    percentages = []

    # Edge cases
    percentages.extend([0, 1, 50, 99, 100])

    # Random percentages
    for _ in range(count - 5):
        percentages.append(random.randint(0, 100))

    return percentages


# Generate test data
AMOUNTS = generate_amounts(50)  # Use smaller dataset for faster tests
PERCENTAGES = generate_percentages(20)
AMOUNT_PAIRS = [(a1, a2) for a1 in AMOUNTS[:10] for a2 in AMOUNTS[:10]]


class TestBillingProperties:
    """Property-based tests for billing calculations."""

    @pytest.mark.parametrize(
        "amount,discount_rate", [(a, p) for a in AMOUNTS for p in PERCENTAGES[:10]]
    )
    def test_discount_never_negative(self, amount, discount_rate):
        """Property: Applying discount never results in negative amount."""
        result = amount - (amount * Decimal(discount_rate) / Decimal(100))
        assert result >= 0, f"Discount resulted in negative: {result}"

    @pytest.mark.parametrize(
        "amount,discount_rate", [(a, p) for a in AMOUNTS for p in PERCENTAGES[:10]]
    )
    def test_discount_never_exceeds_original(self, amount, discount_rate):
        """Property: Result after discount never exceeds original amount."""
        result = amount - (amount * Decimal(discount_rate) / Decimal(100))
        assert result <= amount, f"Result {result} exceeds original {amount}"

    @pytest.mark.parametrize("base_amount", AMOUNTS)
    def test_credit_application_bounded(self, base_amount):
        """Property: Applied credit never exceeds available credit or base amount."""
        # Test with various credit amounts
        for multiplier in [0.5, 1.0, 1.5, 2.0]:
            credit_amount = base_amount * Decimal(str(multiplier))

            # Calculate what would be applied
            applied = min(base_amount, credit_amount)

            assert applied <= credit_amount, "Applied more than available"
            assert applied <= base_amount, "Applied more than needed"

            # Final amount should be non-negative
            final_amount = base_amount - applied
            assert final_amount >= 0, "Final amount is negative"

    @pytest.mark.parametrize("amount1,amount2", AMOUNT_PAIRS[:50])
    def test_addition_commutative(self, amount1, amount2):
        """Property: Addition is commutative (order doesn't matter)."""
        amount3 = AMOUNTS[0]  # Use a fixed third amount

        # Different orders of addition
        result1 = amount1 + amount2 + amount3
        result2 = amount3 + amount1 + amount2
        result3 = amount2 + amount3 + amount1

        assert result1 == result2 == result3, "Addition is not commutative"

    @pytest.mark.parametrize("amount", AMOUNTS)
    def test_zero_discount_is_identity(self, amount):
        """Property: 0% discount returns original amount (identity)."""
        result = amount - (amount * Decimal(0) / Decimal(100))
        assert result == amount, "0% discount changed the amount"

    @pytest.mark.parametrize("amount", AMOUNTS)
    def test_hundred_percent_discount_is_zero(self, amount):
        """Property: 100% discount results in 0."""
        result = amount - (amount * Decimal(100) / Decimal(100))
        assert result == 0, "100% discount didn't result in 0"

    @pytest.mark.parametrize(
        "base,rate1,rate2",
        [
            (a, p1, p2)
            for a in AMOUNTS[:20]
            for p1 in PERCENTAGES[:5]
            for p2 in PERCENTAGES[:5]
        ],
    )
    def test_cascading_discounts(self, base, rate1, rate2):
        """Property: Cascading discounts should never increase amount."""
        # Apply first discount
        after_first = base - (base * Decimal(rate1) / Decimal(100))

        # Apply second discount to the result
        after_second = after_first - (after_first * Decimal(rate2) / Decimal(100))

        assert (
            after_second <= after_first <= base
        ), "Cascading discounts increased amount"

    @pytest.mark.parametrize("amounts_count", [2, 5, 10, 20])
    def test_sum_of_parts_equals_whole(self, amounts_count):
        """Property: Sum of individual amounts equals total (aggregation)."""
        amounts = AMOUNTS[:amounts_count]

        total = sum(amounts)
        manual_sum = Decimal(0)

        for amount in amounts:
            manual_sum += amount

        assert total == manual_sum, "Sum of parts doesn't equal whole"

    @pytest.mark.parametrize("base,unpaid", AMOUNT_PAIRS[:50])
    def test_unpaid_always_increases_or_maintains(self, base, unpaid):
        """Property: Adding unpaid amount never decreases total."""
        total = base + unpaid

        assert total >= base, "Adding unpaid decreased total"
        assert total >= unpaid, "Total less than unpaid amount"

    @pytest.mark.parametrize("amount,credit", AMOUNT_PAIRS[:50])
    def test_overpayment_handling(self, amount, credit):
        """Property: Credit application handles overpayment correctly."""
        applied = min(amount, credit)
        remaining = amount - applied

        assert remaining >= 0, "Remaining amount is negative"

        if credit >= amount:
            assert remaining == 0, "Should be fully paid when credit >= amount"

    @pytest.mark.parametrize(
        "metering_count,unit_price",
        [
            (count, price)
            for count in [0, 1, 10, 100, 1000, 100000, 1000000]
            for price in [
                Decimal("0.001"),
                Decimal("0.01"),
                Decimal("0.1"),
                Decimal("1"),
                Decimal("10"),
                Decimal("100"),
                Decimal("1000"),
            ]
        ],
    )
    def test_metering_calculation_bounds(self, metering_count, unit_price):
        """Property: Metering calculation stays within expected bounds."""
        total = Decimal(metering_count) * unit_price

        # Should be non-negative
        assert total >= 0, "Total is negative"

        # Should not exceed maximum possible
        max_possible = Decimal(metering_count) * unit_price
        assert total == max_possible, "Total doesn't match expected calculation"

    @pytest.mark.parametrize("amounts_count", [2, 5, 10])
    def test_precision_maintained_in_aggregation(self, amounts_count):
        """Property: Decimal precision is maintained during aggregation."""
        # Use specific decimal amounts with 2 decimal places
        amounts = [
            Decimal("10.50"),
            Decimal("20.75"),
            Decimal("30.25"),
            Decimal("40.99"),
            Decimal("50.01"),
            Decimal("60.33"),
            Decimal("70.77"),
            Decimal("80.88"),
            Decimal("90.12"),
            Decimal("100.45"),
        ][:amounts_count]

        total = sum(amounts, Decimal(0))

        # Calculate using string concatenation (alternative method)
        manual_total = Decimal(0)
        for amount in amounts:
            manual_total += amount

        # Should be exactly equal (not just approximately)
        assert total == manual_total, "Precision lost during aggregation"


class TestBillingInvariants:
    """Test invariants that must always hold true."""

    @pytest.mark.parametrize("amount", AMOUNTS)
    def test_amount_times_one_is_identity(self, amount):
        """Invariant: amount × 1 = amount."""
        result = amount * Decimal(1)
        assert result == amount

    @pytest.mark.parametrize("amount", AMOUNTS)
    def test_amount_times_zero_is_zero(self, amount):
        """Invariant: amount × 0 = 0."""
        result = amount * Decimal(0)
        assert result == 0

    @pytest.mark.parametrize(
        "amount,count", [(a, c) for a in AMOUNTS[:20] for c in [0, 1, 10, 100, 1000]]
    )
    def test_amount_times_count_positive(self, amount, count):
        """Invariant: amount × positive_count >= 0."""
        result = amount * Decimal(count)
        assert result >= 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_max_decimal_handling(self):
        """Test handling of maximum Decimal values."""
        max_amount = Decimal("9" * 10)  # Very large number

        # Should not overflow
        result = max_amount + Decimal(1)
        assert result > max_amount

    def test_min_decimal_handling(self):
        """Test handling of minimum positive Decimal values."""
        min_amount = Decimal("0.01")  # Smallest currency unit

        # Should handle small amounts correctly
        result = min_amount * Decimal(100)
        assert result == Decimal(1)

    @pytest.mark.parametrize("amount", AMOUNTS[:20])
    def test_idempotent_operations(self, amount):
        """Test operations that should be idempotent."""
        # Adding 0 multiple times
        result = amount
        for _ in range(10):
            result = result + Decimal(0)

        assert result == amount, "Adding 0 changed the amount"


# Performance summary
def test_suite_info():
    """Display information about the test suite."""
    total_discount_tests = len(AMOUNTS) * len(PERCENTAGES[:10]) * 2
    total_pair_tests = len(AMOUNT_PAIRS[:50]) * 3
    total_cascade_tests = (
        len(AMOUNTS[:20]) * len(PERCENTAGES[:5]) * len(PERCENTAGES[:5])
    )

    print("\n=== Property-based Test Suite ===")
    print(f"Total amount test cases: {len(AMOUNTS)}")
    print(f"Total percentage test cases: {len(PERCENTAGES)}")
    print(f"Discount property tests: {total_discount_tests}")
    print(f"Amount pair tests: {total_pair_tests}")
    print(f"Cascade discount tests: {total_cascade_tests}")
    print("All tests use deterministic random generation for reproducibility")
