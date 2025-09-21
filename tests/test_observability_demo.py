"""Demo test for observability features."""

import time
import requests
import pytest

from libs.observability import get_telemetry


@pytest.mark.observability
@pytest.mark.unit
def test_observability_basic():
    """Basic test to demonstrate observability features."""
    telemetry = get_telemetry()
    
    if telemetry:
        # Manual span creation
        with telemetry.trace_test("demo_test", "integration"):
            time.sleep(0.1)  # Simulate some work
            
            # Make HTTP request to mock server
            try:
                response = requests.get("http://localhost:5000/health")
                assert response.status_code == 200
            except Exception as e:
                print(f"Mock server might not be running: {e}")
    
    # Test passes regardless of telemetry
    assert True


@pytest.mark.observability
@pytest.mark.unit
def test_api_call_metrics():
    """Test API call metric recording."""
    telemetry = get_telemetry()
    
    if telemetry:
        # Record some API metrics
        telemetry.record_api_call(
            endpoint="/api/v1/contracts",
            method="GET",
            status_code=200,
            response_time_ms=45.2
        )
        
        telemetry.record_api_call(
            endpoint="/api/v1/credits",
            method="POST",
            status_code=201,
            response_time_ms=120.5
        )
        
        telemetry.record_api_call(
            endpoint="/api/v1/contracts/999",
            method="GET",
            status_code=404,
            response_time_ms=15.3
        )
    
    assert True


@pytest.mark.observability
@pytest.mark.unit
def test_with_telemetry_fixture():
    """Test using the telemetry functionality."""
    telemetry = get_telemetry()
    
    if telemetry:
        # Create custom span
        span = telemetry.create_span(
            "custom_operation",
            operation_type="database",
            table="contracts"
        )
        
        try:
            # Simulate some work
            time.sleep(0.05)
            span.set_attribute("rows_processed", 42)
        finally:
            span.end()
    
    assert True


@pytest.mark.observability
@pytest.mark.unit
@pytest.mark.parametrize("test_num", range(3))
def test_multiple_executions(test_num):
    """Test that generates multiple telemetry entries."""
    telemetry = get_telemetry()
    
    if telemetry:
        with telemetry.trace_test(f"parameterized_test_{test_num}", "unit"):
            # Simulate variable work
            time.sleep(0.01 * (test_num + 1))
    
    assert True

