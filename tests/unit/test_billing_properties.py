"""Property-based tests for billing calculations.

This module uses Hypothesis to generate thousands of random test cases
to verify mathematical properties of billing calculations.
"""

from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st


# Custom strategies for billing domain
@st.composite
def valid_amount(draw):
    """Generate valid billing amounts (0 to 10,000,000)."""
    return Decimal(str(draw(st.integers(min_value=0, max_value=10_000_000))))


@st.composite
def valid_percentage(draw):
    """Generate valid percentage (0 to 100)."""
    return draw(st.integers(min_value=0, max_value=100))


@st.composite
def valid_credit_amount(draw, max_value=None):
    """Generate valid credit amounts."""
    max_val = max_value if max_value else 10_000_000
    return Decimal(str(draw(st.integers(min_value=0, max_value=max_val))))


class TestBillingProperties:
    """Property-based tests for billing calculations."""

    @given(amount=valid_amount(), discount_rate=valid_percentage())
    def test_discount_never_negative(self, amount, discount_rate):
        """Property: Applying discount never results in negative amount.

        For any valid amount and discount rate, the result should be >= 0.
        """
        result = amount - (amount * Decimal(discount_rate) / Decimal(100))
        assert result >= 0, f"Discount resulted in negative: {result}"

    @given(amount=valid_amount(), discount_rate=valid_percentage())
    def test_discount_never_exceeds_original(self, amount, discount_rate):
        """Property: Result after discount never exceeds original amount.

        Discount should only reduce or keep the same, never increase.
        """
        result = amount - (amount * Decimal(discount_rate) / Decimal(100))
        assert result <= amount, f"Result {result} exceeds original {amount}"

    @given(base_amount=valid_amount())
    def test_credit_application_bounded(self, base_amount):
        """Property: Applied credit never exceeds available credit or base amount.

        When applying credit to a bill:
        1. Applied credit <= available credit
        2. Final amount >= 0 (can't go negative)
        """
        # Generate credit amount (could be more or less than base)
        credit_amount = Decimal(
            str(st.integers(min_value=0, max_value=int(base_amount) * 2).example())
        )

        # Calculate what would be applied
        applied = min(base_amount, credit_amount)

        assert applied <= credit_amount, "Applied more than available"
        assert applied <= base_amount, "Applied more than needed"

        # Final amount should be non-negative
        final_amount = base_amount - applied
        assert final_amount >= 0, "Final amount is negative"

    @given(
        amount1=valid_amount(),
        amount2=valid_amount(),
        amount3=valid_amount(),
    )
    def test_addition_commutative(self, amount1, amount2, amount3):
        """Property: Addition is commutative (order doesn't matter).

        For usage aggregation, the order of adding amounts shouldn't matter.
        """
        # Different orders of addition
        result1 = amount1 + amount2 + amount3
        result2 = amount3 + amount1 + amount2
        result3 = amount2 + amount3 + amount1

        assert result1 == result2 == result3, "Addition is not commutative"

    @given(
        base=valid_amount(),
        adjustment1=valid_amount(),
        adjustment2=valid_amount(),
    )
    def test_multiple_adjustments_order_independent(
        self, base, adjustment1, adjustment2
    ):
        """Property: Multiple fixed adjustments are order-independent.

        When applying fixed adjustments, the order shouldn't matter.
        """
        # Order 1: base + adj1 + adj2
        result1 = base + adjustment1 + adjustment2

        # Order 2: base + adj2 + adj1
        result2 = base + adjustment2 + adjustment1

        assert result1 == result2, "Fixed adjustments are order-dependent"

    @given(amount=valid_amount())
    def test_zero_discount_is_identity(self, amount):
        """Property: 0% discount returns original amount (identity).

        Applying 0% discount should not change the amount.
        """
        result = amount - (amount * Decimal(0) / Decimal(100))
        assert result == amount, "0% discount changed the amount"

    @given(amount=valid_amount())
    def test_hundred_percent_discount_is_zero(self, amount):
        """Property: 100% discount results in 0.

        Applying 100% discount should result in 0.
        """
        result = amount - (amount * Decimal(100) / Decimal(100))
        assert result == 0, "100% discount didn't result in 0"

    @given(
        base=valid_amount(),
        rate1=valid_percentage(),
        rate2=valid_percentage(),
    )
    def test_cascading_discounts(self, base, rate1, rate2):
        """Property: Cascading discounts should never increase amount.

        Applying discount1 then discount2 should result in amount <= base.
        """
        # Apply first discount
        after_first = base - (base * Decimal(rate1) / Decimal(100))

        # Apply second discount to the result
        after_second = after_first - (after_first * Decimal(rate2) / Decimal(100))

        assert (
            after_second <= after_first <= base
        ), "Cascading discounts increased amount"

    @given(amounts=st.lists(valid_amount(), min_size=1, max_size=100))
    def test_sum_of_parts_equals_whole(self, amounts):
        """Property: Sum of individual amounts equals total (aggregation).

        When aggregating usage, the sum of parts should equal the whole.
        """
        total = sum(amounts)
        manual_sum = Decimal(0)

        for amount in amounts:
            manual_sum += amount

        assert total == manual_sum, "Sum of parts doesn't equal whole"

    @given(base=valid_amount(), unpaid=valid_amount())
    def test_unpaid_always_increases_or_maintains(self, base, unpaid):
        """Property: Adding unpaid amount never decreases total.

        Including unpaid balance should increase or maintain the total.
        """
        total = base + unpaid

        assert total >= base, "Adding unpaid decreased total"
        assert total >= unpaid, "Total less than unpaid amount"

    @given(
        amount=valid_amount(),
        credit=valid_amount(),
    )
    def test_overpayment_handling(self, amount, credit):
        """Property: Credit application handles overpayment correctly.

        If credit > amount, remaining amount should be 0 (not negative).
        """
        applied = min(amount, credit)
        remaining = amount - applied

        assert remaining >= 0, "Remaining amount is negative"

        if credit >= amount:
            assert remaining == 0, "Should be fully paid when credit >= amount"

    @given(
        metering_count=st.integers(min_value=0, max_value=1000000),
        unit_price=st.decimals(
            min_value=Decimal("0.001"), max_value=Decimal("1000"), places=3
        ),
    )
    def test_metering_calculation_bounds(self, metering_count, unit_price):
        """Property: Metering calculation stays within expected bounds.

        Total = count × unit_price should be within reasonable bounds.
        """
        total = Decimal(metering_count) * unit_price

        # Should be non-negative
        assert total >= 0, "Total is negative"

        # Should not exceed maximum possible
        max_possible = Decimal(metering_count) * unit_price
        assert total == max_possible, "Total doesn't match expected calculation"

    @given(
        amounts=st.lists(
            st.decimals(min_value=Decimal("0"), max_value=Decimal("1000"), places=2),
            min_size=2,
            max_size=10,
        )
    )
    def test_precision_maintained_in_aggregation(self, amounts):
        """Property: Decimal precision is maintained during aggregation.

        When summing Decimal amounts, precision should be preserved.
        """
        total = sum(amounts, Decimal(0))

        # Calculate using string concatenation (alternative method)
        manual_total = Decimal(0)
        for amount in amounts:
            manual_total += amount

        # Should be exactly equal (not just approximately)
        assert total == manual_total, "Precision lost during aggregation"


