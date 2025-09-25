"""Demo tests to showcase observability features."""

import random
import time

import pytest

from libs.observability import get_telemetry


@pytest.mark.observability
class TestObservabilityDemo:
    """Demo tests to generate telemetry data."""

    @pytest.fixture
    def telemetry(self):
        """Get telemetry instance."""
        return get_telemetry()

    def test_fast_operation(self, telemetry) -> None:
        """Test that completes quickly."""
        if telemetry:
            with telemetry.trace_test("fast_operation", "demo"):
                time.sleep(0.01)
                assert True

    def test_slow_operation(self, telemetry) -> None:
        """Test that takes some time."""
        if telemetry:
            with telemetry.trace_test("slow_operation", "demo"):
                time.sleep(0.5)
                assert True

    def test_with_multiple_spans(self, telemetry) -> None:
        """Test with nested operations."""
        if telemetry:
            with telemetry.trace_test("parent_operation", "demo"):
                # First child operation
                span1 = telemetry.create_span(
                    "database_query",
                    operation_type="database",
                    attributes={"query": "SELECT * FROM users"},
                )
                time.sleep(0.1)
                if span1:
                    span1.end()

                # Second child operation
                span2 = telemetry.create_span(
                    "cache_lookup",
                    operation_type="cache",
                    attributes={"key": "user_123"},
                )
                time.sleep(0.05)
                if span2:
                    span2.end()

                assert True

    def test_with_api_calls(self, telemetry) -> None:
        """Test that simulates API calls."""
        if telemetry:
            with telemetry.trace_test("api_test", "demo"):
                # Simulate various API calls
                endpoints = ["/users", "/products", "/orders"]
                methods = ["GET", "POST", "PUT"]

                for _i in range(5):
                    endpoint = random.choice(endpoints)
                    method = random.choice(methods)
                    status = random.choice([200, 201, 400, 404, 500])
                    response_time = random.uniform(0.01, 0.5)

                    telemetry.record_api_call(
                        method=method,
                        endpoint=endpoint,
                        status_code=status,
                        response_time=response_time,
                    )

                    time.sleep(0.1)

                assert True

    @pytest.mark.xfail(reason="Intentional failure for demo")
    def test_failing_operation(self, telemetry) -> None:
        """Test that fails to demonstrate error tracking."""
        if telemetry:
            with telemetry.trace_test("failing_operation", "demo"):
                time.sleep(0.1)
                msg = "This is an intentional error for demo purposes"
                raise ValueError(msg)
