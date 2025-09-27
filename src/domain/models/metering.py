"""Metering and usage domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum


class CounterType(Enum):
    """Types of metering counters."""

    DELTA = "DELTA"  # Accumulative (e.g., hours used)
    GAUGE = "GAUGE"  # Current state (e.g., storage size)
    CUMULATIVE = "CUMULATIVE"  # Running total


@dataclass(frozen=True)
class MeteringData:
    """Individual metering data point."""

    id: str
    app_key: str
    counter_name: str
    counter_type: CounterType
    counter_unit: str
    counter_volume: Decimal
    timestamp: datetime
    resource_id: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate metering data."""
        if self.counter_volume < 0:
            msg = "Counter volume cannot be negative"
            raise ValueError(msg)

    @property
    def is_delta(self) -> bool:
        """Check if this is delta type counter."""
        return self.counter_type == CounterType.DELTA

    @property
    def is_gauge(self) -> bool:
        """Check if this is gauge type counter."""
        return self.counter_type == CounterType.GAUGE


@dataclass
class UsageAggregation:
    """Aggregated usage for a billing period."""

    period_start: datetime
    period_end: datetime
    meters: list[MeteringData] = field(default_factory=list)

    def add_meter(self, meter: MeteringData) -> None:
        """Add a meter reading to the aggregation."""
        # Validate meter is within period
        if not (self.period_start <= meter.timestamp <= self.period_end):
            msg = "Meter timestamp outside of aggregation period"
            raise ValueError(msg)

        self.meters.append(meter)

    def get_usage_by_counter(self, counter_name: str) -> Decimal:
        """Get total usage for a specific counter."""
        matching_meters = [m for m in self.meters if m.counter_name == counter_name]

        if not matching_meters:
            return Decimal(0)

        # Aggregation logic depends on counter type
        first_meter = matching_meters[0]

        if first_meter.is_delta:
            # Sum all delta values
            return Decimal(sum(m.counter_volume for m in matching_meters))
        if first_meter.is_gauge:
            # Use latest gauge value (or average, depending on business rules)
            latest = max(matching_meters, key=lambda m: m.timestamp)
            return latest.counter_volume
        # CUMULATIVE
        # Use maximum value
        return max(m.counter_volume for m in matching_meters)

    def get_usage_by_app(self, app_key: str) -> dict[str, Decimal]:
        """Get usage breakdown by counter for a specific app."""
        app_meters = [m for m in self.meters if m.app_key == app_key]

        usage = {}
        counter_names = {m.counter_name for m in app_meters}

        for counter_name in counter_names:
            usage[counter_name] = self.get_usage_by_counter(counter_name)

        return usage

    @property
    def total_meters(self) -> int:
        """Get total number of meter readings."""
        return len(self.meters)

    @property
    def unique_counters(self) -> set[str]:
        """Get unique counter names."""
        return {m.counter_name for m in self.meters}

    @property
    def unique_apps(self) -> set[str]:
        """Get unique app keys."""
        return {m.app_key for m in self.meters}

    def calculate_cost(self, pricing_rules: dict[str, Decimal]) -> Decimal:
        """Calculate cost based on pricing rules.

        Args:
            pricing_rules: Dict mapping counter_name to price per unit

        Returns:
            Total cost
        """
        total_cost = Decimal(0)

        for counter_name in self.unique_counters:
            if counter_name in pricing_rules:
                usage = self.get_usage_by_counter(counter_name)
                price_per_unit = pricing_rules[counter_name]
                total_cost += usage * price_per_unit

        return total_cost