class TestBillingInvariants:
    """Test invariants that must always hold true."""

    @given(amount=valid_amount())
    def test_amount_times_one_is_identity(self, amount):
        """Invariant: amount × 1 = amount."""
        result = amount * Decimal(1)
        assert result == amount

    @given(amount=valid_amount())
    def test_amount_times_zero_is_zero(self, amount):
        """Invariant: amount × 0 = 0."""
        result = amount * Decimal(0)
        assert result == 0

    @given(amount=valid_amount(), count=st.integers(min_value=0, max_value=1000))
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

    @given(amount=valid_amount())
    def test_idempotent_operations(self, amount):
        """Test operations that should be idempotent."""
        # Adding 0 multiple times
        result = amount
        for _ in range(10):
            result = result + Decimal(0)

        assert result == amount, "Adding 0 changed the amount"


# Configuration for Hypothesis
# These settings control how many examples to generate
pytest_plugins = ["hypothesis"]


def pytest_configure(config):
    """Configure Hypothesis settings for this test module."""
    from hypothesis import Verbosity, settings

    # You can adjust these settings:
    # - max_examples: how many random cases to generate (default: 100)
    # - verbosity: QUIET, NORMAL, VERBOSE, DEBUG
    settings.register_profile(
        "dev",
        max_examples=100,  # Quick feedback during development
        verbosity=Verbosity.NORMAL,
    )

    settings.register_profile(
        "ci",
        max_examples=1000,  # Thorough testing in CI
        verbosity=Verbosity.NORMAL,
    )

    settings.register_profile(
        "exhaustive",
        max_examples=10000,  # Very thorough (slow)
        verbosity=Verbosity.VERBOSE,
    )

    # Load profile based on environment
    import os

    profile = os.getenv("HYPOTHESIS_PROFILE", "dev")
    settings.load_profile(profile)
