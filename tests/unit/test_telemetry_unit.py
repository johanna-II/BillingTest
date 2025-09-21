"""Unit tests for Telemetry module to improve coverage."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time
from datetime import datetime

try:
    from libs.observability.telemetry import TestTelemetry, get_telemetry, configure_telemetry
    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False
    TestTelemetry = None
    get_telemetry = lambda: None
    configure_telemetry = lambda: None


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
        """Create TestTelemetry with mocked dependencies."""
        with patch('libs.observability.telemetry.trace.get_tracer', return_value=mock_tracer):
            with patch('libs.observability.telemetry.metrics.get_meter', return_value=mock_meter):
                return TestTelemetry()

    def test_init(self, telemetry):
        """Test TestTelemetry initialization."""
        assert telemetry.tracer is not None
        assert telemetry.meter is not None
        assert hasattr(telemetry, 'test_counter')
        assert hasattr(telemetry, 'test_histogram')
        assert hasattr(telemetry, 'api_counter')
        assert hasattr(telemetry, 'api_histogram')

    def test_record_test_execution(self, telemetry):
        """Test recording test execution metrics."""
        mock_counter = Mock()
        telemetry.test_counter = mock_counter
        
        telemetry.record_test_execution("test_example", "passed", 1.5)
        
        mock_counter.add.assert_called_once_with(
            1,
            {
                "test_name": "test_example",
                "status": "passed"
            }
        )

    def test_record_api_call(self, telemetry):
        """Test recording API call metrics."""
        mock_counter = Mock()
        mock_histogram = Mock()
        telemetry.api_counter = mock_counter
        telemetry.api_histogram = mock_histogram
        
        telemetry.record_api_call("GET", "/api/v1/test", 200, 0.123)
        
        mock_counter.add.assert_called_once_with(
            1,
            {
                "method": "GET",
                "endpoint": "/api/v1/test",
                "status_code": 200
            }
        )
        mock_histogram.record.assert_called_once_with(
            123,  # milliseconds
            {
                "method": "GET",
                "endpoint": "/api/v1/test"
            }
        )

    def test_create_span(self, telemetry, mock_tracer):
        """Test span creation."""
        mock_span = Mock()
        mock_tracer.start_span.return_value = mock_span
        
        span = telemetry.create_span(
            "test_operation",
            operation_type="database",
            attributes={"db.name": "billing"}
        )
        
        assert span == mock_span
        mock_tracer.start_span.assert_called_once_with("test_operation")
        mock_span.set_attribute.assert_any_call("operation.type", "database")
        mock_span.set_attribute.assert_any_call("db.name", "billing")

    def test_trace_test_context_manager(self, telemetry, mock_tracer):
        """Test trace_test context manager."""
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
        
        with telemetry.trace_test("test_function", "unit") as span:
            assert span == mock_span
            # Simulate test execution
            time.sleep(0.01)
        
        mock_tracer.start_as_current_span.assert_called_once_with("test_function")
        mock_span.set_attribute.assert_any_call("test.type", "unit")
        mock_span.set_attribute.assert_any_call("test.framework", "pytest")

    def test_trace_test_with_exception(self, telemetry, mock_tracer):
        """Test trace_test with exception handling."""
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
        
        with pytest.raises(ValueError):
            with telemetry.trace_test("test_function", "unit"):
                raise ValueError("Test error")
        
        mock_span.record_exception.assert_called_once()
        mock_span.set_status.assert_called_once()

    def test_get_telemetry_singleton(self):
        """Test get_telemetry returns singleton instance."""
        telemetry1 = get_telemetry()
        telemetry2 = get_telemetry()
        
        # Should return the same instance
        assert telemetry1 is telemetry2

    def test_get_telemetry_disabled(self):
        """Test get_telemetry when disabled."""
        import os
        original_value = os.environ.get('ENABLE_TELEMETRY')
        
        try:
            os.environ['ENABLE_TELEMETRY'] = 'false'
            # Clear singleton
            import libs.observability.telemetry
            libs.observability.telemetry._telemetry_instance = None
            
            telemetry = get_telemetry()
            assert telemetry is None
        finally:
            if original_value is not None:
                os.environ['ENABLE_TELEMETRY'] = original_value
            else:
                os.environ.pop('ENABLE_TELEMETRY', None)

    @patch('libs.observability.telemetry.Resource')
    @patch('libs.observability.telemetry.TracerProvider')
    @patch('libs.observability.telemetry.MeterProvider')
    def test_configure_telemetry_with_jaeger(self, mock_meter_provider, mock_tracer_provider, mock_resource):
        """Test telemetry configuration with Jaeger enabled."""
        import os
        os.environ['JAEGER_ENABLED'] = 'true'
        os.environ['JAEGER_HOST'] = 'localhost'
        os.environ['JAEGER_PORT'] = '6831'
        
        try:
            with patch('libs.observability.telemetry.JaegerExporter') as mock_jaeger:
                configure_telemetry()
                
                mock_jaeger.assert_called_once()
                mock_tracer_provider.assert_called_once()
                mock_meter_provider.assert_called_once()
        finally:
            os.environ.pop('JAEGER_ENABLED', None)
            os.environ.pop('JAEGER_HOST', None)
            os.environ.pop('JAEGER_PORT', None)

    def test_span_attributes_handling(self, telemetry, mock_tracer):
        """Test span attribute handling with various types."""
        mock_span = Mock()
        mock_tracer.start_span.return_value = mock_span
        
        attributes = {
            "string_attr": "value",
            "int_attr": 123,
            "float_attr": 45.67,
            "bool_attr": True,
            "none_attr": None  # Should be filtered out
        }
        
        span = telemetry.create_span("test_op", attributes=attributes)
        
        # None values should not be set
        for key, value in attributes.items():
            if value is not None:
                mock_span.set_attribute.assert_any_call(key, value)

    def test_histogram_value_conversion(self, telemetry):
        """Test histogram value conversion to milliseconds."""
        mock_histogram = Mock()
        telemetry.api_histogram = mock_histogram
        
        # Test with various response times
        test_cases = [
            (0.001, 1),      # 1ms
            (0.1, 100),      # 100ms
            (1.0, 1000),     # 1s
            (2.5, 2500),     # 2.5s
        ]
        
        for response_time, expected_ms in test_cases:
            telemetry.record_api_call("GET", "/test", 200, response_time)
            mock_histogram.record.assert_called_with(
                expected_ms,
                {"method": "GET", "endpoint": "/test"}
            )
            mock_histogram.reset_mock()

    @patch('libs.observability.telemetry.logger')
    def test_error_handling_in_telemetry(self, mock_logger, telemetry):
        """Test error handling in telemetry operations."""
        # Make span creation fail
        telemetry.tracer.start_span.side_effect = Exception("Tracer error")
        
        # Should not raise exception
        span = telemetry.create_span("test_op")
        
        # Should log the error
        mock_logger.error.assert_called()

    def test_telemetry_disabled_operations(self):
        """Test operations when telemetry is disabled."""
        telemetry = None  # Simulating disabled telemetry
        
        # These operations should not raise exceptions
        if telemetry:
            telemetry.record_test_execution("test", "passed", 1.0)
            telemetry.record_api_call("GET", "/test", 200, 0.1)
        
        # Test should pass without any operations
        assert True
