"""Metering Calculator for billing calculations and usage aggregation."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple

from .constants import CounterType


@dataclass
class MeteringRecord:
    """Represents a single metering record."""

    app_key: str
    counter_name: str
    counter_type: CounterType
    counter_unit: str
    counter_volume: float
    timestamp: datetime
    resource_id: str
    resource_name: str


@dataclass
class UsageSummary:
    """Summary of usage for a resource."""

    total_volume: float
    unit: str
    start_time: datetime
    end_time: datetime
    record_count: int


class MeteringCalculator:
    """Handles metering calculations and aggregations.

    This class encapsulates pure calculation logic for metering data,
    making it easier to test independently from API interactions.
    """

    # Common unit conversions
    UNIT_MULTIPLIERS = {
        "KB": 1,
        "MB": 1024,
        "GB": 1024 * 1024,
        "TB": 1024 * 1024 * 1024,
        "SECONDS": 1,
        "MINUTES": 60,
        "HOURS": 3600,
        "DAYS": 86400,
    }

    # Pricing per unit (example rates)
    DEFAULT_RATES = {
        "compute.instance.small": 0.10,  # per hour
        "compute.instance.medium": 0.25,  # per hour
        "compute.instance.large": 0.50,  # per hour
        "storage.block": 0.0001,  # per GB per hour
        "network.bandwidth": 0.01,  # per GB
    }

    @classmethod
    def parse_volume(cls, volume_str: str) -> float:
        """Parse volume string to float, handling various formats.

        Args:
            volume_str: Volume as string (e.g., "100", "1.5", "1e3")

        Returns:
            Volume as float

        Raises:
            ValueError: If volume cannot be parsed
        """
        try:
            return float(volume_str)
        except ValueError as e:
            raise ValueError(f"Invalid volume format: {volume_str}") from e

    @classmethod
    def convert_units(cls, value: float, from_unit: str, to_unit: str) -> float:
        """Convert between units.

        Args:
            value: Value to convert
            from_unit: Source unit
            to_unit: Target unit

        Returns:
            Converted value

        Raises:
            ValueError: If conversion is not possible
        """
        if from_unit == to_unit:
            return value

        # Get multipliers
        from_multiplier = cls.UNIT_MULTIPLIERS.get(from_unit.upper())
        to_multiplier = cls.UNIT_MULTIPLIERS.get(to_unit.upper())

        if from_multiplier is None or to_multiplier is None:
            raise ValueError(f"Cannot convert from {from_unit} to {to_unit}")

        # Check if units are compatible (same category)
        from_category = cls._get_unit_category(from_unit)
        to_category = cls._get_unit_category(to_unit)

        if from_category != to_category:
            raise ValueError(f"Incompatible units: {from_unit} and {to_unit}")

        # Convert through base unit
        base_value = value * from_multiplier
        return base_value / to_multiplier

    @classmethod
    def _get_unit_category(cls, unit: str) -> str:
        """Get category of unit (storage, time, etc)."""
        unit_upper = unit.upper()
        if unit_upper in ["KB", "MB", "GB", "TB"]:
            return "storage"
        elif unit_upper in ["SECONDS", "MINUTES", "HOURS", "DAYS"]:
            return "time"
        else:
            return "other"

    @classmethod
    def aggregate_usage(cls, records: List[MeteringRecord]) -> Dict[str, UsageSummary]:
        """Aggregate usage records by counter name.

        Args:
            records: List of metering records

        Returns:
            Dictionary mapping counter names to usage summaries
        """
        aggregates: Dict[str, List[MeteringRecord]] = {}

        # Group by counter name
        for record in records:
            key = record.counter_name
            if key not in aggregates:
                aggregates[key] = []
            aggregates[key].append(record)

        # Create summaries
        summaries = {}
        for counter_name, counter_records in aggregates.items():
            if not counter_records:
                continue

            # Calculate totals based on counter type
            first_record = counter_records[0]
            if first_record.counter_type == CounterType.DELTA:
                # Sum all delta values
                total_volume = sum(r.counter_volume for r in counter_records)
            else:  # GAUGE
                # For gauge, take the average or latest value
                total_volume = counter_records[-1].counter_volume

            # Find time range
            timestamps = [r.timestamp for r in counter_records]
            start_time = min(timestamps)
            end_time = max(timestamps)

            summaries[counter_name] = UsageSummary(
                total_volume=total_volume,
                unit=first_record.counter_unit,
                start_time=start_time,
                end_time=end_time,
                record_count=len(counter_records),
            )

        return summaries

    @classmethod
    def calculate_cost(
        cls,
        counter_name: str,
        volume: float,
        unit: str,
        rates: Dict[str, float] | None = None,
    ) -> float:
        """Calculate cost for usage.

        Args:
            counter_name: Name of the counter
            volume: Usage volume
            unit: Unit of measurement
            rates: Optional custom rates (uses defaults if not provided)

        Returns:
            Calculated cost
        """
        if rates is None:
            rates = cls.DEFAULT_RATES

        rate = rates.get(counter_name, 0.0)

        # Adjust for unit if needed
        # For example, if rate is per hour but usage is in minutes
        if counter_name.startswith("compute.") and unit == "MINUTES":
            volume = cls.convert_units(volume, "MINUTES", "HOURS")

        return volume * rate

    @classmethod
    def calculate_monthly_projection(
        cls, daily_usage: float, days_elapsed: int, days_in_month: int = 30
    ) -> float:
        """Project monthly usage based on current daily average.

        Args:
            daily_usage: Average daily usage so far
            days_elapsed: Number of days elapsed in month
            days_in_month: Total days in month

        Returns:
            Projected total monthly usage
        """
        if days_elapsed <= 0:
            return 0.0

        # Calculate average daily rate
        avg_daily_rate = daily_usage / days_elapsed

        # Project for full month
        return avg_daily_rate * days_in_month

    @classmethod
    def detect_usage_anomalies(
        cls,
        current_usage: float,
        historical_average: float,
        threshold_percentage: float = 50.0,
    ) -> Tuple[bool, float]:
        """Detect if current usage is anomalous compared to historical average.

        Args:
            current_usage: Current usage value
            historical_average: Historical average usage
            threshold_percentage: Percentage threshold for anomaly detection

        Returns:
            Tuple of (is_anomaly, deviation_percentage)
        """
        if historical_average == 0:
            # Can't calculate deviation
            return current_usage > 0, float("inf") if current_usage > 0 else 0.0

        # Calculate percentage deviation
        deviation = abs(current_usage - historical_average) / historical_average * 100

        # Check if exceeds threshold
        is_anomaly = deviation > threshold_percentage

        return is_anomaly, deviation

    @classmethod
    def format_volume_human_readable(cls, volume: float, unit: str) -> str:
        """Format volume in human-readable format.

        Args:
            volume: Volume value
            unit: Unit of measurement

        Returns:
            Human-readable string
        """
        # For storage units, convert to appropriate scale
        if unit.upper() in ["KB", "MB", "GB", "TB"]:
            if volume >= 1024 * 1024 * 1024:  # TB
                return f"{volume / (1024 * 1024 * 1024):.2f} TB"
            elif volume >= 1024 * 1024:  # GB
                return f"{volume / (1024 * 1024):.2f} GB"
            elif volume >= 1024:  # MB
                return f"{volume / 1024:.2f} MB"
            else:
                return f"{volume:.2f} KB"

        # For time units
        elif unit.upper() in ["SECONDS", "MINUTES", "HOURS", "DAYS"]:
            if unit.upper() == "SECONDS":
                if volume >= 86400:
                    return f"{volume / 86400:.2f} days"
                elif volume >= 3600:
                    return f"{volume / 3600:.2f} hours"
                elif volume >= 60:
                    return f"{volume / 60:.2f} minutes"
                else:
                    return f"{volume:.2f} seconds"
            elif unit.upper() == "HOURS":
                if volume >= 24:
                    return f"{volume / 24:.2f} days"
                else:
                    return f"{volume:.2f} hours"

        # Default formatting
        return f"{volume:.2f} {unit}"
