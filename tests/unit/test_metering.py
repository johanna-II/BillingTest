"""Unit tests for metering module."""

from unittest.mock import Mock, patch

import pytest

from libs.constants import CounterType
from libs.exceptions import APIRequestException, ValidationException
from libs.Metering import MeteringManager


class TestMeteringManagerUnit:
    """Unit tests for MeteringManager class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        with patch("libs.Metering.BillingAPIClient") as mock_client_class:
            self.mock_client = Mock()
            mock_client_class.return_value = self.mock_client
            self.metering = MeteringManager(month="2024-01")
            yield

    def test_send_metering_success(self) -> None:
        """Test successful metering data submission."""
        mock_response = {"status": "SUCCESS", "processedCount": 1}
        self.mock_client.post.return_value = mock_response

        result = self.metering.send_metering(
            app_key="test-app-key",
            counter_name="compute.c2.c8m8",
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume="100",
            resource_id="vm-123",
            resource_name="Test VM",
        )

        assert result == mock_response

        # Verify API call
        expected_data = {
            "meterList": [
                {
                    "appKey": "test-app-key",
                    "counterName": "compute.c2.c8m8",
                    "counterType": "DELTA",
                    "counterUnit": "HOURS",
                    "counterVolume": "100",
                    "parentResourceId": "test",
                    "resourceId": "vm-123",
                    "resourceName": "Test VM",
                    "source": "qa.billing.test",
                    "timestamp": "2024-01-01T13:00:00.000+09:00",
                }
            ]
        }

        self.mock_client.post.assert_called_once_with(
            "billing/meters", json_data=expected_data
        )

    def test_send_metering_with_string_counter_type(self) -> None:
        """Test sending metering with string counter type."""
        self.mock_client.post.return_value = {"status": "SUCCESS"}

        result = self.metering.send_metering(
            app_key="test-app",
            counter_name="storage.volume",
            counter_type="GAUGE",  # String instead of enum
            counter_unit="GB",
            counter_volume="500",
        )

        assert result["status"] == "SUCCESS"

        # Verify counter type was correctly used
        call_args = self.mock_client.post.call_args
        meter_data = call_args[1]["json_data"]["meterList"][0]
        assert meter_data["counterType"] == "GAUGE"

    def test_send_metering_invalid_counter_type(self) -> None:
        """Test sending metering with invalid counter type."""
        with pytest.raises(ValidationException) as exc_info:
            self.metering.send_metering(
                app_key="test-app",
                counter_name="test.counter",
                counter_type="INVALID_TYPE",
                counter_unit="COUNT",
                counter_volume="10",
            )

        assert "Invalid counter type" in str(exc_info.value)

    def test_delete_metering_single_app_key(self) -> None:
        """Test deleting metering data for single app key."""
        self.metering.delete_metering("test-app-key")

        expected_params = {
            "appKey": "test-app-key",
            "from": "2024-01-01",
            "to": "2024-01-31",
        }

        self.mock_client.delete.assert_called_once_with(
            "billing/admin/meters", params=expected_params
        )

    def test_delete_metering_multiple_app_keys(self) -> None:
        """Test deleting metering data for multiple app keys."""
        app_keys = ["app-1", "app-2", "app-3"]

        result = self.metering.delete_metering(app_keys)

        assert result["deleted_count"] == 3
        assert self.mock_client.delete.call_count == 3

        # Verify each delete call
        for idx, app_key in enumerate(app_keys):
            expected_params = {
                "appKey": app_key,
                "from": "2024-01-01",
                "to": "2024-01-31",
            }
            actual_call = self.mock_client.delete.call_args_list[idx]
            assert actual_call[0][0] == "billing/admin/meters"
            assert actual_call[1]["params"] == expected_params

    @patch("libs.Metering.calendar.monthrange")
    def test_delete_metering_different_months(self, mock_monthrange) -> None:
        """Test delete metering for different months."""
        # Test February (non-leap year)
        mock_monthrange.return_value = (0, 28)
        metering_feb = MeteringManager(month="2023-02")
        metering_feb._client = self.mock_client

        metering_feb.delete_metering("test-app")

        expected_params = {
            "appKey": "test-app",
            "from": "2023-02-01",
            "to": "2023-02-28",
        }
        self.mock_client.delete.assert_called_with(
            "billing/admin/meters", params=expected_params
        )

    def test_send_batch_metering_success(self) -> None:
        """Test sending batch metering data."""
        metering_items = [
            {
                "counter_name": "compute.c2.c8m8",
                "counter_type": "DELTA",
                "counter_unit": "HOURS",
                "counter_volume": "100",
            },
            {
                "counter_name": "storage.volume",
                "counter_type": "GAUGE",
                "counter_unit": "GB",
                "counter_volume": "500",
            },
        ]

        self.mock_client.post.return_value = {"status": "SUCCESS"}

        result = self.metering.send_batch_metering("test-app", metering_items)

        assert len(result["results"]) == 2
        assert all(r["success"] for r in result["results"])
        assert self.mock_client.post.call_count == 2

    def test_send_batch_metering_partial_failure(self) -> None:
        """Test batch metering with partial failures."""
        metering_items = [
            {
                "counter_name": "compute.c2.c8m8",
                "counter_type": "DELTA",
                "counter_unit": "HOURS",
                "counter_volume": "100",
            },
            {
                "counter_name": "storage.volume",
                "counter_type": "GAUGE",
                "counter_unit": "GB",
                "counter_volume": "500",
            },
        ]

        # First call succeeds, second fails
        self.mock_client.post.side_effect = [
            {"status": "SUCCESS"},
            APIRequestException("Failed"),
        ]

        result = self.metering.send_batch_metering("test-app", metering_items)

        assert len(result["results"]) == 2
        assert result["results"][0]["success"] is True
        assert result["results"][1]["success"] is False
        assert "Failed" in result["results"][1]["error"]

    def test_create_default_template(self) -> None:
        """Test creation of default metering template."""
        template = MeteringManager._create_default_template()

        assert "meterList" in template
        assert len(template["meterList"]) == 1

        meter = template["meterList"][0]
        assert meter["source"] == "qa.billing.test"
        assert meter["parentResourceId"] == "test"
        assert meter["resourceId"] == "test"
        assert meter["resourceName"] == "test"

    def test_send_iaas_metering_success(self) -> None:
        """Test successful IaaS metering submission."""
        self.mock_client.post.return_value = {"status": "SUCCESS"}

        result = self.metering.send_iaas_metering(
            app_key="test-app-key",
            counter_name="compute.c2.c8m8",
            counter_unit="HOURS",
            counter_volume=100.5,
        )

        assert result == {"status": "SUCCESS"}

        # Verify API was called with correct data
        call_args = self.mock_client.post.call_args
        meter_data = call_args[1]["json_data"]["meterList"][0]
        assert meter_data["appKey"] == "test-app-key"
        assert meter_data["counterName"] == "compute.c2.c8m8"
        assert meter_data["counterUnit"] == "HOURS"
        assert meter_data["counterVolume"] == "100.5"  # Should be converted to string

    @patch("libs.Metering.logger")
    @pytest.mark.parametrize(
        "param_name,param_value",
        [
            ("target_time", "2024-01-01"),
            ("uuid", "test-uuid-123"),
            ("app_id", "old-app-id"),
            ("project_id", "old-project-id"),
        ],
    )
    def test_send_iaas_metering_deprecated_params(
        self, mock_logger, param_name, param_value
    ) -> None:
        """Test that deprecated parameters emit warnings."""
        self.mock_client.post.return_value = {"status": "SUCCESS"}

        kwargs = {
            "app_key": "test-app",
            "counter_name": "test.counter",
            "counter_unit": "HOURS",
            "counter_volume": "10",
            param_name: param_value,
        }
        self.metering.send_iaas_metering(**kwargs)

        # Verify warning was logged
        mock_logger.warning.assert_called()
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        assert any(
            param_name in str(call) and "deprecated" in str(call).lower()
            for call in warning_calls
        )

    @patch("libs.Metering.logger")
    def test_send_iaas_metering_multiple_deprecated_params(self, mock_logger) -> None:
        """Test that multiple deprecated parameters each emit their own warning."""
        self.mock_client.post.return_value = {"status": "SUCCESS"}

        self.metering.send_iaas_metering(
            app_key="test-app",
            counter_name="test.counter",
            counter_unit="HOURS",
            counter_volume="10",
            target_time="2024-01-01",
            uuid="test-uuid",
            app_id="old-app-id",
            project_id="old-project-id",
        )

        # Verify all deprecated parameters triggered warnings
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]

        assert any("target_time" in str(call) for call in warning_calls)
        assert any("uuid" in str(call) for call in warning_calls)
        assert any("app_id" in str(call) for call in warning_calls)
        assert any("project_id" in str(call) for call in warning_calls)

        # Should have at least 4 warning calls (one for each deprecated param)
        assert mock_logger.warning.call_count >= 4

    @patch("libs.Metering.logger")
    def test_send_iaas_metering_unexpected_kwargs(self, mock_logger) -> None:
        """Test that unexpected kwargs trigger warning."""
        self.mock_client.post.return_value = {"status": "SUCCESS"}

        self.metering.send_iaas_metering(
            app_key="test-app",
            counter_name="test.counter",
            counter_unit="HOURS",
            counter_volume="10",
            unknown_param="value",
            another_param="value2",
        )

        # Verify warning was logged for unexpected parameters
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        assert any("unexpected" in str(call).lower() for call in warning_calls)

        # Verify unexpected kwargs are not included in the API payload
        call_args = self.mock_client.post.call_args
        json_data = call_args[1]["json_data"]
        meter_entry = json_data["meterList"][0]
        assert "unknown_param" not in meter_entry
        assert "another_param" not in meter_entry

    @patch("libs.Metering.logger")
    def test_send_iaas_metering_deprecated_params_ignored(self, mock_logger) -> None:
        """Test that deprecated parameters are actually ignored and don't affect functionality."""
        self.mock_client.post.return_value = {"status": "SUCCESS"}

        # Call with deprecated params
        result = self.metering.send_iaas_metering(
            app_key="correct-app-key",
            counter_name="test.counter",
            counter_unit="HOURS",
            counter_volume="10",
            app_id="wrong-app-id",  # Should be ignored
            target_time="2020-01-01",  # Should be ignored
        )

        # Verify the function still returns success
        assert result == {"status": "SUCCESS"}

        # Verify that the underlying send_metering was called with correct params
        call_args = self.mock_client.post.call_args
        meter_data = call_args[1]["json_data"]["meterList"][0]

        # Verify correct app_key is used (not app_id)
        assert meter_data["appKey"] == "correct-app-key"

    def test_send_iaas_metering_appkey_fallback(self) -> None:
        """Test that self.appkey is used when app_key is not provided."""
        self.mock_client.post.return_value = {"status": "SUCCESS"}
        self.metering.appkey = "fallback-app-key"

        result = self.metering.send_iaas_metering(
            # app_key intentionally omitted
            counter_name="test.counter",
            counter_unit="HOURS",
            counter_volume="10",
        )

        assert result == {"status": "SUCCESS"}

        # Verify fallback appkey was used
        call_args = self.mock_client.post.call_args
        meter_data = call_args[1]["json_data"]["meterList"][0]
        assert meter_data["appKey"] == "fallback-app-key"

    def test_send_iaas_metering_missing_app_key_raises_error(self) -> None:
        """Test that ValueError is raised when app_key is not provided and self.appkey is None."""
        # Ensure self.appkey is None
        self.metering.appkey = None

        with pytest.raises(ValueError) as exc_info:
            self.metering.send_iaas_metering(
                counter_name="test.counter",
                counter_unit="HOURS",
                counter_volume="10",
            )

        assert "app_key must be provided" in str(exc_info.value)
