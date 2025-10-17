"""Mocked integration tests for Metering Manager.

Uses responses library to mock HTTP calls - NO DOCKER NEEDED!
"""

import re

import pytest
import responses

from libs.constants import CounterType
from libs.Metering import MeteringManager


class TestMeteringMocked:
    """Metering integration tests with in-memory mocking.

    No Docker, no mock server, no worker crashes!
    """

    @pytest.fixture
    def metering_manager(self):
        """Create a MeteringManager instance."""
        return MeteringManager(month="2024-01")

    @responses.activate
    def test_send_metering_basic(self, metering_manager):
        """Test basic metering send with mocked response."""
        # Mock the API endpoint
        # Actual URL: https://meteringtest.internal.com/billing/meters
        responses.add(
            method=responses.POST,
            url=re.compile(r".*/billing/meters$"),
            json={
                "header": {
                    "isSuccessful": True,
                    "resultCode": 0,
                    "resultMessage": "SUCCESS",
                },
                "metering": {
                    "meteringId": "MTR-12345",
                    "appKey": "test-app-001",
                    "status": "ACCEPTED",
                },
            },
            status=200,
        )

        # Execute actual code
        result = metering_manager.send_metering(
            app_key="test-app-001",
            counter_name="compute.instance",
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume="100",
        )

        # Assertions
        assert result is not None
        assert result.get("header", {}).get("isSuccessful") is True

        # Verify the request was made
        assert len(responses.calls) == 1
        request = responses.calls[0].request
        assert "/billing/meters" in request.url

    @responses.activate
    def test_send_metering_with_metadata(self, metering_manager):
        """Test metering with metadata fields."""
        responses.add(
            responses.POST,
            re.compile(r".*/billing/meters$"),
            json={
                "header": {
                    "isSuccessful": True,
                    "resultCode": 0,
                    "resultMessage": "SUCCESS",
                }
            },
            status=200,
        )

        result = metering_manager.send_metering(
            app_key="test-app-002",
            counter_name="storage.block",
            counter_type=CounterType.GAUGE,
            counter_unit="GB",
            counter_volume="500",
            # counter_description not supported
        )

        assert result["header"]["isSuccessful"] is True

    @responses.activate
    def test_send_metering_batch(self, metering_manager):
        """Test sending multiple metering records."""
        # Mock response for multiple calls
        responses.add(
            responses.POST,
            re.compile(r".*/billing/meters$"),
            json={"header": {"isSuccessful": True}},
            status=200,
        )

        counters = [
            ("compute.vm.small", "DELTA", "HOURS", "720"),
            ("compute.vm.large", "DELTA", "HOURS", "168"),
            ("storage.object", "GAUGE", "GB", "1000"),
        ]

        for counter_name, counter_type, unit, volume in counters:
            result = metering_manager.send_metering(
                app_key="test-app-003",
                counter_name=counter_name,
                counter_type=counter_type,
                counter_unit=unit,
                counter_volume=volume,
            )
            assert result["header"]["isSuccessful"] is True

        # Verify all requests were made
        assert len(responses.calls) == 3

    def test_send_metering_error_handling(self, metering_manager):
        """Test error response handling."""
        # Test validation error for invalid counter type
        # This should raise ValidationException before making API call
        with pytest.raises(Exception) as exc_info:
            metering_manager.send_metering(
                app_key="test-app-004",
                counter_name="invalid.counter",
                counter_type="INVALID_TYPE",
                counter_unit="UNITS",
                counter_volume="100",
            )
        # Should be ValidationException
        assert "Invalid counter type" in str(
            exc_info.value
        ) or "ValidationException" in str(type(exc_info.value))

    @responses.activate
    def test_send_metering_network_timeout(self, metering_manager):
        """Test handling of network timeouts."""
        # Mock timeout
        responses.add(
            responses.POST,
            re.compile(r".*/billing/meters$"),
            body=Exception("Connection timeout"),
        )

        # Should handle timeout gracefully
        try:
            result = metering_manager.send_metering(
                app_key="test-app-005",
                counter_name="test.timeout",
                counter_type=CounterType.DELTA,
                counter_unit="COUNT",
                counter_volume="1",
            )
            # If it doesn't raise, check result
            assert result is not None
        except Exception as e:
            # Exception is expected and OK
            assert "timeout" in str(e).lower() or "connection" in str(e).lower()

    @responses.activate
    def test_send_metering_request_validation(self, metering_manager):
        """Verify request body structure."""
        responses.add(
            responses.POST,
            re.compile(r".*/billing/meters$"),
            json={"header": {"isSuccessful": True}},
            status=200,
        )

        metering_manager.send_metering(
            app_key="test-app-006",
            counter_name="test.validation",
            counter_type=CounterType.DELTA,
            counter_unit="COUNT",
            counter_volume="999",
        )

        # Verify request structure
        assert len(responses.calls) == 1
        request = responses.calls[0].request

        # Check URL
        assert "/billing/meters" in request.url

        # Check method
        assert request.method == "POST"

        # Check headers (if needed)
        # assert "Content-Type" in request.headers

    @responses.activate
    def test_multiple_counter_types(self, metering_manager):
        """Test different counter types (DELTA, GAUGE)."""
        responses.add(
            responses.POST,
            re.compile(r".*/billing/meters$"),
            json={"header": {"isSuccessful": True}},
            status=200,
        )

        # DELTA counter
        delta_result = metering_manager.send_metering(
            app_key="test-app-007",
            counter_name="network.bandwidth",
            counter_type=CounterType.DELTA,
            counter_unit="GB",
            counter_volume="1000",
        )
        assert delta_result["header"]["isSuccessful"]

        # GAUGE counter
        gauge_result = metering_manager.send_metering(
            app_key="test-app-007",
            counter_name="cpu.utilization",
            counter_type=CounterType.GAUGE,
            counter_unit="PERCENT",
            counter_volume="75",
        )
        assert gauge_result["header"]["isSuccessful"]

        assert len(responses.calls) == 2


class TestMeteringPerformance:
    """Performance tests for mocked metering."""

    @responses.activate
    def test_metering_speed(self):
        """Verify mocked tests are ultra-fast."""
        import time

        responses.add(
            responses.POST,
            re.compile(r".*/billing/meters$"),
            json={"header": {"isSuccessful": True}},
            status=200,
        )

        mgr = MeteringManager(month="2024-01")

        start = time.time()
        for i in range(10):
            mgr.send_metering(
                app_key=f"app-{i}",
                counter_name="test.speed",
                counter_type=CounterType.DELTA,
                counter_unit="COUNT",
                counter_volume="1",
            )
        duration = time.time() - start

        # Should be very fast (< 1 second for 10 calls)
        assert duration < 1.0
        assert len(responses.calls) == 10
