"""Unit tests for MeteringAggregator - pure metering aggregation logic."""

from decimal import Decimal

import pytest

from libs.constants import CounterType
from libs.metering_aggregator import AggregationDimension, MeteringAggregator


class TestMeteringAggregator:
    """Unit tests for metering aggregation logic."""

    def test_aggregation_dimension_to_key(self):
        """Test aggregation dimension key generation."""
        # Full dimension
        dim = AggregationDimension(
            app_key="app-123",
            counter_name="cpu.usage",
            counter_type=CounterType.DELTA,
            resource_id="vm-001",
            time_bucket="2024-01",
        )
        assert (
            dim.to_key()
            == "app:app-123|counter:cpu.usage|type:DELTA|resource:vm-001|time:2024-01"
        )

        # Partial dimension
        dim = AggregationDimension(app_key="app-123", counter_name="cpu.usage")
        assert dim.to_key() == "app:app-123|counter:cpu.usage"

        # Empty dimension
        dim = AggregationDimension()
        assert dim.to_key() == ""

    def test_aggregate_by_dimensions_single(self):
        """Test aggregation by single dimension."""
        metering_data = [
            {
                "appKey": "app-123",
                "counterName": "cpu.usage",
                "counterType": "DELTA",
                "counterVolume": "10.5",
                "timestamp": "2024-01-01T10:00:00+09:00",
                "resourceId": "vm-001",
            },
            {
                "appKey": "app-123",
                "counterName": "cpu.usage",
                "counterType": "DELTA",
                "counterVolume": "20.5",
                "timestamp": "2024-01-01T11:00:00+09:00",
                "resourceId": "vm-001",
            },
            {
                "appKey": "app-456",
                "counterName": "cpu.usage",
                "counterType": "DELTA",
                "counterVolume": "15.0",
                "timestamp": "2024-01-01T10:00:00+09:00",
                "resourceId": "vm-002",
            },
        ]

        # Aggregate by app_key
        results = MeteringAggregator.aggregate_by_dimensions(metering_data, ["app_key"])

        assert len(results) == 2
        assert "app:app-123" in results
        assert "app:app-456" in results

        # Check app-123 aggregation
        app123 = results["app:app-123"]
        assert app123.total_volume == Decimal("31.0")
        assert app123.record_count == 2
        assert app123.min_volume == Decimal("10.5")
        assert app123.max_volume == Decimal("20.5")
        assert app123.avg_volume == Decimal("15.5")

    def test_aggregate_by_dimensions_multiple(self):
        """Test aggregation by multiple dimensions."""
        metering_data = [
            {
                "appKey": "app-123",
                "counterName": "cpu.usage",
                "counterType": "DELTA",
                "counterVolume": "10",
                "timestamp": "2024-01-01T10:00:00+09:00",
                "resourceId": "vm-001",
            },
            {
                "appKey": "app-123",
                "counterName": "cpu.usage",
                "counterType": "DELTA",
                "counterVolume": "20",
                "timestamp": "2024-01-01T11:00:00+09:00",
                "resourceId": "vm-001",
            },
            {
                "appKey": "app-123",
                "counterName": "memory.usage",
                "counterType": "GAUGE",
                "counterVolume": "1000",
                "timestamp": "2024-01-01T10:00:00+09:00",
                "resourceId": "vm-001",
            },
        ]

        # Aggregate by app_key and counter_name
        results = MeteringAggregator.aggregate_by_dimensions(
            metering_data, ["app_key", "counter_name"]
        )

        assert len(results) == 2
        assert "app:app-123|counter:cpu.usage" in results
        assert "app:app-123|counter:memory.usage" in results

    def test_aggregate_by_time_bucket(self):
        """Test aggregation by time buckets."""
        metering_data = [
            {
                "counterName": "cpu.usage",
                "counterVolume": "10",
                "timestamp": "2024-01-01T10:30:00+09:00",
            },
            {
                "counterName": "cpu.usage",
                "counterVolume": "20",
                "timestamp": "2024-01-01T10:45:00+09:00",
            },
            {
                "counterName": "cpu.usage",
                "counterVolume": "15",
                "timestamp": "2024-01-01T11:15:00+09:00",
            },
            {
                "counterName": "cpu.usage",
                "counterVolume": "25",
                "timestamp": "2024-01-02T10:00:00+09:00",
            },
        ]

        # Hour buckets
        hour_buckets = MeteringAggregator.aggregate_by_time_bucket(
            metering_data, "hour"
        )
        assert len(hour_buckets) == 3
        assert "2024-01-01 10:00" in hour_buckets
        assert len(hour_buckets["2024-01-01 10:00"]) == 2

        # Day buckets
        day_buckets = MeteringAggregator.aggregate_by_time_bucket(metering_data, "day")
        assert len(day_buckets) == 2
        assert "2024-01-01" in day_buckets
        assert len(day_buckets["2024-01-01"]) == 3

        # Month buckets
        month_buckets = MeteringAggregator.aggregate_by_time_bucket(
            metering_data, "month"
        )
        assert len(month_buckets) == 1
        assert "2024-01" in month_buckets
        assert len(month_buckets["2024-01"]) == 4

    def test_aggregate_by_time_bucket_invalid(self):
        """Test aggregation with invalid time bucket."""
        with pytest.raises(ValueError, match="Invalid bucket size"):
            MeteringAggregator.aggregate_by_time_bucket([], "invalid")

    def test_calculate_delta_sum(self):
        """Test DELTA counter sum calculation."""
        metering_data = [
            {
                "counterName": "cpu.usage",
                "counterType": "DELTA",
                "counterVolume": "10.5",
            },
            {
                "counterName": "cpu.usage",
                "counterType": "DELTA",
                "counterVolume": "20.5",
            },
            {
                "counterName": "cpu.usage",
                "counterType": "GAUGE",  # Should be ignored
                "counterVolume": "100",
            },
            {
                "counterName": "memory.usage",
                "counterType": "DELTA",
                "counterVolume": "50",
            },
        ]

        # All DELTA counters
        total = MeteringAggregator.calculate_delta_sum(metering_data)
        assert total == Decimal("81.00")  # 10.5 + 20.5 + 50

        # Specific counter
        cpu_total = MeteringAggregator.calculate_delta_sum(metering_data, "cpu.usage")
        assert cpu_total == Decimal("31.00")  # 10.5 + 20.5

    def test_get_latest_gauge_values(self):
        """Test getting latest GAUGE values."""
        metering_data = [
            {
                "counterName": "memory.usage",
                "counterType": "GAUGE",
                "counterVolume": "1000",
                "timestamp": "2024-01-01T10:00:00+09:00",
            },
            {
                "counterName": "memory.usage",
                "counterType": "GAUGE",
                "counterVolume": "1500",
                "timestamp": "2024-01-01T11:00:00+09:00",
            },
            {
                "counterName": "memory.usage",
                "counterType": "GAUGE",
                "counterVolume": "1200",
                "timestamp": "2024-01-01T10:30:00+09:00",
            },
            {
                "counterName": "disk.usage",
                "counterType": "GAUGE",
                "counterVolume": "5000",
                "timestamp": "2024-01-01T10:00:00+09:00",
            },
        ]

        gauges = MeteringAggregator.get_latest_gauge_values(metering_data)

        assert len(gauges) == 2
        assert gauges["memory.usage"] == Decimal("1500.00")  # Latest value
        assert gauges["disk.usage"] == Decimal("5000.00")

    def test_detect_outliers(self):
        """Test outlier detection."""
        # Normal data with clear outliers
        metering_data = [
            {"counterVolume": "10"},
            {"counterVolume": "11"},
            {"counterVolume": "9"},
            {"counterVolume": "10"},
            {"counterVolume": "11"},
            {"counterVolume": "10"},
            {"counterVolume": "9"},
            {"counterVolume": "1000"},  # Clear outlier
        ]

        outliers = MeteringAggregator.detect_outliers(
            metering_data, std_dev_threshold=2.0
        )

        assert len(outliers) >= 1
        assert any(float(o["counterVolume"]) == 1000 for o in outliers)

    def test_detect_outliers_edge_cases(self):
        """Test outlier detection edge cases."""
        # Too few records
        assert MeteringAggregator.detect_outliers([{"counterVolume": "10"}]) == []

        # All same values
        same_data = [{"counterVolume": "10"} for _ in range(10)]
        assert MeteringAggregator.detect_outliers(same_data) == []

    def test_calculate_growth_rate(self):
        """Test growth rate calculation."""
        previous_data = [
            {
                "counterName": "cpu.usage",
                "counterType": "DELTA",
                "counterVolume": "100",
            },
            {"counterName": "cpu.usage", "counterType": "DELTA", "counterVolume": "50"},
        ]

        current_data = [
            {
                "counterName": "cpu.usage",
                "counterType": "DELTA",
                "counterVolume": "120",
            },
            {"counterName": "cpu.usage", "counterType": "DELTA", "counterVolume": "80"},
        ]

        absolute_growth, percentage_growth = MeteringAggregator.calculate_growth_rate(
            previous_data, current_data, "cpu.usage"
        )

        # Previous: 150, Current: 200
        assert absolute_growth == Decimal("50.00")
        assert percentage_growth == Decimal("33.33")  # 50/150 * 100

    def test_calculate_growth_rate_zero_base(self):
        """Test growth rate calculation with zero base."""
        previous_data = []
        current_data = [
            {"counterName": "cpu.usage", "counterType": "DELTA", "counterVolume": "100"}
        ]

        absolute_growth, percentage_growth = MeteringAggregator.calculate_growth_rate(
            previous_data, current_data, "cpu.usage"
        )

        assert absolute_growth == Decimal("100.00")
        assert percentage_growth == Decimal(
            "0.00"
        )  # Can't calculate percentage from zero

    def test_create_usage_summary(self):
        """Test comprehensive usage summary creation."""
        metering_data = [
            {
                "counterName": "cpu.usage",
                "counterType": "DELTA",
                "counterVolume": "10",
                "resourceId": "vm-001",
                "timestamp": "2024-01-01T10:00:00+09:00",
            },
            {
                "counterName": "cpu.usage",
                "counterType": "DELTA",
                "counterVolume": "20",
                "resourceId": "vm-001",
                "timestamp": "2024-01-01T11:00:00+09:00",
            },
            {
                "counterName": "memory.usage",
                "counterType": "GAUGE",
                "counterVolume": "1500",
                "resourceId": "vm-002",
                "timestamp": "2024-01-01T11:00:00+09:00",
            },
        ]

        summary = MeteringAggregator.create_usage_summary(metering_data)

        assert summary["total_records"] == 3
        assert len(summary["resources"]) == 2
        assert "vm-001" in summary["resources"]
        assert "vm-002" in summary["resources"]

        assert "cpu.usage" in summary["counters"]
        assert summary["counters"]["cpu.usage"]["delta_total"] == 30.0
        assert summary["counters"]["cpu.usage"]["latest_gauge"] is None

        assert "memory.usage" in summary["counters"]
        assert summary["counters"]["memory.usage"]["delta_total"] == 0.0
        assert summary["counters"]["memory.usage"]["latest_gauge"] == 1500.0

        assert summary["time_range"] is not None
        assert "start" in summary["time_range"]
        assert "end" in summary["time_range"]

    def test_create_usage_summary_empty(self):
        """Test usage summary with empty data."""
        summary = MeteringAggregator.create_usage_summary([])

        assert summary["total_records"] == 0
        assert summary["counters"] == {}
        assert summary["resources"] == []
        assert summary["time_range"] is None
