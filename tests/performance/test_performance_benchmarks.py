"""Performance benchmarks for billing system.

This module tests the performance of critical billing operations
and tracks regression over time.
"""

import random
import string
from datetime import datetime

import pytest

from libs.Adjustment import AdjustmentManager
from libs.Calculation import CalculationManager
from libs.constants import AdjustmentTarget, AdjustmentType, CounterType
from libs.Credit import CreditManager
from libs.Metering import MeteringManager


class TestPerformanceBenchmarks:
    """Performance benchmark tests."""

    @pytest.fixture
    def test_data_generator(self):
        """Generate test data for benchmarks."""

        def _generate_app_key():
            return f"APP-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"

        def _generate_campaign_id():
            return f"CAMPAIGN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

        return {
            "app_keys": [_generate_app_key() for _ in range(100)],
            "campaign_ids": [_generate_campaign_id() for _ in range(50)],
            "month": datetime.now().strftime("%Y-%m"),
        }

    @pytest.mark.benchmark(group="metering")
    def test_metering_send_performance(self, benchmark, mock_api_client):
        """Benchmark metering data submission."""
        manager = MeteringManager(month="2024-01", client=mock_api_client)

        def send_metering():
            return manager.send_metering(
                app_key="TEST-APP-001",
                counter_name="compute.instance",
                counter_type=CounterType.DELTA,
                counter_unit="HOURS",
                counter_volume="100",
            )

        result = benchmark(send_metering)
        assert result is not None

    @pytest.mark.benchmark(group="metering")
    def test_batch_metering_performance(
        self, benchmark, mock_api_client, test_data_generator
    ):
        """Benchmark batch metering submission."""
        manager = MeteringManager(month="2024-01", client=mock_api_client)
        app_keys = test_data_generator["app_keys"][:10]

        def send_batch():
            meters = []
            for i, app_key in enumerate(app_keys):
                meters.append(
                    {
                        "counter_name": f"test.meter.{i}",
                        "counter_type": CounterType.DELTA.value,
                        "counter_unit": "UNITS",
                        "counter_volume": str(random.randint(1, 1000)),
                    }
                )
            return manager.send_batch_metering(app_keys[0], meters)

        result = benchmark(send_batch)
        assert result is not None

    @pytest.mark.benchmark(group="adjustment")
    def test_adjustment_apply_performance(self, benchmark, mock_api_client):
        """Benchmark adjustment application."""
        manager = AdjustmentManager(month="2024-01", client=mock_api_client)

        def apply_adjustment():
            return manager.apply_adjustment(
                adjustment_name="Performance Test Discount",
                adjustment_type=AdjustmentType.RATE_DISCOUNT,
                adjustment_amount=10,
                target_type=AdjustmentTarget.PROJECT,
                target_id="PROJ-TEST-001",
            )

        result = benchmark(apply_adjustment)
        assert result is not None

    @pytest.mark.benchmark(group="adjustment")
    def test_bulk_adjustments_performance(
        self, benchmark, mock_api_client, test_data_generator
    ):
        """Benchmark bulk adjustment operations."""
        manager = AdjustmentManager(month="2024-01", client=mock_api_client)
        app_keys = test_data_generator["app_keys"][:20]

        def apply_bulk():
            results = []
            for app_key in app_keys:
                result = manager.apply_adjustment(
                    adjustment_name=f"Bulk Test - {app_key}",
                    adjustment_type=AdjustmentType.FIXED_DISCOUNT,
                    adjustment_amount=1000,
                    target_type=AdjustmentTarget.PROJECT,
                    target_id=app_key,
                )
                results.append(result)
            return results

        results = benchmark(apply_bulk)
        assert len(results) == 20

    @pytest.mark.benchmark(group="credit")
    def test_credit_grant_performance(
        self, benchmark, mock_api_client, test_data_generator
    ):
        """Benchmark credit granting."""
        manager = CreditManager(uuid="TEST-USER-001", client=mock_api_client)
        campaign_id = test_data_generator["campaign_ids"][0]

        def grant_credit():
            return manager.grant_campaign_credit(
                campaign_id=campaign_id,
                credit_name="Performance Test Credit",
                credit_amount=10000,
            )

        result = benchmark(grant_credit)
        assert result is not None

    @pytest.mark.benchmark(group="calculation")
    def test_calculation_performance(self, benchmark, mock_api_client):
        """Benchmark calculation operations."""
        manager = CalculationManager(
            month="2024-01", uuid="TEST-USER-001", client=mock_api_client
        )

        def recalculate():
            return manager.recalculate_all()

        result = benchmark(recalculate)
        assert result is not None

    @pytest.mark.benchmark(group="complex", min_rounds=5)
    def test_full_billing_cycle_performance(self, benchmark, mock_api_client):
        """Benchmark a complete billing cycle."""
        month = "2024-01"
        uuid = "TEST-USER-001"
        app_key = "TEST-APP-001"

        def full_cycle():
            # 1. Send metering data
            metering = MeteringManager(month=month, client=mock_api_client)
            metering.send_metering(
                app_key=app_key,
                counter_name="compute.large",
                counter_type=CounterType.DELTA,
                counter_unit="HOURS",
                counter_volume="720",  # Full month
            )

            # 2. Apply discount
            adjustment = AdjustmentManager(month=month, client=mock_api_client)
            adjustment.apply_adjustment(
                adjustment_name="Monthly Discount",
                adjustment_type=AdjustmentType.RATE_DISCOUNT,
                adjustment_amount=15,
                target_type=AdjustmentTarget.PROJECT,
                target_id=app_key,
            )

            # 3. Grant credit
            credit = CreditManager(uuid=uuid, client=mock_api_client)
            credit.grant_campaign_credit(
                campaign_id="MONTHLY-PROMO",
                credit_name="Monthly Promotion",
                credit_amount=50000,
            )

            # 4. Calculate
            calc = CalculationManager(month=month, uuid=uuid, client=mock_api_client)
            return calc.recalculate_all()

        result = benchmark(full_cycle)
        assert result is not None

    @pytest.mark.benchmark(group="stress")
    @pytest.mark.parametrize("num_operations", [10, 50, 100])
    def test_concurrent_operations_stress(
        self, benchmark, mock_api_client, num_operations
    ):
        """Stress test with multiple concurrent operations."""
        import concurrent.futures

        def single_operation(i):
            manager = MeteringManager(month="2024-01", client=mock_api_client)
            return manager.send_metering(
                app_key=f"APP-{i:04d}",
                counter_name=f"test.stress.{i}",
                counter_type=CounterType.DELTA,
                counter_unit="UNITS",
                counter_volume=str(random.randint(1, 1000)),
            )

        def stress_test():
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(single_operation, i) for i in range(num_operations)
                ]
                return [f.result() for f in concurrent.futures.as_completed(futures)]

        results = benchmark(stress_test)
        assert len(results) == num_operations


@pytest.fixture
def mock_api_client():
    """Create a mock API client for performance tests."""
    from unittest.mock import Mock

    client = Mock()
    # Mock responses for performance testing
    client.post.return_value = {"status": "SUCCESS", "id": "TEST-001"}
    client.get.return_value = {"status": "SUCCESS", "data": []}
    client.put.return_value = {"status": "SUCCESS"}
    client.delete.return_value = {"status": "SUCCESS"}

    return client
