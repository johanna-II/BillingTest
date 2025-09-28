"""Unit tests for MeteringCalculator - pure calculation logic."""

from datetime import datetime

import pytest
from pytest import approx

from libs.constants import CounterType
from libs.metering_calculator import MeteringCalculator, MeteringRecord


class TestMeteringCalculator:
    """Unit tests for metering calculation logic."""

    def test_parse_volume_valid(self):
        """Test parsing valid volume strings."""
        assert MeteringCalculator.parse_volume("100") == approx(100.0)
        assert MeteringCalculator.parse_volume("100.5") == approx(100.5)
        assert MeteringCalculator.parse_volume("0") == approx(0.0)
        assert MeteringCalculator.parse_volume("1e3") == approx(1000.0)
        assert MeteringCalculator.parse_volume("1.5e2") == approx(150.0)
        assert MeteringCalculator.parse_volume("-50") == approx(-50.0)

    def test_parse_volume_invalid(self):
        """Test parsing invalid volume strings."""
        with pytest.raises(ValueError, match="Invalid volume format"):
            MeteringCalculator.parse_volume("abc")

        with pytest.raises(ValueError, match="Invalid volume format"):
            MeteringCalculator.parse_volume("")

        with pytest.raises(ValueError, match="Invalid volume format"):
            MeteringCalculator.parse_volume("10.5.5")

    def test_convert_units_storage(self):
        """Test unit conversion for storage units."""
        # KB to MB
        assert MeteringCalculator.convert_units(1024, "KB", "MB") == approx(1.0)

        # MB to GB
        assert MeteringCalculator.convert_units(1024, "MB", "GB") == approx(1.0)

        # GB to TB
        assert MeteringCalculator.convert_units(1024, "GB", "TB") == approx(1.0)

        # KB to GB
        assert MeteringCalculator.convert_units(1048576, "KB", "GB") == approx(1.0)

        # TB to KB
        assert MeteringCalculator.convert_units(1, "TB", "KB") == 1024 * 1024 * 1024

    def test_convert_units_time(self):
        """Test unit conversion for time units."""
        # Seconds to Minutes
        assert MeteringCalculator.convert_units(60, "SECONDS", "MINUTES") == approx(1.0)

        # Minutes to Hours
        assert MeteringCalculator.convert_units(60, "MINUTES", "HOURS") == approx(1.0)

        # Hours to Days
        assert MeteringCalculator.convert_units(24, "HOURS", "DAYS") == approx(1.0)

        # Seconds to Hours
        assert MeteringCalculator.convert_units(3600, "SECONDS", "HOURS") == approx(1.0)

    def test_convert_units_same_unit(self):
        """Test conversion when units are the same."""
        assert MeteringCalculator.convert_units(100, "KB", "KB") == 100
        assert MeteringCalculator.convert_units(50, "HOURS", "HOURS") == 50

    def test_convert_units_incompatible(self):
        """Test conversion between incompatible units."""
        with pytest.raises(ValueError, match="Incompatible units"):
            MeteringCalculator.convert_units(100, "KB", "HOURS")

        with pytest.raises(ValueError, match="Incompatible units"):
            MeteringCalculator.convert_units(100, "MINUTES", "GB")

    def test_convert_units_unknown(self):
        """Test conversion with unknown units."""
        with pytest.raises(ValueError, match="Cannot convert"):
            MeteringCalculator.convert_units(100, "UNKNOWN", "KB")

        with pytest.raises(ValueError, match="Cannot convert"):
            MeteringCalculator.convert_units(100, "KB", "UNKNOWN")

    def test_aggregate_usage_delta(self):
        """Test aggregating DELTA type usage records."""
        records = [
            MeteringRecord(
                app_key="app-1",
                counter_name="compute.instance",
                counter_type=CounterType.DELTA,
                counter_unit="HOURS",
                counter_volume=10.0,
                timestamp=datetime(2024, 1, 1, 10, 0),
                resource_id="vm-1",
                resource_name="VM 1",
            ),
            MeteringRecord(
                app_key="app-1",
                counter_name="compute.instance",
                counter_type=CounterType.DELTA,
                counter_unit="HOURS",
                counter_volume=20.0,
                timestamp=datetime(2024, 1, 1, 11, 0),
                resource_id="vm-1",
                resource_name="VM 1",
            ),
            MeteringRecord(
                app_key="app-1",
                counter_name="compute.instance",
                counter_type=CounterType.DELTA,
                counter_unit="HOURS",
                counter_volume=15.0,
                timestamp=datetime(2024, 1, 1, 12, 0),
                resource_id="vm-1",
                resource_name="VM 1",
            ),
        ]

        summaries = MeteringCalculator.aggregate_usage(records)

        assert "compute.instance" in summaries
        summary = summaries["compute.instance"]
        assert summary.total_volume == approx(45.0)  # 10 + 20 + 15
        assert summary.unit == "HOURS"
        assert summary.record_count == 3
        assert summary.start_time == datetime(2024, 1, 1, 10, 0)
        assert summary.end_time == datetime(2024, 1, 1, 12, 0)

    def test_aggregate_usage_gauge(self):
        """Test aggregating GAUGE type usage records."""
        records = [
            MeteringRecord(
                app_key="app-1",
                counter_name="storage.used",
                counter_type=CounterType.GAUGE,
                counter_unit="GB",
                counter_volume=100.0,
                timestamp=datetime(2024, 1, 1, 10, 0),
                resource_id="disk-1",
                resource_name="Disk 1",
            ),
            MeteringRecord(
                app_key="app-1",
                counter_name="storage.used",
                counter_type=CounterType.GAUGE,
                counter_unit="GB",
                counter_volume=150.0,
                timestamp=datetime(2024, 1, 1, 11, 0),
                resource_id="disk-1",
                resource_name="Disk 1",
            ),
            MeteringRecord(
                app_key="app-1",
                counter_name="storage.used",
                counter_type=CounterType.GAUGE,
                counter_unit="GB",
                counter_volume=200.0,
                timestamp=datetime(2024, 1, 1, 12, 0),
                resource_id="disk-1",
                resource_name="Disk 1",
            ),
        ]

        summaries = MeteringCalculator.aggregate_usage(records)

        assert "storage.used" in summaries
        summary = summaries["storage.used"]
        assert summary.total_volume == approx(200.0)  # Latest value for GAUGE
        assert summary.unit == "GB"
        assert summary.record_count == 3

    def test_calculate_cost_default_rates(self):
        """Test cost calculation with default rates."""
        # Compute instance
        cost = MeteringCalculator.calculate_cost("compute.instance.small", 24, "HOURS")
        assert cost == approx(24 * 0.10)  # 2.4

        # Storage
        cost = MeteringCalculator.calculate_cost("storage.block", 1000, "GB")
        assert cost == approx(1000 * 0.0001)  # 0.1

        # Network
        cost = MeteringCalculator.calculate_cost("network.bandwidth", 100, "GB")
        assert cost == approx(100 * 0.01)  # 1.0

    def test_calculate_cost_custom_rates(self):
        """Test cost calculation with custom rates."""
        custom_rates = {"compute.special": 1.5, "storage.premium": 0.001}

        cost = MeteringCalculator.calculate_cost(
            "compute.special", 10, "HOURS", rates=custom_rates
        )
        assert cost == approx(10 * 1.5)  # 15.0

        cost = MeteringCalculator.calculate_cost(
            "storage.premium", 500, "GB", rates=custom_rates
        )
        assert cost == approx(500 * 0.001)  # 0.5

    def test_calculate_cost_unit_conversion(self):
        """Test cost calculation with unit conversion."""
        # Rate is per hour, but usage is in minutes
        cost = MeteringCalculator.calculate_cost(
            "compute.instance.small", 120, "MINUTES"
        )
        assert cost == approx(2 * 0.10)  # 120 minutes = 2 hours

    def test_calculate_monthly_projection(self):
        """Test monthly usage projection."""
        # 10 days elapsed, 100 units used
        projection = MeteringCalculator.calculate_monthly_projection(
            daily_usage=100, days_elapsed=10, days_in_month=30
        )
        assert projection == 300  # 10 units/day * 30 days

        # 15 days elapsed, 450 units used
        projection = MeteringCalculator.calculate_monthly_projection(
            daily_usage=450, days_elapsed=15, days_in_month=31
        )
        assert projection == 930  # 30 units/day * 31 days

        # No days elapsed
        projection = MeteringCalculator.calculate_monthly_projection(
            daily_usage=0, days_elapsed=0
        )
        assert projection == 0

    def test_detect_usage_anomalies(self):
        """Test usage anomaly detection."""
        # Normal usage (within threshold)
        is_anomaly, deviation = MeteringCalculator.detect_usage_anomalies(
            current_usage=110, historical_average=100, threshold_percentage=50
        )
        assert not is_anomaly
        assert deviation == approx(10.0)

        # High anomaly (above threshold)
        is_anomaly, deviation = MeteringCalculator.detect_usage_anomalies(
            current_usage=200, historical_average=100, threshold_percentage=50
        )
        assert is_anomaly
        assert deviation == approx(100.0)

        # Low anomaly (below threshold)
        is_anomaly, deviation = MeteringCalculator.detect_usage_anomalies(
            current_usage=25, historical_average=100, threshold_percentage=50
        )
        assert is_anomaly
        assert deviation == approx(75.0)

        # Zero historical average
        is_anomaly, deviation = MeteringCalculator.detect_usage_anomalies(
            current_usage=100, historical_average=0
        )
        assert is_anomaly
        assert deviation == float("inf")

    def test_format_volume_human_readable_storage(self):
        """Test human-readable formatting for storage units."""
        assert MeteringCalculator.format_volume_human_readable(512, "KB") == "512.00 KB"
        assert MeteringCalculator.format_volume_human_readable(2048, "KB") == "2.00 MB"
        assert (
            MeteringCalculator.format_volume_human_readable(1048576, "KB") == "1.00 GB"
        )
        assert (
            MeteringCalculator.format_volume_human_readable(1073741824, "KB")
            == "1.00 TB"
        )

    def test_format_volume_human_readable_time(self):
        """Test human-readable formatting for time units."""
        assert (
            MeteringCalculator.format_volume_human_readable(30, "SECONDS")
            == "30.00 seconds"
        )
        assert (
            MeteringCalculator.format_volume_human_readable(90, "SECONDS")
            == "1.50 minutes"
        )
        assert (
            MeteringCalculator.format_volume_human_readable(3600, "SECONDS")
            == "1.00 hours"
        )
        assert (
            MeteringCalculator.format_volume_human_readable(86400, "SECONDS")
            == "1.00 days"
        )

        assert (
            MeteringCalculator.format_volume_human_readable(12, "HOURS")
            == "12.00 hours"
        )
        assert (
            MeteringCalculator.format_volume_human_readable(48, "HOURS") == "2.00 days"
        )

    def test_format_volume_human_readable_other(self):
        """Test human-readable formatting for other units."""
        assert (
            MeteringCalculator.format_volume_human_readable(100, "requests")
            == "100.00 requests"
        )
        assert (
            MeteringCalculator.format_volume_human_readable(50.5, "items")
            == "50.50 items"
        )
