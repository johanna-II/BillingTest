"""API response time performance tests using pytest-benchmark."""

import pytest
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from libs.http_client import BillingAPIClient
from libs.Payments import PaymentManager
from libs.Metering import MeteringManager
from libs.Batch import BatchManager


class TestAPIResponseTimes:
    """Test API response time performance."""
    
    @pytest.fixture
    def api_client(self):
        """Create API client."""
        base_url = "http://localhost:5000"
        return BillingAPIClient(base_url)
    
    @pytest.fixture
    def test_uuid(self):
        """Generate unique test UUID."""
        return f"PERF_{uuid.uuid4().hex[:8]}"
    
    @pytest.mark.performance
    @pytest.mark.benchmark(group="api-response")
    def test_single_meter_submission(self, benchmark, api_client, test_uuid):
        """Benchmark single meter submission."""
        def submit_meter():
            headers = {"uuid": test_uuid}
            data = {
                "counterName": "cpu.usage",
                "counterType": "DELTA",
                "counterUnit": "n",
                "counterVolume": 100,
                "resourceId": f"resource-{uuid.uuid4().hex[:8]}"
            }
            return api_client.post("/billing/meters", headers=headers, json_data=data)
        
        # Run benchmark
        result = benchmark(submit_meter)
        assert result is not None
    
    @pytest.mark.performance
    @pytest.mark.benchmark(group="api-response")
    def test_bulk_meter_submission(self, benchmark, api_client, test_uuid):
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
                        "resourceId": f"resource-{uuid.uuid4().hex[:8]}"
                    }
                    for i in range(100)  # 100 meters
                ]
            }
            return api_client.post("/billing/meters", headers=headers, json_data=data)
        
        # Run benchmark
        result = benchmark(submit_bulk_meters)
        assert result is not None
    
    @pytest.mark.performance
    @pytest.mark.benchmark(group="api-response")  
    def test_payment_status_retrieval(self, benchmark, api_client, test_uuid):
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
    def test_concurrent_operations(self, api_client, test_uuid):
        """Test performance under concurrent load."""
        start_time = time.time()
        successful_requests = 0
        failed_requests = 0
        
        def make_request(i):
            """Make a single request."""
            try:
                headers = {"uuid": f"{test_uuid}_{i}"}
                data = {
                    "counterName": f"cpu.usage.{i}",
                    "counterType": "DELTA",
                    "counterUnit": "n",
                    "counterVolume": 100,
                    "resourceId": f"resource-{uuid.uuid4().hex[:8]}"
                }
                response = api_client.post("/billing/meters", headers=headers, json_data=data)
                return True
            except Exception as e:
                print(f"Request {i} failed: {e}")
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
        assert elapsed_time < 10.0  # Should complete within 10 seconds
        
        # Calculate metrics
        requests_per_second = successful_requests / elapsed_time
        average_response_time = elapsed_time / 100 * 1000  # ms
        
        print(f"\nConcurrent Test Results:")
        print(f"Total requests: 100")
        print(f"Successful: {successful_requests}")
        print(f"Failed: {failed_requests}")
        print(f"Total time: {elapsed_time:.2f}s")
        print(f"Requests/second: {requests_per_second:.2f}")
        print(f"Avg response time: {average_response_time:.2f}ms")
    
    @pytest.mark.performance
    def test_memory_usage_under_load(self, api_client, test_uuid):
        """Test memory usage doesn't grow excessively under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Submit 1000 meters
        for i in range(10):
            headers = {"uuid": test_uuid}
            data = {
                "meterList": [
                    {
                        "counterName": f"memory.test.{j}",
                        "counterType": "GAUGE",
                        "counterUnit": "MB",
                        "counterVolume": j,
                        "resourceId": f"resource-{uuid.uuid4().hex[:8]}"
                    }
                    for j in range(100)
                ]
            }
            api_client.post("/billing/meters", headers=headers, json_data=data)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        print(f"\nMemory Usage Test:")
        print(f"Initial memory: {initial_memory:.2f} MB")
        print(f"Final memory: {final_memory:.2f} MB")
        print(f"Memory growth: {memory_growth:.2f} MB")
        
        # Memory shouldn't grow by more than 50MB
        assert memory_growth < 50, f"Memory grew by {memory_growth:.2f} MB (> 50 MB limit)"
    
    @pytest.mark.performance
    @pytest.mark.benchmark(group="batch-operations")
    def test_batch_job_submission(self, benchmark, api_client):
        """Benchmark batch job submission."""
        def submit_batch_job():
            data = {
                "month": "2024-01",
                "jobCode": "API_CALCULATE_USAGE_AND_PRICE"
            }
            return api_client.post("/batch/jobs", json_data=data)
        
        # Run benchmark with specific settings
        result = benchmark.pedantic(
            submit_batch_job,
            rounds=10,
            iterations=5,
            warmup_rounds=2
        )
        assert result is not None
    
    @pytest.mark.performance
    def test_response_time_sla(self, api_client, test_uuid):
        """Verify response times meet SLA requirements."""
        sla_requirements = {
            "meter_submission": 200,  # ms
            "payment_status": 100,    # ms
            "batch_job": 500,         # ms
        }
        
        results = {}
        
        # Test meter submission
        headers = {"uuid": test_uuid}
        data = {"counterName": "sla.test", "counterVolume": 1}
        
        start = time.time()
        api_client.post("/billing/meters", headers=headers, json_data=data)
        results["meter_submission"] = (time.time() - start) * 1000
        
        # Test payment status
        start = time.time()
        api_client.get("/billing/payments/2024-01/statements", headers=headers)
        results["payment_status"] = (time.time() - start) * 1000
        
        # Test batch job
        start = time.time()
        api_client.post("/batch/jobs", json_data={"month": "2024-01", "jobCode": "API_CALCULATE_USAGE_AND_PRICE"})
        results["batch_job"] = (time.time() - start) * 1000
        
        # Check SLAs
        for operation, response_time in results.items():
            sla = sla_requirements[operation]
            assert response_time < sla, f"{operation} took {response_time:.2f}ms (SLA: {sla}ms)"
            print(f"{operation}: {response_time:.2f}ms (SLA: {sla}ms) ✓")
