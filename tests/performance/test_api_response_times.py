"""API response time performance tests using pytest-benchmark."""

import os
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

from libs.http_client import BillingAPIClient

# Check if running in parallel mode
PARALLEL_MODE = any(arg.startswith("-n") for arg in sys.argv) or "xdist" in sys.modules


# Create a simple benchmark replacement for parallel mode
class SimpleBenchmark:
    """Simple benchmark replacement for parallel test mode."""

    def __init__(self) -> None:
        self.stats: dict[str, float] = {}

    def __call__(self, func):
        start = time.time()
        result = func()
        self.stats["time"] = time.time() - start
        return result

    def pedantic(self, func, *args, **kwargs):
        return self(func)


# Create a custom decorator for benchmark tests
def pytest_benchmark(**kwargs):
    """Decorator for benchmark tests that handles parallel mode."""
    if PARALLEL_MODE:
        return pytest.mark.skip(reason="Benchmark tests skipped in parallel mode")
    # In non-parallel mode, use the benchmark mark with kwargs
    return pytest.mark.benchmark(**kwargs)


class TestAPIResponseTimes:
    """Test API response time performance."""

    @pytest.fixture
    def benchmark(self):
        """Provide benchmark fixture for parallel mode compatibility."""
        if PARALLEL_MODE:
            return SimpleBenchmark()
        # This will be overridden by pytest-benchmark in non-parallel mode
        return SimpleBenchmark()

    @pytest.fixture
    def api_client(self):
        """Create API client."""
        mock_url = os.environ.get("MOCK_SERVER_URL", "http://localhost:5000")
        return BillingAPIClient(mock_url)

    @pytest.fixture
    def test_uuid(self) -> str:
        """Generate unique test UUID."""
        return f"PERF_{uuid.uuid4().hex[:8]}"

    @pytest.mark.performance
    @pytest_benchmark(group="api-response")
    def test_single_meter_submission(self, benchmark, api_client, test_uuid) -> None:
        """Benchmark single meter submission."""

        def submit_meter():
            headers = {"uuid": test_uuid}
            data = {
                "meterList": [
                    {
                        "counterName": "cpu.usage",
                        "counterType": "DELTA",
                        "counterUnit": "n",
                        "counterVolume": 100,
                        "resourceId": f"resource-{uuid.uuid4().hex[:8]}",
                        "appKey": "PERF-TEST-APP",
                        "targetDate": "2024-01-01",
                    }
                ]
            }
            return api_client.post("/billing/meters", headers=headers, json_data=data)

        # Run benchmark
        result = benchmark(submit_meter)
        assert result is not None

    @pytest.mark.performance
    @pytest_benchmark(group="api-response")
    def test_bulk_meter_submission(self, benchmark, api_client, test_uuid) -> None:
        """Benchmark bulk meter submission."""

        def submit_bulk_meters():
            headers = {"uuid": test_uuid}
            data = {
                "meterList": [
                    {
                        "counterName": f"cpu.usage.{i}",
                        "counterType": "DELTA",
                        "counterUnit": "n",
                        "counterVolume": 100 + i,
                        "resourceId": f"resource-{uuid.uuid4().hex[:8]}",
                    }
                    for i in range(100)  # 100 meters
                ]
            }
            return api_client.post("/billing/meters", headers=headers, json_data=data)

        # Run benchmark
        result = benchmark(submit_bulk_meters)
        assert result is not None

    @pytest.mark.performance
    @pytest_benchmark(group="api-response")
    def test_payment_status_retrieval(self, benchmark, api_client, test_uuid) -> None:
        """Benchmark payment status retrieval."""
        month = "2024-01"

        def get_payment_status():
            headers = {"uuid": test_uuid}
            return api_client.get(f"/billing/payments/{month}/statements", headers=headers)

        # Run benchmark
        result = benchmark(get_payment_status)
        assert result is not None

    @pytest.mark.performance
    @pytest.mark.slow
    def test_concurrent_operations(self, api_client, test_uuid) -> None:
        """Test performance under concurrent load."""
        start_time = time.time()
        successful_requests = 0
        failed_requests = 0

        def make_request(i) -> bool | None:
            """Make a single request."""
            try:
                headers = {"uuid": f"{test_uuid}_{i}"}
                data = {
                    "counterName": f"cpu.usage.{i}",
                    "counterType": "DELTA",
                    "counterUnit": "n",
                    "counterVolume": 100,
                    "resourceId": f"resource-{uuid.uuid4().hex[:8]}",
                }
                api_client.post("/billing/meters", headers=headers, json_data=data)
                return True
            except Exception:
                return False

        # Run 100 concurrent requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request, i) for i in range(100)]

            for future in as_completed(futures):
                if future.result():
                    successful_requests += 1
                else:
                    failed_requests += 1

        elapsed_time = time.time() - start_time

        # Performance assertions
        assert successful_requests >= 95  # At least 95% success rate
        assert elapsed_time < 15.0  # Should complete within 15 seconds

        # Calculate metrics
        requests_per_second = successful_requests / elapsed_time
        elapsed_time_ms = elapsed_time * 1000  # Convert to milliseconds

        # Verify performance metrics
        assert requests_per_second > 6.0  # At least 6 requests per second
        assert elapsed_time_ms < 15000  # Less than 15 seconds in milliseconds

    @pytest.mark.performance
    def test_memory_usage_under_load(self, api_client, test_uuid) -> None:
        """Test memory usage doesn't grow excessively under load."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Submit 1000 meters
        for _i in range(10):
            headers = {"uuid": test_uuid}
            data = {
                "meterList": [
                    {
                        "counterName": f"memory.test.{j}",
                        "counterType": "GAUGE",
                        "counterUnit": "MB",
                        "counterVolume": j,
                        "resourceId": f"resource-{uuid.uuid4().hex[:8]}",
                    }
                    for j in range(100)
                ]
            }
            api_client.post("/billing/meters", headers=headers, json_data=data)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory

        # Memory shouldn't grow by more than 50MB
        assert memory_growth < 50, f"Memory grew by {memory_growth:.2f} MB (> 50 MB limit)"

    @pytest.mark.performance
    @pytest_benchmark(group="batch-operations")
    def test_batch_job_submission(self, benchmark, api_client) -> None:
        """Benchmark batch job submission."""

        def submit_batch_job():
            data = {"month": "2024-01", "jobCode": "API_CALCULATE_USAGE_AND_PRICE"}
            return api_client.post("/batch/jobs", json_data=data)

        # Run benchmark with specific settings
        result = benchmark.pedantic(submit_batch_job, rounds=10, iterations=5, warmup_rounds=2)
        assert result is not None

    @pytest.mark.performance
    def test_response_time_sla(self, api_client, test_uuid) -> None:
        """Verify response times meet SLA requirements."""
        # Realistic SLA for mock server testing
        # In production, these would be stricter
        sla_requirements = {
            "meter_submission": 3000,  # ms (3 seconds for mock)
            "payment_status": 2500,  # ms (2.5 seconds for mock - includes network latency)
            "batch_job": 5000,  # ms (5 seconds for mock)
        }

        results = {}

        # Test meter submission
        headers = {"uuid": test_uuid}
        data = {
            "meterList": [
                {
                    "counterName": "sla.test",
                    "counterVolume": 1,
                    "counterType": "DELTA",
                    "counterUnit": "n",
                    "appKey": "SLA-TEST-APP",
                    "targetDate": "2024-01-01",
                }
            ]
        }

        start = time.time()
        api_client.post("/billing/meters", headers=headers, json_data=data)
        results["meter_submission"] = (time.time() - start) * 1000

        # Test payment status
        start = time.time()
        api_client.get("/billing/payments/2024-01/statements", headers=headers)
        results["payment_status"] = (time.time() - start) * 1000

        # Test batch job
        start = time.time()
        api_client.post(
            "/batch/jobs",
            json_data={"month": "2024-01", "jobCode": "API_CALCULATE_USAGE_AND_PRICE"},
        )
        results["batch_job"] = (time.time() - start) * 1000

        # Check SLAs
        for operation, response_time in results.items():
            sla = sla_requirements[operation]
            assert response_time < sla, f"{operation} took {response_time:.2f}ms (SLA: {sla}ms)"
