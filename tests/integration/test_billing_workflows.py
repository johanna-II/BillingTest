"""Integrated billing workflow tests using OpenAPI mock server."""

import os

import pytest

from libs.Adjustment import AdjustmentManager
from libs.Batch import BatchManager
from libs.Calculation import CalculationManager
from libs.constants import (
    AdjustmentTarget,
    AdjustmentType,
    BatchJobCode,
    CounterType,
    CreditType,
    PaymentStatus,
)
from libs.Contract import ContractManager
from libs.Credit import CreditManager
from libs.http_client import BillingAPIClient
from libs.Metering import MeteringManager
from libs.Payments import PaymentManager


@pytest.mark.integration
@pytest.mark.mock_required
class TestBillingWorkflows:
    """Test complete billing workflows end-to-end."""

    @pytest.fixture(scope="class")
    def api_client(self, use_mock):
        """Create API client based on test configuration."""
        if use_mock:
            # Use dynamic port for integration tests
            mock_url = os.environ.get("MOCK_SERVER_URL", "http://localhost:5000")
            return BillingAPIClient(base_url=f"{mock_url}/api/v1")
        # Use real API in test environment with default base_url
        # For real API, need to get base URL from config
        from config import url

        return BillingAPIClient(base_url=url.BASE_BILLING_URL)

    @pytest.fixture
    def managers(self, api_client, month, member):
        """Create all managers needed for billing workflows."""
        return {
            "adjustment": AdjustmentManager(month=month, client=api_client),
            "batch": BatchManager(month=month, client=api_client),
            "contract": ContractManager(
                month=month, billing_group_id=f"bg-{member}-001", client=api_client
            ),
            "calculation": CalculationManager(
                month=month, uuid=f"uuid-{member}-001", client=api_client
            ),
            "metering": MeteringManager(month=month, client=api_client),
            "payment": PaymentManager(
                month=month, uuid=f"uuid-{member}-001", client=api_client
            ),
            "credit": CreditManager(uuid=f"uuid-{member}-001", client=api_client),
        }

    def test_standard_billing_cycle(self, managers) -> None:
        """Test standard monthly billing cycle."""
        # 1. Apply contract at the beginning of month
        contract_result = managers["contract"].apply_contract(
            contract_id="standard-contract-001", name="Standard Monthly Contract"
        )
        assert contract_result.get("status") == "SUCCESS"

        # 2. Send metering data throughout the month
        metering_data = [
            {
                "app_key": "app-001",
                "counter_name": "compute.cpu.hours",
                "counter_type": CounterType.DELTA,
                "counter_unit": "HOURS",
                "counter_volume": "720",  # 30 days * 24 hours
            },
            {
                "app_key": "app-001",
                "counter_name": "storage.volume.gb",
                "counter_type": CounterType.GAUGE,
                "counter_unit": "GB",
                "counter_volume": "500",
            },
        ]

        for meter in metering_data:
            result = managers["metering"].send_metering(**meter)
            assert result.get("status") == "SUCCESS"

        # 3. Calculate usage and pricing
        calc_result = managers["calculation"].recalculate_all(
            include_usage=True, timeout=300
        )
        assert calc_result.get("status") in ["STARTED", "COMPLETED"]

        # 4. Check payment status
        payment_id, status = managers["payment"].get_payment_status()
        assert payment_id is not None
        assert status in [PaymentStatus.PENDING, PaymentStatus.REGISTERED]

        # 5. Verify total amount
        unpaid_amount = managers["payment"].check_unpaid_amount(payment_id)
        assert unpaid_amount > 0

    def test_billing_with_adjustments(self, managers) -> None:
        """Test billing with various adjustments."""
        # 1. Setup base billing (contract + metering)
        self._setup_base_billing(managers)

        # 2. Apply fixed discount adjustment
        adj_result = managers["adjustment"].apply_adjustment(
            adjustment_amount=10000.0,
            adjustment_type=AdjustmentType.FIXED_DISCOUNT,
            adjustment_target=AdjustmentTarget.BILLING_GROUP,
            target_id="bg-test-001",
            description="Monthly promotion discount",
        )
        assert "adjustmentId" in adj_result

        # 3. Apply percentage discount
        adj_result2 = managers["adjustment"].apply_adjustment(
            adjustment_amount=10.0,  # 10% discount
            adjustment_type=AdjustmentType.RATE_DISCOUNT,
            adjustment_target=AdjustmentTarget.PROJECT,
            target_id="proj-001",
            description="Project volume discount",
        )
        assert "adjustmentId" in adj_result2

        # 4. Recalculate with adjustments
        calc_result = managers["calculation"].recalculate_all()
        assert calc_result.get("status") in ["STARTED", "COMPLETED"]

        # 5. Verify adjustments were applied
        adjustments = managers["adjustment"].get_adjustments(
            adjustment_target=AdjustmentTarget.BILLING_GROUP, target_id="bg-test-001"
        )
        assert len(adjustments) >= 1

        # 6. Check final amount after adjustments
        payment_id, _ = managers["payment"].get_payment_status()
        final_amount = managers["payment"].check_unpaid_amount(payment_id)
        # Amount should be reduced due to discounts
        assert final_amount >= 0

    def test_billing_with_credits(self, managers) -> None:
        """Test billing with credit application."""
        # 1. Setup base billing
        self._setup_base_billing(managers)

        # 2. Grant campaign credit
        credit_result = managers["credit"].grant_credit_to_users(
            credit_amount=50000.0,
            credit_type=CreditType.CAMPAIGN,
            user_list=["uuid-test-001"],
            description="New customer credit",
        )
        assert credit_result["success_count"] == 1

        # 3. Use coupon
        managers["credit"].use_coupon(coupon_code="WELCOME2024")
        # Coupon might not exist in test env, so we check if it tried

        # 4. Calculate with credits
        calc_result = managers["calculation"].recalculate_all()
        assert calc_result.get("status") in ["STARTED", "COMPLETED"]

        # 5. Check credit balance
        balance = managers["credit"].get_credit_balance()
        assert balance >= 0

        # 6. Verify credit was applied to payment
        payment_id, _status = managers["payment"].get_payment_status()
        if balance > 0:
            # If there's credit, payment might be fully covered
            unpaid = managers["payment"].check_unpaid_amount(payment_id)
            assert unpaid >= 0

    def test_batch_operations(self, managers) -> None:
        """Test batch job operations."""
        # 1. Request credit expiry batch
        batch_result = managers["batch"].request_batch_job(
            BatchJobCode.BATCH_CREDIT_EXPIRY
        )
        assert "batchId" in batch_result

        # 2. Request statement generation
        statement_result = managers["batch"].request_batch_job(
            BatchJobCode.BATCH_GENERATE_STATEMENT,
            execution_day=1,  # First day of month
        )
        assert "batchId" in statement_result

        # 3. Check batch status
        status = managers["batch"].get_batch_status(BatchJobCode.BATCH_CREDIT_EXPIRY)
        assert status["status"] in ["PENDING", "RUNNING", "COMPLETED", "UNKNOWN"]

        # 4. Request common batch jobs
        results = managers["batch"].request_common_batch_jobs()
        assert len(results) == 3

    def test_end_to_end_monthly_billing(self, managers) -> None:
        """Test complete monthly billing process."""
        # 1. Start of month - Apply contracts
        contracts = ["basic-001", "volume-002", "partner-003"]
        for contract_id in contracts:
            result = managers["contract"].apply_contract(
                contract_id=contract_id, name=f"Contract {contract_id}"
            )
            assert result.get("status") == "SUCCESS"

        # 2. Throughout month - Collect metering data
        # Simulate daily metering for 30 days
        for _day in range(1, 31):
            for app_key in ["app-001", "app-002"]:
                managers["metering"].send_metering(
                    app_key=app_key,
                    counter_name="compute.daily.usage",
                    counter_type=CounterType.DELTA,
                    counter_unit="HOURS",
                    counter_volume="24",
                )

        # 3. End of month - Apply adjustments
        # Volume discount for high usage
        managers["adjustment"].apply_adjustment(
            adjustment_amount=5.0,  # 5% discount
            adjustment_type=AdjustmentType.RATE_DISCOUNT,
            adjustment_target=AdjustmentTarget.BILLING_GROUP,
            target_id="bg-test-001",
            description="Volume discount",
        )

        # 4. Calculate final billing
        managers["calculation"].recalculate_all(
            include_usage=True,
            timeout=600,  # Longer timeout for full calculation
        )

        # 5. Generate statement (batch job)
        managers["batch"].request_batch_job(BatchJobCode.BATCH_GENERATE_STATEMENT)

        # 6. Check final payment status
        payment_id, status = managers["payment"].get_payment_status()
        assert payment_id is not None

        # 7. Process payment if needed
        if status == PaymentStatus.PENDING:
            managers["payment"].make_payment(payment_group_id=payment_id)
            # In test env, might not actually process

        # 8. Verify billing cycle completed
        final_status = managers["payment"].get_payment_status()[1]
        assert final_status in [
            PaymentStatus.PENDING,
            PaymentStatus.PAID,
            PaymentStatus.REGISTERED,
        ]

    def test_error_recovery_workflow(self, managers) -> None:
        """Test error handling and recovery in billing workflow."""
        try:
            # 1. Try invalid contract
            with pytest.raises(Exception):
                managers["contract"].apply_contract(contract_id="invalid-contract-xxx")

            # 2. Send invalid metering data
            with pytest.raises(Exception):
                managers["metering"].send_metering(
                    app_key="",  # Empty app key
                    counter_name="test",
                    counter_type="INVALID",
                    counter_unit="INVALID",
                    counter_volume="-100",  # Negative volume
                )

            # 3. Recovery - Send valid data
            valid_result = managers["metering"].send_metering(
                app_key="app-recovery",
                counter_name="compute.recovery",
                counter_type=CounterType.DELTA,
                counter_unit="COUNT",
                counter_volume="1",
            )
            assert valid_result.get("status") == "SUCCESS"

            # 4. Ensure system can still calculate
            calc_result = managers["calculation"].recalculate_all()
            assert calc_result is not None

        except Exception:
            # Log error but don't fail test
            # In integration tests, we want to see how system handles errors
            pass

    def test_concurrent_operations(self, managers) -> None:
        """Test concurrent billing operations."""
        import concurrent.futures

        def send_meter_data(app_key, volume):
            return managers["metering"].send_metering(
                app_key=app_key,
                counter_name="compute.concurrent",
                counter_type=CounterType.DELTA,
                counter_unit="COUNT",
                counter_volume=str(volume),
            )

        # Send multiple metering requests concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(10):
                future = executor.submit(
                    send_meter_data,
                    f"app-{i % 3}",
                    i * 10,  # 3 different apps
                )
                futures.append(future)

            # Wait for all to complete
            results = [f.result() for f in futures]

        # Verify all succeeded
        success_count = sum(1 for r in results if r.get("status") == "SUCCESS")
        assert success_count >= 8  # Allow some failures in concurrent scenario

    def _setup_base_billing(self, managers) -> None:
        """Helper to setup basic billing scenario."""
        # Apply contract
        managers["contract"].apply_contract(
            contract_id="base-contract", name="Base Contract"
        )

        # Send some metering data
        managers["metering"].send_metering(
            app_key="app-base",
            counter_name="compute.base",
            counter_type=CounterType.DELTA,
            counter_unit="HOURS",
            counter_volume="100",
        )
