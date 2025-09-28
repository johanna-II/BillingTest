"""Contract Validator for billing contracts validation and calculations."""

import re
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, Optional, Tuple

from .exceptions import ValidationException


class ContractValidator:
    """Handles contract validations and calculations.

    This class encapsulates pure validation and calculation logic for contracts,
    making it easier to test independently from API interactions.
    """

    # Contract ID patterns
    CONTRACT_ID_PATTERN = re.compile(r"^[A-Za-z0-9\-_]+$")

    # Price limits
    MIN_PRICE = Decimal("0")
    MAX_PRICE = Decimal("1000000000")  # 1 billion

    # Discount limits
    MAX_DISCOUNT_RATE = Decimal("100")  # 100% maximum discount

    # Month format pattern
    MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")

    @classmethod
    def validate_month_format(cls, month: str) -> None:
        """Validate month format is YYYY-MM.

        Args:
            month: Month string to validate

        Raises:
            ValidationException: If month format is invalid
        """
        # Check regex pattern
        if not cls.MONTH_PATTERN.match(month):
            raise ValidationException(
                f"Invalid month format: {month}. Expected YYYY-MM"
            )

        # Validate it's a real date
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            raise ValidationException(
                f"Invalid month value: {month}. Must be a valid year-month"
            )

    @classmethod
    def validate_contract_id(cls, contract_id: str) -> None:
        """Validate contract ID format.

        Args:
            contract_id: Contract ID to validate

        Raises:
            ValidationException: If contract ID is invalid
        """
        if not contract_id:
            raise ValidationException("Contract ID cannot be empty")

        if not cls.CONTRACT_ID_PATTERN.match(contract_id):
            raise ValidationException(
                f"Invalid contract ID format: {contract_id}. "
                "Only alphanumeric, hyphen, and underscore allowed"
            )

    @classmethod
    def validate_billing_group_id(cls, billing_group_id: str) -> None:
        """Validate billing group ID.

        Args:
            billing_group_id: Billing group ID to validate

        Raises:
            ValidationException: If billing group ID is invalid
        """
        if not billing_group_id or not billing_group_id.strip():
            raise ValidationException("Billing group ID cannot be empty")

    @classmethod
    def calculate_discount(
        cls, original_price: float | Decimal, discounted_price: float | Decimal
    ) -> Tuple[Decimal, Decimal]:
        """Calculate discount amount and rate.

        Args:
            original_price: Original price before discount
            discounted_price: Price after discount

        Returns:
            Tuple of (discount_amount, discount_rate_percentage)
        """
        # Convert to Decimal for precise calculation
        original = Decimal(str(original_price))
        discounted = Decimal(str(discounted_price))

        # Calculate discount amount
        discount_amount = original - discounted

        # Calculate discount rate
        if original > 0:
            discount_rate = (discount_amount / original) * Decimal("100")
        else:
            discount_rate = Decimal("0")

        # Round to 2 decimal places
        discount_amount = discount_amount.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        discount_rate = discount_rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return discount_amount, discount_rate

    @classmethod
    def validate_price(cls, price: float | Decimal, price_type: str = "price") -> None:
        """Validate price value.

        Args:
            price: Price to validate
            price_type: Type of price for error message

        Raises:
            ValidationException: If price is invalid
        """
        decimal_price = Decimal(str(price))

        if decimal_price < cls.MIN_PRICE:
            raise ValidationException(f"{price_type} cannot be negative")

        if decimal_price > cls.MAX_PRICE:
            raise ValidationException(f"{price_type} cannot exceed {cls.MAX_PRICE}")

    @classmethod
    def validate_discount_rate(cls, discount_rate: Decimal) -> None:
        """Validate discount rate.

        Args:
            discount_rate: Discount rate percentage to validate

        Raises:
            ValidationException: If discount rate is invalid
        """
        if discount_rate < Decimal("0"):
            raise ValidationException("Discount rate cannot be negative")

        if discount_rate > cls.MAX_DISCOUNT_RATE:
            raise ValidationException(
                f"Discount rate cannot exceed {cls.MAX_DISCOUNT_RATE}%"
            )

    @classmethod
    def calculate_total_discount(
        cls, counter_prices: Dict[str, Dict[str, float]]
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """Calculate total discount from multiple counter prices.

        Args:
            counter_prices: Dictionary of counter names to price info
                           containing 'original_price' and 'price' keys

        Returns:
            Tuple of (total_original, total_discounted, total_discount_amount)
        """
        total_original = Decimal("0")
        total_discounted = Decimal("0")

        for counter_name, price_info in counter_prices.items():
            if "error" in price_info:
                continue

            original = Decimal(str(price_info.get("original_price", 0)))
            discounted = Decimal(str(price_info.get("price", 0)))

            total_original += original
            total_discounted += discounted

        total_discount = total_original - total_discounted

        # Round all values
        return (
            total_original.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_discounted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_discount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        )

    @classmethod
    def validate_counter_name(cls, counter_name: str) -> None:
        """Validate counter name.

        Args:
            counter_name: Counter name to validate

        Raises:
            ValidationException: If counter name is invalid
        """
        if not counter_name or not counter_name.strip():
            raise ValidationException("Counter name cannot be empty")

        # Check for valid characters (alphanumeric, dots, underscores, hyphens)
        if not re.match(r"^[a-zA-Z0-9._\-]+$", counter_name):
            raise ValidationException(f"Invalid counter name format: {counter_name}")

    @classmethod
    def is_default_contract(cls, default_yn: str) -> bool:
        """Check if contract is marked as default.

        Args:
            default_yn: Default flag value ('Y', 'N', 'Yes', 'No', etc.)

        Returns:
            True if default, False otherwise
        """
        return default_yn.upper() in ["Y", "YES", "TRUE", "1"]

    @classmethod
    def format_contract_name(cls, name: Optional[str]) -> str:
        """Format contract name with defaults.

        Args:
            name: Contract name or None

        Returns:
            Formatted contract name
        """
        if not name or not name.strip():
            return "billing group default"
        return name.strip()

    @classmethod
    def calculate_base_fee_impact(cls, base_fee: Decimal, months: int = 12) -> Decimal:
        """Calculate total base fee impact over time.

        Args:
            base_fee: Monthly base fee
            months: Number of months

        Returns:
            Total base fee amount
        """
        total = base_fee * Decimal(str(months))
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def compare_contracts(
        cls, contract1_fees: Dict[str, Decimal], contract2_fees: Dict[str, Decimal]
    ) -> Dict[str, Dict[str, Decimal] | Decimal]:
        """Compare two contracts' fee structures.

        Args:
            contract1_fees: First contract's fees by counter
            contract2_fees: Second contract's fees by counter

        Returns:
            Dictionary with comparison results
        """
        all_counters = set(contract1_fees.keys()) | set(contract2_fees.keys())

        comparison: Dict[str, Dict[str, Decimal] | Decimal] = {}
        total_diff = Decimal("0")

        for counter in all_counters:
            fee1 = contract1_fees.get(counter, Decimal("0"))
            fee2 = contract2_fees.get(counter, Decimal("0"))
            diff = fee2 - fee1

            comparison[counter] = {
                "contract1_fee": fee1,
                "contract2_fee": fee2,
                "difference": diff,
                "percentage_change": (
                    (diff / fee1 * Decimal("100")) if fee1 > 0 else Decimal("0")
                ),
            }
            total_diff += diff

        comparison["total_difference"] = total_diff

        return comparison
