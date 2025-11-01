"""Performance tests for payment processing using pytest-benchmark.

For comprehensive load testing, consider using external tools:
- k6 (https://k6.io/) - Modern, JavaScript-based load testing
- Apache JMeter - Enterprise-grade, GUI-based
- wrk - Simple, fast HTTP benchmarking tool

These tests measure single-request performance. For concurrent load testing,
use the tools mentioned above.
"""

import time
import uuid as uuid_module
from datetime import datetime

import pytest
import requests

# Test configuration
BASE_URL = "http://localhost:5000"  # Update with your test server URL
TEST_UUID = f"PERF_TEST_{uuid_module.uuid4().hex[:8]}"
HEADERS = {
    "Accept": "application/json;charset=UTF-8",
    "Content-Type": "application/json",
    "uuid": TEST_UUID,
}
MONTH = datetime.now().strftime("%Y-%m")

# Benchmark configuration to avoid rate limiting (HTTP 429)
BENCHMARK_CONFIG = {
    "min_rounds": 3,  # Reduced from default to avoid rate limiting
    "max_time": 0.5,  # Maximum time in seconds
    "warmup": False,  # Skip warmup to reduce total requests
}


@pytest.fixture(scope="module")
def test_session():
    """Create a requests session for performance tests."""
    session = requests.Session()
    session.headers.update(HEADERS)
    yield session
    # Cleanup
    try:
        session.post(f"{BASE_URL}/test/reset", json={"uuid": TEST_UUID})
    except Exception:
        pass  # Cleanup failures are non-critical
    session.close()


@pytest.mark.performance
@pytest.mark.benchmark(group="metering", **BENCHMARK_CONFIG)
def test_send_metering_data_performance(benchmark, test_session):
    """Benchmark metering data submission."""

    def send_metering():
        metering_data = {
            "meterList": [
                {
                    "counterName": f"cpu.usage.{i}",
                    "counterType": "DELTA",
                    "counterUnit": "n",
                    "counterVolume": 100 + i,
                    "resourceId": f"resource-{uuid_module.uuid4().hex[:8]}",
                    "projectId": "test-project",
                    "serviceName": "compute",
                }
                for i in range(5)  # Send 5 meters at once
            ]
        }
        response = test_session.post(f"{BASE_URL}/billing/meters", json=metering_data)
        assert response.status_code == 200
        time.sleep(0.1)  # Small delay to avoid rate limiting
        return response

    benchmark(send_metering)


@pytest.mark.performance
@pytest.mark.benchmark(group="payments", **BENCHMARK_CONFIG)
def test_get_payment_status_performance(benchmark, test_session):
    """Benchmark payment status retrieval."""

    def get_status():
        response = test_session.get(f"{BASE_URL}/billing/payments/{MONTH}/statements")
        assert response.status_code == 200
        time.sleep(0.1)  # Small delay to avoid rate limiting
        return response

    benchmark(get_status)


@pytest.mark.performance
@pytest.mark.benchmark(group="bulk", **BENCHMARK_CONFIG)
def test_bulk_metering_performance(benchmark, test_session):
    """Benchmark bulk metering data submission (50 meters)."""

    def bulk_send():
        metering_data = {
            "meterList": [
                {
                    "counterName": f"network.bandwidth.{i}",
                    "counterType": "GAUGE",
                    "counterUnit": "MB",
                    "counterVolume": 1024 * (i + 1),
                    "resourceId": f"vm-{uuid_module.uuid4().hex[:8]}",
                    "projectId": f"project-{i % 10}",
                    "serviceName": "network",
                }
                for i in range(50)
            ]
        }
        response = test_session.post(f"{BASE_URL}/billing/meters", json=metering_data)
        assert response.status_code == 200
        time.sleep(0.2)  # Larger delay for bulk operations
        return response

    benchmark(bulk_send)
    # Assert SLA: should complete within 2 seconds
    assert (
        benchmark.stats["mean"] < 2.0
    ), f"Mean response time {benchmark.stats['mean']:.2f}s exceeds 2s SLA"


@pytest.mark.performance
@pytest.mark.benchmark(group="batch", **BENCHMARK_CONFIG)
def test_batch_job_performance(benchmark, test_session):
    """Benchmark batch job submission."""

    def run_batch():
        batch_data = {"month": MONTH, "jobCode": "API_CALCULATE_USAGE_AND_PRICE"}
        response = test_session.post(
            f"{BASE_URL}/batch/jobs",
            json=batch_data,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in [200, 201, 202]
        time.sleep(0.1)  # Small delay to avoid rate limiting
        return response

    benchmark(run_batch)


@pytest.mark.performance
def test_concurrent_requests():
    """Simple concurrent request test (not a benchmark).

    Note: Each thread creates its own session to ensure thread-safety.
    requests.Session is not guaranteed to be thread-safe.
    """
    import concurrent.futures

    def make_request():
        """Make a single request with its own session for thread-safety."""
        # Each thread creates its own session
        session = requests.Session()
        session.headers.update(HEADERS)

        metering_data = {
            "meterList": [
                {
                    "counterName": "test.counter",
                    "counterType": "DELTA",
                    "counterUnit": "n",
                    "counterVolume": 1,
                    "resourceId": f"resource-{uuid_module.uuid4().hex[:8]}",
                    "projectId": "test-project",
                    "serviceName": "test",
                }
            ]
        }

        try:
            response = session.post(f"{BASE_URL}/billing/meters", json=metering_data)
            return response
        finally:
            session.close()

    # Test with 10 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert all(r.status_code == 200 for r in results), "Some requests failed"
    print("✓ Successfully handled 10 concurrent requests")


# Instructions for running these tests:
#
# Run all performance tests:
#   pytest tests/performance/test_payment_performance.py -v
#
# Run with benchmark output:
#   pytest tests/performance/test_payment_performance.py -v --benchmark-only
#
# Save benchmark results:
#   pytest tests/performance/test_payment_performance.py --benchmark-save=baseline
#
# Compare with baseline:
#   pytest tests/performance/test_payment_performance.py --benchmark-compare=baseline
#
# For comprehensive load testing, use k6:
#   k6 run --vus 100 --duration 30s load_test.js
