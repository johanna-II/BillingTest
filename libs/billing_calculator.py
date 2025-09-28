"""Billing Calculator for complex billing calculations and aggregations."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple


class DiscountType(Enum):
    """Types of discounts that can be applied."""

    FIXED = "FIXED"
    PERCENTAGE = "PERCENTAGE"
    TIERED = "TIERED"
    VOLUME = "VOLUME"


class TaxType(Enum):
    """Types of taxes."""

    VAT = "VAT"
    GST = "GST"
    SALES_TAX = "SALES_TAX"


@dataclass
class LineItem:
    """Represents a single line item in billing."""

    description: str
    quantity: Decimal
    unit_price: Decimal
    unit: str
    tax_rate: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")

    @property
    def subtotal(self) -> Decimal:
        """Calculate subtotal before tax and discounts."""
        return self.quantity * self.unit_price

    @property
    def discount_total(self) -> Decimal:
        """Get total discount amount."""
        return self.discount_amount

    @property
    def taxable_amount(self) -> Decimal:
        """Calculate amount subject to tax."""
        return self.subtotal - self.discount_total

    @property
    def tax_amount(self) -> Decimal:
        """Calculate tax amount."""
        return self.taxable_amount * self.tax_rate / 100

    @property
    def total(self) -> Decimal:
        """Calculate total including tax and discounts."""
        return self.taxable_amount + self.tax_amount


@dataclass
class Discount:
    """Represents a discount to be applied."""

    name: str
    discount_type: DiscountType
    value: Decimal
    min_amount: Optional[Decimal] = None
    max_discount: Optional[Decimal] = None
    applicable_items: Optional[List[str]] = None


@dataclass
class TierRule:
    """Rule for tiered pricing."""

    min_quantity: Decimal
    max_quantity: Optional[Decimal]
    unit_price: Decimal


class BillingCalculator:
    """Handles complex billing calculations.

    This class provides pure calculation logic for billing operations,
    including discounts, taxes, tiered pricing, and aggregations.
    """

    # Default precision for monetary calculations
    DECIMAL_PLACES = 2

    # Common tax rates
    DEFAULT_TAX_RATES = {
        TaxType.VAT: Decimal("10"),  # 10% VAT (Korea)
        TaxType.GST: Decimal("10"),  # 10% GST
        TaxType.SALES_TAX: Decimal("8.25"),  # Example US sales tax
    }

    @classmethod
    def round_amount(cls, amount: Decimal) -> Decimal:
        """Round amount to standard decimal places.

        Args:
            amount: Amount to round

        Returns:
            Rounded amount
        """
        return amount.quantize(
            Decimal(f"0.{'0' * cls.DECIMAL_PLACES}"), rounding=ROUND_HALF_UP
        )

    @classmethod
    def calculate_discount(cls, base_amount: Decimal, discount: Discount) -> Decimal:
        """Calculate discount amount.

        Args:
            base_amount: Base amount to apply discount to
            discount: Discount details

        Returns:
            Discount amount
        """
        # Check minimum amount requirement
        if discount.min_amount and base_amount < discount.min_amount:
            return Decimal("0")

        if discount.discount_type == DiscountType.FIXED:
            discount_amount = discount.value
        elif discount.discount_type == DiscountType.PERCENTAGE:
            discount_amount = base_amount * discount.value / 100
        else:
            # Other discount types not implemented yet
            discount_amount = Decimal("0")

        # Apply maximum discount cap if specified
        if discount.max_discount:
            discount_amount = min(discount_amount, discount.max_discount)

        # Ensure discount doesn't exceed base amount
        discount_amount = min(discount_amount, base_amount)

        return cls.round_amount(discount_amount)

    @classmethod
    def apply_multiple_discounts(
        cls, base_amount: Decimal, discounts: List[Discount], compound: bool = False
    ) -> Tuple[Decimal, Decimal]:
        """Apply multiple discounts to an amount.

        Args:
            base_amount: Base amount to apply discounts to
            discounts: List of discounts to apply
            compound: If True, apply discounts sequentially; if False, sum them

        Returns:
            Tuple of (final_amount, total_discount)
        """
        if compound:
            # Apply discounts one after another
            current_amount = base_amount
            total_discount = Decimal("0")

            for discount in discounts:
                discount_amount = cls.calculate_discount(current_amount, discount)
                current_amount -= discount_amount
                total_discount += discount_amount
        else:
            # Sum all discounts and apply together
            total_discount = Decimal("0")
            for discount in discounts:
                discount_amount = cls.calculate_discount(base_amount, discount)
                total_discount += discount_amount

            # Ensure total discount doesn't exceed base amount
            total_discount = min(total_discount, base_amount)
            current_amount = base_amount - total_discount

        return cls.round_amount(current_amount), cls.round_amount(total_discount)

    @classmethod
    def calculate_tiered_pricing(
        cls, quantity: Decimal, tier_rules: List[TierRule]
    ) -> Decimal:
        """Calculate price using tiered pricing rules.

        Args:
            quantity: Total quantity
            tier_rules: List of tier rules (must be sorted by min_quantity)

        Returns:
            Total price
        """
        total_price = Decimal("0")
        remaining_quantity = quantity

        # Sort rules by min_quantity to ensure correct order
        sorted_rules = sorted(tier_rules, key=lambda r: r.min_quantity)

        for i, rule in enumerate(sorted_rules):
            if remaining_quantity <= 0:
                break

            # Determine the quantity for this tier
            if rule.max_quantity:
                tier_quantity = min(
                    remaining_quantity, rule.max_quantity - rule.min_quantity + 1
                )
            else:
                # Last tier - use all remaining
                tier_quantity = remaining_quantity

            # Only apply if we've reached the minimum for this tier
            if quantity >= rule.min_quantity:
                tier_price = tier_quantity * rule.unit_price
                total_price += tier_price
                remaining_quantity -= tier_quantity

        return cls.round_amount(total_price)

    @classmethod
    def calculate_tax(
        cls,
        taxable_amount: Decimal,
        tax_type: TaxType,
        tax_rate: Optional[Decimal] = None,
        tax_exempt: bool = False,
    ) -> Decimal:
        """Calculate tax amount.

        Args:
            taxable_amount: Amount subject to tax
            tax_type: Type of tax
            tax_rate: Tax rate (uses default if not provided)
            tax_exempt: If True, returns 0

        Returns:
            Tax amount
        """
        if tax_exempt:
            return Decimal("0")

        if tax_rate is None:
            tax_rate = cls.DEFAULT_TAX_RATES.get(tax_type, Decimal("0"))

        tax_amount = taxable_amount * tax_rate / 100
        return cls.round_amount(tax_amount)

    @classmethod
    def calculate_invoice_total(
        cls,
        line_items: List[LineItem],
        discounts: Optional[List[Discount]] = None,
        tax_type: Optional[TaxType] = None,
        tax_rate: Optional[Decimal] = None,
        shipping_fee: Decimal = Decimal("0"),
    ) -> Dict[str, Decimal]:
        """Calculate complete invoice totals.

        Args:
            line_items: List of line items
            discounts: Optional list of discounts to apply
            tax_type: Type of tax to apply
            tax_rate: Tax rate (uses default if not provided)
            shipping_fee: Shipping fee to add

        Returns:
            Dictionary with breakdown of totals
        """
        # Calculate subtotal
        subtotal = sum((item.subtotal for item in line_items), Decimal("0"))

        # Apply item-level discounts
        item_discounts = sum((item.discount_total for item in line_items), Decimal("0"))

        # Apply invoice-level discounts
        invoice_discounts = Decimal("0")
        if discounts:
            discountable_amount = subtotal - item_discounts
            _, invoice_discounts = cls.apply_multiple_discounts(
                discountable_amount, discounts
            )

        # Calculate taxable amount
        total_discounts = item_discounts + invoice_discounts
        taxable_amount = subtotal - total_discounts + shipping_fee

        # Calculate tax
        tax_amount = Decimal("0")
        if tax_type:
            tax_amount = cls.calculate_tax(taxable_amount, tax_type, tax_rate)

        # Calculate total
        total = taxable_amount + tax_amount

        return {
            "subtotal": cls.round_amount(subtotal),
            "item_discounts": cls.round_amount(item_discounts),
            "invoice_discounts": cls.round_amount(invoice_discounts),
            "total_discounts": cls.round_amount(total_discounts),
            "shipping": cls.round_amount(shipping_fee),
            "taxable_amount": cls.round_amount(taxable_amount),
            "tax_amount": cls.round_amount(tax_amount),
            "total": cls.round_amount(total),
        }

    @classmethod
    def calculate_proration(
        cls,
        full_amount: Decimal,
        days_used: int,
        days_in_period: int,
        minimum_days: int = 1,
    ) -> Decimal:
        """Calculate prorated amount.

        Args:
            full_amount: Full period amount
            days_used: Number of days used
            days_in_period: Total days in billing period
            minimum_days: Minimum billable days

        Returns:
            Prorated amount
        """
        # Ensure minimum billing
        billable_days = max(days_used, minimum_days)

        # Calculate proration
        if days_in_period > 0:
            prorated = full_amount * billable_days / days_in_period
        else:
            prorated = Decimal("0")

        return cls.round_amount(prorated)

    @classmethod
    def calculate_compound_interest(
        cls,
        principal: Decimal,
        annual_rate: Decimal,
        days: int,
        compound_frequency: int = 365,
    ) -> Decimal:
        """Calculate compound interest (for late fees, etc).

        Args:
            principal: Principal amount
            annual_rate: Annual interest rate (percentage)
            days: Number of days
            compound_frequency: How often interest compounds per year

        Returns:
            Interest amount
        """
        # Convert to decimal rate
        rate = annual_rate / 100

        # Calculate compound interest
        # A = P(1 + r/n)^(nt) - P
        periods = Decimal(days) / Decimal(365) * compound_frequency

        # For more accurate calculation with Decimal
        base = 1 + rate / compound_frequency
        multiplier = base**periods

        total_amount = principal * multiplier
        interest = total_amount - principal

        return cls.round_amount(interest)

    @classmethod
    def distribute_amount(
        cls, total_amount: Decimal, weights: List[Decimal]
    ) -> List[Decimal]:
        """Distribute an amount according to weights.

        Ensures the sum equals the total amount exactly (handles rounding).

        Args:
            total_amount: Total amount to distribute
            weights: List of weights for distribution

        Returns:
            List of distributed amounts
        """
        if not weights or sum(weights, Decimal("0")) == 0:
            return []

        total_weight = sum(weights, Decimal("0"))
        distributions = []
        accumulated = Decimal("0")

        for i, weight in enumerate(weights[:-1]):
            # Calculate this portion
            portion = total_amount * weight / total_weight
            rounded_portion = cls.round_amount(portion)
            distributions.append(rounded_portion)
            accumulated += rounded_portion

        # Last portion gets the remainder to ensure exact total
        if weights:
            last_portion = total_amount - accumulated
            distributions.append(cls.round_amount(last_portion))

        return distributions
