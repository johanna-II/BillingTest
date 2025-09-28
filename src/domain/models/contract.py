"""Contract and pricing domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class PricingTier:
    """Represents a pricing tier for volume-based pricing."""

    min_volume: Decimal
    max_volume: Decimal | None  # None means unlimited
    price_per_unit: Decimal
    tier_name: str = ""

    def __post_init__(self) -> None:
        """Validate pricing tier."""
        if self.min_volume < 0:
            msg = "Min volume cannot be negative"
            raise ValueError(msg)
        if self.max_volume is not None and self.max_volume <= self.min_volume:
            msg = "Max volume must be greater than min volume"
            raise ValueError(msg)
        if self.price_per_unit < 0:
            msg = "Price cannot be negative"
            raise ValueError(msg)

    def contains_volume(self, volume: Decimal) -> bool:
        """Check if volume falls within this tier."""
        if volume < self.min_volume:
            return False
        if self.max_volume is None:
            return True
        return volume <= self.max_volume

    def calculate_cost(self, volume: Decimal) -> Decimal:
        """Calculate cost for volume within this tier."""
        if not self.contains_volume(volume):
            msg = f"Volume {volume} not in tier range"
            raise ValueError(msg)

        return volume * self.price_per_unit


@dataclass
class Contract:
    """Represents a pricing contract."""

    id: str
    name: str
    billing_group_id: str
    start_date: datetime
    end_date: datetime | None = None
    pricing_rules: dict[str, list[PricingTier]] = field(default_factory=dict)
    discount_rate: Decimal = Decimal(0)
    minimum_charge: Decimal = Decimal(0)

    def __post_init__(self) -> None:
        """Validate contract."""
        if self.end_date and self.end_date <= self.start_date:
            msg = "End date must be after start date"
            raise ValueError(msg)
        if self.discount_rate < 0 or self.discount_rate > 100:
            msg = "Discount rate must be between 0 and 100"
            raise ValueError(msg)
        if self.minimum_charge < 0:
            msg = "Minimum charge cannot be negative"
            raise ValueError(msg)

    @property
    def is_active(self) -> bool:
        """Check if contract is currently active."""
        now = datetime.now()
        if now < self.start_date:
            return False
        return not (self.end_date and now > self.end_date)

    def add_pricing_tier(self, counter_name: str, tier: PricingTier) -> None:
        """Add a pricing tier for a counter."""
        if counter_name not in self.pricing_rules:
            self.pricing_rules[counter_name] = []

        # Validate no overlap with existing tiers
        for existing_tier in self.pricing_rules[counter_name]:
            if self._tiers_overlap(tier, existing_tier):
                msg = f"Tier overlaps with existing tier for {counter_name}"
                raise ValueError(msg)

        self.pricing_rules[counter_name].append(tier)
        # Sort tiers by min_volume
        self.pricing_rules[counter_name].sort(key=lambda t: t.min_volume)

    def _tiers_overlap(self, tier1: PricingTier, tier2: PricingTier) -> bool:
        """Check if two pricing tiers overlap."""
        # If either has no max, check if min is in range
        if tier1.max_volume is None:
            return tier2.min_volume >= tier1.min_volume
        if tier2.max_volume is None:
            return tier1.min_volume >= tier2.min_volume

        # Check for overlap
        return not (tier1.max_volume <= tier2.min_volume or tier2.max_volume <= tier1.min_volume)

    def calculate_cost(self, counter_name: str, volume: Decimal) -> Decimal:
        """Calculate cost for a counter based on tiered pricing."""
        if counter_name not in self.pricing_rules:
            msg = f"No pricing rules for counter: {counter_name}"
            raise ValueError(msg)

        tiers = self.pricing_rules[counter_name]
        total_cost = Decimal(0)
        remaining_volume = volume

        for tier in tiers:
            if remaining_volume <= 0:
                break

            # Calculate volume in this tier
            if tier.max_volume is None:
                tier_volume = remaining_volume
            else:
                tier_max = tier.max_volume - tier.min_volume
                tier_volume = min(remaining_volume, tier_max)

            # Add cost for this tier
            total_cost += tier_volume * tier.price_per_unit
            remaining_volume -= tier_volume

        # Apply contract discount
        if self.discount_rate > 0:
            discount = total_cost * (self.discount_rate / 100)
            total_cost -= discount

        # Apply minimum charge
        return max(total_cost, self.minimum_charge)
