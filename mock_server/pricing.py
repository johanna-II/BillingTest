"""Pricing calculation module.

Centralized pricing logic for all billing calculations.
Follows DRY and Single Responsibility principles.
"""

from __future__ import annotations

# ============================================================================
# Constants - Pricing Rules
# ============================================================================

# Unit prices (price per unit)
UNIT_PRICES = {
    "compute.c2.c8m8": 397,  # 397원/시간
    "compute.g2.t4.c8m64": 166.67,  # 166.67원/시간
    "storage.volume.ssd": 100,  # 100원/GB/월 (volume already in GB)
    "network.floating_ip": 25,  # 25원/시간
}

DEFAULT_UNIT_PRICE = 100

# VAT rate
VAT_RATE = 0.1

# Contract discount rates
CONTRACT_DEFAULT_DISCOUNT_RATE = 0.3
CONTRACT_HIGHER_DISCOUNT_RATE = 0.4

# ============================================================================
# Pricing Functions
# ============================================================================


def get_unit_price(counter_name: str) -> float:
    """Get unit price for a counter.

    Args:
        counter_name: Counter name (e.g., 'compute.c2.c8m8')

    Returns:
        Unit price in KRW
    """
    return UNIT_PRICES.get(counter_name, DEFAULT_UNIT_PRICE)


def calculate_amount(counter_name: str, volume: float) -> int:
    """Calculate billing amount for a counter.

    Args:
        counter_name: Counter name
        volume: Usage volume (in appropriate units)
            - Compute: hours
            - Storage: GB (already converted)
            - Network: hours

    Returns:
        Calculated amount in KRW (rounded to nearest won)
    """
    unit_price = get_unit_price(counter_name)

    # All counters: direct multiplication
    # Storage volume is already in GB units
    # Use round() for proper rounding instead of truncation
    return int(round(volume * unit_price))


def calculate_vat(charge: int) -> int:
    """Calculate VAT (10%) on charge amount.

    Args:
        charge: Charge amount before VAT

    Returns:
        VAT amount (rounded to nearest won)
    """
    rounded_vat = round(charge * VAT_RATE)
    return int(rounded_vat)


def calculate_total_with_vat(charge: int) -> int:
    """Calculate total amount including VAT.

    Args:
        charge: Charge amount before VAT

    Returns:
        Total amount (charge + VAT)
    """
    vat = calculate_vat(charge)
    return charge + vat


def calculate_contract_discount(
    subtotal: int, has_contract: bool, discount_rate: float
) -> int:
    """Calculate contract discount amount.

    Args:
        subtotal: Subtotal before discount
        has_contract: Whether customer has contract
        discount_rate: Discount rate (e.g., 0.3 for 30%)

    Returns:
        Discount amount in KRW (rounded to nearest won)
    """
    if not has_contract:
        return 0

    return int(round(subtotal * discount_rate))


def calculate_compute_amount_with_contract(
    volume: float, _contract_discount_rate: float
) -> int:
    """Calculate compute amount using standard pricing formula.

    NOTE: This is a mock server function. Contract discounts are applied
    at the billing calculation level, not at the counter level.

    Args:
        volume: Usage volume in hours
        _contract_discount_rate: Unused in mock (discount applied elsewhere)

    Returns:
        Calculated compute amount using standard pricing (rounded to nearest won)
    """
    # Standard compute pricing formula
    # Contract discounts are applied later in the billing calculation
    # Use round() for proper rounding instead of truncation
    return int(round(volume * UNIT_PRICES["compute.c2.c8m8"]))
