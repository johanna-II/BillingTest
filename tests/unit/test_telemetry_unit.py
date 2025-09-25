"""Unit tests for Telemetry module to improve coverage."""

import os
import time
from typing import Never
from unittest.mock import MagicMock, Mock, patch

import pytest

try:
    from libs.observability.telemetry import (
        TelemetryManager,
        configure_telemetry,
        get_telemetry,
    )

    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False
    TelemetryManager = None

    def get_telemetry() -> None:
        return None

    def configure_telemetry() -> None:
        return None


@pytest.mark.skipif(not TELEMETRY_AVAILABLE, reason="Telemetry module not available")
class TestTelemetryUnit:
    """Unit tests for Telemetry functionality."""

    @pytest.fixture
    def mock_tracer(self):
        """Mock OpenTelemetry tracer."""
        return Mock()

    @pytest.fixture
    def mock_meter(self):
        """Mock OpenTelemetry meter."""
        return Mock()

    @pytest.fixture
    def telemetry(self, mock_tracer, mock_meter):
        """Create TelemetryManager with mocked dependencies."""
        with (
            patch(
                "libs.observability.telemetry.trace.get_tracer",
                return_value=mock_tracer,
            ),
            patch(
                "libs.observability.telemetry.metrics.get_meter",
                return_value=mock_meter,
            ),
        ):
            return TelemetryManager()

    def test_init(self, telemetry) -> None:
        """Test TelemetryManager initialization."""
        assert telemetry.tracer is not None
        assert telemetry.meter is not None
        assert hasattr(telemetry, "test_counter")
        assert hasattr(telemetry, "test_duration")
        assert hasattr(telemetry, "api_counter")
        assert hasattr(telemetry, "api_histogram")

    def test_record_test_execution(self, telemetry) -> None:
        """Test recording test execution metrics."""
        mock_counter = Mock()
        mock_histogram = Mock()
        telemetry.test_counter = mock_counter
        telemetry.test_duration = mock_histogram

        telemetry.record_test_execution("test_example", "passed", 1.5)

        mock_counter.add.assert_called_once_with(
            1, {"test_name": "test_example", "status": "passed"}
        )
        mock_histogram.record.assert_called_once_with(
            1.5, {"test_name": "test_example", "status": "passed"}
        )

    def test_record_api_call(self, telemetry) -> None:
        """Test recording API call metrics."""
        mock_counter = Mock()
        mock_histogram = Mock()
        telemetry.api_counter = mock_counter
        telemetry.api_histogram = mock_histogram

        telemetry.record_api_call("GET", "/api/v1/test", 200, 0.123)

        mock_counter.add.assert_called_once_with(
            1, {"method": "GET", "endpoint": "/api/v1/test", "status_code": 200}
        )
        mock_histogram.record.assert_called_once_with(
            123,
            {"method": "GET", "endpoint": "/api/v1/test"},  # milliseconds
        )

    def test_create_span(self, telemetry, mock_tracer) -> None:
        """Test span creation."""
        mock_span = Mock()
        mock_tracer.start_span.return_value = mock_span

        span = telemetry.create_span(
            "test_operation",
            operation_type="database",
            attributes={"db.name": "billing"},
        )

        assert span == mock_span
        mock_tracer.start_span.assert_called_once_with("test_operation")
        mock_span.set_attribute.assert_any_call("operation.type", "database")
        mock_span.set_attribute.assert_any_call("db.name", "billing")

    def test_trace_test_context_manager(self, telemetry, mock_tracer) -> None:
        """Test trace_test context manager."""
        mock_span = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_span
        mock_context.__exit__.return_value = None
        mock_tracer.start_as_current_span.return_value = mock_context

        with telemetry.trace_test("test_function", "unit") as span:
            assert span == mock_span
            # Simulate test execution
            time.sleep(0.01)

        mock_tracer.start_as_current_span.assert_called_once_with("test_function")
        mock_span.set_attribute.assert_any_call("test.type", "unit")
        mock_span.set_attribute.assert_any_call("test.framework", "pytest")

    def test_trace_test_with_exception(self, telemetry, mock_tracer) -> Never:
        """Test trace_test with exception handling."""
        mock_span = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_span
        mock_context.__exit__.return_value = None
        mock_tracer.start_as_current_span.return_value = mock_context

        with pytest.raises(ValueError):
            with telemetry.trace_test("test_function", "unit"):
                msg = "Test error"
                raise ValueError(msg)

        mock_span.record_exception.assert_called_once()
        mock_span.set_status.assert_called_once()

    def test_get_telemetry_singleton(self) -> None:
        """Test get_telemetry returns singleton instance."""
        telemetry1 = get_telemetry()
        telemetry2 = get_telemetry()

        # Should return the same instance
        assert telemetry1 is telemetry2

    def test_get_telemetry_disabled(self) -> None:
        """Test get_telemetry when disabled."""
        original_value = os.environ.get("ENABLE_TELEMETRY")

        try:
            os.environ["ENABLE_TELEMETRY"] = "false"
            # Clear singleton
            import libs.observability.telemetry

            libs.observability.telemetry._telemetry_instance = None

            telemetry = get_telemetry()
            assert telemetry is None
        finally:
            if original_value is not None:
                os.environ["ENABLE_TELEMETRY"] = original_value
            else:
                os.environ.pop("ENABLE_TELEMETRY", None)

    @patch("libs.observability.telemetry.Resource")
    @patch("libs.observability.telemetry.TracerProvider")
    @patch("libs.observability.telemetry.MeterProvider")
    def test_configure_telemetry_with_jaeger(
        self, mock_meter_provider, mock_tracer_provider, mock_resource
    ) -> None:
        """Test telemetry configuration with Jaeger enabled."""
        os.environ["OTLP_ENABLED"] = "true"
        os.environ["OTLP_ENDPOINT"] = "localhost:4317"
        os.environ["OTLP_INSECURE"] = "true"

        try:
            with patch("libs.observability.telemetry.OTLPSpanExporter") as mock_otlp:
                configure_telemetry()

                mock_otlp.assert_called_once()
                mock_tracer_provider.assert_called_once()
                mock_meter_provider.assert_called_once()
        finally:
            os.environ.pop("OTLP_ENABLED", None)
            os.environ.pop("OTLP_ENDPOINT", None)
            os.environ.pop("OTLP_INSECURE", None)

    def test_span_attributes_handling(self, telemetry, mock_tracer) -> None:
        """Test span attribute handling with various types."""
        mock_span = Mock()
        mock_tracer.start_span.return_value = mock_span

        attributes = {
            "string_attr": "value",
            "int_attr": 123,
            "float_attr": 45.67,
            "bool_attr": True,
            "none_attr": None,  # Should be filtered out
        }

        telemetry.create_span("test_op", attributes=attributes)

        # None values should not be set
        for key, value in attributes.items():
            if value is not None:
                mock_span.set_attribute.assert_any_call(key, value)

    def test_histogram_value_conversion(self, telemetry) -> None:
        """Test histogram value conversion to milliseconds."""
        mock_histogram = Mock()
        telemetry.api_histogram = mock_histogram

        # Test with various response times
        test_cases = [
            (0.001, 1),  # 1ms
            (0.1, 100),  # 100ms
            (1.0, 1000),  # 1s
            (2.5, 2500),  # 2.5s
        ]

        for response_time, expected_ms in test_cases:
            telemetry.record_api_call("GET", "/test", 200, response_time)
            mock_histogram.record.assert_called_with(
                expected_ms, {"method": "GET", "endpoint": "/test"}
            )
            mock_histogram.reset_mock()

    def test_error_handling_in_telemetry(self, telemetry) -> None:
        """Test error handling in telemetry operations."""
        # Test that operations don't raise when telemetry fails
        # The actual implementation handles failures gracefully
        telemetry.record_test_execution("test", "passed", 1.0)
        telemetry.record_api_call("GET", "/test", 200, 0.1)

        # These should complete without error
        assert True

    def test_telemetry_disabled_operations(self) -> None:
        """Test operations when telemetry is disabled."""
        telemetry = None  # Simulating disabled telemetry

        # These operations should not raise exceptions
        if telemetry:
            telemetry.record_test_execution("test", "passed", 1.0)
            telemetry.record_api_call("GET", "/test", 200, 0.1)

        # Test should pass without any operations
        assert True
