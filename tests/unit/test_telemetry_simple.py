"""Simple unit tests for Telemetry module."""

import os
import pytest
from unittest.mock import Mock, MagicMock

from libs.observability.telemetry import TelemetryManager, get_telemetry, configure_telemetry, TELEMETRY_AVAILABLE


class TestTelemetrySimple:
    """Simple tests for telemetry functionality."""
    
    def test_telemetry_import(self):
        """Test that telemetry module can be imported."""
        assert TelemetryManager is not None
        assert get_telemetry is not None
        assert configure_telemetry is not None
    
    def test_telemetry_availability(self):
        """Test telemetry availability flag."""
        assert isinstance(TELEMETRY_AVAILABLE, bool)
    
    def test_telemetry_disabled_environment(self):
        """Test telemetry with disabled environment."""
        original = os.environ.get('ENABLE_TELEMETRY')
        try:
            os.environ['ENABLE_TELEMETRY'] = 'false'
            import libs.observability.telemetry
            libs.observability.telemetry._telemetry_instance = None
            
            telemetry = get_telemetry()
            assert telemetry is None
        finally:
            if original is not None:
                os.environ['ENABLE_TELEMETRY'] = original
            else:
                os.environ.pop('ENABLE_TELEMETRY', None)
    
    def test_telemetry_basic_operations(self):
        """Test basic telemetry operations without mocking internals."""
        telemetry = TelemetryManager()
        
        # These methods should not raise even if telemetry is not available
        telemetry.record_test_execution("test", "passed", 1.0)
        telemetry.record_api_call("GET", "/test", 200, 0.1)
        
        # create_span should return None if not available
        span = telemetry.create_span("test_op")
        if not TELEMETRY_AVAILABLE:
            assert span is None
        
        # Context manager should work
        with telemetry.trace_test("test_name") as span:
            if not TELEMETRY_AVAILABLE:
                assert span is None
    
    def test_get_telemetry_singleton(self):
        """Test singleton behavior."""
        # Reset singleton
        import libs.observability.telemetry
        original = libs.observability.telemetry._telemetry_instance
        libs.observability.telemetry._telemetry_instance = None
        
        try:
            # Enable telemetry
            os.environ['ENABLE_TELEMETRY'] = 'true'
            
            telemetry1 = get_telemetry()
            telemetry2 = get_telemetry()
            
            assert telemetry1 is telemetry2
        finally:
            libs.observability.telemetry._telemetry_instance = original
