"""Unit tests for MeteringManager validation and calculation logic."""

from unittest.mock import Mock

import pytest

from libs.constants import CounterType
from libs.exceptions import ValidationException
from libs.Metering import MeteringManager


class TestMeteringValidation:
    """Unit tests for metering validation logic."""

    @pytest.fixture
    def metering_manager(self):
        """Create MeteringManager with mocked client."""
        mock_client = Mock()
        return MeteringManager(month="2024-01", client=mock_client)

    def test_validate_month_format_valid(self):
        """Test valid month formats."""
        # Should not raise
        MeteringManager._validate_month_format("2024-01")
        MeteringManager._validate_month_format("2024-12")
        MeteringManager._validate_month_format("2025-06")

    def test_validate_month_format_invalid(self):
        """Test invalid month formats."""
        invalid_formats = [
            "2024",  # Missing month
            "01-2024",  # Wrong order
            "2024-1",  # Single digit month
            "2024-13",  # Invalid month
            "2024-00",  # Zero month
            "24-01",  # 2-digit year
            "2024/01",  # Wrong separator
            "",  # Empty
        ]

        for invalid in invalid_formats:
            with pytest.raises(ValidationException, match="Invalid month format"):
                MeteringManager._validate_month_format(invalid)

    def test_create_default_template(self):
        """Test default template creation."""
        template = MeteringManager._create_default_template()

        assert "meterList" in template
        assert len(template["meterList"]) == 1

        meter = template["meterList"][0]
        assert meter["appKey"] == ""
        assert meter["counterName"] == ""
        assert meter["source"] == "qa.billing.test"
        assert meter["resourceId"] == "test"

    def test_counter_type_validation_valid(self, metering_manager):
        """Test valid counter type validation in send_metering."""
        mock_response = {"success": True}
        metering_manager._client.post.return_value = mock_response

        # Test with enum
        result = metering_manager.send_metering(
            app_key="test-app",
            counter_name="test.counter",
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume="100",
        )
        assert result == mock_response

        # Test with string
        result = metering_manager.send_metering(
            app_key="test-app",
            counter_name="test.counter",
            counter_type="GAUGE",
            counter_unit="HOURS",
            counter_volume="100",
        )
        assert result == mock_response

    def test_counter_type_validation_invalid(self, metering_manager):
        """Test invalid counter type validation."""
        with pytest.raises(ValidationException, match="Invalid counter type"):
            metering_manager.send_metering(
                app_key="test-app",
                counter_name="test.counter",
                counter_type="INVALID_TYPE",
                counter_unit="HOURS",
                counter_volume="100",
            )

    def test_timestamp_format(self, metering_manager):
        """Test timestamp generation for metering data."""
        metering_manager._client.post.return_value = {"success": True}

        metering_manager.send_metering(
            app_key="test-app",
            counter_name="test.counter",
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume="100",
        )

        # Check the posted data
        call_args = metering_manager._client.post.call_args
        posted_data = call_args[1]["json_data"]
        timestamp = posted_data["meterList"][0]["timestamp"]

        # Should be in format: YYYY-MM-01T13:00:00.000+09:00
        assert timestamp == "2024-01-01T13:00:00.000+09:00"

    def test_volume_conversion(self, metering_manager):
        """Test volume string handling."""
        metering_manager._client.post.return_value = {"success": True}

        # Test various volume formats
        volumes = ["100", "100.5", "0", "999999"]

        for volume in volumes:
            metering_manager.send_metering(
                app_key="test-app",
                counter_name="test.counter",
                counter_type=CounterType.DELTA,
                counter_unit="HOURS",
                counter_volume=volume,
            )

            call_args = metering_manager._client.post.call_args
            posted_data = call_args[1]["json_data"]
            assert posted_data["meterList"][0]["counterVolume"] == volume

    def test_metering_data_structure(self, metering_manager):
        """Test complete metering data structure."""
        metering_manager._client.post.return_value = {"success": True}

        metering_manager.send_metering(
            app_key="app-123",
            counter_name="compute.instance",
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume="744",
            resource_id="vm-001",
            resource_name="Test VM",
            parent_resource_id="project-001",
        )

        call_args = metering_manager._client.post.call_args
        posted_data = call_args[1]["json_data"]
        meter_data = posted_data["meterList"][0]

        assert meter_data["appKey"] == "app-123"
        assert meter_data["counterName"] == "compute.instance"
        assert meter_data["counterType"] == "DELTA"
        assert meter_data["counterUnit"] == "HOURS"
        assert meter_data["counterVolume"] == "744"
        assert meter_data["resourceId"] == "vm-001"
        assert meter_data["resourceName"] == "Test VM"
        assert meter_data["parentResourceId"] == "project-001"
        assert meter_data["source"] == "qa.billing.test"
