"""Metering Aggregator for aggregating metering data by various dimensions."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, List, Optional, Tuple

from .constants import CounterType


@dataclass
class AggregationDimension:
    """Represents aggregation dimensions."""

    app_key: Optional[str] = None
    counter_name: Optional[str] = None
    counter_type: Optional[CounterType] = None
    resource_id: Optional[str] = None
    time_bucket: Optional[str] = None  # hour, day, month

    def to_key(self) -> str:
        """Convert to aggregation key."""
        parts = []
        if self.app_key:
            parts.append(f"app:{self.app_key}")
        if self.counter_name:
            parts.append(f"counter:{self.counter_name}")
        if self.counter_type:
            parts.append(f"type:{self.counter_type}")
        if self.resource_id:
            parts.append(f"resource:{self.resource_id}")
        if self.time_bucket:
            parts.append(f"time:{self.time_bucket}")
        return "|".join(parts)


@dataclass
class AggregatedMetrics:
    """Aggregated metering metrics."""

    total_volume: Decimal
    record_count: int
    min_volume: Decimal
    max_volume: Decimal
    avg_volume: Decimal
    start_time: datetime
    end_time: datetime
    dimensions: AggregationDimension


class MeteringAggregator:
    """Handles metering data aggregation.

    This class encapsulates pure aggregation logic for metering data,
    making it easier to test independently from API interactions.
    """

    # Time bucket formats
    TIME_FORMATS = {
        "hour": "%Y-%m-%d %H:00",
        "day": "%Y-%m-%d",
        "month": "%Y-%m",
        "year": "%Y",
    }

    @classmethod
    def _build_dimension_key(
        cls, record: Dict[str, Any], dimensions: List[str]
    ) -> tuple[str, Dict[str, str]]:
        """Build dimension key and values from record.

        Args:
            record: Metering record
            dimensions: List of dimensions to extract

        Returns:
            Tuple of (dimension_key, dimension_values)
        """
        dim_parts = []
        dim_values = {}

        dimension_mapping = {
            "app_key": ("appKey", "app"),
            "counter_name": ("counterName", "counter"),
            "counter_type": ("counterType", "type"),
            "resource_id": ("resourceId", "resource"),
        }

        for dim in dimensions:
            if dim in dimension_mapping:
                record_key, prefix = dimension_mapping[dim]
                if record_key in record:
                    value = record[record_key]
                    dim_parts.append(f"{prefix}:{value}")
                    dim_values[dim] = value

        return "|".join(dim_parts), dim_values

    @classmethod
    def _calculate_final_metrics(cls, data: Dict[str, Any]) -> AggregatedMetrics:
        """Calculate final aggregated metrics from collected data."""
        volumes = data["volumes"]
        timestamps = data["timestamps"]

        # Default timestamp if none exists
        default_time = datetime.now()

        return AggregatedMetrics(
            total_volume=sum(volumes),
            record_count=len(volumes),
            avg_volume=sum(volumes) / len(volumes) if volumes else Decimal("0"),
            max_volume=max(volumes) if volumes else Decimal("0"),
            min_volume=min(volumes) if volumes else Decimal("0"),
            start_time=min(timestamps) if timestamps else default_time,
            end_time=max(timestamps) if timestamps else default_time,
            dimensions=AggregationDimension(**data["dimension_values"]),
        )

    @classmethod
    def aggregate_by_dimensions(
        cls, metering_data: List[Dict[str, Any]], dimensions: List[str]
    ) -> Dict[str, AggregatedMetrics]:
        """Aggregate metering data by specified dimensions.

        Args:
            metering_data: List of metering records
            dimensions: List of dimensions to group by (app_key, counter_name, etc.)

        Returns:
            Dictionary mapping dimension keys to aggregated metrics
        """
        aggregated: defaultdict[str, Dict[str, Any]] = defaultdict(
            lambda: {"volumes": [], "timestamps": [], "dimension_values": {}}
        )

        for record in metering_data:
            key, dim_values = cls._build_dimension_key(record, dimensions)

            # Add data to aggregation
            volume = Decimal(str(record.get("counterVolume", 0)))
            timestamp = cls._parse_timestamp(record.get("timestamp", ""))

            aggregated[key]["volumes"].append(volume)
            aggregated[key]["timestamps"].append(timestamp)
            aggregated[key]["dimension_values"] = dim_values

        # Calculate final metrics
        results = {}
        for key, data in aggregated.items():
            if data["volumes"]:
                results[key] = cls._calculate_final_metrics(data)

        return results

    @classmethod
    def aggregate_by_time_bucket(
        cls, metering_data: List[Dict[str, Any]], bucket_size: str = "day"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Aggregate metering data by time buckets.

        Args:
            metering_data: List of metering records
            bucket_size: Size of time bucket (hour, day, month, year)

        Returns:
            Dictionary mapping time bucket to records in that bucket
        """
        if bucket_size not in cls.TIME_FORMATS:
            raise ValueError(f"Invalid bucket size: {bucket_size}")

        buckets = defaultdict(list)
        time_format = cls.TIME_FORMATS[bucket_size]

        for record in metering_data:
            timestamp = cls._parse_timestamp(record.get("timestamp", ""))
            bucket_key = timestamp.strftime(time_format)
            buckets[bucket_key].append(record)

        return dict(buckets)

    @classmethod
    def calculate_delta_sum(
        cls, metering_data: List[Dict[str, Any]], counter_name: Optional[str] = None
    ) -> Decimal:
        """Calculate sum of DELTA type counters.

        Args:
            metering_data: List of metering records
            counter_name: Optional counter name to filter by

        Returns:
            Sum of delta counter volumes
        """
        total = Decimal("0")

        for record in metering_data:
            if record.get("counterType") != CounterType.DELTA.value:
                continue

            if counter_name and record.get("counterName") != counter_name:
                continue

            volume = Decimal(str(record.get("counterVolume", 0)))
            total += volume

        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def get_latest_gauge_values(
        cls, metering_data: List[Dict[str, Any]]
    ) -> Dict[str, Decimal]:
        """Get latest GAUGE values for each counter.

        Args:
            metering_data: List of metering records

        Returns:
            Dictionary mapping counter names to latest gauge values
        """
        gauges = {}

        # Sort by timestamp to ensure we get the latest
        sorted_data = sorted(
            metering_data, key=lambda x: cls._parse_timestamp(x.get("timestamp", ""))
        )

        for record in sorted_data:
            if record.get("counterType") != CounterType.GAUGE.value:
                continue

            counter_name = record.get("counterName")
            if counter_name:
                volume = Decimal(str(record.get("counterVolume", 0)))
                gauges[counter_name] = volume.quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )

        return gauges

    @classmethod
    def detect_outliers(
        cls, metering_data: List[Dict[str, Any]], std_dev_threshold: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Detect outlier records based on volume.

        Args:
            metering_data: List of metering records
            std_dev_threshold: Number of standard deviations for outlier detection

        Returns:
            List of outlier records
        """
        if len(metering_data) < 3:
            return []  # Need at least 3 records for meaningful outlier detection

        volumes = [float(record.get("counterVolume", 0)) for record in metering_data]

        # Calculate mean and standard deviation
        mean = sum(volumes) / len(volumes)
        variance = sum((x - mean) ** 2 for x in volumes) / len(volumes)
        std_dev = variance**0.5

        if std_dev == 0:
            return []  # All values are the same

        # Find outliers
        outliers = []
        for i, volume in enumerate(volumes):
            z_score = abs((volume - mean) / std_dev)
            if z_score > std_dev_threshold:
                outliers.append(metering_data[i])

        return outliers

    @classmethod
    def calculate_growth_rate(
        cls,
        previous_data: List[Dict[str, Any]],
        current_data: List[Dict[str, Any]],
        counter_name: str,
    ) -> Tuple[Decimal, Decimal]:
        """Calculate growth rate between two periods.

        Args:
            previous_data: Previous period metering data
            current_data: Current period metering data
            counter_name: Counter name to calculate growth for

        Returns:
            Tuple of (absolute_growth, percentage_growth)
        """
        prev_sum = cls.calculate_delta_sum(previous_data, counter_name)
        curr_sum = cls.calculate_delta_sum(current_data, counter_name)

        absolute_growth = curr_sum - prev_sum

        if prev_sum > 0:
            percentage_growth = (absolute_growth / prev_sum * 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            percentage_growth = Decimal("0.00")

        return absolute_growth, percentage_growth

    @classmethod
    def _parse_timestamp(cls, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime."""
        if not timestamp_str:
            return datetime.now()

        # Try different formats
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str.replace("+09:00", "+0900"), fmt)
            except ValueError:
                continue

        # If all formats fail, return current time
        return datetime.now()

    @classmethod
    def _aggregate_counter_totals(
        cls, metering_data: List[Dict[str, Any]]
    ) -> tuple[defaultdict, set, list]:
        """Aggregate counter totals from metering data.

        Returns:
            Tuple of (counter_totals, resources, timestamps)
        """
        counter_totals: defaultdict[str, Dict[str, Decimal | None]] = defaultdict(
            lambda: {"delta": Decimal("0"), "gauge": None}
        )
        resources = set()
        timestamps = []

        for record in metering_data:
            counter_name = record.get("counterName", "unknown")
            counter_type = record.get("counterType")
            volume = Decimal(str(record.get("counterVolume", 0)))
            resource_id = record.get("resourceId")
            timestamp = cls._parse_timestamp(record.get("timestamp", ""))

            if resource_id:
                resources.add(resource_id)
            timestamps.append(timestamp)

            if counter_type == CounterType.DELTA.value:
                current_delta = counter_totals[counter_name]["delta"]
                if current_delta is not None:
                    counter_totals[counter_name]["delta"] = current_delta + volume
            elif counter_type == CounterType.GAUGE.value:
                counter_totals[counter_name]["gauge"] = volume

        return counter_totals, resources, timestamps

    @classmethod
    def _format_counter_results(cls, counter_totals: defaultdict) -> Dict[str, Any]:
        """Format counter totals into result dictionary."""
        counters = {}
        for name, values in counter_totals.items():
            delta_value = values["delta"]
            counters[name] = {
                "delta_total": float(
                    delta_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    if delta_value is not None
                    else Decimal("0")
                ),
                "latest_gauge": float(values["gauge"]) if values["gauge"] else None,
            }
        return counters

    @classmethod
    def create_usage_summary(
        cls, metering_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a comprehensive usage summary.

        Args:
            metering_data: List of metering records

        Returns:
            Dictionary containing usage summary
        """
        if not metering_data:
            return {
                "total_records": 0,
                "counters": {},
                "resources": [],
                "time_range": None,
            }

        # Aggregate data
        counter_totals, resources, timestamps = cls._aggregate_counter_totals(
            metering_data
        )

        # Format results
        counters = cls._format_counter_results(counter_totals)

        return {
            "total_records": len(metering_data),
            "counters": counters,
            "resources": list(resources),
            "time_range": (
                {
                    "start": min(timestamps).isoformat(),
                    "end": max(timestamps).isoformat(),
                }
                if timestamps
                else None
            ),
        }
