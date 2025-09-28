"""Unit tests for BillingCalculator - pure billing calculation logic."""

from decimal import Decimal

from libs.billing_calculator import (
    BillingCalculator,
    Discount,
    DiscountType,
    LineItem,
    TaxType,
    TierRule,
)


class TestBillingCalculator:
    """Unit tests for billing calculation logic."""

    def test_round_amount(self):
        """Test amount rounding."""
        assert BillingCalculator.round_amount(Decimal("10.555")) == Decimal("10.56")
        assert BillingCalculator.round_amount(Decimal("10.554")) == Decimal("10.55")
        assert BillingCalculator.round_amount(Decimal("10.5")) == Decimal("10.50")
        assert BillingCalculator.round_amount(Decimal("10")) == Decimal("10.00")

    def test_line_item_calculations(self):
        """Test LineItem property calculations."""
        item = LineItem(
            description="Test Item",
            quantity=Decimal("10"),
            unit_price=Decimal("100"),
            unit="items",
            tax_rate=Decimal("10"),
            discount_amount=Decimal("50"),
        )

        assert item.subtotal == Decimal("1000")  # 10 * 100
        assert item.discount_total == Decimal("50")
        assert item.taxable_amount == Decimal("950")  # 1000 - 50
        assert item.tax_amount == Decimal("95")  # 950 * 10%
        assert item.total == Decimal("1045")  # 950 + 95

    def test_calculate_discount_fixed(self):
        """Test fixed discount calculation."""
        discount = Discount(
            name="Fixed $50 off", discount_type=DiscountType.FIXED, value=Decimal("50")
        )

        # Normal case
        amount = BillingCalculator.calculate_discount(Decimal("200"), discount)
        assert amount == Decimal("50.00")

        # Discount exceeds base amount
        amount = BillingCalculator.calculate_discount(Decimal("30"), discount)
        assert amount == Decimal("30.00")  # Capped at base amount

    def test_calculate_discount_percentage(self):
        """Test percentage discount calculation."""
        discount = Discount(
            name="10% off", discount_type=DiscountType.PERCENTAGE, value=Decimal("10")
        )

        amount = BillingCalculator.calculate_discount(Decimal("200"), discount)
        assert amount == Decimal("20.00")  # 200 * 10%

        amount = BillingCalculator.calculate_discount(Decimal("333.33"), discount)
        assert amount == Decimal("33.33")  # Rounded

    def test_calculate_discount_with_minimum(self):
        """Test discount with minimum amount requirement."""
        discount = Discount(
            name="10% off orders over $100",
            discount_type=DiscountType.PERCENTAGE,
            value=Decimal("10"),
            min_amount=Decimal("100"),
        )

        # Above minimum
        amount = BillingCalculator.calculate_discount(Decimal("200"), discount)
        assert amount == Decimal("20.00")

        # Below minimum
        amount = BillingCalculator.calculate_discount(Decimal("50"), discount)
        assert amount == Decimal("0.00")

    def test_calculate_discount_with_maximum(self):
        """Test discount with maximum cap."""
        discount = Discount(
            name="20% off up to $50",
            discount_type=DiscountType.PERCENTAGE,
            value=Decimal("20"),
            max_discount=Decimal("50"),
        )

        # Below cap
        amount = BillingCalculator.calculate_discount(Decimal("200"), discount)
        assert amount == Decimal("40.00")  # 200 * 20%

        # Above cap
        amount = BillingCalculator.calculate_discount(Decimal("500"), discount)
        assert amount == Decimal("50.00")  # Capped at max

    def test_apply_multiple_discounts_non_compound(self):
        """Test applying multiple discounts without compounding."""
        discounts = [
            Discount("10% off", DiscountType.PERCENTAGE, Decimal("10")),
            Discount("$20 off", DiscountType.FIXED, Decimal("20")),
            Discount("5% off", DiscountType.PERCENTAGE, Decimal("5")),
        ]

        final, total_discount = BillingCalculator.apply_multiple_discounts(
            Decimal("200"), discounts, compound=False
        )

        # 10% = 20, Fixed = 20, 5% = 10, Total = 50
        assert total_discount == Decimal("50.00")
        assert final == Decimal("150.00")

    def test_apply_multiple_discounts_compound(self):
        """Test applying multiple discounts with compounding."""
        discounts = [
            Discount("10% off", DiscountType.PERCENTAGE, Decimal("10")),
            Discount("$20 off", DiscountType.FIXED, Decimal("20")),
            Discount("5% off", DiscountType.PERCENTAGE, Decimal("5")),
        ]

        final, total_discount = BillingCalculator.apply_multiple_discounts(
            Decimal("200"), discounts, compound=True
        )

        # Step 1: 200 - 20 (10%) = 180
        # Step 2: 180 - 20 = 160
        # Step 3: 160 - 8 (5%) = 152
        assert total_discount == Decimal("48.00")
        assert final == Decimal("152.00")

    def test_calculate_tiered_pricing(self):
        """Test tiered pricing calculation."""
        tiers = [
            TierRule(Decimal("0"), Decimal("10"), Decimal("10")),  # $10 each for 1-10
            TierRule(Decimal("10"), Decimal("20"), Decimal("8")),  # $8 each for 11-20
            TierRule(Decimal("20"), None, Decimal("6")),  # $6 each for 21+
        ]

        # 5 units - all in first tier
        price = BillingCalculator.calculate_tiered_pricing(Decimal("5"), tiers)
        assert price == Decimal("50.00")  # 5 * 10

        # 15 units - spans two tiers
        price = BillingCalculator.calculate_tiered_pricing(Decimal("15"), tiers)
        assert price == Decimal("142.00")  # (11 * 10) + (4 * 8)

        # 25 units - all three tiers
        price = BillingCalculator.calculate_tiered_pricing(Decimal("25"), tiers)
        assert price == Decimal("216.00")  # (11 * 10) + (11 * 8) + (3 * 6)

    def test_calculate_tax(self):
        """Test tax calculation."""
        # Default VAT rate
        tax = BillingCalculator.calculate_tax(Decimal("1000"), TaxType.VAT)
        assert tax == Decimal("100.00")  # 10% VAT

        # Custom tax rate
        tax = BillingCalculator.calculate_tax(
            Decimal("1000"), TaxType.SALES_TAX, Decimal("7.5")
        )
        assert tax == Decimal("75.00")  # 7.5%

        # Tax exempt
        tax = BillingCalculator.calculate_tax(
            Decimal("1000"), TaxType.VAT, tax_exempt=True
        )
        assert tax == Decimal("0.00")

    def test_calculate_invoice_total(self):
        """Test complete invoice calculation."""
        line_items = [
            LineItem("Item 1", Decimal("10"), Decimal("100"), "units"),
            LineItem(
                "Item 2",
                Decimal("5"),
                Decimal("50"),
                "units",
                discount_amount=Decimal("25"),
            ),
        ]

        discounts = [
            Discount("Loyalty discount", DiscountType.PERCENTAGE, Decimal("5"))
        ]

        totals = BillingCalculator.calculate_invoice_total(
            line_items,
            discounts=discounts,
            tax_type=TaxType.VAT,
            shipping_fee=Decimal("20"),
        )

        assert totals["subtotal"] == Decimal("1250.00")  # 1000 + 250
        assert totals["item_discounts"] == Decimal("25.00")
        assert totals["invoice_discounts"] == Decimal("61.25")  # 5% of 1225
        assert totals["total_discounts"] == Decimal("86.25")
        assert totals["shipping"] == Decimal("20.00")
        assert totals["taxable_amount"] == Decimal("1183.75")  # 1250 - 86.25 + 20
        assert totals["tax_amount"] == Decimal("118.38")  # 10% VAT (rounded)
        assert totals["total"] == Decimal("1302.13")

    def test_calculate_proration(self):
        """Test proration calculation."""
        # Normal proration
        prorated = BillingCalculator.calculate_proration(
            Decimal("300"), days_used=10, days_in_period=30
        )
        assert prorated == Decimal("100.00")  # 300 * 10/30

        # With minimum days
        prorated = BillingCalculator.calculate_proration(
            Decimal("300"), days_used=0, days_in_period=30, minimum_days=3
        )
        assert prorated == Decimal("30.00")  # 300 * 3/30

        # Full period
        prorated = BillingCalculator.calculate_proration(
            Decimal("300"), days_used=30, days_in_period=30
        )
        assert prorated == Decimal("300.00")

    def test_calculate_compound_interest(self):
        """Test compound interest calculation."""
        # Daily compounding for 30 days at 18% annual
        interest = BillingCalculator.calculate_compound_interest(
            Decimal("1000"), Decimal("18"), days=30, compound_frequency=365
        )
        # Should be approximately 1.5% for 30 days
        assert Decimal("14.00") < interest < Decimal("16.00")

        # Simple case - 1 year at 10%
        interest = BillingCalculator.calculate_compound_interest(
            Decimal("1000"), Decimal("10"), days=365, compound_frequency=1
        )
        assert interest == Decimal("100.00")

    def test_distribute_amount(self):
        """Test amount distribution."""
        # Equal weights
        distributions = BillingCalculator.distribute_amount(
            Decimal("100"), [Decimal("1"), Decimal("1"), Decimal("1")]
        )
        assert distributions == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
        assert sum(distributions) == Decimal("100.00")

        # Different weights
        distributions = BillingCalculator.distribute_amount(
            Decimal("100"), [Decimal("2"), Decimal("3"), Decimal("5")]
        )
        assert distributions == [Decimal("20.00"), Decimal("30.00"), Decimal("50.00")]
        assert sum(distributions) == Decimal("100.00")

        # Edge case - zero weights
        distributions = BillingCalculator.distribute_amount(Decimal("100"), [])
        assert distributions == []

        # Single weight
        distributions = BillingCalculator.distribute_amount(
            Decimal("100"), [Decimal("1")]
        )
        assert distributions == [Decimal("100.00")]
