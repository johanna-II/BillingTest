"""Unit tests for MeteringManager edge cases - extracted from integration tests."""

from unittest.mock import Mock

import pytest

from libs.constants import CounterType
from libs.exceptions import ValidationException
from libs.Metering import MeteringManager


class TestMeteringEdgeCases:
    """Unit tests for metering edge cases and validation."""

    @pytest.fixture
    def metering_manager(self):
        """Create MeteringManager with mocked client."""
        mock_client = Mock()
        return MeteringManager(month="2024-01", client=mock_client)

    def test_empty_app_key_validation(self, metering_manager):
        """Test validation of empty app key."""
        # Currently this might pass through to API, but we can test it
        metering_manager._client.post.return_value = {"success": True}

        # Empty app key should still be allowed to be sent (API will validate)
        result = metering_manager.send_metering(
            app_key="",  # Empty app key
            counter_name="test.counter",
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume="100",
        )
        assert metering_manager._client.post.called

    def test_empty_counter_name_handling(self, metering_manager):
        """Test handling of empty counter name."""
        metering_manager._client.post.return_value = {"success": True}

        # Empty counter name - API will handle validation
        result = metering_manager.send_metering(
            app_key="test-app",
            counter_name="",  # Empty counter name
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume="100",
        )
        assert metering_manager._client.post.called

    def test_negative_volume_handling(self, metering_manager):
        """Test handling of negative volume values."""
        metering_manager._client.post.return_value = {"success": True}

        # Negative volume is passed as string, API handles validation
        result = metering_manager.send_metering(
            app_key="test-app",
            counter_name="test.counter",
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume="-100",  # Negative volume
        )

        # Check that negative volume is sent as-is
        call_args = metering_manager._client.post.call_args
        posted_data = call_args[1]["json_data"]
        assert posted_data["meterList"][0]["counterVolume"] == "-100"

    def test_invalid_counter_type_validation(self, metering_manager):
        """Test validation of invalid counter type."""
        with pytest.raises(ValidationException, match="Invalid counter type"):
            metering_manager.send_metering(
                app_key="test-app",
                counter_name="test.counter",
                counter_type="INVALID_TYPE",
                counter_unit="HOURS",
                counter_volume="100",
            )

    def test_special_characters_in_app_key(self, metering_manager):
        """Test handling of special characters in app key."""
        metering_manager._client.post.return_value = {"success": True}

        special_app_keys = [
            "app-123!@#",
            "app with spaces",
            "app/with/slashes",
            "app\\with\\backslashes",
            "app:with:colons",
            "app;with;semicolons",
        ]

        for app_key in special_app_keys:
            result = metering_manager.send_metering(
                app_key=app_key,
                counter_name="test.counter",
                counter_type=CounterType.DELTA,
                counter_unit="HOURS",
                counter_volume="100",
            )
            assert metering_manager._client.post.called

    def test_extreme_volume_values(self, metering_manager):
        """Test handling of extreme volume values."""
        metering_manager._client.post.return_value = {"success": True}

        extreme_volumes = [
            "0",
            "0.0000001",
            "999999999999",
            "1.23456789012345",
            "1e10",
            "1E-10",
        ]

        for volume in extreme_volumes:
            result = metering_manager.send_metering(
                app_key="test-app",
                counter_name="test.counter",
                counter_type=CounterType.GAUGE,
                counter_unit="BYTES",
                counter_volume=volume,
            )

            call_args = metering_manager._client.post.call_args
            posted_data = call_args[1]["json_data"]
            assert posted_data["meterList"][0]["counterVolume"] == volume

    def test_unicode_in_resource_names(self, metering_manager):
        """Test handling of unicode characters in resource names."""
        metering_manager._client.post.return_value = {"success": True}

        result = metering_manager.send_metering(
            app_key="test-app",
            counter_name="test.counter",
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume="100",
            resource_name="테스트 리소스 🚀",
            resource_id="리소스-123",
        )

        call_args = metering_manager._client.post.call_args
        posted_data = call_args[1]["json_data"]
        meter_data = posted_data["meterList"][0]
        assert meter_data["resourceName"] == "테스트 리소스 🚀"
        assert meter_data["resourceId"] == "리소스-123"

    def test_empty_unit_handling(self, metering_manager):
        """Test handling of empty counter unit."""
        metering_manager._client.post.return_value = {"success": True}

        result = metering_manager.send_metering(
            app_key="test-app",
            counter_name="test.counter",
            counter_type=CounterType.DELTA,
            counter_unit="",  # Empty unit
            counter_volume="100",
        )

        call_args = metering_manager._client.post.call_args
        posted_data = call_args[1]["json_data"]
        assert posted_data["meterList"][0]["counterUnit"] == ""
