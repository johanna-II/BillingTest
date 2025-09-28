"""Performance tests for payment processing using locust."""

import sys

import pytest

# Skip locust tests in parallel mode to avoid gevent conflicts
PARALLEL_MODE = any(arg.startswith("-n") for arg in sys.argv) or "xdist" in sys.modules
if PARALLEL_MODE:
    pytest.skip(
        "Skipping locust tests in parallel mode due to gevent conflict",
        allow_module_level=True,
    )

import time

try:
    from locust import HttpUser, between, task
except ImportError:
    # Mock locust for parallel test mode
    class HttpUser:  # type: ignore[no-redef]
        pass

    def task(f):  # type: ignore[no-redef]
        return f

    def between(a, b):
        return lambda: a


import uuid as uuid_module
from datetime import datetime


class BillingAPIUser(HttpUser):
    """Simulates a billing API user for load testing."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self) -> None:
        """Initialize user session."""
        self.test_uuid = f"PERF_TEST_{uuid_module.uuid4().hex[:8]}"
        self.headers = {
            "Accept": "application/json;charset=UTF-8",
            "Content-Type": "application/json",
            "uuid": self.test_uuid,
        }
        self.month = datetime.now().strftime("%Y-%m")
        self.payment_group_id: str | None = None

    def on_stop(self) -> None:
        """Clean up user session."""
        # Reset test data
        self.client.post("/test/reset", json={"uuid": self.test_uuid}, headers=self.headers)

    @task(3)
    def send_metering_data(self) -> None:
        """Send metering data - most frequent operation."""
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

        with self.client.post(
            "/billing/meters",
            json=metering_data,
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Got status code {response.status_code}")
            else:
                response.success()

    @task(2)
    def get_payment_status(self) -> None:
        """Check payment status."""
        with self.client.get(
            f"/billing/payments/{self.month}/statements",
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                statements = data.get("statements", [])
                if statements:
                    self.payment_group_id = statements[0].get("paymentGroupId")
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def make_payment(self) -> None:
        """Make a payment if payment group exists."""
        if not self.payment_group_id:
            return

        payment_data = {"paymentGroupId": self.payment_group_id}

        with self.client.post(
            f"/billing/payments/{self.month}",
            json=payment_data,
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def run_batch_job(self) -> None:
        """Request a batch job."""
        batch_data = {"month": self.month, "jobCode": "API_CALCULATE_USAGE_AND_PRICE"}

        with self.client.post(
            "/batch/jobs",
            json=batch_data,
            headers={"Content-Type": "application/json"},
            catch_response=True,
        ) as response:
            if response.status_code in [200, 201, 202]:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")


class HighVolumeUser(HttpUser):
    """Simulates high-volume metering data submission."""

    wait_time = between(0.5, 1)  # More aggressive timing

    def on_start(self) -> None:
        """Initialize user session."""
        self.test_uuid = f"VOLUME_TEST_{uuid_module.uuid4().hex[:8]}"
        self.headers = {
            "Accept": "application/json;charset=UTF-8",
            "Content-Type": "application/json",
            "uuid": self.test_uuid,
        }

    @task
    def bulk_metering_submission(self) -> None:
        """Submit large batches of metering data."""
        # Create 50 meters in one request
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

        start_time = time.time()

        with self.client.post(
            "/billing/meters",
            json=metering_data,
            headers=self.headers,
            catch_response=True,
        ) as response:
            response_time = time.time() - start_time

            if response.status_code != 200:
                response.failure(f"Got status code {response.status_code}")
            elif response_time > 2.0:  # Fail if takes more than 2 seconds
                response.failure(f"Response took {response_time:.2f}s (> 2s SLA)")
            else:
                response.success()


if __name__ == "__main__":
    # Example command to run:
    # locust -f test_payment_performance.py --host=http://localhost:5000 --users=100 --spawn-rate=10
    pass
